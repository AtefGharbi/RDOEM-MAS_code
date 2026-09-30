"""Test-system construction for RDOEM-MAS experiments.

Builds a multi-agent energy system from a MATPOWER/PYPOWER IEEE case:
  * generator agents take their quadratic cost data and limits from the case;
  * load agents are created at every bus with positive demand;
  * renewable (solar / wind) and battery agents are added at seeded buses;
  * the communication graph is derived from the electrical topology by
    contracting agent-free buses (communication and electrical graphs are
    distinct objects; only the neighbourhood structure is borrowed).

All profiles and forecast errors are SYNTHETIC (seeded). No external data
set is used; see README for how to substitute measured profiles.
"""
from dataclasses import dataclass, field
import numpy as np
import networkx as nx
from pypower.api import case30, case57, case118

CASES = {"ieee30": case30, "ieee57": case57, "ieee118": case118}

GEN, REN, LOAD, BATT = 0, 1, 2, 3
TYPE_NAMES = {GEN: "gen", REN: "ren", LOAD: "load", BATT: "batt"}


@dataclass
class System:
    name: str
    N: int
    types: np.ndarray            # agent type codes
    bus: np.ndarray              # electrical bus of each agent
    # generators (indexed by position in gen list)
    gi: np.ndarray               # agent indices of generators
    a: np.ndarray                # quadratic coefficient: C = 1/2 a P^2 + b P
    b: np.ndarray
    pmin: np.ndarray
    pmax: np.ndarray
    c_up: np.ndarray             # recourse up-regulation price
    c_dn: np.ndarray             # recourse down-regulation price
    kappa: np.ndarray            # fixed participation factors (sum to 1)
    # renewables
    ri: np.ndarray
    ren_cap: np.ndarray
    ren_is_solar: np.ndarray
    a_R: float
    b_R: float
    # loads
    li: np.ndarray
    load_share: np.ndarray       # share of system demand at each load
    elasticity: float
    flex_lo: float
    flex_hi: float
    # batteries
    bi: np.ndarray
    b_pmax: np.ndarray
    b_emax: np.ndarray
    eta_c: float
    eta_d: float
    kappa_deg: np.ndarray
    # system scalars
    lam_ref: float
    peak_load: float
    loss_frac: float
    c_shed: float
    c_spill: float
    c_short: float
    # communication graph
    edges: np.ndarray            # (E,2) undirected edges i<j
    adj: np.ndarray              # (N,N) bool adjacency
    profiles: dict = field(default_factory=dict)


def _daily_load_shape(T=24):
    h = np.arange(T)
    shape = 0.62 + 0.18 * np.exp(-((h - 9.0) / 2.5) ** 2) + 0.30 * np.exp(-((h - 19.0) / 2.8) ** 2)
    return shape / shape.max()


def _solar_shape(T=24):
    h = np.arange(T)
    s = np.clip(np.sin(np.pi * (h - 6.0) / 13.0), 0, None)
    return s


def build_system(case="ieee30", seed=0, ren_frac=0.30, n_batt=None, peak_util=0.80,
                 elasticity=0.2, flex=(0.90, 1.05), loss_frac=0.02, with_storage=True, n_extra=2):
    """Construct agents, parameters and communication graph.

    peak_util: system demand is scaled so that the peak hour's forecast
    demand equals peak_util * (sum of generator Pmax). This makes headroom
    (and hence risk) matter at peak hours.
    """
    rng = np.random.default_rng(10_000 + seed)
    c = CASES[case]()
    busnum = c["bus"][:, 0].astype(int)
    bus_idx = {b: k for k, b in enumerate(busnum)}
    Pd = c["bus"][:, 2].copy()
    gen = c["gen"]
    gc = c["gencost"]
    online = gen[:, 7] > 0
    gen, gc = gen[online], gc[online]
    ng = len(gen)
    a = 2.0 * gc[:, 4]              # PYPOWER cost c2 P^2 + c1 P -> a = 2 c2
    b = gc[:, 5].copy()
    pmax = gen[:, 8].copy()
    pmin = gen[:, 9].copy()
    a = np.maximum(a, 1e-3)
    peak_load = peak_util * pmax.sum()

    load_buses = np.where(Pd > 0)[0]
    load_share = Pd[load_buses] / Pd[load_buses].sum()

    nb = len(busnum)
    n_R = max(2, int(round(nb / 8)))
    if n_batt is None:
        n_batt = max(2, int(round(nb / 15)))
    if not with_storage:
        n_batt = 0
    ren_buses = rng.choice(nb, n_R, replace=False)
    batt_buses = rng.choice(nb, n_batt, replace=False) if n_batt > 0 else np.array([], int)
    ren_is_solar = np.arange(n_R) % 2 == 0
    ren_cap_total = ren_frac * peak_load / 0.55     # capacity so average contribution ~ ren_frac of peak
    w = rng.uniform(0.6, 1.4, n_R)
    ren_cap = ren_cap_total * w / w.sum()

    types = np.concatenate([np.full(ng, GEN), np.full(n_R, REN), np.full(len(load_buses), LOAD),
                            np.full(n_batt, BATT)])
    agent_bus = np.concatenate([np.array([bus_idx[int(x)] for x in gen[:, 0]]), ren_buses, load_buses,
                                batt_buses]).astype(int)
    N = len(types)
    gi = np.where(types == GEN)[0]
    ri = np.where(types == REN)[0]
    li = np.where(types == LOAD)[0]
    bi = np.where(types == BATT)[0]

    # reference price: risk-neutral marginal cost at 70 % of peak net demand
    target = 0.7 * peak_load
    lo, hi = 0.0, 1e4
    for _ in range(100):
        lam = 0.5 * (lo + hi)
        if np.clip((lam - b) / a, pmin, pmax).sum() > target:
            hi = lam
        else:
            lo = lam
    lam_ref = 0.5 * (lo + hi)

    c_up = 1.15 * np.maximum(b, 0.0) + 0.25 * lam_ref
    c_dn = 0.10 * np.maximum(b, 0.0) + 0.05 * lam_ref
    kappa = pmax / pmax.sum()

    b_pmax = np.full(n_batt, 0.25 * peak_load / max(n_batt, 1)) if n_batt else np.zeros(0)
    b_emax = 4.0 * b_pmax
    # degradation C = kappa (pc^2 + pd^2): full power reached at a price deviation of 0.3 lam_ref
    kappa_deg = 0.3 * lam_ref / (2 * b_pmax) if n_batt else np.zeros(0)

    # ---------- communication graph: contract agent-free buses -------------
    G = nx.Graph()
    G.add_nodes_from(range(nb))
    for br in c["branch"]:
        if br[10] > 0:
            G.add_edge(bus_idx[int(br[0])], bus_idx[int(br[1])])
    agents_at = {k: [] for k in range(nb)}
    for i, bb in enumerate(agent_bus):
        agents_at[int(bb)].append(i)
    adj = np.zeros((N, N), bool)
    for bb in range(nb):                       # clique among agents at the same bus
        ids = agents_at[bb]
        for p in ids:
            for q in ids:
                if p != q:
                    adj[p, q] = True
    for bb in range(nb):                       # BFS through agent-free buses
        if not agents_at[bb]:
            continue
        seen, frontier, reach = {bb}, [bb], set()
        while frontier:
            nxt = []
            for u in frontier:
                for v in G.neighbors(u):
                    if v in seen:
                        continue
                    seen.add(v)
                    if agents_at[v]:
                        reach.add(v)
                    else:
                        nxt.append(v)
            frontier = nxt
        for v in reach:
            # one representative link per bus pair keeps degrees moderate
            p = agents_at[bb][0]
            q = agents_at[v][0]
            adj[p, q] = adj[q, p] = True
    # ensure connectivity (should already hold for the IEEE cases)
    Ga = nx.from_numpy_array(adj.astype(int))
    comps = list(nx.connected_components(Ga))
    for c1, c2 in zip(comps[:-1], comps[1:]):
        p, q = min(c1), min(c2)
        adj[p, q] = adj[q, p] = True
    # long-range overlay: each agent adds n_extra seeded random links (communication
    # overlay is distinct from the electrical topology; improves mixing)
    for i in range(N):
        cand = np.where(~adj[i])[0]
        cand = cand[cand != i]
        if n_extra and len(cand):
            for q in rng.choice(cand, min(n_extra, len(cand)), replace=False):
                adj[i, q] = adj[q, i] = True
    iu = np.triu_indices(N, 1)
    edges = np.array([(i, j) for i, j in zip(*iu) if adj[i, j]])

    return System(name=case, N=N, types=types, bus=agent_bus, gi=gi, a=a, b=b, pmin=pmin, pmax=pmax,
                  c_up=c_up, c_dn=c_dn, kappa=kappa, ri=ri, ren_cap=ren_cap, ren_is_solar=ren_is_solar,
                  a_R=float(np.median(a)), b_R=0.02 * lam_ref, li=li, load_share=load_share,
                  elasticity=elasticity, flex_lo=flex[0], flex_hi=flex[1], bi=bi, b_pmax=b_pmax,
                  b_emax=b_emax, eta_c=0.95, eta_d=0.95, kappa_deg=kappa_deg, lam_ref=lam_ref,
                  peak_load=peak_load, loss_frac=loss_frac, c_shed=30.0 * lam_ref, c_spill=2.0 * lam_ref,
                  c_short=3.0 * lam_ref, edges=edges, adj=adj)


@dataclass
class DayData:
    """Forecasts and scenario sets for one simulated day (T epochs)."""
    T: int
    load_fc: np.ndarray      # (T, nL) forecast demand per load
    ren_fc: np.ndarray       # (T, nR) forecast availability per renewable
    eps: np.ndarray          # (T, M) aggregate load-forecast error per scenario (MW, + = more demand)
    ren_avail: np.ndarray    # (T, M, nR) scenario availability
    pi: np.ndarray           # (M,) scenario probabilities
    refine: np.ndarray       # (T, 2, nL+nR) within-epoch forecast refinements (multiplicative)
    oos_eps: np.ndarray      # (T, S) out-of-sample aggregate load error
    oos_ren: np.ndarray      # (T, S, nR) out-of-sample availability


def build_day(sys: System, seed=0, T=24, M=30, S_oos=500, load_err=0.03, ren_err=0.18):
    """Synthetic forecasts and scenario sets (seeded).

    Load error: Gaussian, aggregate sd = load_err * demand.
    Renewable error: multiplicative, sd = ren_err, truncated to [0, capacity],
    with a common component (correlation ~0.6) to create a heavier tail.
    """
    rng = np.random.default_rng(seed)
    nL, nR = len(sys.li), len(sys.ri)
    shape = _daily_load_shape(T) * (1 + 0.02 * rng.standard_normal(T))
    demand = sys.peak_load * shape
    load_fc = demand[:, None] * sys.load_share[None, :] * (1 + 0.03 * rng.standard_normal((T, nL)))
    solar = _solar_shape(T)
    wind = np.clip(0.45 + 0.25 * np.cumsum(0.25 * rng.standard_normal(T)) / np.sqrt(T), 0.05, 0.95)
    ren_fc = np.where(sys.ren_is_solar[None, :], solar[:, None], wind[:, None]) * sys.ren_cap[None, :]
    ren_fc *= np.clip(1 + 0.05 * rng.standard_normal((T, nR)), 0.5, 1.5)

    def draw(Mn):
        common = rng.standard_normal((T, Mn, 1))
        idio = rng.standard_normal((T, Mn, nR))
        z = 0.77 * common + 0.64 * idio
        av = ren_fc[:, None, :] * (1 + ren_err * z)
        av = np.clip(av, 0, sys.ren_cap[None, None, :])
        e = load_err * demand[:, None] * rng.standard_normal((T, Mn))
        return e, av

    eps, ren_avail = draw(M)
    oos_eps, oos_ren = draw(S_oos)
    pi = np.full(M, 1.0 / M)
    refine = 1 + 0.01 * rng.standard_normal((T, 2, nL + nR))
    return DayData(T=T, load_fc=load_fc, ren_fc=ren_fc, eps=eps, ren_avail=ren_avail, pi=pi,
                   refine=refine, oos_eps=oos_eps, oos_ren=oos_ren)

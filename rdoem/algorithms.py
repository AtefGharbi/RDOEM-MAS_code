"""RDOEM-MAS distributed negotiation (Algorithm 1 of the paper) and baselines.

Per synchronous round k of epoch t (all agents share W_k):
  1. links fail independently with prob. p_loss (symmetric, per edge);
  2. TARC: score fresh reports, update raw trust and counters, mutual-min
     handshake, retain edges, build symmetric doubly stochastic W_k;
  3. price:   lam^{k+1} = Proj[ W_k lam^k - eta_k x^k ];
  4. local best responses at lam^{k+1} with CVaR tail weights from (Qhat, zeta);
  5. trackers: x^{k+1} = W_k x^k + N (u^{k+1}-u^k);  Qhat likewise per scenario;
  6. quantile: zeta_i = local weighted VaR of Qhat_i (default) or the
     consensus-subgradient rule of Section IV-D.
Attacks corrupt the price/mismatch payloads sent by compromised agents.
"""
from dataclasses import dataclass, field
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
from .model import (Epoch, local_response, tracker_input, local_q, tail_weights, var_cvar, evaluate,
                    out_of_sample, kkt_residual)
from .centralized import solve_central


@dataclass
class TarcParams:
    rho_mem: float = 0.8      # trust memory
    gamma: float = 1.0        # score-to-trust sensitivity
    omega1: float = 0.5       # weight of price-innovation term
    omega2: float = 0.5       # weight of mismatch-consistency term
    a_max: float = 10.0       # score clip
    c_sigma: float = 3.0      # scale multiplier (dead zone at r <= 1)
    L: int = 20               # history window
    L_min: int = 5            # adequate-history threshold
    rho_min: float = 0.3      # retention threshold
    rho_edge: float = 0.9     # counter discount base
    tau_max: int = 5          # counter removal threshold
    sig_floor_lam: float = 0.005   # x lam_ref
    sig_floor_x: float = 0.002     # x peak_load
    c_clip: float = 5.0       # winsorisation of history updates
    score: str = "v15"        # 'v15': innovation + mismatch consistency; 'R': adds price consistency
    omega3: float = 0.5       # weight of cross-sectional price-consistency term (score 'R')
    a_flag: float = 1.0       # score 'R': scale history accepts only reports with score <= a_flag
    grace: int = 0            # rounds after each epoch boundary with frozen trust (no scoring/history)


@dataclass
class Config:
    method: str = "rdoem"          # 'rdoem' | 'static'
    weights: str = "tarc"          # 'tarc' | 'metropolis' | 'wmsr'  (rdoem only)
    regimes: tuple = ("S", "C")    # recourse models used for evaluation / central benchmark
    beta: float = 1.0
    alpha: float = 0.9
    K: int = 300                   # communication-round budget per epoch
    eta_c: float = 2.0             # eta0 = eta_c (1-sigma2)/(N max slope)
    k0: float = 100.0
    nu: float = 0.6
    p_loss: float = 0.0
    lam_min_f: float = 0.0         # x lam_ref
    lam_max_f: float = 5.0
    warm_start: bool = True
    reanchor: bool = False         # re-initialise trackers x=N u, Qhat=N q at each epoch boundary
    quantile_rule: str = "local_sort"   # or 'consensus_subgradient'
    global_cost_tracker: bool = True
    refine: bool = False
    attack: dict = None            # dict(type, f_att, e0, e1, ...)
    f_W: int = 1
    tarc: TarcParams = field(default_factory=TarcParams)
    central: bool = True
    kkt: bool = True
    record_traj: bool = False
    record_mats: bool = False      # store (W_k, lam_k, lam_{k+1}) for the Proposition-4 check
    ckpt_every: int = 0            # >0: record (messages, welfare gap, |dP|) every ckpt_every rounds
    k_omega: float = 1.0           # tail-weight averaging: rho_k = 1/(1 + k/k_omega); 0 disables
    tol_f: float = 1e-2            # tolerances as fractions of peak_load / lam_ref
    hold: int = 5
    static_inner_max: int = 2000
    static_outer_max: int = 300
    epochs: tuple = None           # subset of epochs to simulate (None = all)


def response_slopes(sys, ep):
    """Local price-response slopes |du_i/dlam| (MW per $/MWh) of the risk-neutral responses."""
    sl = np.zeros(sys.N)
    sl[sys.gi] = 1 / sys.a
    sl[sys.ri] = 1 / sys.a_R
    sl[sys.li] = 1 / ep.psi
    if len(sys.bi):
        sl[sys.bi] = 1 / (2 * sys.kappa_deg)
    return sl


def nominal_gap(sys):
    W = build_W(sys.N, sys.edges, np.ones(len(sys.edges), bool))
    ev = np.sort(np.abs(np.linalg.eigvalsh(W)))[::-1]
    return 1 - ev[1]


def step_size(sys, ep, c_eta):
    """Declared selection rule: eta0 = c_eta (1 - sigma_2) / (N * max_i slope_i),
    with sigma_2 the second-largest |eigenvalue| of the nominal weight matrix (offline constant)."""
    if not hasattr(sys, "_gap"):
        sys._gap = nominal_gap(sys)
    return c_eta * sys._gap / (sys.N * response_slopes(sys, ep).max())


def dual_lipschitz(sys, ep):
    L = (1 / sys.a).sum() + len(sys.ri) / sys.a_R + (1 / ep.psi).sum()
    if len(sys.bi):
        L += (1 / (2 * sys.kappa_deg)).sum()
    return L


class Attack:
    def __init__(self, spec, sys, rng, N):
        self.spec = spec or {}
        self.on = bool(spec) and spec.get("f_att", 0) > 0
        self.A = np.zeros(N, bool)
        if self.on:
            idx = rng.choice(N, spec["f_att"], replace=False)
            self.A[idx] = True
        self.lam_ref, self.peak = sys.lam_ref, sys.peak_load
        self.k_att = 0
        self.rng = rng

    def active(self, t):
        return self.on and self.spec["e0"] <= t < self.spec["e1"]

    def corrupt(self, t, lam, x):
        if not self.active(t):
            return lam, x
        sp, A = self.spec, self.A
        lr, xr = lam.copy(), x.copy()
        typ = sp["type"]
        if typ == "ATT-1":
            lr[A] += sp.get("b_lam", 0.3) * self.lam_ref
            xr[A] += sp.get("b_x", 0.05) * self.peak
        elif typ == "ATT-2":
            s = sp.get("s", 0.5)
            lr[A] *= (1 + s)
            xr[A] = x[A] * (1 + s) + np.sign(x[A] + 1e-12) * 0.0
        elif typ == "ATT-3":
            g = min(self.k_att * sp.get("g", 1.5e-3), sp.get("cap", 0.15))
            lr[A] += g * self.lam_ref * 2
            xr[A] += g * self.peak
        elif typ == "ATT-4":
            hit = self.rng.random(A.sum()) < sp.get("duty", 0.1)
            sgn = self.rng.choice([-1.0, 1.0], A.sum())
            lr[A] += hit * sgn * sp.get("amp_lam", 0.02) * self.lam_ref
            xr[A] += hit * sgn * sp.get("amp_x", 0.004) * self.peak
        self.k_att += 1
        return lr, xr


def _fast_nanmedian(H):
    S = np.sort(H, axis=1)                      # NaNs sort to the end
    n = (~np.isnan(H)).sum(1)
    r = np.arange(len(H))
    lo = S[r, np.maximum((n - 1) // 2, 0)]
    hi = S[r, np.maximum(n // 2, 0)]
    med = 0.5 * (lo + np.where(n > 0, hi, 0))
    return np.where(n > 0, np.nan_to_num(med), 0.0)


class Tarc:
    """Vectorised TARC state over directed pairs (receiver i, sender j)."""

    def __init__(self, sys, P: TarcParams, compromised):
        E = sys.edges
        self.i = np.concatenate([E[:, 0], E[:, 1]])     # receiver
        self.j = np.concatenate([E[:, 1], E[:, 0]])     # sender
        self.nE = len(E)
        self.P = P
        n2 = 2 * self.nE
        self.rho = np.ones(n2)
        self.cnt = np.zeros(n2, int)
        self.hl = np.full((n2, P.L), np.nan)
        self.hx = np.full((n2, P.L), np.nan)
        self.hp = np.full((n2, P.L), np.nan)
        self.ptr = np.zeros(n2, int)
        self.nh = np.zeros(n2, int)
        self.last_lam = np.full(n2, np.nan)
        self.fl = P.sig_floor_lam * sys.lam_ref
        self.fx = P.sig_floor_x * sys.peak_load
        self.recv_comp = compromised[self.i]
        self.score = np.zeros(n2)

    def step(self, active_e, rep_lam, rep_x, x_true, lam_true=None, frozen=False):
        P = self.P
        act = np.concatenate([active_e, active_e])
        if frozen:
            # grace window: keep trust and counters; only track last reports
            self.last_lam = np.where(act, rep_lam[self.j], self.last_lam)
            n = self.nE
            rho_rep = np.where(self.recv_comp, 1.0, self.rho)
            rho_eff = np.minimum(rho_rep[:n], rho_rep[n:])
            self.score = np.zeros_like(self.rho)
            return active_e & (rho_eff >= P.rho_min), rho_eff
        dev_l = np.abs(rep_lam[self.j] - self.last_lam)
        dev_x = np.abs(rep_x[self.j] - x_true[self.i])
        dev_p = np.abs(rep_lam[self.j] - lam_true[self.i]) if lam_true is not None else np.zeros_like(dev_x)
        have = self.nh >= P.L_min
        med_l = _fast_nanmedian(self.hl)
        med_x = _fast_nanmedian(self.hx)
        med_p = _fast_nanmedian(self.hp)
        sl = P.c_sigma * med_l + self.fl
        sx = P.c_sigma * med_x + self.fx
        rl = np.nan_to_num(dev_l / sl)
        rx = dev_x / sx
        if P.score == "R":
            rp = dev_p / (P.c_sigma * med_p + self.fl)
            w1, w2, w3 = (1 - P.omega3) * P.omega1, (1 - P.omega3) * P.omega2, P.omega3
            a = w1 * np.maximum(rl - 1, 0) + w2 * np.maximum(rx - 1, 0) + w3 * np.maximum(rp - 1, 0)
        else:
            a = P.omega1 * np.maximum(rl - 1, 0) + P.omega2 * np.maximum(rx - 1, 0)
        a = np.clip(a, 0, P.a_max)
        upd = act & have
        self.rho = np.where(upd, P.rho_mem * self.rho + (1 - P.rho_mem) * np.exp(-P.gamma * a), self.rho)
        self.score = np.where(upd, a, 0.0)
        # history (winsorised)
        push = act & ~np.isnan(dev_l)
        if P.score == "R":
            push = push & ((a <= P.a_flag) | ~have)
        cl = np.where(have, np.minimum(dev_l, P.c_clip * np.maximum(med_l, self.fl)), dev_l)
        cx = np.where(have, np.minimum(dev_x, P.c_clip * np.maximum(med_x, self.fx)), dev_x)
        cp_ = np.where(have, np.minimum(dev_p, P.c_clip * np.maximum(med_p, self.fl)), dev_p)
        rows = np.where(push)[0]
        self.hl[rows, self.ptr[rows]] = cl[rows]
        self.hx[rows, self.ptr[rows]] = cx[rows]
        self.hp[rows, self.ptr[rows]] = cp_[rows]
        self.ptr[rows] = (self.ptr[rows] + 1) % P.L
        self.nh[rows] += 1
        self.last_lam = np.where(act, rep_lam[self.j], self.last_lam)
        cnt_prev = self.cnt.copy()
        self.cnt = np.where(act, np.where(have, 0, self.cnt), self.cnt + 1)
        # handshake: compromised receivers report full trust (mutual-min neutralises inflation)
        rho_rep = np.where(self.recv_comp, 1.0, self.rho)
        n = self.nE
        m_sh = np.maximum(cnt_prev[:n], cnt_prev[n:])
        rho_eff = P.rho_edge ** m_sh * np.minimum(rho_rep[:n], rho_rep[n:])
        keep = active_e & (rho_eff >= P.rho_min) & (m_sh < P.tau_max)
        return keep, rho_eff


def build_W(N, edges, keep, w_trust=None):
    """Symmetric doubly stochastic W from retained edges (rule (4))."""
    e = edges[keep]
    deg = np.bincount(e.ravel(), minlength=N) if len(e) else np.zeros(N, int)
    w = np.minimum(1.0 / (deg[e[:, 0]] + 1), 1.0 / (deg[e[:, 1]] + 1))
    if w_trust is not None:
        w = w * w_trust[keep]
    W = np.zeros((N, N))
    W[e[:, 0], e[:, 1]] = w
    W[e[:, 1], e[:, 0]] = w
    W[np.arange(N), np.arange(N)] = 1 - W.sum(1)
    return W


def mix(W, v_true, v_rep):
    """Consensus step where neighbours see reported values but agent i uses its own true value."""
    d = np.diag(W)
    if v_true.ndim == 1:
        return W @ v_rep + d * (v_true - v_rep)
    return W @ v_rep + d[:, None] * (v_true - v_rep)


class WMSR:
    def __init__(self, sys, f):
        N = sys.N
        nb = [[] for _ in range(N)]
        eidx = [[] for _ in range(N)]
        for e, (i, j) in enumerate(sys.edges):
            nb[i].append(j); eidx[i].append(e)
            nb[j].append(i); eidx[j].append(e)
        dmax = max(len(x) for x in nb)
        self.nbr = np.full((N, dmax), -1)
        self.eid = np.full((N, dmax), -1)
        for i in range(N):
            self.nbr[i, :len(nb[i])] = nb[i]
            self.eid[i, :len(nb[i])] = eidx[i]
        self.f = f

    def agg(self, v_true, v_rep, active_e):
        valid = (self.nbr >= 0) & np.where(self.eid >= 0, active_e[np.maximum(self.eid, 0)], False)
        V = np.where(valid, v_rep[np.maximum(self.nbr, 0)], np.nan)
        own = v_true[:, None]
        big = valid & (V > own)
        small = valid & (V < own)
        # rank among larger values (descending) / smaller values (ascending)
        Vb = np.where(big, V, -np.inf)
        rb = np.argsort(np.argsort(-Vb, axis=1), axis=1)
        Vs = np.where(small, V, np.inf)
        rs = np.argsort(np.argsort(Vs, axis=1), axis=1)
        drop = (big & (rb < self.f)) | (small & (rs < self.f))
        keep = valid & ~drop
        s = np.where(keep, V, 0).sum(1) + v_true
        return s / (keep.sum(1) + 1)


def _metropolis_keep(active_e):
    return active_e


def run_day(sys, day, cfg: Config, seed=0, rng=None):
    rng = np.random.default_rng(seed + 777) if rng is None else rng
    N = sys.N
    T = day.T
    epochs = range(T) if cfg.epochs is None else cfg.epochs
    lam_ref, peak = sys.lam_ref, sys.peak_load
    lmin, lmax = cfg.lam_min_f * lam_ref, cfg.lam_max_f * lam_ref
    eps_P = cfg.tol_f * peak
    eps_l = cfg.tol_f * lam_ref
    att = Attack(cfg.attack, sys, np.random.default_rng(seed + 991), N)
    honest = ~att.A
    tarc = Tarc(sys, cfg.tarc, att.A) if cfg.weights == "tarc" else None
    wmsr = WMSR(sys, cfg.f_W) if cfg.weights == "wmsr" else None
    E = sys.edges
    nE = len(E)
    M = day.eps.shape[1]
    soc = 0.5 * sys.b_emax
    Q_ref = 0.05 * lam_ref * peak
    records, traj = [], []

    # ---- day-start initialisation (Section V-D, Init) ----
    ep = Epoch(sys, day, epochs[0], soc)
    lam = np.full(N, lam_ref)
    omega = np.tile(ep.pi, (N, 1))                  # risk-neutral expectation weights before any estimate
    dec = local_response(ep, lam, omega, cfg.beta)
    u = tracker_input(ep, dec)
    q = local_q(ep, dec)
    x = N * u
    Qh = N * q if cfg.global_cost_tracker else q.copy()
    zeta = var_cvar(Qh, ep.pi, cfg.alpha)[0]

    for t in epochs:
        ep = Epoch(sys, day, t, soc, refine_stage=None)
        ckref = None
        if cfg.ckpt_every:
            _cd = solve_central(ep, cfg.beta, cfg.alpha, "S")
            _ce = evaluate(ep, _cd, cfg.beta, cfg.alpha, "S")
            ckref = (_ce["SW"], _ce["gen_cost"])
        if cfg.method == "static":
            rec, lam, dec, tr = _static_epoch(sys, day, ep, cfg, lam, rng, eps_P, eps_l, ckref)
            traj += tr
        else:
            if not cfg.warm_start:
                lam = np.full(N, lam_ref)
            # new forecasts enter as input increments (dynamic tracking), or cold re-init
            omega = tail_weights(Qh, zeta, ep.pi, cfg.alpha)
            omega_bar = omega.copy()
            dec = local_response(ep, lam, omega_bar, cfg.beta)
            u_new, q_new = tracker_input(ep, dec), local_q(ep, dec)
            if cfg.warm_start and not cfg.reanchor:
                x = x + N * (u_new - u)
                Qh = Qh + N * (q_new - q) if cfg.global_cost_tracker else q_new.copy()
            else:
                x = N * u_new
                Qh = N * q_new if cfg.global_cost_tracker else q_new.copy()
            u, q = u_new, q_new
            eta0 = step_size(sys, ep, cfg.eta_c)
            n_msgs = n_scal = 0
            hold, k_tol = 0, None
            maxdis = 0.0
            rem_hh = act_hh = rem_att = act_att = 0
            hh = honest[E[:, 0]] & honest[E[:, 1]]
            ae = att.A[E[:, 0]] | att.A[E[:, 1]]
            for k in range(cfg.K):
                if cfg.refine and k in (cfg.K // 3, 2 * cfg.K // 3):
                    ep = Epoch(sys, day, t, soc, refine_stage=0 if k == cfg.K // 3 else 1)
                active = rng.random(nE) >= cfg.p_loss
                rep_l, rep_x = att.corrupt(t, lam, x)
                if cfg.weights == "tarc":
                    keep, rho_eff = tarc.step(active, rep_l, rep_x, x, lam, frozen=k < cfg.tarc.grace)
                    W = build_W(N, E, keep, rho_eff)
                    n_msgs += 4 * nE
                    n_scal += nE * 2 * (3 + M) + nE * 2 * 4
                    rem_hh += (active & hh & ~keep).sum(); act_hh += (active & hh).sum()
                    rem_att += (active & ae & ~keep).sum(); act_att += (active & ae).sum()
                else:
                    keep = active
                    W = build_W(N, E, keep)            # Metropolis-type (max-degree) weights
                    n_msgs += 2 * nE
                    n_scal += nE * 2 * (4 + M)
                eta = eta0 / (1 + k / cfg.k0) ** cfg.nu
                lam_old = lam
                if cfg.weights == "wmsr":
                    lam_mix = wmsr.agg(lam, rep_l, active)
                else:
                    lam_mix = mix(W, lam, rep_l)
                lam = np.clip(lam_mix - eta * x, lmin, lmax)
                if cfg.record_mats:
                    traj.append(dict(t=t, k=k, W=W.copy(), lam_prev=lam_old.copy(), lam_next=lam.copy(),
                                     honest=honest.copy(), mats=True))
                omega = tail_weights(Qh, zeta, ep.pi, cfg.alpha)
                rho_w = 1.0 / (1.0 + k / cfg.k_omega) if cfg.k_omega > 0 else 1.0
                omega_bar = (1 - rho_w) * omega_bar + rho_w * omega
                dec = local_response(ep, lam, omega_bar, cfg.beta)
                u_new, q_new = tracker_input(ep, dec), local_q(ep, dec)
                if cfg.weights == "wmsr":
                    x = wmsr.agg(x, rep_x, active) + N * (u_new - u)
                else:
                    x = mix(W, x, rep_x) + N * (u_new - u)
                if cfg.global_cost_tracker:
                    Qh = W @ Qh + N * (q_new - q)
                else:
                    Qh = q_new.copy()
                u, q = u_new, q_new
                if cfg.quantile_rule == "local_sort":
                    zeta = var_cvar(Qh, ep.pi, cfg.alpha)[0]
                else:
                    th = tail_weights(Qh, zeta, ep.pi, cfg.alpha) * (1 - cfg.alpha) / ep.pi
                    above = (Qh > zeta[:, None]).astype(float)
                    etaz = 0.2 * Q_ref / (k + 1) ** 0.75
                    zeta = W @ zeta - etaz * (1 - (ep.pi * above).sum(1) / (1 - cfg.alpha))
                dP = dec["s"].sum() - ep.P_loss
                if ckref is not None and (k + 1) % cfg.ckpt_every == 0:
                    _e = evaluate(ep, dec, cfg.beta, cfg.alpha, "S")
                    traj.append(dict(ckpt=True, t=t, k=k + 1, msgs=n_msgs, scal=n_scal, dP=dP,
                                     gap=(ckref[0] - _e["SW"]) / abs(ckref[1])))
                lh = lam[honest]
                dis = lh.max() - lh.min()
                maxdis = max(maxdis, dis) if k > 20 else maxdis
                ok = (np.abs(x[honest]).max() < eps_P) and (abs(dP) < eps_P) and \
                     (np.abs(lam - lam_old)[honest].max() < eps_l)
                hold = hold + 1 if ok else 0
                if hold >= cfg.hold and k_tol is None:
                    k_tol = k + 1
                if cfg.record_traj:
                    Jx = x[honest] - x[honest].mean()
                    traj.append(dict(t=t, k=k, lam_mean=lam[honest].mean(), lam_dis=dis,
                                     x_dis=np.linalg.norm(Jx), dP=dP,
                                     sum_err=abs(x.mean() - u.sum()),
                                     sum_err_honest_view=abs(x[honest].mean() - u.sum()),
                                     retained=int(keep.sum()), active=int(active.sum()),
                                     Q_dis=float(np.abs(Qh - Qh.mean(0)).max()),
                                     att=att.active(t)))
            rec = dict(rounds_to_tol=k_tol if k_tol is not None else np.nan, reached=k_tol is not None,
                       msgs_total=n_msgs, scal_total=n_scal,
                       msgs_to_tol=(n_msgs / cfg.K * k_tol) if k_tol else np.nan,
                       scal_to_tol=(n_scal / cfg.K * k_tol) if k_tol else np.nan,
                       lam_dis_final=dis, lam_dis_max=maxdis,
                       sum_inv_err=abs(x.mean() - u.sum()),
                       fp_rate=(rem_hh / act_hh) if act_hh else np.nan,
                       att_edge_removal=(rem_att / act_att) if act_att else np.nan,
                       lam_mean=lam[honest].mean())
        # ---------------- evaluation of committed schedule -----------------
        rec.update(t=t, attack_active=att.active(t))
        rec.update(out_of_sample(ep, dec, day, cfg.alpha))
        dPc = dec["s"].sum() - ep.P_loss
        rec["dP"] = dPc
        for reg in cfg.regimes:
            ev = evaluate(ep, dec, cfg.beta, cfg.alpha, reg)
            for kk in ("W0", "gen_cost", "CVaR", "EQ", "SW"):
                rec[f"{kk}_{reg}"] = ev[kk]
            if cfg.central:
                cdec = solve_central(ep, cfg.beta, cfg.alpha, reg)
                cev = evaluate(ep, cdec, cfg.beta, cfg.alpha, reg)
                rec[f"SW_central_{reg}"] = cev["SW"]
                rec[f"CVaR_central_{reg}"] = cev["CVaR"]
                rec[f"lam_central_{reg}"] = cdec["lam"]
                rec[f"gap_{reg}"] = (cev["SW"] - ev["SW"]) / max(abs(cev["gen_cost"]), 1e-9)
                coos = out_of_sample(ep, cdec, day, cfg.alpha)
                rec[f"oos_EQ_central_{reg}"] = coos["oos_EQ"]
                rec[f"oos_CVaR_central_{reg}"] = coos["oos_CVaR"]
                if cfg.kkt:
                    rec[f"kkt_central_{reg}"] = kkt_residual(ep, cdec, cfg.beta, cfg.alpha, reg)[0] / lam_ref
            if cfg.kkt:
                rec[f"kkt_{reg}"] = kkt_residual(ep, dec, cfg.beta, cfg.alpha, reg)[0] / lam_ref
        records.append(rec)
        # battery state update with the committed action (Delta t = 1 h)
        if len(sys.bi):
            soc = np.clip(soc + sys.eta_c * dec["pch"] - dec["pdis"] / sys.eta_d, 0.1 * sys.b_emax, 0.9 * sys.b_emax)
    return records, traj


def _static_epoch(sys, day, ep, cfg, lam, rng, eps_P, eps_l, ckref=None):
    """Baseline: at every outer price iteration, static average consensus is
    re-run to tolerance on (lam, u, q) before the price step (our implementation
    of a per-epoch static re-convergence scheme; not a reproduction of [1])."""
    N, E = sys.N, sys.edges
    nE = len(E)
    M = ep.M
    lmin, lmax = cfg.lam_min_f * sys.lam_ref, cfg.lam_max_f * sys.lam_ref
    eta0 = cfg.eta_c / dual_lipschitz(sys, ep)     # exact sums available after inner re-convergence
    zeta = None
    omega = np.tile(ep.pi, (N, 1))
    rounds = 0
    msgs = scal = 0
    k_tol = None
    traj = []
    for p in range(cfg.static_outer_max):
        dec = local_response(ep, lam, omega, cfg.beta)
        u, q = tracker_input(ep, dec), local_q(ep, dec)
        Z = np.column_stack([lam, u, q])
        for r in range(cfg.static_inner_max):
            dis_l = np.abs(Z[:, 0] - Z[:, 0].mean()).max()
            dis_u = N * np.abs(Z[:, 1] - Z[:, 1].mean()).max()
            if dis_l < 0.5 * eps_l and dis_u < 0.5 * eps_P:
                break
            active = rng.random(nE) >= cfg.p_loss
            W = build_W(N, E, active)
            Z = W @ Z
            rounds += 1
            msgs += 2 * nE
            scal += nE * 2 * (3 + M)
        Qh = N * Z[:, 2:]
        zeta = var_cvar(Qh, ep.pi, cfg.alpha)[0]
        rho_w = 1.0 / (1.0 + p / cfg.k_omega) if cfg.k_omega > 0 else 1.0
        omega = (1 - rho_w) * omega + rho_w * tail_weights(Qh, zeta, ep.pi, cfg.alpha) if p > 0 else \
            tail_weights(Qh, zeta, ep.pi, cfg.alpha)
        eta = eta0 / (1 + p / cfg.k0) ** cfg.nu
        lam_new = np.clip(Z[:, 0] - eta * N * Z[:, 1], lmin, lmax)
        dP = dec["s"].sum() - ep.P_loss
        if ckref is not None:
            _e = evaluate(ep, dec, cfg.beta, cfg.alpha, "S")
            traj.append(dict(ckpt=True, t=ep.t, k=rounds, msgs=msgs, scal=scal, dP=dP,
                             gap=(ckref[0] - _e["SW"]) / abs(ckref[1])))
        if cfg.record_traj:
            traj.append(dict(t=ep.t, k=rounds, outer=p, lam_mean=lam_new.mean(), dP=dP))
        if abs(dP) < eps_P and np.abs(lam_new - lam).max() < eps_l and k_tol is None:
            k_tol = rounds
            lam = lam_new
            break
        lam = lam_new
    dec = local_response(ep, lam, omega, cfg.beta)
    rec = dict(rounds_to_tol=k_tol if k_tol is not None else np.nan, reached=k_tol is not None,
               msgs_total=msgs, scal_total=scal, msgs_to_tol=msgs if k_tol else np.nan,
               scal_to_tol=scal if k_tol else np.nan, outer_iters=p + 1, lam_dis_final=0.0,
               lam_dis_max=np.nan, sum_inv_err=np.nan, fp_rate=np.nan, att_edge_removal=np.nan,
               lam_mean=lam.mean())
    return rec, lam, dec, traj

"""Local agent models, recourse models, CVaR and the centralized KKT residual.

Sign convention: every agent reports a net injection s_i (supply minus
demand, MW). The day-ahead balance is  DeltaP = sum_i s_i - P_loss = 0.
The local tracker input is u_i = s_i - l_i where l_i is the agent's share
of the fixed loss forecast (loads carry the loss allocation).

Two recourse models are implemented.
  * Regime S (separable, Assumption R1): fixed-policy recourse. The
    aggregate load-forecast error eps_m is covered by generators with fixed
    participation factors kappa_i; each generator pays up/down regulation on
    its own share and a shedding/spill penalty for the part its own
    headroom/footroom cannot cover. Each renewable agent settles its own
    shortfall (P_R - A_m)^+ at price c_short. Q = sum_i q_i with q_i
    depending only on x_i, so R1 holds exactly.
  * Regime C (network-coupled): an economic-dispatch recourse LP with a
    single shared real-time balance: free renewable flexibility first, then
    generator regulation in merit order, then shedding/spill. Evaluated in
    closed form by merit order (verified against an LP solver in tests).
"""
import numpy as np
from .systems import System, DayData


class Epoch:
    """Per-epoch parameters seen by the agents."""

    def __init__(self, sys: System, day: DayData, t: int, soc: np.ndarray, refine_stage=None, v_b=None):
        self.sys = sys
        self.t = t
        mult = np.ones(len(sys.li) + len(sys.ri)) if refine_stage is None else day.refine[t, refine_stage]
        nL = len(sys.li)
        self.load_fc = day.load_fc[t] * mult[:nL]
        self.ren_fc = np.clip(day.ren_fc[t] * mult[nL:], 0, sys.ren_cap)
        self.eps = day.eps[t]                         # (M,)
        self.avail = day.ren_avail[t]                 # (M, nR)
        self.pi = day.pi
        self.M = len(self.pi)
        lam = sys.lam_ref
        self.psi = lam / (sys.elasticity * self.load_fc)
        self.phi = lam + self.psi * self.load_fc
        self.PD_lo = sys.flex_lo * self.load_fc
        self.PD_hi = sys.flex_hi * self.load_fc
        self.loss_alloc = sys.loss_frac * self.load_fc          # per load agent
        self.P_loss = self.loss_alloc.sum()
        # batteries: one-step with terminal energy value v_b (declared rule)
        self.v_b = sys.lam_ref if v_b is None else v_b
        emin, emax = 0.1 * sys.b_emax, 0.9 * sys.b_emax
        self.soc = soc.copy()
        self.pd_max = np.minimum(sys.b_pmax, np.maximum(soc - emin, 0) * sys.eta_d)
        self.pc_max = np.minimum(sys.b_pmax, np.maximum(emax - soc, 0) / sys.eta_c)
        # generator need under fixed participation (regime S)
        self.need = sys.kappa[None, :] * self.eps[:, None]       # (M, nG)
        self.need_up = np.maximum(self.need, 0)
        self.need_dn = np.maximum(-self.need, 0)


# ----------------------------------------------------------------------------
# Regime-S local recourse costs and their right-derivatives
# ----------------------------------------------------------------------------

def q_gen_S(ep: Epoch, P):
    """P: (..., nG) generator schedules -> (..., M, nG) local recourse cost."""
    s = ep.sys
    P = np.asarray(P)[..., None, :]
    H = s.pmax - P
    F = P - s.pmin
    up = s.c_up * np.minimum(ep.need_up, H) + s.c_shed * np.maximum(ep.need_up - H, 0)
    dn = s.c_dn * np.minimum(ep.need_dn, F) + s.c_spill * np.maximum(ep.need_dn - F, 0)
    return up + dn


def dq_gen_S(ep: Epoch, P):
    s = ep.sys
    P = np.asarray(P)[..., None, :]
    H = s.pmax - P
    F = P - s.pmin
    d = np.where(ep.need_up > H, s.c_shed - s.c_up, 0.0)
    d = d + np.where(ep.need_dn > F, s.c_dn - s.c_spill, 0.0)
    return d


def q_ren_S(ep: Epoch, P):
    return ep.sys.c_short * np.maximum(np.asarray(P)[..., None, :] - ep.avail, 0)


def dq_ren_S(ep: Epoch, P):
    return ep.sys.c_short * (np.asarray(P)[..., None, :] >= ep.avail)


# ----------------------------------------------------------------------------
# Local best responses (exact 1-D convex problems, solved by bisection)
# ----------------------------------------------------------------------------

def _bisect(dfun, lo, hi, iters=32):
    """Root of a nondecreasing (right-)derivative on [lo, hi], vectorised."""
    dlo, dhi = dfun(lo), dfun(hi)
    x_lo, x_hi = lo.copy(), hi.copy()
    for _ in range(iters):
        mid = 0.5 * (x_lo + x_hi)
        pos = dfun(mid) > 0
        x_hi = np.where(pos, mid, x_hi)
        x_lo = np.where(pos, x_lo, mid)
    x = 0.5 * (x_lo + x_hi)
    x = np.where(dlo >= 0, lo, x)
    x = np.where(dhi <= 0, hi, x)
    return x


def local_response(ep: Epoch, lam, omega, beta):
    """Best responses of all agents.

    lam:   (N,) local prices
    omega: (N, M) local CVaR tail weights  pi_m * theta_{i,m} / (1-alpha)
    beta:  risk weight
    Returns dict with net injections s (N,) and per-type decisions.
    """
    s = ep.sys
    out = {}
    # generators
    lg, wg = lam[s.gi], omega[s.gi]

    def dG(P):
        return s.a * P + s.b - lg + beta * np.einsum("gm,mg->g", wg, dq_gen_S(ep, P))

    PG = _bisect(dG, s.pmin.astype(float), s.pmax.astype(float)) if len(s.gi) else np.zeros(0)
    # renewables
    lr, wr = lam[s.ri], omega[s.ri]

    def dR(P):
        return s.a_R * P + s.b_R - lr + beta * np.einsum("km,mk->k", wr, dq_ren_S(ep, P))

    PR = _bisect(dR, np.zeros(len(s.ri)), ep.ren_fc.astype(float)) if len(s.ri) else np.zeros(0)
    # loads
    PD = np.clip((ep.phi - lam[s.li]) / ep.psi, ep.PD_lo, ep.PD_hi)
    # batteries (Lemma 1: at most one of pc, pd positive for nonnegative prices)
    lb = lam[s.bi]
    pdis = np.clip((lb - ep.v_b / s.eta_d) / (2 * s.kappa_deg), 0, ep.pd_max) if len(s.bi) else np.zeros(0)
    pch = np.clip((ep.v_b * s.eta_c - lb) / (2 * s.kappa_deg), 0, ep.pc_max) if len(s.bi) else np.zeros(0)
    sN = np.zeros(s.N)
    sN[s.gi] = PG
    sN[s.ri] = PR
    sN[s.li] = -PD
    sN[s.bi] = pdis - pch
    out.update(s=sN, PG=PG, PR=PR, PD=PD, pch=pch, pdis=pdis)
    return out


def tracker_input(ep: Epoch, dec):
    u = dec["s"].copy()
    u[ep.sys.li] -= ep.loss_alloc
    return u


def local_q(ep: Epoch, dec):
    """(N, M) local scenario-recourse contributions under regime S (surrogate in regime C)."""
    s = ep.sys
    q = np.zeros((s.N, ep.M))
    if len(s.gi):
        q[s.gi] = q_gen_S(ep, dec["PG"]).T
    if len(s.ri):
        q[s.ri] = q_ren_S(ep, dec["PR"]).T
    return q


# ----------------------------------------------------------------------------
# CVaR helpers
# ----------------------------------------------------------------------------

def var_cvar(Q, pi, alpha):
    """Weighted VaR and CVaR (Rockafellar-Uryasev), exact for discrete distributions.
    Q: (..., M). Returns (var, cvar)."""
    Q = np.asarray(Q)
    order = np.argsort(Q, axis=-1)
    Qs = np.take_along_axis(Q, order, -1)
    ps = np.broadcast_to(pi, Q.shape)
    ps = np.take_along_axis(ps, order, -1)
    cum = np.cumsum(ps, -1)
    idx = np.argmax(cum >= alpha - 1e-12, axis=-1)
    var = np.take_along_axis(Qs, idx[..., None], -1)[..., 0]
    cvar = var + (ps * np.maximum(Qs - var[..., None], 0)).sum(-1) / (1 - alpha)
    return var, cvar


def tail_weights(Qhat, zeta, pi, alpha):
    """theta_{i,m} = 1{Qhat_{i,m} > zeta_i}; returns pi*theta/(1-alpha) with the
    fractional atom so that weights sum to one (exact CVaR subgradient)."""
    above = Qhat > zeta[:, None] + 1e-9
    at = np.abs(Qhat - zeta[:, None]) <= 1e-9
    w_above = (pi * above).sum(1)
    w_at = (pi * at).sum(1)
    frac = np.clip((1 - alpha - w_above) / np.maximum(w_at, 1e-15), 0, 1)
    theta = above + at * frac[:, None]
    return pi * theta / (1 - alpha)


# ----------------------------------------------------------------------------
# System-level evaluation (true recourse model)
# ----------------------------------------------------------------------------

def Q_regime_S(ep: Epoch, PG, PR, dP=None):
    """(..., M) separable recourse cost. DA imbalance dP (if given) is priced as
    extra need shared by participation factors."""
    s = ep.sys
    if dP is None:
        return q_gen_S(ep, PG).sum(-1) + q_ren_S(ep, PR).sum(-1)
    ep2 = _shift_need(ep, dP)
    return q_gen_S(ep2, PG).sum(-1) + q_ren_S(ep2, PR).sum(-1)


class _Shifted:
    pass


def _shift_need(ep, dP):
    e = _Shifted()
    e.__dict__.update(ep.__dict__)
    need = ep.sys.kappa[None, :] * (ep.eps[:, None] - dP)
    e.need_up, e.need_dn = np.maximum(need, 0), np.maximum(-need, 0)
    return e


def Q_regime_C(ep: Epoch, PG, PR, dP=0.0, eps=None, avail=None):
    """Network-coupled merit-order recourse, vectorised.
    PG: (..., nG), PR: (..., nR), dP: (...) DA imbalance (supply - demand).
    Returns (..., M)."""
    s = ep.sys
    eps = ep.eps if eps is None else eps
    avail = ep.avail if avail is None else avail
    PG = np.asarray(PG)[..., None, :]
    PR = np.asarray(PR)[..., None, :]
    dP = np.asarray(dP)[..., None]
    short = np.maximum(PR - avail, 0).sum(-1)
    R = eps - dP + short                                  # upward requirement (MW)
    Ufree = np.maximum(avail - PR, 0).sum(-1)
    Dfree = np.minimum(PR, avail).sum(-1)
    ou = np.argsort(s.c_up)
    od = np.argsort(s.c_dn)
    H = np.broadcast_to(s.pmax - PG, PG.shape[:-1] + (len(s.gi),))[..., ou]
    F = np.broadcast_to(PG - s.pmin, PG.shape[:-1] + (len(s.gi),))[..., od]
    # upward
    rem_u = np.maximum(R - Ufree, 0)
    cumH = np.cumsum(H, -1)
    used = np.clip(rem_u[..., None] - (cumH - H), 0, H)
    cost_u = (used * s.c_up[ou]).sum(-1) + s.c_shed * np.maximum(rem_u - cumH[..., -1], 0)
    # downward
    rem_d = np.maximum(-R - Dfree, 0)
    cumF = np.cumsum(F, -1)
    usedd = np.clip(rem_d[..., None] - (cumF - F), 0, F)
    cost_d = (usedd * s.c_dn[od]).sum(-1) + s.c_spill * np.maximum(rem_d - cumF[..., -1], 0)
    return cost_u + cost_d


def welfare0(ep: Epoch, dec):
    s = ep.sys
    PG, PR, PD, pc, pd = dec["PG"], dec["PR"], dec["PD"], dec["pch"], dec["pdis"]
    U = (ep.phi * PD - 0.5 * ep.psi * PD ** 2).sum()
    C = (0.5 * s.a * PG ** 2 + s.b * PG).sum() + (0.5 * s.a_R * PR ** 2 + s.b_R * PR).sum()
    batt = (ep.v_b * (s.eta_c * pc - pd / s.eta_d) - s.kappa_deg * (pc ** 2 + pd ** 2)).sum()
    return U - C + batt, C


def evaluate(ep: Epoch, dec, beta, alpha, regime):
    """Welfare components of a committed schedule under the TRUE recourse model."""
    dP = dec["s"].sum() - ep.P_loss
    W0, C = welfare0(ep, dec)
    if regime == "S":
        Q = Q_regime_S(ep, dec["PG"], dec["PR"], dP=dP)
    else:
        Q = Q_regime_C(ep, dec["PG"], dec["PR"], dP=dP)
    _, cv = var_cvar(Q, ep.pi, alpha)
    EQ = (ep.pi * Q).sum()
    return dict(W0=W0, gen_cost=C, CVaR=cv, EQ=EQ, SW=W0 - beta * cv, dP=dP)


def out_of_sample(ep: Epoch, dec, day: DayData, alpha):
    """Realised recourse cost on held-out samples (always evaluated with the coupled model)."""
    dP = dec["s"].sum() - ep.P_loss
    Q = Q_regime_C(ep, dec["PG"], dec["PR"], dP=dP, eps=day.oos_eps[ep.t], avail=day.oos_ren[ep.t])
    S = Q.shape[-1]
    _, cv = var_cvar(Q, np.full(S, 1.0 / S), alpha)
    return dict(oos_EQ=Q.mean(), oos_CVaR=cv)


# ----------------------------------------------------------------------------
# Centralized KKT residual (coordinatewise, via one-sided directional derivatives)
# ----------------------------------------------------------------------------

def _vectorize_dec(ep, dec):
    s = ep.sys
    x = np.concatenate([dec["PG"], dec["PR"], dec["PD"], dec["pch"], dec["pdis"]])
    lo = np.concatenate([s.pmin, np.zeros(len(s.ri)), ep.PD_lo, np.zeros(len(s.bi)), np.zeros(len(s.bi))])
    hi = np.concatenate([s.pmax, ep.ren_fc, ep.PD_hi, ep.pc_max, ep.pd_max])
    a = np.concatenate([np.ones(len(s.gi)), np.ones(len(s.ri)), -np.ones(len(s.li)), -np.ones(len(s.bi)),
                        np.ones(len(s.bi))])
    return x, lo, hi, a


def _objective_batch(ep, X, beta, alpha, regime):
    """Minimisation objective F = -W0 + beta*CVaR(Q) for a batch of decision vectors X (B, n).
    Balance is NOT included (handled by the multiplier)."""
    s = ep.sys
    nG, nR, nL, nB = len(s.gi), len(s.ri), len(s.li), len(s.bi)
    PG = X[:, :nG]
    PR = X[:, nG:nG + nR]
    PD = X[:, nG + nR:nG + nR + nL]
    pc = X[:, nG + nR + nL:nG + nR + nL + nB]
    pd = X[:, nG + nR + nL + nB:]
    U = (ep.phi * PD - 0.5 * ep.psi * PD ** 2).sum(1)
    C = (0.5 * s.a * PG ** 2 + s.b * PG).sum(1) + (0.5 * s.a_R * PR ** 2 + s.b_R * PR).sum(1)
    batt = (ep.v_b * (s.eta_c * pc - pd / s.eta_d) - s.kappa_deg * (pc ** 2 + pd ** 2)).sum(1)
    if beta == 0:
        return -(U - C + batt)
    Q = Q_regime_S(ep, PG, PR) if regime == "S" else Q_regime_C(ep, PG, PR, dP=np.zeros(len(X)))
    _, cv = var_cvar(Q, ep.pi, alpha)
    return -(U - C + batt) + beta * cv


def kkt_residual(ep: Epoch, dec, beta, alpha, regime, h=None):
    """r_KKT = min_lambda sqrt( mean_i dist(0, [d-_i F - lambda a_i, d+_i F - lambda a_i] + N_{X_i}(x_i))^2 ).

    Uses one-sided directional derivatives of the TRUE centralized objective, so it
    is a lower bound on dist(0, dL) that is exact where F is differentiable. The
    primal balance residual |DeltaP| is reported separately.
    Returns (r_kkt [$/MWh], lambda_star)."""
    x, lo, hi, a = _vectorize_dec(ep, dec)
    n = len(x)
    h = 1e-4 * max(1.0, ep.sys.peak_load / 100) if h is None else h
    X0 = x[None, :]
    E = np.eye(n) * h
    Xp = np.clip(X0 + E, lo, hi)
    Xm = np.clip(X0 - E, lo, hi)
    F0 = _objective_batch(ep, X0, beta, alpha, regime)[0]
    Fp = _objective_batch(ep, Xp, beta, alpha, regime)
    Fm = _objective_batch(ep, Xm, beta, alpha, regime)
    stepp = np.diag(Xp) - x
    stepm = x - np.diag(Xm)
    dplus = np.where(stepp > 1e-12, (Fp - F0) / np.maximum(stepp, 1e-12), np.nan)
    dminus = np.where(stepm > 1e-12, (F0 - Fm) / np.maximum(stepm, 1e-12), np.nan)
    btol = 1e-5 * np.maximum(1.0, hi - lo)
    at_lo = x <= lo + btol
    at_hi = x >= hi - btol

    def res(lam):
        up = dplus - lam * a      # right derivative of Lagrangian
        dn = dminus - lam * a     # left derivative
        r = np.zeros(n)
        interior = ~at_lo & ~at_hi
        # interior: dist(0,[dn,up])
        r_int = np.maximum(0, np.maximum(dn, -up))
        r = np.where(interior, np.nan_to_num(r_int), r)
        # at lower bound: need up >= 0
        r = np.where(at_lo & ~at_hi, np.maximum(0, -np.nan_to_num(up)), r)
        # at upper bound: need dn <= 0
        r = np.where(at_hi & ~at_lo, np.maximum(0, np.nan_to_num(dn)), r)
        return np.sqrt(np.mean(r ** 2))

    from scipy.optimize import minimize_scalar
    lam_ref = ep.sys.lam_ref
    grid = np.linspace(-lam_ref, 6 * lam_ref, 141)
    vals = [res(g) for g in grid]
    g0 = grid[int(np.argmin(vals))]
    step = grid[1] - grid[0]
    opt = minimize_scalar(res, bounds=(g0 - step, g0 + step), method="bounded", options=dict(xatol=1e-8))
    return float(min(opt.fun, min(vals))), float(opt.x)

"""Centralized CVaR-augmented benchmark (extensive form), solved with CVXPY.

maximise  W0(x) - beta * [ zeta + 1/(1-alpha) * sum_m pi_m s_m ]
s.t.      day-ahead balance, local bounds,
          s_m >= Q_m(x) - zeta, s_m >= 0,
          Q_m(x) given by the separable (S) or coupled (C) recourse model.
"""
import numpy as np
import cvxpy as cp
from .model import Epoch


def solve_central(ep: Epoch, beta: float, alpha: float, regime: str = "S", solver=None):
    s = ep.sys
    nG, nR, nL, nB, M = len(s.gi), len(s.ri), len(s.li), len(s.bi), ep.M
    PG = cp.Variable(nG)
    PR = cp.Variable(nR)
    PD = cp.Variable(nL)
    cons = [PG >= s.pmin, PG <= s.pmax, PR >= 0, PR <= ep.ren_fc, PD >= ep.PD_lo, PD <= ep.PD_hi]
    if nB:
        pc = cp.Variable(nB)
        pd = cp.Variable(nB)
        cons += [pc >= 0, pd >= 0, pc <= ep.pc_max, pd <= ep.pd_max]
        batt = cp.sum(ep.v_b * (s.eta_c * pc - pd / s.eta_d) - cp.multiply(s.kappa_deg, cp.square(pc) + cp.square(pd)))
        bnet = cp.sum(pd) - cp.sum(pc)
    else:
        batt, bnet = 0.0, 0.0
    U = cp.sum(cp.multiply(ep.phi, PD) - 0.5 * cp.multiply(ep.psi, cp.square(PD)))
    C = cp.sum(0.5 * cp.multiply(s.a, cp.square(PG)) + cp.multiply(s.b, PG)) + \
        cp.sum(0.5 * s.a_R * cp.square(PR) + s.b_R * PR)
    W0 = U - C + batt
    balance = cp.sum(PG) + cp.sum(PR) + bnet - cp.sum(PD) - ep.P_loss
    bal_con = balance == 0
    cons += [bal_con]
    obj = W0
    if beta > 0:
        zeta = cp.Variable()
        sm = cp.Variable(M, nonneg=True)
        if regime == "S":
            eu = cp.Variable((M, nG), nonneg=True)
            ed = cp.Variable((M, nG), nonneg=True)
            sh = cp.Variable((M, nR), nonneg=True)
            ones = np.ones((M, 1))
            cons += [eu >= ep.need_up + ones @ cp.reshape(PG - s.pmax, (1, nG), order="C"),
                     ed >= ep.need_dn - ones @ cp.reshape(PG - s.pmin, (1, nG), order="C"),
                     sh >= ones @ cp.reshape(PR, (1, nR), order="C") - ep.avail]
            Q = (ep.need_up @ s.c_up + ep.need_dn @ s.c_dn) + eu @ (s.c_shed - s.c_up) + \
                ed @ (s.c_spill - s.c_dn) + s.c_short * cp.sum(sh, axis=1)
        else:
            ones = np.ones((M, 1))
            ru = cp.Variable((M, nG), nonneg=True)
            rd = cp.Variable((M, nG), nonneg=True)
            o = cp.Variable((M, nR), nonneg=True)
            shed = cp.Variable(M, nonneg=True)
            spill = cp.Variable(M, nonneg=True)
            cons += [ru <= ones @ cp.reshape(s.pmax - PG, (1, nG), order="C"),
                     rd <= ones @ cp.reshape(PG - s.pmin, (1, nG), order="C"),
                     o <= ep.avail,
                     cp.sum(ru, 1) - cp.sum(rd, 1) + cp.sum(o, 1) - cp.sum(PR) + shed - spill == ep.eps]
            Q = ru @ s.c_up + rd @ s.c_dn + s.c_shed * shed + s.c_spill * spill
        cons += [sm >= Q - zeta]
        obj = W0 - beta * (zeta + (ep.pi @ sm) / (1 - alpha))
    prob = cp.Problem(cp.Maximize(obj), cons)
    prob.solve(solver=solver or cp.CLARABEL)
    if prob.status not in ("optimal", "optimal_inaccurate"):
        raise RuntimeError(f"central solve failed: {prob.status}")
    dec = dict(PG=np.asarray(PG.value).ravel(), PR=np.asarray(PR.value).ravel(), PD=np.asarray(PD.value).ravel(),
               pch=np.asarray(pc.value).ravel() if nB else np.zeros(0),
               pdis=np.asarray(pd.value).ravel() if nB else np.zeros(0))
    for k in ("PR", "pch", "pdis"):
        dec[k] = np.maximum(dec[k], 0)
    sN = np.zeros(s.N)
    sN[s.gi] = dec["PG"]
    sN[s.ri] = dec["PR"]
    sN[s.li] = -dec["PD"]
    sN[s.bi] = dec["pdis"] - dec["pch"]
    dec["s"] = sN
    dec["lam"] = float(abs(bal_con.dual_value))
    return dec

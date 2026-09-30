"""Sanity tests. Run:  python -m pytest -q tests   (or python tests/test_core.py)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import cvxpy as cp
from rdoem.systems import build_system, build_day
from rdoem.model import Epoch, Q_regime_C, kkt_residual, local_response, var_cvar
from rdoem.centralized import solve_central
from rdoem.algorithms import build_W, Config, run_day


def _setup(case="ieee30", t=18):
    s = build_system(case, seed=0)
    d = build_day(s, seed=0, M=20)
    return s, d, Epoch(s, d, t, 0.5 * s.b_emax)


def test_merit_order_matches_lp():
    s, d, ep = _setup()
    rng = np.random.default_rng(1)
    for _ in range(5):
        PG = rng.uniform(s.pmin, s.pmax)
        PR = rng.uniform(0, ep.ren_fc)
        dP = rng.normal(0, 5)
        Qc = Q_regime_C(ep, PG, PR, dP=dP)
        for m in range(3):
            ru = cp.Variable(len(s.gi), nonneg=True); rd = cp.Variable(len(s.gi), nonneg=True)
            o = cp.Variable(len(s.ri), nonneg=True); sh = cp.Variable(nonneg=True); sp = cp.Variable(nonneg=True)
            cons = [ru <= s.pmax - PG, rd <= PG - s.pmin, o <= ep.avail[m],
                    cp.sum(ru) - cp.sum(rd) + cp.sum(o) - PR.sum() + sh - sp == ep.eps[m] - dP]
            pr = cp.Problem(cp.Minimize(s.c_up @ ru + s.c_dn @ rd + s.c_shed * sh + s.c_spill * sp), cons)
            pr.solve()
            assert abs(pr.value - Qc[m]) < 1e-5 * max(1, abs(pr.value)), (pr.value, Qc[m])


def test_central_kkt_residual_small():
    s, d, ep = _setup()
    for regime in ("S", "C"):
        dec = solve_central(ep, 1.0, 0.9, regime)
        r, lam = kkt_residual(ep, dec, 1.0, 0.9, regime)
        assert r / s.lam_ref < 1e-3, (regime, r)


def test_W_doubly_stochastic_and_positive_diag():
    s, _, _ = _setup()
    rng = np.random.default_rng(0)
    keep = rng.random(len(s.edges)) > 0.3
    W = build_W(s.N, s.edges, keep, rng.uniform(0.3, 1, len(s.edges)))
    assert np.allclose(W, W.T) and np.allclose(W.sum(1), 1) and (np.diag(W) > 0).all()


def test_sum_tracking_invariant():
    s, d, _ = _setup()
    cfg = Config(K=60, central=False, kkt=False, record_traj=True, epochs=(0, 1, 2), p_loss=0.2)
    _, tr = run_day(s, d, cfg, seed=0)
    assert max(r["sum_err"] for r in tr) < 1e-6 * s.peak_load


if __name__ == "__main__":
    for f in (test_merit_order_matches_lp, test_central_kkt_residual_small, test_W_doubly_stochastic_and_positive_diag,
              test_sum_tracking_invariant):
        f(); print("PASS", f.__name__)

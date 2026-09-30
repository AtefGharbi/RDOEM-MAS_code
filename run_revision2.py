"""Experiments added in revision 2: E8 equal-accuracy communication, E9 held-out attack seeds,
E10 TARC-R parameter sensitivity. Resumable like run_experiments.py."""
import os, sys, pickle
import pandas as pd
import run_experiments as R
from run_experiments import run, TarcParams, TARC_R, ATTACKS
OUT = R.OUT

def E8():
    rows = []
    for seed in range(5):
        for m, kw in [("RDOEM-MAS (TARC-R)", {}), ("Dynamic, no TARC", {}),
                      ("Static re-convergence", dict(tol_f=1e-4, static_outer_max=150))]:
            f = os.path.join(OUT, f"E8_ckpt_{seed}_{m[:7]}.pkl")
            if os.path.exists(f):
                continue
            _, tr = run("E8_comm", "ieee30", seed, m, ckpt_every=10, epochs=tuple(range(1, 13)), regimes=("S",),
                        kkt=False, central=False, record_traj=True, **kw)
            ck = pd.DataFrame([r for r in tr if r.get("ckpt")]); ck["method"] = m; ck["seed"] = seed
            ck.to_pickle(f)
        print("E8", seed, flush=True)

def E8b():
    for seed in range(5):
        for tol in (1e-2, 1e-3):
            f = os.path.join(OUT, f"E8_ckpt_{seed}_static_tol{tol:g}.pkl")
            if os.path.exists(f):
                continue
            _, tr = run("E8_comm", "ieee30", seed, "Static re-convergence", ckpt_every=10, epochs=tuple(range(1, 13)),
                        regimes=("S",), kkt=False, central=False, record_traj=True, tol_f=tol, static_outer_max=150,
                        tag=f"tol{tol:g}")
            ck = pd.DataFrame([r for r in tr if r.get("ckpt")]); ck["method"] = f"Static (tol {tol:g})"; ck["seed"] = seed
            ck.to_pickle(f)
        print("E8b", seed, flush=True)


def E9():
    for seed in range(100, 110):
        for an in ("ATT-1", "ATT-2", "ATT-3"):
            att = dict(ATTACKS[an], f_att=2, e0=8, e1=13)
            for m in ("Dynamic, no TARC", "RDOEM-MAS (TARC-R)"):
                run("E9_heldout", "ieee30", seed, m, extra=dict(attack=an), attack=att,
                    epochs=tuple(range(6, 18)), regimes=("S",), kkt=False)
        print("E9", seed, flush=True)

VARIANTS = {"rho_min=0.2": dict(rho_min=0.2), "rho_min=0.5": dict(rho_min=0.5), "G=30": dict(grace=30),
            "G=100": dict(grace=100), "rho_mem=0.3": dict(rho_mem=0.3), "rho_mem=0.8": dict(rho_mem=0.8)}

def E10():
    base = dict(score="R", grace=60, omega1=1.0, omega2=0.0, omega3=0.5, rho_mem=0.5)
    for seed in range(100, 105):
        for v, kw in VARIANTS.items():
            p = dict(base); p.update(kw)
            att = dict(ATTACKS["ATT-1"], f_att=2, e0=8, e1=13)
            run("E10_sens", "ieee30", seed, "RDOEM-MAS (TARC-R)", extra=dict(variant=v), tag=v,
                attack=att, tarc=TarcParams(**p), epochs=tuple(range(6, 18)), regimes=("S",), kkt=False)
        print("E10", seed, flush=True)

if __name__ == "__main__":
    for e in sys.argv[1:] or ["E8", "E9", "E10"]:
        globals()[e]()
        print("==", e, "done", flush=True)

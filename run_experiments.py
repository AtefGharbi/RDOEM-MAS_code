"""Run all experiments reported in the paper.

Usage:  python run_experiments.py E1 E3 ...   (default: all, in the order below)
Outputs: results/<experiment>.csv (one row per run x epoch), appended per run.
Every run is fully determined by (case, seed, method, config) -> reproducible.
"""
import os, sys, time, json, pickle
import numpy as np
import pandas as pd
from rdoem.systems import build_system, build_day
from rdoem.algorithms import Config, run_day, TarcParams

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)

TARC_V15 = TarcParams()                                            # rule as written in v15
TARC_R = TarcParams(score="R", grace=60, omega1=1.0, omega2=0.0,   # revised rule (Section V-B)
                    omega3=0.5, rho_mem=0.5)

METHODS = {
    "RDOEM-MAS (TARC-R)": dict(weights="tarc", reanchor=True, tarc=TARC_R),
    "RDOEM-MAS (TARC-v15)": dict(weights="tarc", reanchor=True, tarc=TARC_V15),
    "Dynamic, no TARC": dict(weights="metropolis", reanchor=True),
    "Dynamic, no TARC, no re-anchor": dict(weights="metropolis", reanchor=False),
    "W-MSR (f_W=1)": dict(weights="wmsr", reanchor=True, f_W=1),
    "Static re-convergence": dict(method="static"),
}

_cache = {}


def system(case, seed, **kw):
    key = (case, seed, tuple(sorted(kw.items())))
    if key not in _cache:
        s = build_system(case, seed=seed, **kw)
        _cache[key] = (s, build_day(s, seed=seed))
    return _cache[key]


def _runid(exp, case, seed, method, extra, sys_kw, tag, cfgkw):
    import hashlib
    key = json.dumps([exp, case, seed, method, extra, sys_kw, tag,
                      {k: str(v) for k, v in sorted(cfgkw.items())}], sort_keys=True, default=str)
    return hashlib.md5(key.encode()).hexdigest()[:16]


def run(exp, case, seed, method, extra=None, sys_kw=None, tag=None, **cfgkw):
    rid = _runid(exp, case, seed, method, extra, sys_kw, tag, cfgkw)
    rdir = os.path.join(OUT, exp)
    os.makedirs(rdir, exist_ok=True)
    fpath = os.path.join(rdir, rid + ".csv")
    if os.path.exists(fpath) and not cfgkw.get("record_traj"):
        return pd.read_csv(fpath), []
    s, d = system(case, seed, **(sys_kw or {}))
    kw = dict(METHODS[method])
    kw.update(cfgkw)
    cfg = Config(**kw)
    t0 = time.time()
    recs, traj = run_day(s, d, cfg, seed=seed)
    df = pd.DataFrame(recs)
    df["case"], df["seed"], df["method"], df["N"] = case, seed, method, s.N
    df["runtime_s"] = time.time() - t0
    if tag:
        df["tag"] = tag
    for k, v in (extra or {}).items():
        df[k] = v
    df.to_csv(fpath + ".tmp", index=False)
    os.replace(fpath + ".tmp", fpath)
    return df, traj


def collect(exp):
    import glob
    fs = sorted(glob.glob(os.path.join(OUT, exp, "*.csv")))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()


def E1():
    """Nominal performance, communication and optimality (both recourse regimes)."""
    plan = [("ieee30", range(20), ["RDOEM-MAS (TARC-R)", "Dynamic, no TARC", "Dynamic, no TARC, no re-anchor",
                                   "Static re-convergence"]),
            ("ieee57", range(10), ["RDOEM-MAS (TARC-R)", "Dynamic, no TARC", "Static re-convergence"]),
            ("ieee118", range(5), ["RDOEM-MAS (TARC-R)", "Static re-convergence"])]
    for case, seeds, methods in plan:
        for seed in seeds:
            for m in methods:
                run("E1_nominal", case, seed, m)
            print("E1", case, seed, flush=True)


def E3():
    """Risk weight sweep (beta = 1 is taken from E1)."""
    for seed in range(10):
        for beta in (0.0, 0.5, 2.0):
            run("E3_beta", "ieee30", seed, "RDOEM-MAS (TARC-R)", extra=dict(beta=beta), beta=beta)
        print("E3", seed, flush=True)


ATTACKS = {
    "ATT-1": dict(type="ATT-1"),
    "ATT-1x (mismatch only)": dict(type="ATT-1", b_lam=0.0),
    "ATT-2": dict(type="ATT-2"),
    "ATT-3": dict(type="ATT-3"),
    "ATT-4": dict(type="ATT-4"),
}


def E4():
    """Attack experiments: 2 compromised agents, attack in epochs 8-12, evaluated 6-17."""
    defenses = ["Dynamic, no TARC", "W-MSR (f_W=1)", "RDOEM-MAS (TARC-v15)", "RDOEM-MAS (TARC-R)"]
    for seed in range(10):
        for an, spec in ATTACKS.items():
            att = dict(spec, f_att=2, e0=8, e1=13)
            for m in defenses:
                run("E4_attacks", "ieee30", seed, m, extra=dict(attack=an), attack=att,
                    epochs=tuple(range(6, 18)), regimes=("S",), kkt=False)
        print("E4", seed, flush=True)


def E5():
    """Phase diagram: packet loss x number of compromised agents (ATT-1)."""
    for seed in range(5):
        for pl in (0.0, 0.1, 0.2, 0.3, 0.4):
            for f in (0, 1, 3, 6, 9):
                for m in ("Dynamic, no TARC", "RDOEM-MAS (TARC-R)"):
                    att = dict(type="ATT-1", f_att=f, e0=8, e1=11)
                    run("E5_phase", "ieee30", seed, m, extra=dict(p_loss=pl, f_att=f), attack=att, p_loss=pl,
                        epochs=(7, 8, 9, 10), regimes=("S",), kkt=False)
        print("E5", seed, flush=True)


def E6():
    """Ablations (nominal, IEEE 30)."""
    for seed in range(10):
        run("E6_ablation", "ieee30", seed, "RDOEM-MAS (TARC-R)", tag="no global-cost tracker",
            global_cost_tracker=False)
        run("E6_ablation", "ieee30", seed, "RDOEM-MAS (TARC-R)", tag="no tail-weight averaging", k_omega=0.0)
        run("E6_ablation", "ieee30", seed, "RDOEM-MAS (TARC-R)", tag="consensus-subgradient quantile",
            quantile_rule="consensus_subgradient")
        run("E6_ablation", "ieee30", seed, "RDOEM-MAS (TARC-R)", tag="no storage", sys_kw=dict(with_storage=False))
        run("E6_ablation", "ieee30", seed, "RDOEM-MAS (TARC-R)", tag="packet loss 20%", p_loss=0.2)
        print("E6", seed, flush=True)


def E7():
    """Single-run traces for figures (convergence, within-epoch refinements, Prop.-4 check)."""
    _, tr = run("E7_trace_runs", "ieee30", 0, "RDOEM-MAS (TARC-R)", record_traj=True, refine=True,
                epochs=tuple(range(0, 6)), regimes=("S",))
    pd.DataFrame(tr).to_csv(os.path.join(OUT, "E7_trace_nominal.csv"), index=False)
    _, tr = run("E7_trace_runs", "ieee30", 0, "Static re-convergence", record_traj=True,
                epochs=tuple(range(0, 6)), regimes=("S",))
    pd.DataFrame(tr).to_csv(os.path.join(OUT, "E7_trace_static.csv"), index=False)
    for m in ("Dynamic, no TARC", "RDOEM-MAS (TARC-R)"):
        att = dict(type="ATT-1", f_att=2, e0=8, e1=10)
        _, tr = run("E7_trace_runs", "ieee30", 0, m, record_traj=True, record_mats=True, attack=att,
                    epochs=(7, 8, 9, 10, 11), regimes=("S",), kkt=False)
        mats = [r for r in tr if r.get("mats")]
        rows = [r for r in tr if not r.get("mats")]
        pd.DataFrame(rows).to_csv(os.path.join(OUT, f"E7_trace_att_{m.split()[0]}_{'tarc' if 'TARC-R' in m else 'none'}.csv"),
                                  index=False)
        with open(os.path.join(OUT, f"E7_mats_{'tarc' if 'TARC-R' in m else 'none'}.pkl"), "wb") as f:
            pickle.dump(mats, f)


if __name__ == "__main__":
    todo = sys.argv[1:] or ["E7", "E1", "E4", "E5", "E3", "E6"]
    for e in todo:
        t0 = time.time()
        globals()[e]()
        print(f"== {e} done in {time.time() - t0:.0f}s", flush=True)

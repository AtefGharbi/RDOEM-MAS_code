# RDOEM-MAS simulation code (companion to manuscript v16)

Reproduces every number, table and figure in the revised manuscript.

## Layout
- `rdoem/systems.py` – IEEE 30/57/118 test systems (MATPOWER/PYPOWER cost data), agents, communication overlay, synthetic day/scenario generation (seeded).
- `rdoem/model.py` – local best responses, separable (R1) and network-coupled recourse, CVaR, welfare, centralized-KKT residual r_KKT.
- `rdoem/centralized.py` – centralized CVaR benchmark (CVXPY/Clarabel, extensive form).
- `rdoem/algorithms.py` – Algorithm 1 (price update, dynamic sum trackers, tail-weight averaging, re-anchoring), TARC-v15 and TARC-R, Metropolis-type and W-MSR comparators, static re-convergence baseline, attacks ATT-1…4.
- `run_experiments.py` – experiments E1 (nominal), E3 (beta), E4 (attacks), E5 (phase diagram), E6 (ablations), E7 (traces). Resumable: one CSV per run in `results/<exp>/`, keyed by a config hash.
- `make_figures.py` – figures (`figures/`) and summary tables (`results/summary_*`), incl. 95% t-CIs, paired Wilcoxon + Holm, rank-biserial.
- `tests/test_core.py` – merit-order recourse vs LP, central KKT residual ~0, doubly stochastic W, sum invariant under packet loss.

## Run
```
pip install numpy scipy pandas matplotlib networkx cvxpy pypower
python tests/test_core.py
python run_experiments.py            # E7 E1 E4 E5 E3 E6  (~1.5 CPU-hours)
python make_figures.py
```
Seed counts are set in `run_experiments.py` (20/10/5 per the manuscript); raise them for a ≥30-seed study.

## Scope
Copper-plate model (no line flows), synthetic profiles, synchronous rounds. See manuscript Section X.

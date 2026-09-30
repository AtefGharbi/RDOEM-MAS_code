"""Summaries and figure for revision-2 experiments (E8-E10)."""
import glob, os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import make_figures as M
RES, FIG = M.RES, M.FIG
out = {}
# ---------------- E8: equal-accuracy communication
ck = pd.concat([pd.read_pickle(f) for f in glob.glob(os.path.join(RES, "E8_ckpt_*.pkl"))], ignore_index=True)
peak = 268.0
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7))
grid = np.logspace(3, 5.3, 40)
e8 = {}
ck["method"] = ck["method"].replace({"Static re-convergence": "Static (tol 0.0001)"})
COL = dict(M.C); COL.update({"Static (tol 0.01)": "#f4a582", "Static (tol 0.001)": "#d6604d", "Static (tol 0.0001)": "#b2182b"})
for m, g in ck.groupby("method"):
    cur_gap, cur_dp = [], []
    for (s, t), h in g.groupby(["seed", "t"]):
        h = h.sort_values("msgs")
        idx = np.searchsorted(h.msgs.values, grid, side="right") - 1
        gp = np.where(idx >= 0, h.gap.values[np.maximum(idx, 0)], np.nan)
        dp = np.where(idx >= 0, np.abs(h.dP.values[np.maximum(idx, 0)]), np.nan)
        cur_gap.append(gp); cur_dp.append(dp)
        # messages to reach accuracy targets
        for lab, cond in [("dP<1%", np.abs(h.dP) < 0.01 * peak), ("dP<0.1%", np.abs(h.dP) < 0.001 * peak),
                          ("gap<1%", h.gap < 0.01), ("gap<0.5%", h.gap < 0.005)]:
            ok = np.where(cond.values)[0]
            # require the target to hold from that checkpoint onwards
            first = next((i for i in ok if cond.values[i:].all()), None)
            e8.setdefault((m, lab), []).append(h.msgs.values[first] if first is not None else np.nan)
    G = np.nanmedian(np.array(cur_gap), 0); D = np.nanmedian(np.array(cur_dp), 0)
    axs[0].semilogx(grid, 100 * G, label=m, color=COL[m]); axs[1].loglog(grid, D, label=m, color=COL[m])
axs[0].set_xlabel("cumulative messages in epoch"); axs[0].set_ylabel("median welfare gap (%)"); axs[0].set_ylim(-0.5, 5)
axs[1].set_xlabel("cumulative messages in epoch"); axs[1].set_ylabel("median |ΔP| (MW)")
axs[0].legend(fontsize=6.5)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig11_equal_accuracy.png"), bbox_inches="tight"); plt.close(fig)
tab = []
for (m, lab), v in e8.items():
    v = np.array(v, float)
    tab.append(dict(method=m, target=lab, reached=np.mean(~np.isnan(v)), median_msgs=np.nanmedian(v) if (~np.isnan(v)).any() else np.nan))
out["E8"] = pd.DataFrame(tab).to_dict("records")
# ---------------- E9: held-out seeds
d9 = M.collect("E9_heldout")
d9["phase"] = np.where(d9.t < 8, "pre", np.where(d9.t < 13, "during", "post"))
med = d9.groupby(["attack", "method", "phase"]).gap_S.median().unstack()
e9 = []
for a, g in d9.groupby("attack"):
    ps = g[g.phase == "during"].groupby(["method", "seed"]).gap_S.mean().unstack(0)
    pt = M.paired_tests(g, metric="gap_S", ref="Dynamic, no TARC", phase_filter=lambda x: x.phase == "during")
    rr = g[g.phase == "during"].groupby("method").agg(fp=("fp_rate", "mean"), rem=("att_edge_removal", "mean"))
    for m in ("Dynamic, no TARC", "RDOEM-MAS (TARC-R)"):
        r = dict(attack=a, method=m, pre=med.loc[(a, m), "pre"], during=med.loc[(a, m), "during"],
                 post=med.loc[(a, m), "post"], fp=rr.loc[m, "fp"], rem=rr.loc[m, "rem"],
                 ci_during=M.ci(ps[m]))
        if m != "Dynamic, no TARC" and len(pt):
            r.update(p_holm=float(pt.p_holm.iloc[0]), rb=float(pt.rank_biserial.iloc[0]))
        e9.append(r)
out["E9"] = e9
# ---------------- E10: sensitivity
d10 = M.collect("E10_sens")
d10["phase"] = np.where(d10.t < 8, "pre", np.where(d10.t < 13, "during", "post"))
base = d9[(d9.method == "RDOEM-MAS (TARC-R)") & (d9.attack == "ATT-1") & (d9.seed < 105)].copy()
base["variant"] = "default (rho_min=0.3, G=60, rho_mem=0.5)"
allv = pd.concat([base, d10], ignore_index=True)
e10 = []
for v, g in allv.groupby("variant", sort=False):
    e10.append(dict(variant=v, seeds=g.seed.nunique(),
                    during=g[g.phase == "during"].gap_S.median(), post=g[g.phase == "post"].gap_S.median(),
                    fp_pre=g[g.phase == "pre"].fp_rate.mean(), fp_during=g[g.phase == "during"].fp_rate.mean(),
                    rem=g[g.phase == "during"].att_edge_removal.mean()))
out["E10"] = e10
# ---------------- E5: per-seed spread for f_att = 1 (TARC-R)
d5 = M.collect("E5_phase"); d5 = d5[(d5.t >= 8) & (d5.f_att == 1) & (d5.method == "RDOEM-MAS (TARC-R)")]
ps = d5.groupby(["seed", "p_loss"]).gap_S.mean()
out["E5_f1"] = dict(n=len(ps), min=float(ps.min()), max=float(ps.max()), ci=M.ci(ps.values))
json.dump(out, open(os.path.join(RES, "summary_rev2.json"), "w"), indent=1, default=float)
print(pd.DataFrame(out["E8"]).to_string()); print(pd.DataFrame(e9).round(4).to_string()); print(pd.DataFrame(e10).round(4).to_string()); print(out["E5_f1"])

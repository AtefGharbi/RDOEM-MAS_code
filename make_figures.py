"""Generate figures (figures/*.png) and summary tables (results/summary_*.csv) from results/."""
import os, glob, pickle, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scipy import stats

ROOT = os.path.dirname(__file__)
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Serif", "axes.grid": True, "grid.alpha": 0.3,
                     "savefig.dpi": 200, "figure.dpi": 100})
C = {"RDOEM-MAS (TARC-R)": "#1f4e79", "RDOEM-MAS (TARC-v15)": "#7f7f7f", "Dynamic, no TARC": "#2ca02c",
     "Dynamic, no TARC, no re-anchor": "#98df8a", "W-MSR (f_W=1)": "#ff7f0e", "Static re-convergence": "#d62728"}


def collect(exp):
    fs = sorted(glob.glob(os.path.join(RES, exp, "*.csv")))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()


def ci(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (np.nan, np.nan, np.nan, len(x))
    m = x.mean()
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return (m, m - h, m + h, len(x))


def fmt(m, lo, hi, p=3, pct=False):
    if np.isnan(m):
        return "n/a"
    k = 100 if pct else 1
    return f"{m*k:.{p}f} [{lo*k:.{p}f}, {hi*k:.{p}f}]"


# ------------------------------------------------------------------ diagrams
def box(ax, x, y, w, h, text, fc="#dce6f2", ec="#1f4e79", fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, wrap=True)


def arrow(ax, x0, y0, x1, y1, text=None):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", lw=1, color="#333"))
    if text:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.02, text, fontsize=7, ha="center", color="#333")


def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.97, "Physical layer (copper-plate balance, fixed loss forecast)", ha="center", fontsize=8, style="italic")
    for i, (lab, fc) in enumerate([("Generator\nagents", "#f2dcdb"), ("Renewable\nagents", "#ebf1de"),
                                   ("Load\nagents", "#fde9d9"), ("Battery\nagents", "#e4dfec")]):
        box(ax, 0.04 + i * 0.24, 0.74, 0.18, 0.16, lab, fc=fc)
    box(ax, 0.04, 0.42, 0.9, 0.2,
        "Each EMA i:  local best response (IV-C)  |  price  $\\lambda_i$  |  mismatch tracker  $x_i$  |  "
        "scenario-cost trackers $\\hat Q_{i,m}$  |  quantile $\\zeta_i$  |  TARC trust state", fs=7.5)
    for i in range(4):
        arrow(ax, 0.13 + i * 0.24, 0.74, 0.13 + i * 0.24, 0.62)
    box(ax, 0.04, 0.12, 0.42, 0.2, "Authenticated synchronous\ncommunication layer (barrier,\nsequence numbers, packet loss)",
        fc="#f2f2f2", ec="#555")
    box(ax, 0.52, 0.12, 0.42, 0.2, "TARC: score -> raw trust -> mutual-min\nhandshake -> retained graph -> $W_k$\n(symmetric, doubly stochastic)",
        fc="#dce6f2")
    arrow(ax, 0.25, 0.42, 0.25, 0.32, "reports")
    arrow(ax, 0.73, 0.32, 0.73, 0.42, "$W_k$")
    ax.text(0.5, 0.03, "After negotiation: commit day-ahead schedule; realised deviations handled by recourse (IV-B)",
            ha="center", fontsize=7.5, style="italic")
    fig.savefig(os.path.join(FIG, "fig1_architecture.png"), bbox_inches="tight")
    plt.close(fig)


def fig_flowchart():
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    steps = ["1. Links: fresh authenticated reports (packet loss -> counter m_ij += 1)",
             "2. TARC score a_ij (innovation + price consistency), grace window after epoch boundary",
             "3. Raw trust update, gated scale history, mutual-min handshake -> retained edges",
             "4. Weights (4): w_ij = min(1/(d_i+1), 1/(d_j+1)) rho_eff;  w_ii = 1 - sum_j w_ij",
             "5. Price: lambda <- Proj[W lambda - eta_k x]",
             "6. Local best responses at lambda with averaged CVaR tail weights -> u, q",
             "7. Trackers: x <- W x + N(u+ - u);  Q_hat <- W Q_hat + N(q+ - q);  zeta <- local VaR(Q_hat)",
             "8. k = K ?  -> commit schedule; next epoch: re-anchor x = N u, Q_hat = N q; keep lambda, trust"]
    for i, s in enumerate(steps):
        y = 0.9 - i * 0.115
        fc = "#dce6f2" if i in (1, 2, 3) else ("#ebf1de" if i in (4, 5, 6) else "#f2f2f2")
        box(ax, 0.05, y - 0.045, 0.9, 0.085, s, fc=fc, fs=7.5)
        if i < len(steps) - 1:
            arrow(ax, 0.5, y - 0.045, 0.5, y - 0.07)
    ax.annotate("", xy=(0.05, 0.9), xytext=(0.05, 0.9 - 7 * 0.115),
                arrowprops=dict(arrowstyle="->", lw=1, color="#1f4e79", connectionstyle="arc3,rad=-0.4"))
    ax.text(0.0, 0.5, "round k+1", rotation=90, fontsize=7, color="#1f4e79", va="center")
    fig.savefig(os.path.join(FIG, "fig2_flowchart.png"), bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------ traces
def fig_traces():
    f = os.path.join(RES, "E7_trace_nominal.csv")
    if not os.path.exists(f):
        return
    d = pd.read_csv(f)
    d["g"] = np.arange(len(d))
    fig, axs = plt.subplots(3, 1, figsize=(7, 5.2), sharex=True)
    axs[0].plot(d.g, d.lam_mean, color=C["RDOEM-MAS (TARC-R)"], lw=1)
    axs[0].set_ylabel("mean price\n($/MWh)")
    axs[1].semilogy(d.g, d.dP.abs() + 1e-6, color="k", lw=0.8, label="|ΔP| (true)")
    axs[1].semilogy(d.g, d.x_dis + 1e-6, color="#ff7f0e", lw=0.8, label="‖J⊥x‖ (tracker disagreement)")
    axs[1].set_ylabel("MW"); axs[1].legend(fontsize=7, loc="upper right")
    axs[2].semilogy(d.g, d.sum_err + 1e-16, color="#2ca02c", lw=0.8)
    axs[2].set_ylabel("|mean(x) − Σu|\n(MW)"); axs[2].set_xlabel("communication round (6 epochs × 300)")
    for ax in axs:
        for t in range(1, 6):
            ax.axvline(t * 300, color="grey", lw=0.5, ls="--")
        for r in (100, 200):
            for t in range(6):
                ax.axvline(t * 300 + r, color="purple", lw=0.3, ls=":")
    axs[0].set_title("IEEE-30, seed 0: dashed = epoch boundary, dotted = within-epoch forecast refinement", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_convergence.png"), bbox_inches="tight")
    plt.close(fig)


def fig_prop4():
    """Empirical check of Proposition 4 on the price recursion under ATT-1."""
    out = {}
    fig, axs = plt.subplots(1, 2, figsize=(7, 2.8), sharey=True)
    for ax, tag, title in zip(axs, ("none", "tarc"), ("no defense", "TARC-R")):
        f = os.path.join(RES, f"E7_mats_{tag}.pkl")
        if not os.path.exists(f):
            continue
        mats = pickle.load(open(f, "rb"))
        hon = mats[0]["honest"]
        Nh = int(hon.sum())
        J = np.eye(Nh) - np.ones((Nh, Nh)) / Nh
        B = 10
        # honest subsystem: lam_h+ = W_hh lam_h + d_h, attacker reports and projection enter d_h
        e = [np.linalg.norm(J @ m["lam_prev"][hon]) for m in mats]
        gams, Ds = [], []
        for h in range(len(mats) // B - 1):
            Phi = np.eye(Nh)
            v = np.zeros(Nh)
            for r in range(B):
                m = mats[h * B + r]
                Whh = m["W"][np.ix_(hon, hon)]
                Whh = Whh + np.diag(1 - Whh.sum(1))          # attacker weight folded into self-loop
                dk = m["lam_next"][hon] - Whh @ m["lam_prev"][hon]
                Phi = Whh @ Phi
                v = Whh @ v + dk
            gams.append(np.linalg.norm(J @ Phi, 2))
            Ds.append(np.linalg.norm(J @ v))
        gB = float(np.quantile(gams, 0.5))
        b = e[0]
        env = [b]
        for g_h, D in zip(gams, Ds):
            b = g_h * b + D                      # time-varying form of Prop. 4 (per-block gamma_h)
            env.append(b)
        ks = np.arange(len(e))
        ax.semilogy(ks, np.array(e) + 1e-9, lw=0.7, label="‖J⊥λ^k‖ (measured)")
        ax.semilogy(np.arange(len(env)) * B, np.array(env) + 1e-9, "r--", lw=0.8, label="Proposition 5 envelope")
        att = [m["t"] in (8, 9) for m in mats]
        k_on = np.where(att)[0]
        if len(k_on):
            ax.axvspan(k_on[0], k_on[-1], color="orange", alpha=0.15, label="attack active")
        frac1 = float(np.mean(np.array(gams) > 0.999))
        ax.set_title(f"{title}: median γ_h={gB:.3f}; G1 fails in {100*frac1:.0f}% of blocks", fontsize=7.5)
        ax.set_xlabel("round (epochs 7–11)")
        viol = np.mean([e[(h + 1) * B] > env[h + 1] * (1 + 1e-9) for h in range(len(Ds)) if (h + 1) * B < len(e)])
        out[tag] = dict(gamma_median=gB, gamma_max=float(max(gams)), frac_blocks_no_contraction=frac1,
                        envelope_violations=float(viol), max_D=float(max(Ds)))
    axs[0].set_ylabel("price disagreement ($/MWh)")
    axs[0].legend(fontsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_prop4_check.png"), bbox_inches="tight")
    plt.close(fig)
    json.dump(out, open(os.path.join(RES, "summary_prop4.json"), "w"), indent=1)


# ------------------------------------------------------------------ E1
def e1_tables():
    d = collect("E1_nominal")
    if d.empty:
        return None
    d = d[d.t > 0]            # exclude day-start cold initialisation epoch
    rows = []
    for (case, m), g in d.groupby(["case", "method"], sort=False):
        per_seed = g.groupby("seed").agg(gap_S=("gap_S", "mean"), gap_C=("gap_C", "mean"), kkt_S=("kkt_S", "mean"),
                                         kkt_C=("kkt_C", "mean"), reached=("reached", "mean"),
                                         rounds=("rounds_to_tol", "median"), msgs=("msgs_to_tol", "median"),
                                         scal=("scal_to_tol", "median"), dP=("dP", lambda x: np.abs(x).mean()),
                                         N=("N", "first"), fp=("fp_rate", "mean"), kktc=("kkt_central_C", "mean"))
        r = dict(case=case, method=m, seeds=len(per_seed), N=int(per_seed.N.iloc[0]))
        for k in ("gap_S", "gap_C", "kkt_S", "kkt_C", "reached", "rounds", "msgs", "scal", "dP", "fp", "kktc"):
            r[k] = ci(per_seed[k])
        rows.append(r)
    return pd.DataFrame(rows), d


def fig_comm_welfare(d):
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6))
    for ax, case in zip(axs, ["ieee30", "ieee57", "ieee118"]):
        g = d[d.case == case]
        for m, gm in g.groupby("method"):
            ps = gm.groupby("seed").agg(gap=("gap_S", "mean"), msgs=("msgs_to_tol", "median"),
                                        reach=("reached", "mean"), tot=("msgs_total", "mean"))
            ax.scatter(ps.tot / 1e3, ps.gap * 100, s=10, color=C.get(m, "k"), alpha=0.7, label=m)
        ax.set_title(case.upper().replace("IEEE", "IEEE-"), fontsize=8)
        ax.set_xlabel("messages per epoch (×10³)")
    axs[0].set_ylabel("welfare gap, regime S (%)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=6.5, bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_welfare_vs_comm.png"), bbox_inches="tight")
    plt.close(fig)


def fig_kkt(d):
    fig, ax = plt.subplots(figsize=(7, 2.6))
    methods = [m for m in C if m in d.method.unique()]
    pos = 0
    ticks, labels = [], []
    for case in ["ieee30", "ieee57", "ieee118"]:
        for m in methods:
            g = d[(d.case == case) & (d.method == m)]
            if g.empty:
                continue
            for j, (col, hatch) in enumerate([("kkt_S", ""), ("kkt_C", "//")]):
                v = g.groupby("seed")[col].mean()
                ax.bar(pos + j * 0.4, v.mean(), 0.38, yerr=v.std(ddof=1) if len(v) > 1 else 0, color=C[m],
                       hatch=hatch, edgecolor="k", lw=0.4, capsize=2)
            ticks.append(pos + 0.2); labels.append(f"{case[4:]}\n{m.split('(')[0][:13]}")
            pos += 1
        pos += 0.5
    ax.set_xticks(ticks); ax.set_xticklabels(labels, fontsize=5.5)
    ax.set_ylabel("r_KKT / λ_ref")
    ax.set_title("Centralized-KKT residual at committed schedules (plain: separable R1; hatched: network-coupled)",
                 fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_kkt_residual.png"), bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------ E4 / E5
def e4_tables():
    d = collect("E4_attacks")
    if d.empty:
        return None, None
    d["phase"] = np.where(d.t < 8, "pre", np.where(d.t < 13, "during", "post"))
    rows = []
    for (a, m), g in d.groupby(["attack", "method"]):
        ps = g.groupby(["seed", "phase"]).agg(gap=("gap_S", "mean"), dP=("dP", lambda x: np.abs(x).mean()),
                                              dis=("lam_dis_final", "mean"), fp=("fp_rate", "mean"),
                                              rem=("att_edge_removal", "mean")).reset_index()
        r = dict(attack=a, method=m, seeds=ps.seed.nunique())
        for ph in ("during", "post"):
            q = ps[ps.phase == ph]
            r[f"gap_{ph}"] = ci(q.gap)
            r[f"dP_{ph}"] = ci(q.dP)
        q = ps[ps.phase == "during"]
        r["fp"] = ci(q.fp)
        r["rem"] = ci(q.rem)
        # paired test vs no defense on during-attack gap
        base = ps[(ps.phase == "during")].set_index("seed").gap
        rows.append(r)
    T = pd.DataFrame(rows)
    return T, d


def paired_tests(d, metric="gap_S", ref="Dynamic, no TARC", phase_filter=None, by="attack"):
    out = []
    for a, g in d.groupby(by):
        if phase_filter is not None:
            g = g[phase_filter(g)]
        ps = g.groupby(["method", "seed"])[metric].mean().unstack(0)
        others = [c for c in ps.columns if c != ref]
        pv = []
        for m in others:
            diff = (ps[m] - ps[ref]).dropna()
            if len(diff) < 3:
                continue
            w = stats.wilcoxon(diff) if (diff != 0).any() else None
            p = w.pvalue if w is not None else 1.0
            # matched-pairs rank-biserial correlation
            rk = stats.rankdata(np.abs(diff))
            rb = (rk[diff > 0].sum() - rk[diff < 0].sum()) / rk.sum() if rk.sum() > 0 else 0.0
            pv.append([a, m, len(diff), diff.mean(), p, rb])
        # Holm-Bonferroni within this group
        pv.sort(key=lambda z: z[4])
        k = len(pv)
        adj, prev = [], 0
        for i, z in enumerate(pv):
            pa = min(1.0, max(prev, (k - i) * z[4]))
            prev = pa
            adj.append(z + [pa])
        out += adj
    return pd.DataFrame(out, columns=[by, "method", "n", "mean_diff", "p_wilcoxon", "rank_biserial", "p_holm"])


def fig_attacks(d):
    atts = sorted(d.attack.unique())
    meths = [m for m in ["Dynamic, no TARC", "W-MSR (f_W=1)", "RDOEM-MAS (TARC-v15)", "RDOEM-MAS (TARC-R)"]
             if m in d.method.unique()]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8))
    for ax, ph in zip(axs, ("during", "post")):
        w = 0.8 / len(meths)
        for j, m in enumerate(meths):
            vals, errs = [], []
            for a in atts:
                v = d[(d.attack == a) & (d.method == m) & (d.phase == ph)].groupby("seed").gap_S.mean()
                vals.append(max(v.median(), 1e-5)); errs.append(0)
            ax.bar(np.arange(len(atts)) + j * w, vals, w, color=C[m], label=m, edgecolor="k", lw=0.3)
        ax.set_yscale("log")
        ax.set_xticks(np.arange(len(atts)) + 0.4 - w / 2)
        ax.set_xticklabels([a.replace(" (mismatch only)", "") for a in atts], fontsize=7)
        ax.set_title(f"{'During attack (epochs 8–12)' if ph == 'during' else 'After attack (epochs 13–17)'}", fontsize=8)
    axs[0].set_ylabel("median welfare gap (log)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=6.5, bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_attacks.png"), bbox_inches="tight")
    plt.close(fig)


def fig_phase():
    d = collect("E5_phase")
    if d.empty:
        return None
    d = d[d.t >= 8]
    meths = ["Dynamic, no TARC", "RDOEM-MAS (TARC-R)"]
    fig, axs = plt.subplots(1, 2, figsize=(7, 2.9), sharey=True)
    tabs = {}
    for ax, m in zip(axs, meths):
        g = d[d.method == m].groupby(["f_att", "p_loss"]).gap_S.median().unstack()
        tabs[m] = g
        N = d.N.iloc[0]
        im = ax.imshow(np.log10(np.maximum(g.values, 1e-4)), origin="lower", aspect="auto", cmap="viridis_r",
                       vmin=-4, vmax=1)
        ax.set_xticks(range(len(g.columns))); ax.set_xticklabels([f"{int(p*100)}" for p in g.columns])
        ax.set_yticks(range(len(g.index))); ax.set_yticklabels([f"{f}/{N}" for f in g.index])
        ax.set_xlabel("packet loss (%)"); ax.set_title(m, fontsize=8)
        for i in range(g.shape[0]):
            for j in range(g.shape[1]):
                v = g.values[i, j]
                ax.text(j, i, f"{v*100:.1f}" if v < 10 else ">999", ha="center", va="center", fontsize=6,
                        color="w" if np.log10(max(v, 1e-4)) > -1.5 else "k")
    axs[0].set_ylabel("f_att / N")
    cb = fig.colorbar(im, ax=axs, shrink=0.8)
    cb.set_label("log10 median gap")
    fig.savefig(os.path.join(FIG, "fig7_phase.png"), bbox_inches="tight")
    plt.close(fig)
    return tabs


# ------------------------------------------------------------------ E3 / E6
def e3_e6(d1):
    base = d1[(d1.case == "ieee30") & (d1.method == "RDOEM-MAS (TARC-R)")].copy()
    rows = []
    d3 = collect("E3_beta")
    if not d3.empty:
        b1 = base.copy(); b1["beta"] = 1.0
        allb = pd.concat([d3[d3.t > 0], b1], ignore_index=True)
        seeds = set(d3.seed.unique())
        allb = allb[allb.seed.isin(seeds)]
        for beta, g in allb.groupby("beta"):
            ps = g.groupby("seed").agg(EQ=("oos_EQ", "mean"), CV=("oos_CVaR", "mean"), gen=("gen_cost_S", "mean"),
                                       gap=("gap_S", "mean"), gapc=("gap_C", "mean"), kkt=("kkt_C", "mean"))
            rows.append(dict(beta=beta, seeds=len(ps), **{k: ci(ps[k]) for k in ps.columns}))
    T3 = pd.DataFrame(rows)
    if not T3.empty:
        fig, ax = plt.subplots(figsize=(4.2, 3.0))
        ax.errorbar([r[0] for r in T3["EQ"]], [r[0] for r in T3["CV"]],
                    xerr=[[r[0] - r[1] for r in T3["EQ"]], [r[2] - r[0] for r in T3["EQ"]]],
                    yerr=[[r[0] - r[1] for r in T3["CV"]], [r[2] - r[0] for r in T3["CV"]]], fmt="o-", color="#1f4e79",
                    ms=4, capsize=2)
        for _, r in T3.iterrows():
            ax.annotate(f"β={r.beta:g}", (r["EQ"][0], r["CV"][0]), fontsize=7, xytext=(4, 4), textcoords="offset points")
        ax.set_xlabel("out-of-sample E[recourse cost] ($/h)")
        ax.set_ylabel("out-of-sample CVaR 0.9 ($/h)")
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, "fig8a_risk_tradeoff.png"), bbox_inches="tight")
        plt.close(fig)
    d6 = collect("E6_ablation")
    rows = []
    if not d6.empty:
        seeds = set(d6.seed.unique())
        full = base[base.seed.isin(seeds)].copy(); full["tag"] = "full RDOEM-MAS (TARC-R)"
        st = d1[(d1.case == "ieee30") & (d1.method == "Static re-convergence") & d1.seed.isin(seeds)].copy()
        st["tag"] = "no dynamic tracking (static)"
        nr = d1[(d1.case == "ieee30") & (d1.method == "Dynamic, no TARC, no re-anchor") & d1.seed.isin(seeds)].copy()
        nr["tag"] = "no TARC, no re-anchoring"
        nt = d1[(d1.case == "ieee30") & (d1.method == "Dynamic, no TARC") & d1.seed.isin(seeds)].copy()
        nt["tag"] = "no TARC"
        allx = pd.concat([full, nt, nr, st, d6[d6.t > 0]], ignore_index=True)
        allx = allx[allx.t > 0]
        for tag, g in allx.groupby("tag", sort=False):
            ps = g.groupby("seed").agg(gap=("gap_S", "mean"), gapc=("gap_C", "mean"), kkt=("kkt_S", "mean"),
                                       reach=("reached", "mean"), dP=("dP", lambda x: np.abs(x).mean()),
                                       cv=("oos_CVaR", "mean"), msgs=("msgs_total", "mean"))
            rows.append(dict(tag=tag, seeds=len(ps), **{k: ci(ps[k]) for k in ps.columns}))
    T6 = pd.DataFrame(rows)
    if not T6.empty:
        fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8))
        y = np.arange(len(T6))
        for ax, col, lab in zip(axs, ("gap", "kkt"), ("welfare gap, regime S (%)", "r_KKT/λ_ref, regime S")):
            m = np.array([r[0] for r in T6[col]]) * (100 if col == "gap" else 1)
            lo = np.array([r[1] for r in T6[col]]) * (100 if col == "gap" else 1)
            hi = np.array([r[2] for r in T6[col]]) * (100 if col == "gap" else 1)
            ax.barh(y, m, xerr=[m - lo, hi - m], color="#9dc3e6", edgecolor="k", lw=0.4, capsize=2)
            ax.set_xlabel(lab)
            ax.set_yticks(y); ax.set_yticklabels(T6.tag if ax is axs[0] else [], fontsize=7)
            ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, "fig8b_ablation.png"), bbox_inches="tight")
        plt.close(fig)
    return T3, T6


def main():
    fig_architecture(); fig_flowchart(); fig_traces(); fig_prop4()
    out = {}
    r = e1_tables()
    if r is not None:
        T1, d1 = r
        T1.to_pickle(os.path.join(RES, "summary_E1.pkl"))
        fig_comm_welfare(d1); fig_kkt(d1)
        pt = paired_tests(d1[d1.case == "ieee30"], metric="msgs_total", ref="Static re-convergence", by="case")
        pt.to_csv(os.path.join(RES, "summary_E1_tests.csv"), index=False)
        T3, T6 = e3_e6(d1)
        T3.to_pickle(os.path.join(RES, "summary_E3.pkl")); T6.to_pickle(os.path.join(RES, "summary_E6.pkl"))
    T4, d4 = e4_tables()
    if T4 is not None:
        T4.to_pickle(os.path.join(RES, "summary_E4.pkl"))
        fig_attacks(d4)
        pt = paired_tests(d4, metric="gap_S", ref="Dynamic, no TARC", phase_filter=lambda g: g.phase == "during")
        pt.to_csv(os.path.join(RES, "summary_E4_tests.csv"), index=False)
    tabs = fig_phase()
    if tabs:
        pd.to_pickle(tabs, os.path.join(RES, "summary_E5.pkl"))
    print("figures:", sorted(os.listdir(FIG)))


if __name__ == "__main__":
    main()

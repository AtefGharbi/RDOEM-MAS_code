"""Assemble the revised manuscript as JSON blocks; numbers are read from ../rdoem/results."""
import os, sys, json
import numpy as np
import pandas as pd
from PIL import Image

ROOT = "/home/claude/rdoem"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import make_figures as M
from rdoem.systems import build_system
from rdoem.algorithms import nominal_gap

FIG = os.path.join(ROOT, "figures")
B = []


def H1(t): B.append(dict(type="h1", text=t))
def H2(t): B.append(dict(type="h2", text=t))
def P(*r): B.append(dict(type="p", runs=list(r)))
def BOX(*r): B.append(dict(type="box", runs=list(r)))
def EQ(t, n=None): B.append(dict(type="eq", text=t, num=n))
def LIST(items, ordered=False, inst=0): B.append(dict(type="list", items=items, ordered=ordered, instance=inst))
def TABLE(cap, header, rows, widths=None, note=None, size=15):
    B.append(dict(type="table", caption=cap, header=header, rows=rows, widths=widths, note=note, size=size))
def FIGURE(fn, cap, width=620):
    im = Image.open(os.path.join(FIG, fn))
    B.append(dict(type="figure", path=os.path.join(FIG, fn), aspect=im.height / im.width, caption=cap, width=width,
                  alt=cap))
def b(t): return dict(t=t, b=True)
def i(t): return dict(t=t, i=True)


# ------------------------------------------------------------------ numbers
T1, d1 = M.e1_tables()
allE1 = M.collect("E1_nominal")
T3 = pd.read_pickle("results/summary_E3.pkl")
T6 = pd.read_pickle("results/summary_E6.pkl")
T4, d4 = M.e4_tables()
tests4 = pd.read_csv("results/summary_E4_tests.csv")
tabs5 = pd.read_pickle("results/summary_E5.pkl")
p4 = json.load(open("results/summary_prop4.json"))
FULL, STAT, NOT = "RDOEM-MAS (TARC-R)", "Static re-convergence", "Dynamic, no TARC"


def r1(case, method, col):
    return T1[(T1.case == case) & (T1.method == method)][col].iloc[0]


def pc(x, p=2): return f"{100 * x:.{p}f}"


msgs = allE1[allE1.t > 0].groupby(["case", "method"]).msgs_total.mean()
ratio = {c: msgs[(c, FULL)] / msgs[(c, STAT)] for c in ("ieee30", "ieee57", "ieee118")}
syst = {}
for c in ("ieee30", "ieee57", "ieee118"):
    s = build_system(c, seed=0)
    syst[c] = dict(N=s.N, E=len(s.edges), nG=len(s.gi), nR=len(s.ri), nL=len(s.li), nB=len(s.bi),
                   peak=s.peak_load, gap=nominal_gap(s), lam=s.lam_ref)
gapS = {c: r1(c, FULL, "gap_S")[0] for c in syst}
gapC = {c: r1(c, FULL, "gap_C")[0] for c in syst}
med4 = d4.groupby(["attack", "method", "phase"]).gap_S.median().unstack()


def m4(a, m, ph): return med4.loc[(a, m), ph]


def t4(a, m, col):
    return T4[(T4.attack == a) & (T4.method == m)][col].iloc[0]


def ptest(a, m):
    r = tests4[(tests4.attack == a) & (tests4.method == m)]
    return (r.p_holm.iloc[0], r.rank_biserial.iloc[0]) if len(r) else (np.nan, np.nan)


e3 = {row.beta: row for _, row in T3.iterrows()}
e6 = {row.tag: row for _, row in T6.iterrows()}
S_GAP_RANGE = f"{pc(min(gapS.values()), 1)}–{pc(max(gapS.values()), 1)}%"
C_GAP_RANGE = f"{pc(min(gapC.values()), 1)}–{pc(max(gapC.values()), 1)}%"
RATIO = f"{min(ratio.values()):.1f}–{max(ratio.values()):.1f}"
A1n, A1r = m4("ATT-1", NOT, "during"), m4("ATT-1", FULL, "during")

R2 = json.load(open("results/summary_rev2.json"))
E8 = {(r["method"], r["target"]): r for r in R2["E8"]}
E9 = {(r["attack"], r["method"]): r for r in R2["E9"]}
E10 = R2["E10"]
E5f1 = R2["E5_f1"]
def e8(m, tgt):
    r = E8[(m, tgt)]
    return r["median_msgs"] / 1e3, 100 * r["reached"]
DYN, ST2, ST3, ST4 = "Dynamic, no TARC", "Static (tol 0.01)", "Static (tol 0.001)", "Static (tol 0.0001)"
H1n, H1r = E9[("ATT-1", NOT)]["during"], E9[("ATT-1", FULL)]["during"]
from rdoem.systems import build_system as _bs
EDGES = {c: [len(_bs(c, seed=s).edges) for s in rr] for c, rr in
         [("ieee30", range(20)), ("ieee57", range(10)), ("ieee118", range(5))]}
_d1 = allE1[allE1.t > 0]
NEG_S, NEG_C = (_d1.gap_S < 0).mean(), (_d1.gap_C < 0).mean()
MIN_S, MIN_C = _d1.gap_S.min(), _d1.gap_C.min()
def _vn(s): return s.replace("rho_min", "ρ_min").replace("rho_mem", "ρ_mem")



# ------------------------------------------------------------------ front matter
B.append(dict(type="title", text="Trust-Aware Dynamic Consensus for Risk-Aware Distributed Energy Management: "
                                  "Design, Conditional Analysis, and Simulation Evidence"))
B.append(dict(type="authors", text="Revised manuscript (v19) — author names and affiliations to be inserted"))
H1("Abstract")
P("This paper presents RDOEM-MAS, a trust-aware distributed energy-management architecture that combines "
  "peer-to-peer price negotiation, scenario-based recourse with a conditional value-at-risk (CVaR) term, dynamic sum "
  "tracking of the mismatch and of scenario recourse costs, CVaR tail-weight averaging, and trust-reweighted "
  "consensus (TARC). The theoretical contribution is conditional. Under common symmetric doubly stochastic mixing "
  "and uncorrupted exchanged tracker states, we establish a sum-tracking invariant, a tracking-error bound and an "
  "input-to-state disagreement bound. Under separable recourse, or a KKT-consistent marginal allocation, fixed "
  "points satisfy the centralized CVaR KKT conditions. For network-coupled recourse the agents use surrogate "
  "sensitivities, and the method is evaluated only as an approximate stationarity mechanism; convergence of the "
  "full coupled iteration, attack detection and Byzantine consensus are not established. On IEEE 30-, 57- and "
  f"118-bus cost data with synthetic scenarios, welfare gaps to the centralized optimum were {S_GAP_RANGE} "
  f"(separable) and {C_GAP_RANGE} (coupled). Communication depends on the accounting convention and the accuracy "
  f"target. Under a fixed 300-round budget, the static re-convergence baseline used {RATIO}× fewer messages than "
  "dynamic tracking. For holding the mismatch below 1% of peak, dynamic tracking without the TARC handshake "
  f"required a median of {e8(DYN, 'dP<1%')[0]:.1f}k messages per epoch and TARC-R required "
  f"{e8(FULL, 'dP<1%')[0]:.1f}k, compared with {e8(ST2, 'dP<1%')[0]:.1f}k for the best static configuration; at "
  "0.1% accuracy the static baseline was more reliable. On held-out seeds, a revised trust score (TARC-R) reduced "
  f"the median welfare gap during a constant-bias attack from {pc(H1n, 0)}% to {pc(H1r, 1)}%, but it left honest "
  "agents excluded after the attack and did not detect attacks confined to the mismatch payload.")
P(b("Index Terms— "), "Distributed algorithms, multi-agent systems, economic dispatch, dynamic sum tracking, "
  "conditional value-at-risk, resilient consensus, false data injection.")

# ------------------------------------------------------------------ I
H1("I. Introduction")
P("Consensus-based distributed economic dispatch replaces a central dispatcher with local price and mismatch "
  "exchanges among energy management agents (EMAs) [1], [16]–[18], [26], [27]. Two practical demands strain the "
  "classical design. First, uncertainty in renewable output and demand makes the tail of the recourse cost relevant, "
  "which motivates risk measures such as CVaR [12]. Second, consensus exchanges are an attack surface: false data "
  "injected into broadcast values can steer the dispatch [22], [24], [25], and resilient consensus rules such as "
  "W-MSR [4], [5] or trust-based weighting [8]–[10] trade robustness against efficiency and graph assumptions.")
P("This paper asks three questions. (Q1) Can a peer-to-peer price negotiation with dynamic sum tracking reproduce "
  "the centralized CVaR-augmented dispatch, and when is that reproduction exact rather than approximate? (Q2) Does "
  "dynamic tracking reduce communication relative to re-running static consensus to convergence? (Q3) Does folding "
  "an estimated trust score into the doubly stochastic weights limit the damage of false-data attacks, and at what "
  "cost to honest agents?")
H2("Contributions")
P("We classify each contribution by type, as requested in the review: a new algorithmic element, a new combination "
  "of existing mechanisms, a theorem, or an application-specific adaptation.")
P("In brief, the architecture combines dynamic sum tracking, CVaR tail-weight averaging and trust-reweighted "
  "consensus. The theory is conditional: under common symmetric doubly stochastic mixing and uncorrupted exchanged "
  "tracker states we establish a sum-tracking invariant and a disagreement bound, and under separable recourse or "
  "a KKT-consistent marginal allocation, fixed points satisfy the centralized CVaR KKT conditions. For "
  "network-coupled recourse the method is evaluated only as an approximate stationarity mechanism. The "
  "experiments quantify benefits and failure modes alike, including communication overhead, persistent trust "
  "exclusions and blindness to mismatch-only attacks.")
LIST([
    [b("Formulation (application-specific adaptation). "),
     "A two-stage day-ahead/recourse optimal energy management (OEM) problem with a Rockafellar–Uryasev CVaR term, instantiated with two recourse models: "
     "a separable fixed-policy model that satisfies the exact-separability assumption R1 by construction, and a "
     "network-coupled merit-order recourse that violates it. We define a centralized-KKT residual r_KKT (Section IV-E) "
     "that makes “approximate stationarity” measurable."],
    [b("Algorithm (new combination with two design elements introduced in this work). "),
     "Dynamic sum tracking of the mismatch and of every scenario recourse cost through trust-weighted symmetric "
     "consensus (Section V). The design elements introduced in this work are (i) ergodic averaging of CVaR tail weights, which removes a "
     "tail-set chattering we observed with the plain subgradient rule, and (ii) re-anchoring of the trackers at "
     "epoch boundaries, which removes the permanent sum error that injected data otherwise leaves. We also report a "
     "revised trust score, TARC-R, motivated by a failure of the originally specified score."],
    [b("Analysis (conditional theorems built on standard techniques). "),
     "A sum-tracking invariant that is exact for truthful exchanges, a tracking-error bound with explicit constants, fixed-point/KKT equivalence statements that separate "
     "existence, KKT equivalence and convergence, and a conditional input-to-state disagreement bound for the "
     "projected consensus recursion (Section VI). The proof techniques are standard [2], [28], [29]; the "
     "contribution is their precise scoping to this architecture."],
    [b("Empirical evaluation, including negative results. "),
     "IEEE 30/57/118-bus experiments with baselines, attacks, a packet-loss × adversary phase diagram, ablations, "
     "confidence intervals and paired tests; accompanying code intended to reproduce every reported number (Appendix C)."],
], ordered=True, inst=1)
P("The main findings are mixed and are stated as such. The distributed schedule approaches the centralized CVaR "
  f"optimum within {S_GAP_RANGE} (separable recourse) and {C_GAP_RANGE} (coupled recourse). Dynamic tracking saves "
  "messages at moderate accuracy but not at a fixed round budget, and it is less reliable than static "
  "re-convergence at high accuracy. TARC-R reduced the damage of constant-bias and scaling attacks on held-out "
  "seeds, but introduced persistent exclusions and did not detect mismatch-only attacks.")

# ------------------------------------------------------------------ II
H1("II. Related Work and Positioning")
H2("A. Distributed Economic Dispatch")
P("Incremental-cost consensus [26], consensus-plus-innovations [17], dispatch over directed and delayed networks "
  "[27], coordination of DERs with storage [16], economic dispatch with demand response [18], and ADMM-based "
  "dispatch with encrypted exchanges [23] establish the price-negotiation architecture that we retain. Zhang et "
  "al. [1] provide the online peer-to-peer reference; our static baseline re-runs consensus to tolerance at every "
  "price iteration and is our own implementation, not a reproduction of [1].")
H2("B. Dynamic Consensus and Gradient Tracking")
P("Dynamic average consensus tracks averages of time-varying inputs from their increments [3], [29]. Gradient "
  "tracking uses the same increment recursion inside distributed optimization [28]. Our mismatch tracker is this "
  "recursion scaled by N, applied to the dual gradient, so each agent estimates the network-wide sum. The scaling "
  "matters for stability: it multiplies the loop gain by N (Section V-D).")
H2("C. Risk-Aware Dispatch")
P("CVaR [12] and distributionally robust chance constraints [13]–[15], [20] are established in centralized and "
  "ADMM-based dispatch. Distributed CVaR designs typically keep a coordinator or apply CVaR per prosumer. Here the "
  "tail is defined on the network-wide scenario cost, which is itself tracked; this is what makes separability (R1) "
  "the decisive condition.")
H2("D. Resilient and Trust-Based Consensus")
P("W-MSR discards extreme neighbour values and is resilient under (2f+1)-robustness [4], [5], [7]. It has been "
  "applied to dispatch with (F+1, F+1)-robust graph conditions, and stealthy attacks on consensus dispatch have been "
  "characterized [24]. Trust-based approaches estimate a per-neighbour trust or reputation [8]–[11], [25]. "
  "Resilient resource allocation under false data injection is studied in [21]. TARC belongs to the trust-based "
  "line; it multiplies trust into the same doubly stochastic weights that carry the sum tracker. That coupling is "
  "exactly what exposes the tracker to injected mass (Section VIII-E).")
H2("E. Novelty Assessment")
TABLE("Table I. Component-level novelty assessment (search protocol in Appendix B)",
      ["Component", "Status", "Closest prior work", "What is specific here"],
      [["Price negotiation with N-scaled mismatch tracking", "Known technique", "[3], [28], [29]",
        "Applied jointly to mismatch and M scenario costs"],
       ["CVaR on tracked network-wide scenario cost", "New combination", "[12]–[15]",
        "Tail indicator computed from tracked sums; exact only under R1"],
       ["Ergodic tail-weight averaging", "Design element introduced here (empirically motivated)", "Subgradient averaging",
        "Removes tail-set chattering; ablation −13 pp gap"],
       ["Epoch re-anchoring of trackers", "Design element introduced here", "Reset control in consensus ED",
        "Restores the sum invariant after corrupted input"],
       ["TARC / TARC-R trust weights", "New combination", "[8]–[11], [25]",
        "Mutual-min trust inside doubly stochastic weights; gated scales"],
       ["Propositions 1–4", "Standard-technique theorems", "[2], [28]", "Scoped to retained-graph assumptions"],
       ["Centralized-KKT residual r_KKT", "Evaluation device", "—", "Coordinatewise directional residual"]],
      widths=[3, 2.2, 2, 3.2])
P("We therefore claim no new consensus or CVaR primitive. We claim a specific combination, two design elements "
  "whose value the ablations quantify, a precise statement of when the combination is exact, and an evaluation that "
  "includes its failure modes.")

# ------------------------------------------------------------------ III
H1("III. System and Threat Model")
H2("A. Agents and Local Models")
P("The system has n_G generator, n_R renewable, n_L load and n_B battery agents, N = n_G+n_R+n_L+n_B. The optional "
  "EV aggregator of the previous version is omitted, and no EV claim is made. Every agent reports a net injection "
  "s_i (supply minus demand, MW). Generators have cost C_i(P) = ½a_iP² + b_iP on [P_i^min, P_i^max], taken from the "
  "MATPOWER case data [30]. Renewable agents schedule P_R ≤ P̂_R (forecast availability) at cost ½a_RP² + b_RP. Loads "
  "have concave utility U_j(P) = φ_jP − ½ψ_jP² on [0.90, 1.05]·P̂_D,j, with ψ_j set by a price elasticity of 0.2 at "
  "the reference price λ_ref.")
P(b("Losses and local inputs. "), "P_loss = 0.02·Σ_j P̂_D,j is a fixed forecast parameter, not a decision-dependent "
  "quantity, and it carries no cost term. It enters the physical optimization model only through the day-ahead "
  "balance ΔP = Σ_i s_i − P_loss. The recourse balances contain the committed imbalance ΔP (equation (1a)), not "
  "P_loss separately, so losses are counted once. Its appearance in the partition P_loss = Σ_i ℓ_i, with "
  "ℓ_j = 0.02·P̂_D,j for load agents and ℓ_i = 0 otherwise, is bookkeeping for distributed tracking: it makes the "
  "tracker inputs u_i = s_i − ℓ_i sum to ΔP. Losses enter no local cost and no stationarity condition.")
P(b("Agent allocation. "), "One generator agent is created for every online generator of the case, and one load "
  "agent for every bus with positive demand. round(n_bus/8) renewable agents (alternately solar and wind) and "
  "round(n_bus/15) battery agents are placed at seeded random buses, so several agents may share a bus. IEEE-30 "
  f"therefore has N = {syst['ieee30']['nG']} + {syst['ieee30']['nR']} + {syst['ieee30']['nL']} + "
  f"{syst['ieee30']['nB']} = {syst['ieee30']['N']} agents, IEEE-57 has {syst['ieee57']['N']} and IEEE-118 has "
  f"{syst['ieee118']['N']} (Table IV). The counts are identical across seeds; the renewable and battery buses and "
  "the random overlay links vary with the seed.")
P(b("Reference price. "), "λ_ref is a normalization constant, computed as follows. At a trial price λ, each "
  "generator’s bounded risk-neutral response is P_i(λ) = Π_[P_i^min, P_i^max][(λ − b_i)/a_i]; renewables, loads, "
  "batteries and risk are ignored. Because every a_i > 0, the aggregate Σ_iP_i(λ) is continuous and nondecreasing, "
  "and it is flat only where all generators are saturated. λ_ref is the midpoint of the final bracket of a "
  "100-step bisection on [0, 10⁴] $/MWh for the price at which the aggregate equals 0.7·P_peak. Since "
  "0.7·P_peak = 0.56·Σ_iP_i^max lies strictly inside the aggregate’s range, such a price exists. λ_ref is "
  f"{syst['ieee30']['lam']:.2f} $/MWh for IEEE-30, whose MATPOWER linear cost coefficients are 1–3.25 $/MWh, and "
  f"{syst['ieee57']['lam']:.1f} and {syst['ieee118']['lam']:.1f} $/MWh for IEEE-57 and IEEE-118, whose coefficients "
  "are 20–40 $/MWh. The penalty parameters and price bounds that are defined relative to λ_ref (Section IV-C, "
  "Table II) are scaled with this normalization. Generator cost coefficients are the case data and are not "
  "rescaled.")
P("Each battery b has energy capacity E_b = 4·P_b^max × 1 h (MWh) and stored energy e_b (its state of charge, in "
  "MWh), kept in [0.1E_b, 0.9E_b]. Its power limits for the coming epoch are "
  "p̄_dis(e_b) = min{P_b^max, η_d(e_b − 0.1E_b)/Δt} and p̄_ch(e_b) = min{P_b^max, (0.9E_b − e_b)/(η_cΔt)}, with "
  "Δt = 1 h. It maximizes λ(p_dis − p_ch) + v_b(η_c p_ch − p_dis/η_d) − κ_b(p_ch² + p_dis²), with a quadratic "
  "degradation proxy (cf. [19]). The objective is separable in p_ch and p_dis, so the maximizer is "
  "p_dis = Π_[0, p̄_dis][(λ − v_b/η_d)/(2κ_b)] and p_ch = Π_[0, p̄_ch][(v_bη_c − λ)/(2κ_b)], where Π_[a,b] "
  "denotes projection onto [a, b]. After the epoch, the stored energy is updated with the committed powers:")
EQ("e_b⁺ = e_b + η_c p_ch Δt − p_dis Δt / η_d")
P(b("No simultaneous charge and discharge. "), "Assume η_cη_d < 1, v_b > 0 and κ_b > 0. The unconstrained "
  "maximizers are positive only if λ > v_b/η_d (discharge) or λ < v_bη_c (charge), and these two conditions cannot "
  "hold together because v_bη_c < v_b/η_d. Both projection intervals contain 0, and projection onto an interval "
  "containing 0 maps a nonpositive value to 0, so at most one projected power is positive. No assumption on the "
  "sign of the price is needed. This direct argument replaces Lemma 1 of the previous version for the model used "
  "here. The lookahead-horizon QP of the previous version is not used.")
FIGURE("fig1_architecture.png", "Fig. 1. RDOEM-MAS architecture: physical agents, per-agent states, the authenticated communication layer, and TARC weight construction.", 520)
H2("B. Communication Graph")
P("The communication graph is distinct from the electrical network. It joins agents at the same bus, agents at "
  "buses adjacent after contracting agent-free buses, and two seeded long-range links per agent. Without these "
  "links the IEEE-118 graph has a spectral gap of 0.0026 and the tracker–price loop was unstable (Section V-D). "
  "Links fail independently in each round with probability p_loss.")
H2("C. Uncertainty")
P("For each epoch, M = 30 equiprobable scenarios are drawn: aggregate load error with standard deviation 3% of "
  "demand, and multiplicative renewable error with standard deviation 18% and a common factor giving pairwise "
  "correlation ≈0.6, truncated to [0, capacity]. A further 500 independent draws are held out for out-of-sample "
  "evaluation. No distributional assumption enters the algorithm; Gaussian draws are a simulation choice.")
H2("D. Threat Model")
P("A compromised set A of f_att agents corrupts the price and/or mismatch payloads it broadcasts, identically to all "
  "neighbours (no equivocation). Identities, sequence numbers, link indicators, counters and trust records are "
  "authenticated by a lower layer that TARC assumes and does not provide. Scenario-cost and quantile payloads are "
  "not attacked in our experiments. Byzantine behaviour beyond this model is out of scope.")

# ------------------------------------------------------------------ IV
H1("IV. Risk-Aware Formulation")
H2("A. Timescales")
P("Epochs t are hourly dispatch intervals (24 per day). Within an epoch, agents run K synchronous communication "
  "rounds k and then commit a day-ahead schedule. Realized deviations are handled afterwards by recourse; "
  "negotiation is not re-run.")
H2("B. Centralized Problem")
EQ("max_{z, ζ, s}  W₀(z) − β[ζ + (1−α)⁻¹ Σ_m π_m s_m]   s.t.  ΔP(z) = 0,  s_m ≥ Q_m(z) − ζ,  s_m ≥ 0,  z ∈ Z", 1)
P("Here z = (z_1, …, z_N) stacks the agents’ physical decisions and Z is the product of their local boxes; the "
  "symbol x_i is reserved for the mismatch tracker. ΔP(z) = Σ_i s_i(z_i) − P_loss is the day-ahead mismatch "
  "(Section III-A), W₀ is utility minus generation cost plus battery value, and Q_m(z) is the recourse cost of "
  "scenario m. The constraints s_m ≥ Q_m(z) − ζ, s_m ≥ 0 are the Rockafellar–Uryasev representation of CVaR_α "
  "[12], with scenario probabilities π_m.")
H2("C. Two Recourse Models")
P(b("Regime S (separable, satisfies R1). "), "The aggregate load error ε_m is covered by generators with fixed "
  "participation κ_i ∝ P_i^max. Generator i pays c_i^up·min(n_im, H_i) + c^shed·(n_im − H_i)₊ for need "
  "n_im = κ_iε_m > 0 and headroom H_i = P_i^max − P_i (symmetrically, down-regulation at c_i^dn and spill at "
  "c^spill). Each renewable settles its own shortfall at c^short·(P_R,k − A_k,m)₊, where A_k,m is scenario "
  "availability. Hence Q_m = Σ_i q_i,m(z_i), each term depending only on the agent’s own decision.")
P(b("Regime C (network-coupled). "), "A recourse LP with one shared real-time balance: free renewable flexibility "
  "first, then generator regulation in merit order of c^up (or c^dn), then shedding (or spill). Q_m depends jointly on "
  "all headrooms, so R1 fails. It is evaluated in closed form; the closed form matches an LP solver in unit tests.")
P("Explicitly, scenario m has aggregate load-forecast error ε_m (MW, positive meaning more demand) and renewable "
  "availabilities A_k,m. The regime-C recourse decisions are r^up_i, r^dn_i ≥ 0, renewable outputs "
  "o_k,m ∈ [0, A_k,m], and shed_m, spill_m ≥ 0, with r^up_i ≤ P_i^max − P_G,i and r^dn_i ≤ P_G,i − P_i^min. They "
  "satisfy the single balance")
EQ("Σ_i r^up_i − Σ_i r^dn_i + Σ_k (o_k,m − P_R,k) + shed_m − spill_m = b_m(z),    b_m(z) := ε_m − ΔP(z)", "1a")
P("The committed day-ahead imbalance ΔP(z) enters only through b_m(z): a day-ahead surplus (ΔP > 0) reduces the "
  "upward requirement. P_loss appears only inside ΔP(z), so it is counted once. In regime S the same shift is "
  "applied to the generators’ fixed-participation need, n_i,m = κ_i(ε_m − ΔP(z)). In the centralized benchmark "
  "ΔP(z) = 0, so b_m = ε_m.")
P(b("Terminology. "), "“Regime C” and “network-coupled recourse” (shortened to “coupled recourse”) are "
  "synonyms, as are “regime S” and “separable recourse”. The “evaluation recourse model” of a regime is that "
  "regime’s own Q_m, which is used to score committed schedules and in the centralized benchmark.")
P("Cost parameters: c_i^up = 1.15b_i + 0.25λ_ref, c_i^dn = 0.10b_i + 0.05λ_ref, c^shed = 30λ_ref, "
  "c^spill = 2λ_ref, c^short = 3λ_ref. In both regimes the distributed agents use the separable costs q_i,m as their "
  "local contributions. In regime C these are a surrogate, which is the source of approximation.")
P(b("Convexity check. "), "Under a_i > 0, a_R > 0, ψ_j > 0 and κ_b > 0, W₀ is strictly concave, and every local "
  "minimization problem of Section V-A (a strictly convex cost plus a convex piecewise-linear risk term, over a box) "
  "is strictly convex. If any of these coefficients were zero, strict convexity of that agent’s problem would fail. "
  "In regime S, each q_i,m is convex piecewise linear in z_i, because the penalty slopes exceed the regulation "
  "slopes (c^shed > c^up, c^spill > c^dn).")
P("In regime C, Q_m(z) is the optimal value of the recourse LP defined by (1a). The LP is feasible for every z "
  "(shedding and spill are unbounded slacks) and bounded below by 0, so strong duality holds. Dualizing the "
  "balance (1a) with a scalar multiplier y and eliminating the capacity multipliers gives")
EQ("Q_m(z) = max_{−c^spill ≤ y ≤ c^shed} [ y·(b_m(z) + Σ_kP_R,k) − Σ_i (P_i^max − P_G,i)(y − c^up_i)₊ − Σ_i (P_G,i − P_i^min)(−y − c^dn_i)₊ − Σ_k A_k,m y₊ ]", "1b")
P("For every fixed y, the bracket is affine in z, because b_m(z), P_R,k, P_G,i and the headroom and footroom "
  "coefficients are affine in z; hence Q_m is a supremum of affine functions of z and therefore convex. In the "
  "implemented model the bracket is also concave and piecewise linear in y, with breakpoints only at the finitely "
  "many values {c^up_i, −c^dn_i, 0} and the interval endpoints {−c^spill, c^shed}. Its maximum over the interval "
  "is therefore attained at one of these points. So Q_m(z) is the maximum of finitely many affine functions of z, "
  "and it is piecewise affine on the whole domain.")
P("CVaR is convex and nondecreasing in (Q_1, …, Q_M), so β·CVaR(Q(z)) is convex, and problem (1) is convex in both "
  "regimes. What fails in regime C is therefore not convexity but R1: the local surrogate sensitivities ∂q_i,m "
  "differ from the centralized partial subgradients ∂_{z_i}Q_m. Regime S satisfies all assumptions of Propositions "
  "3–4; regime C satisfies all except R1.")
H2("D. Stationarity and the Exact/Approximate Distinction")
P("The CVaR quantities are distinguished as follows. π_m is the probability of scenario m (π_m = 1/M = 1/30 in all "
  "experiments). ζ is chosen as an α-quantile (VaR_α) of {Q_m}, so that Σ_{m: Q_m>ζ} π_m ≤ 1 − α ≤ "
  "Σ_{m: Q_m≥ζ} π_m. The tail indicator θ_m ∈ [0, 1] is then assigned in three cases: θ_m = 1 when Q_m > ζ; "
  "θ_m = 0 when Q_m < ζ; and, for Q_m = ζ, values θ_m ∈ [0, 1] chosen so that the total weighted tail mass "
  "Σ_m π_mθ_m equals 1 − α. The quantile inequalities guarantee that such an assignment exists. Our implementation "
  "gives all tied scenarios the same fraction. Every such θ yields a CVaR subgradient weight vector "
  "ω_m = π_mθ_m/(1 − α), with ω_m ≥ 0 and Σ_m ω_m = 1. ω̄_i,m is agent i’s running average of the weights it "
  "computes from its own tracked costs (Section V-D). For generator i, interior stationarity reads "
  "C_i′(P_i) + β g_i − λ = 0 with g_i = Σ_m ω_m ∂q_i,m/∂P_i; the sign of g_i is not restricted.")
BOX(b("Scope of the risk-aware result. "),
    b("Exact: "), "separable recourse (R1) or a proven KKT-consistent marginal allocation — local sensitivities then "
    "equal the centralized subgradients. ",
    b("Approximate: "), "network-coupled recourse with surrogate local sensitivities — measured by r_KKT and the "
    "welfare gap. ",
    b("Not established: "), "exact centralized optimality for general network-coupled recourse, and convergence of "
    "the coupled iteration to any fixed point.")
H2("E. Centralized-KKT Residual")
P("Let F(z) = −W₀(z) + β CVaR_α(Q(z)) with the evaluation recourse model, a_i = ∂ΔP/∂z_i ∈ {±1}, and Z_i the "
  "local box of coordinate i. With one-sided directional derivatives ∂⁻_iF and ∂⁺_iF (difference step "
  "10⁻⁴·max{1, P_peak/100 MW} MW), define")
EQ("r_KKT(z) = min_λ [ (1/n) Σ_i ρ_i(z, λ)² ]^½,   ρ_i = dist(0, [∂⁻_iF − λa_i, ∂⁺_iF − λa_i] + N_Zi(z_i))", 2)
P("r_KKT is a coordinatewise necessary stationarity diagnostic. It is zero whenever a compatible coordinatewise KKT "
  "selection exists, that is, whenever one common λ puts zero in every coordinate interval (plus normal cone). It is "
  "not a complete subgradient KKT certificate for the nonsmooth coupled problem, because a coordinatewise selection "
  "need not come from a single subgradient of F. We report r_KKT/λ_ref together with |ΔP|, which it excludes. At "
  "CVXPY solutions of the centralized problem r_KKT/λ_ref ≤ 10⁻⁶ in both regimes, which checks the implementation.")
P(b("Why r_KKT can be large while the gap is small. "), "With α = 0.9, M = 30 and π_m = 1/30, each tail scenario "
  "carries weight ω_m = (1/30)/0.1 = 1/3. Consider a renewable schedule near a piecewise-linear kink of the "
  "renewable’s shortfall cost in a tail scenario. One of its one-sided derivatives contains the jump "
  "βω_m c^short = λ_ref (β = 1, c^short = 3λ_ref) and the other does not, so that coordinate can show a residual of "
  "about λ_ref. If exactly one coordinate contributes and the other n − 1 contribute zero, the RMS definition (2) "
  "gives r_KKT ≈ λ_ref/√n. For the n = 34 decision coordinates of IEEE-30 (6 generators, 4 renewables, 20 loads, "
  "and 2 batteries with two powers each), this is ≈ 0.17λ_ref, while the welfare effect of a schedule a few kW "
  "from such a kink is below 0.01%. r_KKT must therefore be read together with the welfare gap.")

# ------------------------------------------------------------------ V
H1("V. RDOEM-MAS Algorithm")
H2("A. Local Best Responses")
P("Given its price λ_i and tail weights ω̄_i,m, each agent solves exactly its local minimization problem, which "
  "is the negative of its local welfare maximization (cost minus revenue, plus weighted risk). For a generator "
  "this is min ½a_iP² + b_iP − λ_iP + β Σ_m ω̄_i,m q_i,m(P) over [P^min, P^max]. Under the default "
  "local-quantile rule every weight vector ω(·) is nonnegative and sums to one, and so is its running average ω̄_i; "
  "with β ≥ 0 and each q_i,m convex, the risk term is therefore convex. The problem is solved by 32 bisection "
  "steps on the nondecreasing right derivative. Renewables are handled the same way; loads (the negative of "
  "concave utility plus payment) and batteries are solved in closed form. Decisions are recomputed in every round "
  "from the current price. The tracker input is u_i = s_i − ℓ_i.")
P(b("Surrogate contributions in regime C. "), "In both regimes every agent computes and tracks the separable "
  "fixed-policy costs q_i,m of Section IV-C, and uses their derivatives as its risk sensitivities. In regime S "
  "these are exact: Σ_i q_i,m = Q_m and ∂q_i,m = ∂_{z_i}Q_m. In regime C they are a surrogate: the agents do not use "
  "marginal contributions of the coupled merit-order recourse, and the tracked sums Σ_i q_i,m differ from the true "
  "Q_m. The coupled model is used only in the centralized benchmark and to evaluate committed schedules.")
H2("B. Weights on the Retained Graph")
P("Let R_k be the retained edge set of round k, common to both endpoints of every edge (Section VI, conditions "
  "(i)–(iv)), and let d_i be the degree of agent i in R_k; both endpoints of an edge therefore use the same d_i and "
  "d_j. For {i,j} ∈ R_k set w_ij = w_ji = min{1/(d_i+1), 1/(d_j+1)}·ρ_ij^eff. Here "
  "ρ^eff = ρ_edge^m_sh·min(ρ_ij, ρ_ji) ∈ (0, 1] is the mutual-minimum effective trust, identical at both endpoints. "
  "Set w_ij = 0 otherwise, and w_ii = 1 − Σ_j w_ij.")
P(b("Lemma 2 (weights). "), "W_k is symmetric and doubly stochastic, and w_ii ≥ 1/(d_i+1). ", i("Proof. "),
  "Symmetry holds because both factors of w_ij are symmetric in (i, j). Rows sum to one by the choice of w_ii, and "
  "symmetry then gives unit column sums. Each off-diagonal weight satisfies "
  "w_ij ≤ min{1/(d_i+1), 1/(d_j+1)} ≤ 1/(d_i+1), because ρ^eff ≤ 1. Agent i has d_i retained neighbours, so "
  "Σ_j w_ij ≤ d_i/(d_i+1) and w_ii ≥ 1 − d_i/(d_i+1) = 1/(d_i+1) > 0. All entries are nonnegative. ∎")
H2("C. Trust Scores: TARC-v15 and TARC-R")
P(b("TARC-v15 "), "(as specified in the previous version) scores a fresh report from j at receiver i as "
  "a_ij = ω₁(r^inn − 1)₊ + ω₂(r^x − 1)₊. Here r^inn = |λ_j^k − λ_j^last|/σ^inn is the price-innovation ratio and "
  "r^x = |x_j − x_i|/σ^x is the mismatch-consistency ratio. Each scale σ is 3× the median of the last L = 20 valid "
  "values plus a floor. Scores are dimensionless, and the dead zone r ≤ 1 gives honest reports a score of zero.")
P(b("TARC-R "), "(revised). Experiments exposed three failures of TARC-v15, detailed in Section VIII-E: an innovation "
  "score cannot see a constant bias; self-calibrating scales absorb a persistent attack within ≈40 rounds; and the "
  "mismatch-consistency term creates a deadlock after edges are removed. TARC-R responds with three changes. It "
  "replaces the mismatch term by cross-sectional price consistency r^p = |λ_j − λ_i|/σ^p, so that "
  "a_ij = 0.5(r^inn − 1)₊ + 0.5(r^p − 1)₊. It admits a report into the scale history only if a_ij ≤ 1 (gating). "
  "It freezes trust for G = 60 rounds after each epoch boundary, a publicly known time, so that legitimate "
  "transients are not scored.")
P("In both variants, raw trust follows ρ ← ρ_mem ρ + (1 − ρ_mem)e^(−γa) (ρ_mem = 0.8 for v15, 0.5 for R; γ = 1). "
  "Missing reports increment the counter m_ij and leave trust unchanged. Insufficient history (fewer than 5 reports) "
  "produces no score and does not increment the counter. An edge is retained iff the link is up, ρ^eff ≥ ρ_min = 0.3 "
  "and m_sh < τ_max = 5, where m_sh is taken from the previous round.")
H2("D. Price Update, Trackers and Step-Size Rule")
EQ("λ^{k+1} = Π_[0, 5λ_ref](W_k λ^k − η_k x^k),    x^{k+1} = W_k x^k + N(u^{k+1} − u^k),    x^0 = N u^0", 3)
EQ("Q̂^{k+1}_{·,m} = W_k Q̂^k_{·,m} + N(q^{k+1}_{·,m} − q^k_{·,m}),   ζ_i^{k+1} = VaR_α(Q̂^{k+1}_{i,·}),   ω̄^{k+1} = (1−ρ_k)ω̄^k + ρ_k ω(Q̂^k, ζ^k)", 4)
P(b("Time indices. "), "In (4), ω̄^{k+1} is formed from the round-k tracker values (Q̂^k, ζ^k), not from "
  "Q̂^{k+1}: it is computed before the responses. u^{k+1} and q^{k+1} are then computed from the new price λ^{k+1} "
  "and the new weights ω̄^{k+1}, while u^k and q^k are the responses computed from λ^k and ω̄^k. W_k is built "
  "after the round-k trust handshake and before any mixing, and the same W_k mixes λ, x and Q̂ in round k. Mixing "
  "uses the values reported by neighbours and the agent’s own true value. ω(Q̂, ζ) applies the tail rule of "
  "Section IV-D to each agent’s own tracked costs. Averaging uses ρ_k = 1/(1 + k/k_ω), with k_ω = 1. The quantile "
  "ζ_i is the local weighted α-quantile of the tracked scenario costs. It is exact once the trackers agree with "
  "the quantities they are designed to track; in regime C these are the surrogate scenario costs Σ_i q_i,m, not "
  "the true Q_m. The consensus–subgradient rule of the previous version is retained as an alternative; the two "
  "perform equivalently (Table VIII-B).")
P(b("Step size (empirical tuning rule). "), "Let ℓ_i be an upper bound, in MW per $/MWh, on the magnitude of the "
  "slope of agent i’s local unconstrained risk-neutral response: ℓ_i = 1/a_i for generators, 1/a_R for renewables, "
  "1/ψ_j for loads and 1/(2κ_b) for batteries. The actual response is flatter or nonsmooth in places. Box limits and "
  "recourse kinks make the slope set-valued in [0, ℓ_i]. For a battery, the net injection p_dis − p_ch has slope "
  "1/(2κ_b) only while one of the two powers lies strictly inside its interval; the slope is zero at saturation and "
  "in the dead band v_bη_c ≤ λ ≤ v_b/η_d, and the response is nonsmooth at the switching points. A price "
  "perturbation at agent i therefore changes u_i by at most ℓ_i per unit, and x_i by at most Nℓ_i, which motivates "
  "keeping ηNℓ_i small relative to the mixing rate.")
P("We use η₀ = c_η(1 − σ₂)/(N max_i ℓ_i), with c_η = 2, and η_k = η₀/(1 + k/100)^0.6. Here σ₂ is the second-largest "
  "eigenvalue modulus of the nominal (all links, full trust) weight matrix, an offline constant. This is an "
  "empirical tuning rule, motivated by the local response-slope bounds and the nominal spectral gap. It is not a "
  "convergence guarantee for the time-varying trust-weighted iteration, whose W_k differ from the nominal matrix. "
  "In pilot runs the loop was stable at c_η = 2 and unstable at c_η = 4 without decay.")
H2("E. Initialization, Stopping and Edge Cases")
LIST([["Day start: λ_i^0 = λ_ref; ω̄ = π (risk-neutral weights); x_i^0 = Nu_i^0; Q̂_i,m^0 = Nq_i,m^0; ζ_i^0 = "
       "VaR_α(Q̂_i,·^0); raw trust 1; counters 0."],
      ["Epoch boundary: λ and trust are kept. Trackers are re-anchored, x_i = Nu_i and Q̂_i = Nq_i, which restores the "
       "invariant (Proposition 2). Tail weights are re-initialized because scenario indices change."],
      ["Stopping: a fixed budget of K = 300 rounds. The tolerance test (max_i|x_i| < 0.01P_peak, |ΔP| < 0.01P_peak, "
       "max|Δλ| < 0.01λ_ref for 5 consecutive rounds) is an evaluation metric only (the “full test” of Table VI), because |ΔP| needs a central "
       "observer."],
      ["No retained neighbour: w_ii = 1. The agent updates its price from its own tracker, and its increments stay in "
       "the network sum, so the invariant is unaffected."],
      ["Feasibility: all local problems are feasible by construction (box constraints, bisection). Any committed "
       "day-ahead imbalance ΔP enters the recourse requirement, so the balance convention is preserved in the "
       "evaluation."]])
B.append(dict(type="algo", title="Algorithm 1: RDOEM-MAS (one epoch t)", lines=[
    dict(runs=["Input: forecasts, scenarios {ξ_m, π_m}, α, β, K, G, weight-rule and trust parameters; warm states "
               "λ^0, trust and counters from the previous epoch."]),
    dict(runs=["Initialize (k = 0): ω̄^0 = ω(Q̂^prev, ζ^prev) from the previous epoch’s trackers (π at day start); "
               "(u^0, q^0) = best responses at (λ^0, ω̄^0); re-anchor x^0 = Nu^0 and Q̂^0 = Nq^0; ζ^0 is carried "
               "over and refreshed after the first tracker update (day start: ζ_i^0 = VaR_α(Q̂^0_{i,·}))."]),
    dict(runs=["for k = 0, 1, …, K − 1 do"]),
    dict(level=1, runs=["1. Exchange authenticated reports (λ_j^k, x_j^k, Q̂_j^k, ζ_j^k); a lost link increments "
                        "m_ij at both endpoints."]),
    dict(level=1, runs=["2. TARC: if k ≥ G, score fresh reports and update raw trust and gated scale histories; "
                        "mutual-min handshake → common retained edge set R_k."]),
    dict(level=1, runs=["3. Build W_k from R_k by the rule of Section V-B (after the handshake, before any mixing)."]),
    dict(level=1, runs=["4. Price: λ^{k+1} = Π(W_kλ^k − η_k x^k)."]),
    dict(level=1, runs=["5. Tail weights: ω̄^{k+1} = (1 − ρ_k)ω̄^k + ρ_k ω(Q̂^k, ζ^k)."]),
    dict(level=1, runs=["6. Responses: (u^{k+1}, q^{k+1}) = local best responses at (λ^{k+1}, ω̄^{k+1})."]),
    dict(level=1, runs=["7. Trackers: x^{k+1} = W_k x^k + N(u^{k+1} − u^k); Q̂^{k+1} = W_k Q̂^k + N(q^{k+1} − q^k)."]),
    dict(level=1, runs=["8. Quantile: ζ_i^{k+1} = VaR_α(Q̂^{k+1}_{i,·})."]),
    dict(runs=["end for"]),
    dict(runs=["Commit the day-ahead schedule z^K; after uncertainty is realized, apply recourse (Section IV-C). "
               "Carry λ^K, trust and counters to the next epoch. In steps 4 and 7, neighbours’ reported values and "
               "the agent’s own true value are mixed."]),
]))
FIGURE("fig2_flowchart.png", "Fig. 2. One communication round of RDOEM-MAS with TARC-R and the dynamic trackers (Algorithm 1).", 540)
TABLE("Table II. Parameters used in all experiments unless stated otherwise",
      ["Group", "Parameter", "Value / selection rule"],
      [["Negotiation", "K, epochs/day", "300 rounds; 24"],
       ["", "Price step", "η₀ = 2(1−σ₂)/(N max ℓ_i); η_k = η₀/(1+k/100)^0.6; λ ∈ [0, 5λ_ref]"],
       ["", "Tail-weight averaging", "ρ_k = 1/(1 + k/k_ω), k_ω = 1"],
       ["Risk", "α, β, M, out-of-sample", "0.9; 1 (sweep 0, 0.5, 2); 30 equiprobable; 500"],
       ["", "Quantile", "local weighted VaR (alt.: η_ζ,k = 0.2Q_ref/(k+1)^0.75, Q_ref = 0.05λ_ref P_peak)"],
       ["TARC-v15", "ρ_mem, γ, ω₁, ω₂, a_max", "0.8, 1, 0.5, 0.5, 10"],
       ["", "L, L_min, c_σ, floors", "20, 5, 3, 0.005λ_ref and 0.002P_peak"],
       ["", "ρ_min, ρ_edge, τ_max", "0.3, 0.9, 5"],
       ["TARC-R", "changes vs v15", "ρ_mem = 0.5; weights 0.5 innovation / 0.5 price consistency / 0 mismatch; "
                                    "gate a ≤ 1; grace G = 60"],
       ["Battery", "η_c, η_d, SOC, κ_b, v_b", "0.95, 0.95, [0.1, 0.9]E, 0.3λ_ref/(2P_b^max), λ_ref; E = 4P_b^max"],
       ["System", "Peak demand, renewables", "0.8ΣP_G^max; capacity 0.3·peak/0.55"],
       ["", "Graph", "contracted electrical neighbourhood + 2 random links/agent"]],
      widths=[1.5, 2.5, 5.5])
H2("F. Message Accounting")
P("A message is one packet sent by one agent to one neighbour in one round. Attempted transmissions are counted "
  "whether or not they are lost. Let E be the undirected communication edge set and K the round budget.")
LIST([["Dynamic tracking without TARC sends N_data = 2|E|K data messages per epoch, each carrying 4 + M scalars "
       "(λ_j, x_j, ζ_j, the sender degree, and M values Q̂_j,m)."],
      ["TARC adds N_hs = 2|E|K handshake messages of 4 scalars (raw trust, counter, retention decision, sequence "
       "number), so N_msg = N_data + N_hs = 4|E|K, with data messages of 3 + M scalars."],
      ["The static baseline sends N_msg = 2|E|Σ_p r_p messages of 3 + M scalars, where r_p is the number of inner "
       "consensus rounds at price iteration p."]])
P("For IEEE-30 (|E| = 115, K = 300) this gives 69,000 messages per epoch without TARC and 138,000 with TARC. If the "
  "handshake fields are piggybacked on data packets, the TARC message count equals the no-TARC count and only the "
  "payload grows, by 4/(3+M) ≈ 12%. We report the conservative separate-packet count.")

# ------------------------------------------------------------------ VI
H1("VI. Theoretical Analysis")
P(b("Assumption G1 (retained-graph mixing). "), "(a) N is fixed. (b) In every round all agents apply the same W_k, "
  "which is symmetric and therefore row- and column-stochastic. (c) Every retained off-diagonal weight is at least "
  "w_min = ρ_min/(d_max+1), and every diagonal weight is at least 1/(d_max+1). (d) The union of retained graphs over "
  "every window of B₀ consecutive rounds is connected (uniform joint connectivity). G1 is an assumption on the "
  "retained graph; TARC does not guarantee it.")
P(b("Proposition 1 (consensus mixing only). "), "Under G1 there exist B ≥ B₀ and γ_B ∈ (0,1) such that "
  "‖J_⊥W_{k+B−1}⋯W_k‖₂ ≤ γ_B for every k, with J_⊥ = I − 11ᵀ/N. ",
  i("Scope: "), "a property of the matrix sequence only; it implies nothing about prices or decisions.")
P(b("Proposition 2 (dynamic sum tracking). "), "Let x^{k+1} = W_kx^k + N(u^{k+1} − u^k), where every agent "
  "mixes truthful tracker states with a common symmetric doubly stochastic W_k, and let x^0 = Nu^0. (a) For all k, "
  "(1/N)1ᵀx^k = 1ᵀu^k. (b) Suppose in addition that G1 holds with block length B and contraction factor γ_B "
  "(Proposition 1). Let Φ(t, s) = W_{t−1}⋯W_s with Φ(s, s) = I, let "
  "δ_h = max_{0≤r<B}‖u^{hB+r+1} − u^{hB+r}‖, and define")
EQ("c_B = N Σ_{r=0}^{B−1} sup_h ‖J_⊥Φ(hB+B, hB+r+1)‖  ≤  NB", 5)
P("Then ‖J_⊥x^{(h+1)B}‖ ≤ γ_B‖J_⊥x^{hB}‖ + c_Bδ_h, and limsup_h‖J_⊥x^{hB}‖ ≤ c_B·sup_h δ_h/(1 − γ_B). If, "
  "moreover, u^k converges to some u^∞, then x_i^k → Σ_j u_j^∞ for every i.")
P(i("Proof of (a). "), "1ᵀx^{k+1} = 1ᵀW_kx^k + N1ᵀ(u^{k+1} − u^k) = 1ᵀx^k + N(1ᵀu^{k+1} − 1ᵀu^k), using "
  "1ᵀW_k = 1ᵀ. With 1ᵀx^0 = N1ᵀu^0, induction gives 1ᵀx^k = N1ᵀu^k. ∎")
P(i("Proof of (b). "), "Unrolling B rounds gives x^{(h+1)B} = Φ(hB+B, hB)x^{hB} + "
  "NΣ_{r=0}^{B−1}Φ(hB+B, hB+r+1)(u^{hB+r+1} − u^{hB+r}). Each W_k is symmetric and doubly stochastic, so J_⊥ "
  "commutes with W_k, and J_⊥Φx = J_⊥ΦJ_⊥x. Hence ‖J_⊥Φ(hB+B, hB)x^{hB}‖ ≤ ‖J_⊥Φ(hB+B, hB)‖·‖J_⊥x^{hB}‖ "
  "≤ γ_B‖J_⊥x^{hB}‖ by Proposition 1. Applying J_⊥ to the sum and bounding each increment by δ_h gives the term "
  "c_Bδ_h. Since ‖J_⊥‖ = 1 and every Φ has unit spectral norm, c_B ≤ NB. Iterating the scalar recursion gives the "
  "limsup bound. If u^k → u^∞, then δ_h → 0, and the recursion with γ_B < 1 gives ‖J_⊥x^{hB}‖ → 0. Within a "
  "block, ‖J_⊥x^{hB+r}‖ ≤ ‖J_⊥x^{hB}‖ + NBδ_h → 0 as well. By (a), mean(x^k) = 1ᵀu^k → 1ᵀu^∞, so every "
  "x_i^k → Σ_j u_j^∞. This is the standard dynamic-consensus argument [3], [29], stated for the N-scaled sum. ∎")
BOX(b("Remark (sum, not average; conditions for exactness). "), "Each x_i estimates Σ_j u_j = ΔP, the day-ahead "
    "mismatch that the price must drive to zero; it does not estimate the average. Invariant (a) uses only "
    "1ᵀW_k = 1ᵀ, which the construction guarantees when four conditions hold in every round. (i) The status of every "
    "link is common to both endpoints, fixed by the authenticated handshake; in our simulations a lost link is lost "
    "in both directions. (ii) Both endpoints use the same effective trust ρ^eff = ρ_edge^m_sh·min(ρ_ij, ρ_ji) and the "
    "same retention decision. (iii) Degrees are computed on that common retained graph, so w_ij = w_ji. (iv) All "
    "agents apply W_k synchronously. Under (i)–(iv), packet loss only zeroes symmetric pairs of weights and the "
    "invariant stays exact. If one endpoint could retain an edge that its neighbour drops, for example after a "
    "one-sided loss without handshake, W_k would be non-symmetric and the invariant would fail. Corrupted reports "
    "also break it: an honest agent mixing y_j = x_j + b_j adds w_ij b_j to 1ᵀx, and doubly stochastic mixing "
    "conserves that error. Re-anchoring (Section V-E) restores the base case at every epoch.")
P(b("Proposition 3 (fixed-point characterization under exact tracking). "), "The proposition applies to any "
  "allocation of the scenario costs into local contributions q_i,m with Σ_i q_i,m(z_i) = Q_m(z), in particular to "
  "regime S. In regime C the tracked contributions are surrogates with Σ_i q_i,m ≠ Q_m, and the statement then "
  "characterizes the surrogate problem only. Fix an epoch, and let λ* lie in the interior of the price interval. "
  "Let z^loc(λ, ω̄) be the vector of local best responses (Section V-A). Write q*_i,m = q_i,m(z_i^loc(λ*, ω*)) "
  "and Q*_m = Σ_i q*_i,m. Consider the state S* in which, for every agent i, λ_i = λ*, x_i = 0, Q̂_i,m = Q*_m, ζ_i "
  "is the α-quantile ζ* of {Q*_m}, and ω̄_i = ω* = ω(Q̂, ζ*). Assume three conditions.")
LIST([["(A1) Every local problem is strictly convex, so z^loc(λ*, ω*) is unique."],
      ["(A2) No Q*_m equals ζ*."],
      ["(A3) ΔP(z^loc(λ*, ω*)) = 0."]])
P("Then S* is invariant under one round of Algorithm 1 for every step size and every retained graph.")
P(i("Proof. "), "First, the tracker state is consistent with Proposition 2(a). By the invariant and (A3), "
  "(1/N)1ᵀx = Σ_i u_i = ΔP(z^loc(λ*, ω*)) = 0. Because x is consensual in S*, every x_i equals this mean, so "
  "x_i = 0. Likewise, (1/N)1ᵀQ̂_{·,m} = Σ_i q*_i,m = Q*_m, so the consensual value Q̂_i,m = Q*_m is the one that "
  "the invariant for the scenario-cost trackers requires. Second, one round leaves S* unchanged. The price step "
  "returns W_kλ* − η_k·0 = λ*. By (A2), ω(Q̂, ζ*) = ω*, so the averaged weights stay at ω*. By (A1), the responses "
  "at (λ*, ω*) are unchanged, so u and q do not change and their increments vanish. Consensual vectors are fixed "
  "by every W_k, so x = 0 and Q̂ are preserved, and the recomputed quantile is ζ*. ∎")
P(i("Existence. "), "Assume R1 (so Σ_i q_i,m = Q_m and ∂q_i,m = ∂_{z_i}Q_m), the conditions of the convexity "
  "check, and a centralized KKT pair (z*, λ*) with λ* in the interior whose optimal ζ* is tied with no Q_m(z*). "
  "The tail weights at z* are then the indicator weights ω*. Under R1 the centralized KKT inclusion decomposes "
  "into each agent’s local optimality condition at (λ*, ω*), so z^loc(λ*, ω*) = z* by strict convexity. Hence "
  "(A1)–(A3) hold, and S* is a fixed point. If some Q_m(z*) ties with ζ*, the KKT subgradient may need particular "
  "fractional weights that the rule ω(·) need not produce at S*. Existence of a fixed point of Algorithm 1 is then "
  "not established, and the running averages ω̄ can only approach such weights (Section VIII-G). Existence of an "
  "optimizer of (1) does not by itself imply existence of a fixed point.")
P(b("Proposition 4 (centralized KKT equivalence under separability). "), "Let S̄ be a fixed point of one round in "
  "which four things hold. The price is consensual, λ_i = λ̄, in the interior of the interval. The trackers "
  "satisfy x̄_i = 0 and Q̂_i,m = Σ_j q_j,m(z̄_j). The averaged weights are common, ω̄_i = ω̄, and satisfy the "
  "tail-weight constraints of Section IV-D at the tracked costs. Finally, z̄ is the corresponding vector of "
  "responses. By Proposition 2(a) (uncorrupted states), ΔP(z̄) = 0.")
LIST([["(a) If β = 0, (z̄, λ̄) satisfies the centralized KKT conditions of (1)."],
      ["(b) If β > 0 and R1 holds, or the allocation is proven KKT-consistent (Σ_i q_i,m = Q_m and "
       "∂q_i,m(z_i) ⊆ ∂_{z_i}Q_m(z)), then (z̄, λ̄) satisfies the centralized CVaR KKT conditions."],
      ["(c) Without R1, (z̄, λ̄) satisfies the KKT conditions of the surrogate problem in which Σ_i q_i,m replaces "
       "Q_m. Its distance from the centralized conditions is what r_KKT diagnoses."]])
P(i("Proof. "), "Local optimality of each agent gives a selection: for each m there is a local subgradient "
  "g_i,m ∈ ∂q_i,m(z̄_i), and a normal-cone element ν_i ∈ N_Zi(z̄_i), such that "
  "0 = ∇f_i(z̄_i) + βΣ_m ω̄_m g_i,m − λ̄a_i + ν_i. Under R1, Q_m(z) = Σ_i q_i,m(z_i) with each term depending only "
  "on z_i, so for each scenario m the stacked vector g_m = (g_1,m, …, g_N,m) belongs to ∂Q_m(z̄). Because ω̄ "
  "satisfies the CVaR tail-weight conditions of Section IV-D at Q(z̄), the combination Σ_m ω̄_m g_m belongs to "
  "∂CVaR_α(Q(z̄)); this holds since Q_m is convex and CVaR_α is convex and nondecreasing in (Q_1, …, Q_M). "
  "Stacking the local conditions therefore yields 0 ∈ ∂F(z̄) − λ̄a + N_Z(z̄), with ν = (ν_1, …, ν_N) ∈ N_Z(z̄). "
  "Together with ΔP(z̄) = 0 and the convexity of Section IV-C, this is the centralized KKT inclusion of (1). For a "
  "KKT-consistent allocation the same argument applies with ∂q_i,m(z_i) ⊆ ∂_{z_i}Q_m(z) in place of R1. ∎")
P(b("Remark (convergence). "), "Neither proposition asserts convergence. Convergence of the coupled "
  "price–decision–tracker–trust iteration from arbitrary initial states is not established and is assessed only "
  "empirically (Section VIII).")
P(b("Proposition 5 (conditional input-to-state disagreement bound for the projected consensus recursion). "),
  "Let y^{k+1} = W_ky^k + d_k with W_k satisfying G1 and e_k = J_⊥y^k, where y is a generic consensus state such as the price vector. If the block-projected disturbance "
  "v_h = J_⊥Σ_r Φ(hB+B, hB+r+1)d_{hB+r} satisfies ‖v_h‖ ≤ D_h, then ‖e_{(h+1)B}‖ ≤ γ_B‖e_{hB}‖ + D_h and "
  "limsup‖e_{hB}‖ ≤ sup_h D_h/(1 − γ_B).")
P(i("Application to TARC. "), "For the price recursion, d_k collects −η_kx^k, the attack contribution "
  "Σ_{j∈A} w_ij b_j, and the projection residual. The bound applies to TARC only after two things are verified "
  "analytically or empirically: that this combined disturbance is bounded, and that the retained graph satisfies G1. "
  "Proposition 5 says nothing about detection, edge removal or Byzantine resilience. In our attack traces G1 failed "
  "in most blocks under TARC-R (Section VIII-F).")
TABLE("Table III. Status of each claim",
      ["Claim", "Status", "Conditions / evidence"],
      [["Sum-tracking invariant (Proposition 2a)", "Exact under stated conditions", "Common symmetric doubly stochastic W, x⁰ = Nu⁰, "
        "uncorrupted exchanged tracker states; "
        "measured error ≤ 10⁻¹³ MW"],
       ["Disagreement contraction (Proposition 1), tracking bound (Proposition 2b)", "Conditional", "G1"],
       ["Fixed-point invariance (Proposition 3); KKT equivalence (Proposition 4)", "Conditional, exact", "Strict convexity, no tie; R1 or "
        "consistent allocation, exact trackers"],
       ["Risk-aware stationarity under coupled recourse", "Approximate", f"Gap {pc(min(gapC.values()), 1)}–"
        f"{pc(max(gapC.values()), 1)}%; r_KKT reported"],
       ["Convergence of the coupled iteration", "Not established", "Empirical only; tolerance reached in few "
        "epochs within K = 300"],
       ["ISS disagreement bound (Proposition 5)", "Conditional", "Bounded combined disturbance and G1; G1 violated "
        "in attack traces"],
       ["Attack detection, Byzantine consensus", "Not established", "Empirical, attack-dependent (Section VIII-E)"],
       ["Communication reduction by dynamic tracking", "Accuracy- and budget-dependent",
        f"Fewer messages at 1% accuracy; static used {RATIO}× fewer at fixed K and was more reliable at 0.1%"]],
      widths=[3.2, 1.6, 4.2])

# ------------------------------------------------------------------ VII
H1("VII. Experimental Setup")
TABLE("Table IV. Test systems (cost data from MATPOWER cases [30]; profiles synthetic)",
      ["System", "N (G/R/L/B)", "|E|: mean over evaluation seeds (range)", "1 − σ₂ (seed 0)", "Peak demand (MW)",
       "λ_ref ($/MWh)"],
      [[c.upper().replace("IEEE", "IEEE-"), f"{v['N']} ({v['nG']}/{v['nR']}/{v['nL']}/{v['nB']})",
        f"{np.mean(EDGES[c]):.1f} ({min(EDGES[c])}–{max(EDGES[c])})", f"{v['gap']:.3f}", f"{v['peak']:.0f}",
        f"{v['lam']:.2f}"] for c, v in syst.items()],
      widths=[1.3, 2, 2.2, 1.2, 1.6, 1.4],
      note="|E| varies with the seeded overlay links. Message counts use each seed’s own |E|; for example, IEEE-118 "
           "has mean |E| = 626.6 over seeds 0–4, so 4·626.6·300 = 751,920 ≈ 752k messages per epoch with TARC.")
P("Data. Generator costs and limits come from the IEEE cases. Demand is scaled so that the peak hour uses 80% of "
  "generation capacity, which makes headroom, and hence risk, matter. Daily load and solar/wind shapes and all "
  "forecast errors are synthetic and seeded. No measured data set is used; validation on measured profiles "
  "(e.g., NREL, PJM, ENTSO-E) remains future work. The model is copper-plate: there are no line flows, voltage "
  "or frequency, so grid-constraint metrics are not reported.")
P("Methods. (1) Centralized CVaR benchmark (CVXPY/Clarabel, extensive form) under the same scenarios and the same "
  "battery state. (2) RDOEM-MAS with TARC-R (full method). (3) RDOEM-MAS with TARC-v15. (4) Dynamic tracking without "
  "TARC (trust ≡ 1, same weight rule). (5) The same without re-anchoring (the previous version’s warm start). "
  "(6) W-MSR with trimming parameter f_W = 1, applied to price and mismatch. Each agent discards up to f_W neighbour values above its own and f_W below; in the W-MSR theory [5], f_W is the assumed number of malicious neighbours, but here it is only a trimming parameter, since the actual number of compromised neighbours can exceed it. Other states use standard weights; its (2f+1)-robustness "
  "was not verified and generally fails on these graphs. (7) Static re-convergence: at every price iteration, "
  "static average consensus on (λ, u, q) runs until disagreement < 0.5·tolerance, followed by a dual step "
  "η = 2/L with L = Σ_iℓ_i. The ADMM and primal–dual baselines listed in the previous protocol were not implemented "
  "and are no longer claimed.")
TABLE("Table V. Attack models (two compromised agents, epochs 8–12 of the evaluated window 6–17)",
      ["ID", "Report corruption", "Magnitude"],
      [["ATT-1", "constant bias on λ and x", "b_λ = 0.3λ_ref, b_x = 0.05P_peak"],
       ["ATT-1x", "constant bias on x only", "b_x = 0.05P_peak"],
       ["ATT-2", "scaling of λ and x", "(1 + s), s = 0.5"],
       ["ATT-3", "bounded ramp on λ and x", "slope 1.5·10⁻³/round, capped at 0.3λ_ref and 0.15P_peak"],
       ["ATT-4", "intermittent random-sign pulses", "duty 10%; 0.02λ_ref and 0.004P_peak"]],
      widths=[1, 3, 4])
P("Metrics. The welfare gap is g = (SW_central − SW_method)/C_gen,central with SW = W₀ − βCVaR, evaluated under the "
  "evaluation recourse model of each regime (a committed imbalance enters recourse). Also reported: r_KKT/λ_ref; |ΔP|; "
  "the fraction of epochs reaching tolerance; messages per epoch (every attempted link carries two data messages "
  "per round, and TARC adds two handshake messages); out-of-sample E[recourse cost] and CVaR; the false-positive "
  "rate (share of active honest–honest edge-rounds removed); and the attacker-edge removal rate.")
P(b("Sign of the welfare gap. "), "The gap g is reported signed. The benchmark enforces exact day-ahead balance "
  "ΔP = 0. A committed distributed schedule may violate that balance, and the evaluation recourse model then "
  "absorbs the imbalance through b_m(z) in (1a). Because of this, the signed comparison is not guaranteed to be "
  "nonnegative; solver tolerances add noise of order 10⁻⁶. Of all nominal epoch values behind Table VI, "
  f"{100 * NEG_S:.1f}% of regime-S gaps and {100 * NEG_C:.1f}% of regime-C gaps were negative (minima "
  f"{100 * MIN_S:.2f}% and {100 * MIN_C:.2f}%). The static baseline, which stops at 1% mismatch, accounts for most "
  "of them. Negative values are not clipped.")
P("Statistics. Seeds per configuration are 20 (IEEE-30 nominal), 10 (IEEE-57, attacks, β sweep, ablations), "
  "5 (IEEE-118) and 5 (phase diagram). This is fewer than the ≥30 of the previous protocol, because of computational "
  "budget. The unit of analysis is the per-seed mean over epochs 1–23 (epoch 0 is the cold start). We report means "
  "with 95% t-intervals and, for skewed attack outcomes, medians. Directional claims use paired Wilcoxon "
  "signed-rank tests on matched seeds with Holm correction across methods within a system or attack, and "
  "matched-pairs rank-biserial correlation r_rb as effect size. Non-rejection is not read as equivalence.")
P(b("Parameter selection and independence. "), "The step constant c_η, the averaging constant k_ω and the TARC-R "
  "parameters were chosen on IEEE-30 pilot runs with seed 0, which is also an evaluation seed in E1 and E4. To "
  "limit the resulting optimism, the attack results are replicated on held-out seeds 100–109 that were never used "
  "for tuning (E9). A one-at-a-time sensitivity analysis of ρ_min, G and ρ_mem is run on held-out seeds 100–104 "
  "(E10). No held-out system was used: IEEE-57 and IEEE-118 were not used for tuning, but attacks were evaluated on "
  "IEEE-30 only.")
P(b("Statistical units per table. "), "Each table uses one of the following units.")
LIST([["Tables VI, VII and VIII-B: one value per seed, the mean over epochs 1–23. n = 20 (IEEE-30), 10 (IEEE-57, "
       "Table VII, Table VIII-B) or 5 (IEEE-118). Intervals are 95% t-intervals over the seed means."],
      ["Table VI-B: the unit is the epoch (5 seeds × 12 epochs = 60 per method). Medians are over the epochs that "
       "reached each target, and no intervals are given."],
      ["Tables VIII-A and VIII-C: medians are over seed–epoch values within each phase (pre: 2 epochs, during: 5, "
       "post: 5, times 10 seeds). FP and removal rates are means over the same seed–epochs."],
      ["Table VIII-C mean and 95% t-interval, and every Wilcoxon test: one value per seed, the mean over the attack "
       "window (epochs 8–12), paired by seed across methods (n = 10)."],
      ["Table VIII-D: medians over seed–epochs (5 seeds)."],
      ["Fig. 9: medians over 15 seed–epochs per cell (5 seeds × epochs 8–10). The dispersion statistics in Section "
       "VIII-F use one value per seed and loss level (25 values)."]])

# ------------------------------------------------------------------ VIII
H1("VIII. Results")
H2("A. Nominal Convergence and Tracking")
FIGURE("fig3_convergence.png", "Fig. 3. Six epochs on IEEE-30 (seed 0, TARC-R, within-epoch forecast refinements "
       "at rounds 100 and 200). Top: mean price. Middle: true mismatch |ΔP| and tracker disagreement. Bottom: "
       "sum-invariant error |mean(x) − Σu|, at floating-point level throughout (Proposition 2a).", 560)
P("Fig. 3 shows the expected behaviour. Each epoch boundary and forecast refinement injects an input increment. "
  "The tracker disagreement then contracts, and |ΔP| decays towards 10⁻²–10⁻¹ MW. The invariant error stays at "
  "10⁻¹⁶–10⁻¹³ MW, confirming Proposition 2(a) numerically, including under packet loss (unit test with "
  "p_loss = 0.2).")
H2("B. Optimality: Exact versus Approximate Regime")
rows = []
for c in ("ieee30", "ieee57", "ieee118"):
    for m in (FULL, NOT, "Dynamic, no TARC, no re-anchor", STAT):
        if ((T1.case == c) & (T1.method == m)).any():
            g = lambda col: r1(c, m, col)
            rows.append([c.upper().replace("IEEE", "IEEE-") if m == FULL else "", m.replace("RDOEM-MAS ", ""),
                         f"{pc(g('gap_S')[0])} [{pc(g('gap_S')[1])}, {pc(g('gap_S')[2])}]",
                         f"{pc(g('gap_C')[0])} [{pc(g('gap_C')[1])}, {pc(g('gap_C')[2])}]",
                         f"{g('kkt_S')[0]:.3f}", f"{g('kkt_C')[0]:.3f}", f"{g('dP')[0]:.2f}",
                         f"{100 * g('reached')[0]:.0f}", f"{msgs[(c, m)] / 1e3:.0f}"])
TABLE("Table VI. Nominal performance (mean [95% CI] over seeds; epochs 1–23; β = 1, α = 0.9)",
      ["System", "Method", "Gap S (%)", "Gap C (%)", "r_KKT S", "r_KKT C", "|ΔP| (MW)", "Full test reached (%)",
       "Msgs/epoch (k)"], rows, widths=[1.1, 2.4, 1.7, 1.7, 0.9, 0.9, 0.9, 0.9, 1.0], size=14,
      note="Gap S / Gap C: separable / coupled recourse. r_KKT normalized by λ_ref. Centralized solutions: "
           "r_KKT/λ_ref ≤ 10⁻⁶ in both regimes. Msgs/epoch: total at the "
           "fixed 300-round budget (4|E|K with TARC, 2|E|K without; per-seed |E|, Table IV). Full test: the "
           "three-part tolerance test of Section V-E.")
P(f"Under separable recourse the distributed schedule is within {pc(gapS['ieee30'])}% (IEEE-30), "
  f"{pc(gapS['ieee57'])}% (IEEE-57) and {pc(gapS['ieee118'])}% (IEEE-118) of the centralized optimum. Under "
  f"coupled recourse the gaps rise to {pc(gapC['ieee30'])}%, {pc(gapC['ieee57'])}% and {pc(gapC['ieee118'])}%. "
  "The static baseline shows the same increase from regime S to regime C. The additional loss therefore comes from "
  "the surrogate local sensitivities, not from the tracking. This is the exact/approximate distinction of "
  "Section IV-D, made quantitative. The residual r_KKT/λ_ref is 0.07–0.14 for all methods, including the static "
  "baseline in regime S. It reflects the finite round budget and the nonsmooth tail, not a systematic bias "
  "(Fig. 4).")
FIGURE("fig5_kkt_residual.png", "Fig. 4. Centralized-KKT residual of committed schedules (mean ± SD over seeds). "
       "Plain: separable recourse; hatched: coupled recourse.", 560)
H2("C. Communication")
FIGURE("fig4_welfare_vs_comm.png", "Fig. 5. Welfare gap (regime S) versus total messages per epoch at the fixed "
       "budget K = 300; one point per seed.", 560)
P(f"Under the fixed 300-round accounting convention (Fig. 5, Table VI), the static re-convergence baseline used "
  f"{RATIO}× fewer messages than "
  f"dynamic tracking: RDOEM-MAS spent {msgs[('ieee30', FULL)] / 1e3:.0f}k, {msgs[('ieee57', FULL)] / 1e3:.0f}k and "
  f"{msgs[('ieee118', FULL)] / 1e3:.0f}k messages per epoch on IEEE-30/57/118, against "
  f"{msgs[('ieee30', STAT)] / 1e3:.0f}k, {msgs[('ieee57', STAT)] / 1e3:.0f}k and {msgs[('ieee118', STAT)] / 1e3:.0f}k "
  "(paired Wilcoxon, Holm-adjusted p < 0.01 on IEEE-30 and IEEE-57; p = 0.06 on IEEE-118 with 5 seeds). This "
  "comparison is not balanced. The dynamic run spends its whole budget, whereas the static run stops at its 1% "
  "tolerance, and the static run can take the aggressive dual step 2/L because it works with exact sums.")
P("We therefore also compare at equal accuracy (E8: IEEE-30, 5 seeds, epochs 1–12). Welfare gap and |ΔP| are "
  "recorded every 10 rounds against cumulative messages. The static baseline is run with inner tolerances 10⁻², "
  "10⁻³ and 10⁻⁴, so it can be credited with its best setting for each target (Fig. 6, Table VI-B). A target "
  "counts as reached at the first checkpoint from which it holds for the rest of the epoch.")
_tg = ["dP<1%", "gap<1%", "gap<0.5%", "dP<0.1%"]
TABLE("Table VI-B. Equal-accuracy communication (IEEE-30): median messages per epoch (k) to reach and keep each "
      "target, and share of epochs reaching it (%)",
      ["Method", "|ΔP| < 1% peak", "Gap < 1%", "Gap < 0.5%", "|ΔP| < 0.1% peak"],
      [[m] + [f"{e8(m, tg)[0]:.1f} ({e8(m, tg)[1]:.0f}%)" for tg in _tg]
       for m in [DYN, FULL, ST2, ST3, ST4]], widths=[2.6, 1.6, 1.6, 1.6, 1.6], size=15,
      note="Medians are over the epochs that reached each target, so methods are not compared on identical sets of "
           "epochs; read them with the reach shares. Targets are single criteria, unlike the full test of Table "
           "VI. Unit: epoch (60 per method).")
P("At moderate accuracy the ranking reverses. Every method held |ΔP| below 1% of peak in every epoch, with "
  f"medians of {e8(DYN, 'dP<1%')[0]:.1f}k messages for dynamic tracking without TARC, {e8(FULL, 'dP<1%')[0]:.1f}k "
  f"with TARC-R, and {e8(ST2, 'dP<1%')[0]:.1f}k for the best static setting. For a welfare gap below 1%, dynamic "
  f"tracking needed {e8(DYN, 'gap<1%')[0]:.1f}k messages but reached the target within the budget in only "
  f"{e8(DYN, 'gap<1%')[1]:.0f}% of epochs, against {e8(ST3, 'gap<1%')[0]:.1f}k messages and "
  f"{e8(ST3, 'gap<1%')[1]:.0f}% for static re-convergence with tolerance 10⁻³. At high accuracy "
  f"(|ΔP| < 0.1%), the static baseline with tolerance 10⁻³ needed {e8(ST3, 'dP<0.1%')[0]:.1f}k messages and "
  f"succeeded in {e8(ST3, 'dP<0.1%')[1]:.0f}% of epochs, whereas dynamic tracking needed "
  f"{e8(DYN, 'dP<0.1%')[0]:.1f}k and succeeded in {e8(DYN, 'dP<0.1%')[1]:.0f}%. Dynamic tracking therefore saves "
  "communication at moderate accuracy targets. The separate-packet TARC handshake roughly doubles its cost. Static "
  "re-convergence is preferable when high accuracy must be guaranteed. The earlier conclusion that dynamic tracking "
  "“did not save communication” holds only at a fixed budget.")
FIGURE("fig11_equal_accuracy.png", "Fig. 6. Median welfare gap and |ΔP| versus cumulative messages within an epoch "
       "(IEEE-30, 5 seeds × 12 epochs). Static curves are shown for three inner tolerances.", 580)
P(f"At the fixed budget, RDOEM-MAS left a mean |ΔP| of {r1('ieee30', FULL, 'dP')[0]:.2f} MW (IEEE-30) and "
  f"{r1('ieee118', FULL, 'dP')[0]:.1f} MW (IEEE-118), against {r1('ieee30', STAT, 'dP')[0]:.2f} and "
  f"{r1('ieee118', STAT, 'dP')[0]:.1f} MW for the static baseline, which stops as soon as its 1% tolerance is met. "
  f"Nominally, TARC-R removed a fraction {r1('ieee30', FULL, 'fp')[0]:.1e} of honest edge-rounds on IEEE-30 and "
  "none on IEEE-57/118. Its welfare equals that of dynamic tracking without TARC.")
H2("D. Risk Weight")
rows = [[f"{bb:g}", f"{e3[bb]['EQ'][0]:.2f}", f"{e3[bb]['CV'][0]:.2f} [{e3[bb]['CV'][1]:.2f}, {e3[bb]['CV'][2]:.2f}]",
         f"{e3[bb]['gen'][0]:.1f}", pc(e3[bb]['gap'][0]), pc(e3[bb]['gapc'][0])] for bb in sorted(e3)]
TABLE("Table VII. Effect of β (IEEE-30, 10 seeds; out-of-sample recourse evaluated with the regime-C (network-coupled) model)",
      ["β", "E[recourse] ($/h)", "CVaR₀.₉ ($/h) [95% CI]", "Gen. cost ($/h)", "Gap S (%)", "Gap C (%)"], rows,
      widths=[0.7, 1.6, 2.4, 1.5, 1.2, 1.2])
P(f"Raising β from 0 to 2 cut the out-of-sample CVaR from {e3[0.0]['CV'][0]:.1f} to {e3[2.0]['CV'][0]:.1f} $/h and "
  f"the expected recourse cost from {e3[0.0]['EQ'][0]:.1f} to {e3[2.0]['EQ'][0]:.2f} $/h. In exchange, day-ahead "
  f"generation cost rose from {e3[0.0]['gen'][0]:.0f} to {e3[2.0]['gen'][0]:.0f} $/h, as reserve headroom was "
  "withheld and renewable schedules became more conservative. At β = 0 the gap is essentially zero "
  f"({100 * e3[0.0]['gap'][0]:.4f}%), so the risk term is what makes the negotiation hard. As β grows, the regime-S "
  "gap grows and the regime-C gap shrinks, because the regime-C model’s marginal costs become better approximated as "
  "risk dominates.")
FIGURE("fig8a_risk_tradeoff.png", "Fig. 7. Out-of-sample expected recourse cost versus CVaR as β varies (mean, 95% CI).",
       300)
H2("E. Attacks")
P("All attack results are for IEEE-30. TARC-R was tuned on seed 0, which is among seeds 0–9 below, so Table "
  "VIII-A may be optimistic for TARC-R. Tables VIII-C and VIII-D replicate the analysis on held-out seeds.")
FIGURE("fig6_attacks.png", "Fig. 8. Median welfare gap during and after attacks (log scale; 10 seeds).", 580)
rows = []
for a in ["ATT-1", "ATT-1x (mismatch only)", "ATT-2", "ATT-3", "ATT-4"]:
    for m in [NOT, "W-MSR (f_W=1)", "RDOEM-MAS (TARC-v15)", FULL]:
        p, rb = ptest(a, m) if m != NOT else (np.nan, np.nan)
        fp = t4(a, m, "fp")[0]
        rem = t4(a, m, "rem")[0]
        rows.append([a.replace(" (mismatch only)", "") if m == NOT else "", m.replace("RDOEM-MAS ", ""),
                     pc(m4(a, m, "pre"), 1), pc(m4(a, m, "during"), 1), pc(m4(a, m, "post"), 1),
                     "—" if np.isnan(fp) else pc(fp, 1), "—" if np.isnan(rem) else pc(rem, 0),
                     "ref." if m == NOT else f"{p:.3f} ({rb:+.2f})"])
TABLE("Table VIII-A. Attack outcomes on IEEE-30 (seeds 0–9). Medians are computed over seed–epoch observations; hypothesis tests use paired per-seed attack-window means (n = 10). Columns: median gap (%) before/during/after, false-positive (FP) and attacker-edge "
      "removal rates (%), Holm-adjusted p and r_rb versus no defense (during-attack gap)",
      ["Attack", "Method", "Pre", "During", "Post", "FP", "Att. removed", "p_Holm (r_rb)"], rows,
      widths=[0.9, 2.1, 0.8, 0.9, 0.9, 0.8, 1.0, 1.5], size=14,
      note="Negative r_rb: smaller gap than no defense. The W-MSR “pre” value is the gap before any attack.")
p1, _ = ptest("ATT-1", FULL)
p2, _ = ptest("ATT-2", FULL)
P(b("No defense. "), f"Constant bias (ATT-1) raised the median gap to {pc(A1n, 0)}%. This is the sum-invariant "
  "failure described in Section VI: injected mass persists in the tracker and drives the price. With re-anchoring, "
  f"recovery after the attack was fast (post-attack median {pc(m4('ATT-1', NOT, 'post'), 1)}%). The previous "
  f"version’s warm start carries the corruption forward; in pilot runs the post-attack gap stayed at ≈30%.")
P(b("TARC-v15 gave no protection against ATT-1 "), f"({pc(m4('ATT-1', 'RDOEM-MAS (TARC-v15)', 'during'), 0)}%). "
  "Its innovation term |λ_j^k − λ_j^last| is zero for a constant offset after the first round. Its self-calibrating "
  "scale absorbed the attack within ≈40 rounds, after which trust recovered to 1; attacker edges were removed in "
  f"only {pc(t4('ATT-1', 'RDOEM-MAS (TARC-v15)', 'rem')[0], 1)}% of edge-rounds.")
P(b("TARC-R "), f"removed {pc(t4('ATT-1', FULL, 'rem')[0], 0)}% of attacker edge-rounds under ATT-1 and reduced the "
  f"median during-attack gap to {pc(A1r, 1)}% (p_Holm = {p1:.3f}). Under ATT-2 it reduced the gap from "
  f"{pc(m4('ATT-2', NOT, 'during'), 0)}% to {pc(m4('ATT-2', FULL, 'during'), 0)}% (p_Holm = {p2:.3f}). The effect "
  "under ATT-3 was not significant, and TARC-R neither helped nor hurt under ATT-4. It had three costs. (i) "
  f"False-positive exclusion of honest edges during attacks ({pc(t4('ATT-1', FULL, 'fp')[0], 0)}% under ATT-1, "
  f"{pc(t4('ATT-2', FULL, 'fp')[0], 0)}% under ATT-2), as injected mass disturbs honest neighbours. (ii) Persistence: "
  "gated scales and frozen trust keep attackers and disturbed honest agents excluded after the attack, so the "
  f"post-attack gap stayed at {pc(m4('ATT-1', FULL, 'post'), 1)}% (ATT-1) and {pc(m4('ATT-2', FULL, 'post'), 0)}% "
  "(ATT-2), against about 1% without defense. (iii) Blindness to ATT-1x: a bias on the mismatch payload alone is "
  "not scored, because the mismatch term was removed to avoid the deadlock (Section V-C); TARC-R and no defense "
  f"performed identically ({pc(m4('ATT-1x (mismatch only)', FULL, 'during'), 1)}%).")
P(b("W-MSR "), f"limited ATT-1 damage ({pc(m4('ATT-1', 'W-MSR (f_W=1)', 'during'), 0)}%). However, trimming breaks "
  f"the doubly stochastic mass balance of the sum tracker, and its nominal gap was "
  f"{pc(m4('ATT-1', 'W-MSR (f_W=1)', 'pre'), 0)}% before any attack. A trimming rule is incompatible with sum "
  "tracking unless the tracker is redesigned.")
_r9 = []
for _a in ("ATT-1", "ATT-2", "ATT-3"):
    for _m in (NOT, FULL):
        _e = E9[(_a, _m)]
        _r9.append([_a if _m == NOT else "", _m.replace("RDOEM-MAS ", ""), pc(_e["during"], 1),
                    f"{pc(_e['ci_during'][0], 1)} [{pc(_e['ci_during'][1], 1)}, {pc(_e['ci_during'][2], 1)}]",
                    pc(_e["post"], 1), "—" if _m == NOT else pc(_e["fp"], 0), "—" if _m == NOT else pc(_e["rem"], 0),
                    "ref." if _m == NOT else f"{_e['p_holm']:.3f} ({_e['rb']:+.2f})"])
TABLE("Table VIII-C. Held-out replication on IEEE-30 (seeds 100–109, never used for tuning). Medians are computed over "
      "seed–epoch observations; the mean, 95% CI and tests use paired per-seed attack-window means (n = 10)",
      ["Attack", "Method", "During (median %)", "During (mean % [95% CI])", "Post (median %)", "FP (%)",
       "Att. removed (%)", "p_Holm (r_rb)"], _r9, widths=[0.9, 1.9, 1.1, 1.9, 1.1, 0.8, 1.0, 1.3], size=14)
_e1, _e2, _e3 = E9[("ATT-1", FULL)], E9[("ATT-2", FULL)], E9[("ATT-3", FULL)]
P(b("Held-out replication. "), f"On seeds never used for tuning, TARC-R reduced the median during-attack gap under "
  f"ATT-1 from {pc(H1n, 0)}% to {pc(H1r, 1)}% (p_Holm = {_e1['p_holm']:.3f}, r_rb = {_e1['rb']:+.2f}). Under ATT-2 "
  f"it fell from {pc(E9[('ATT-2', NOT)]['during'], 0)}% to {pc(_e2['during'], 0)}% (p_Holm = {_e2['p_holm']:.3f}). "
  f"Under ATT-3 the reduction ({pc(E9[('ATT-3', NOT)]['during'], 1)}% → {pc(_e3['during'], 1)}%) was again not "
  f"significant (p_Holm = {_e3['p_holm']:.2f}). The costs replicate too: during-attack false positives were "
  f"{pc(_e1['fp'], 0)}% (ATT-1) and {pc(_e2['fp'], 0)}% (ATT-2), and post-attack gaps stayed at "
  f"{pc(_e1['post'], 0)}% and {pc(_e2['post'], 0)}% against about 1% without defense. The qualitative conclusions "
  "of Table VIII-A therefore do not depend on the tuning seed.")
TABLE("Table VIII-D. TARC-R sensitivity (ATT-1, IEEE-30, held-out seeds 100–104; one parameter varied at a time; medians over seed–epoch observations)",
      ["Variant", "During (median %)", "Post (median %)", "FP pre-attack (%)", "FP during (%)", "Att. removed (%)"],
      [[_vn(v["variant"]), pc(v["during"], 1), pc(v["post"], 1), pc(v["fp_pre"], 1), pc(v["fp_during"], 0),
        pc(v["rem"], 0)] for v in E10], widths=[3.2, 1.3, 1.3, 1.3, 1.2, 1.3], size=14)
_d = [v["during"] for v in E10]; _p = [v["post"] for v in E10]; _rm = [v["rem"] for v in E10]
_fd = [v["fp_during"] for v in E10]
P(b("Sensitivity. "), "Varying ρ_min ∈ {0.2, 0.5}, G ∈ {30, 100} and ρ_mem ∈ {0.3, 0.8} one at a time around "
  f"the default kept attacker-edge removal within {pc(min(_rm), 0)}–{pc(max(_rm), 0)}%. No variant produced "
  f"false positives before the attack, and false positives during the attack stayed at {pc(min(_fd), 0)}–"
  f"{pc(max(_fd), 0)}%. The during-attack gap ranged from {pc(min(_d), 1)}% to {pc(max(_d), 1)}%, and the "
  f"post-attack gap from {pc(min(_p), 1)}% to {pc(max(_p), 1)}%. Slow trust memory (ρ_mem = 0.8) was clearly worse "
  "during the attack, and a shorter grace window (G = 30) was better on these seeds. The default is therefore not "
  "an especially favourable setting.")
H2("F. Phase Diagram and Proposition 5 Check")
FIGURE("fig7_phase.png", "Fig. 9. Median welfare gap (%) under ATT-1 versus packet loss and number of compromised "
       "agents (IEEE-30, 5 seeds, epochs 8–10).", 560)
tn, tr = tabs5[NOT], tabs5[FULL]
P(f"Without defense, one compromised agent already produced gaps of {pc(tn.loc[1].min(), 0)}–{pc(tn.loc[1].max(), 0)}%, "
  f"and three or more produced ≈{pc(tn.loc[3].mean(), 0)}% (Fig. 9). For one attacker and packet-loss rates up to 40%, TARC-R kept the median gap "
  f"at {pc(tr.loc[1].min(), 1)}–{pc(tr.loc[1].max(), 1)}% at every loss level up to 40% (medians over 15 seed–epochs per "
  "cell: 5 seeds × epochs 8–10). The median hides dispersion. For the 25 one-attacker seed–loss cells (5 seeds × 5 loss levels), each summarized by that seed’s mean gap over epochs 8–10, the values ranged "
  f"from {pc(E5f1['min'], 1)}% to {pc(E5f1['max'], 0)}% (mean {pc(E5f1['ci'][0], 1)}%, 95% CI "
  f"[{pc(E5f1['ci'][1], 1)}, {pc(E5f1['ci'][2], 1)}]%), so a single attacker occasionally still caused a large "
  f"loss. With three attackers, the median rose from {pc(tr.loc[3].iloc[0], 1)}% to {pc(tr.loc[3].iloc[-1], 1)}% as "
  f"packet loss grew, and with nine it reached {pc(tr.loc[9].min(), 0)}–{pc(tr.loc[9].max(), 0)}%. Packet loss "
  "mattered only in combination with attacks: nominally (f_att = 0) it had no effect on welfare.")
FIGURE("fig9_prop4_check.png", "Fig. 10. Honest-subsystem price disagreement and the Proposition 5 envelope built "
       "from measured per-block γ_h and D_h (B = 10) under ATT-1 (epochs 8–9).", 560)
P("Fig. 10 evaluates Proposition 5 on the honest subsystem, with attacker influence and projection treated as input. "
  "The envelope was never violated. Without defense, the honest retained graph mixes uniformly (γ_h = "
  f"{p4['none']['gamma_median']:.3f}), and disagreement stays small even though the price level is badly biased: "
  "a disagreement bound says nothing about optimality. Under TARC-R, G1 failed in "
  f"{100 * p4['tarc']['frac_blocks_no_contraction']:.0f}% of blocks, because exclusions isolated honest agents that "
  "were not re-admitted. The premise of Proposition 5 therefore does not hold for TARC-R under attack. This is the "
  "scenario the analysis flagged as unguaranteed, and it is now observed.")
H2("G. Ablations")
rows = [[r["tag"], f"{pc(r['gap'][0])} [{pc(r['gap'][1])}, {pc(r['gap'][2])}]", pc(r["gapc"][0]),
         f"{r['kkt'][0]:.3f}", f"{r['dP'][0]:.2f}", f"{r['cv'][0]:.2f}", f"{r['msgs'][0] / 1e3:.0f}"]
        for _, r in T6.iterrows()]
TABLE("Table VIII-B. Ablations (IEEE-30, 10 seeds, nominal; mean [95% CI])",
      ["Variant", "Gap S (%)", "Gap C (%)", "r_KKT S", "|ΔP| (MW)", "OOS CVaR ($/h)", "Msgs (k)"], rows,
      widths=[2.8, 1.8, 1, 1, 1, 1.2, 1], size=14)
P(f"Tail-weight averaging is essential: without it the gap rose to {pc(e6['no tail-weight averaging']['gap'][0], 1)}% "
  f"and r_KKT to {e6['no tail-weight averaging']['kkt'][0]:.2f}λ_ref, because renewable agents oscillate between "
  "tail sets that their own schedules create. Tracking the global scenario cost matters: local-only tail "
  f"indicators raised the gap to {pc(e6['no global-cost tracker']['gap'][0])}%, although they produced a lower "
  "(more conservative) CVaR. The two quantile rules, the presence of storage, 20% packet loss and re-anchoring had no "
  "material nominal effect. Re-anchoring is therefore free nominally and decisive after attacks.")
P("The packet-loss result is empirical, for the tested graphs and loss rates up to 20% (40% in Fig. 9). It relies on "
  "the symmetric authenticated handshake of Section VI and is not a general property of packet loss.")
FIGURE("fig8b_ablation.png", "Fig. 11. Ablations: welfare gap and KKT residual (mean, 95% CI).", 560)
H2("H. Computation")
rt = allE1.groupby(["case", "method"]).runtime_s.mean()
P(f"On a single CPU core, one simulated day (24 epochs × 300 rounds, all agents, plus centralized benchmarks and "
  f"residuals) took {rt[('ieee30', FULL)]:.0f} s (IEEE-30), {rt[('ieee57', FULL)]:.0f} s (IEEE-57) and "
  f"{rt[('ieee118', FULL)]:.0f} s (IEEE-118). The per-agent work per round is O(d_i + M) arithmetic plus a "
  "32-step bisection, and each data message carries 3 + M scalars.")

# ------------------------------------------------------------------ IX-XI
H1("IX. Discussion")
P(b("What is supported. "), "The formulation and trackers reproduce the centralized CVaR dispatch to within about "
  "1–2% when recourse is separable. The loss grows when it is not, exactly as the conditional theory predicts. The "
  "sum invariant holds to machine precision, and the two design elements introduced here are each justified by an ablation "
  "(averaging) or an attack experiment (re-anchoring).")
P(b("What is not, or only partly. "), "Dynamic tracking saves messages only at moderate accuracy targets, and "
  "the separate-packet TARC handshake roughly halves that saving. When high accuracy must be guaranteed, static "
  "re-convergence with exact sums was more reliable. TARC as originally specified fails against the simplest "
  "persistent attack, and TARC-R replaces that failure with sticky exclusions.")
P(b("Design lessons. "), "(1) Sum tracking through doubly stochastic mixing conserves any injected error, so a "
  "defense must either stop injection before it happens or periodically re-anchor. (2) Innovation-based scores "
  "detect changes, not offsets; cross-sectional consistency is needed. (3) Self-calibrating scales must be gated, "
  "but gating makes exclusion sticky; a principled re-admission rule is the main open design problem. (4) A "
  "consistency term that depends on the consensus state itself can deadlock the trust dynamics.")
P(b("Threats to validity. "), "The model is copper-plate and the profiles are synthetic. Seed counts are 5–20, with "
  "one attack placement per seed. TARC-R was tuned on an IEEE-30 pilot with seed 0; this is mitigated by the "
  "held-out seeds 100–109 and the sensitivity analysis, both on IEEE-30 only. The static baseline is a single "
  "comparator of our own design, and the round budget K = 300 is not adapted to the accuracy target.")
H1("X. Limitations")
LIST([["Exact risk-aware KKT equivalence requires R1 or a proven consistent allocation. The coupled case is "
       "approximate, and no quantitative error bound is proved."],
      ["No convergence proof exists for the coupled price–decision–tracker–trust iteration."],
      ["Proposition 5 needs G1 and a bounded combined disturbance. Neither is guaranteed by TARC, and G1 was "
       "violated under attack."],
      ["TARC-R does not detect mismatch-only attacks, excludes honest agents during attacks, and lacks a re-admission "
       "rule."],
      ["Communication savings depend on the accuracy target and on counting handshakes as separate packets."],
      ["Synchronous rounds, symmetric links and an authenticated lower layer are assumed; directed links would "
       "need push-sum."],
      ["Evaluation uses synthetic profiles on IEEE cost data without network constraints. Field deployment would "
       "further require clock synchronization, authentication, and SCADA/AMI integration."]])
H1("XI. Conclusion")
P("RDOEM-MAS combines peer-to-peer price negotiation, CVaR risk weighting on tracked network-wide scenario costs, "
  "and trust-weighted doubly stochastic consensus. Its exact guarantees are an invariant and fixed-point "
  "characterizations under explicit assumptions. Its behaviour beyond them is now measured rather than conjectured. "
  f"The dispatch is near-optimal under separable recourse ({S_GAP_RANGE}) and approximate under coupled recourse "
  f"({C_GAP_RANGE}). Dynamic tracking saved messages at moderate accuracy, but not at a fixed budget or at high accuracy. The revised trust rule limits constant-bias and scaling "
  "attacks at the price of sticky exclusions and blindness to mismatch-only attacks. The most valuable next steps "
  "are a re-admission rule with provable honest-graph connectivity, a KKT-consistent allocation for coupled "
  "recourse, and validation on measured data with network constraints.")

# ------------------------------------------------------------------ appendices
H1("Appendix A. Symbols")
TABLE("Table A1. Principal symbols",
      ["Symbol", "Meaning", "Unit"],
      [["t, k, m", "epoch, communication round, scenario index", "—"],
       ["N, d_i", "number of agents; retained degree of agent i", "—"],
       ["z, z_i", "centralized decision vector; decisions of agent i (P_G, P_R, P_D or "
        "(p_ch, p_dis))", "MW"],
       ["s_i, u_i", "net injection (supply − demand); tracker input u_i = s_i − ℓ_i", "MW"],
       ["ΔP", "day-ahead mismatch Σ_i s_i − P_loss", "MW"],
       ["λ_i", "local price", "$/MWh"],
       ["x_i", "mismatch tracker (estimate of ΔP; not an optimization variable)", "MW"],
       ["q_i,m, Q̂_i,m", "local scenario recourse cost; tracked network-wide scenario cost", "$/h"],
       ["ζ_i, θ_i,m, ω̄_i,m", "VaR estimate; tail indicator; averaged tail weight", "$/h; —; —"],
       ["W_k, w_ij", "consensus matrix and weights", "—"],
       ["ρ_ij, ρ^eff, m_ij", "raw trust; effective trust; missing-report counter", "—"],
       ["a_ij, r^inn, r^p, r^x", "anomaly score and its normalized ratios", "dimensionless"],
       ["η_k, ℓ_i, σ₂", "price step; local response slope; 2nd eigenvalue modulus of nominal W", "($/MWh)/MW; MW/($/MWh); —"],
       ["d_k, v_h, D_h, γ_B", "disturbance, block disturbance, its bound, block contraction factor", "—"],
       ["α, β, π_m", "CVaR level; risk weight; scenario probability", "—"],
       ["P_G, P_R, P_D, p_ch, p_dis", "generator, renewable, load, battery charge/discharge powers", "MW"]],
      widths=[2, 5.5, 1.8])
H1("Appendix B. Literature Search Protocol")
P("On 28 September 2026 we ran targeted queries through a general web search engine indexing IEEE Xplore, "
  "ScienceDirect, SpringerLink, MDPI and arXiv. The queries were: “trust-based resilient distributed economic "
  "dispatch false data injection consensus”, “distributed CVaR energy management consensus dynamic average "
  "tracking peer-to-peer”, and title look-ups. The first result pages were screened, and [24]–[27] were added. "
  "This is a targeted search, not a systematic review. The bibliographic entries of [24]–[30] were taken from the "
  "records returned by these searches or from standard citations of well-known works. The search logs are not "
  "archived with this manuscript, and every entry still has to be verified against the publisher page "
  "(capitalization, page ranges, DOIs) before submission. [21] remains an arXiv preprint.")
H1("Appendix C. Reproducibility")
P("The accompanying package (rdoem/) contains the code, the raw per-run results (one CSV per run, keyed by a "
  "configuration hash) and the figure scripts, and is intended to reproduce every reported number. It includes "
  "unit tests, which reviewers can run, for the merit-order recourse against an LP solver, the centralized KKT "
  "residual, the doubly stochastic weights and the sum invariant under packet loss. The package is not yet "
  "deposited in a public archive; a DOI-bearing archive should be created before submission. Seeds are the "
  "integers 0–19 (evaluation) and 100–109 (held-out); system seed s and day seed s are used for run s.")

H1("References")
B.append(dict(type="refs", items=[
    "W. Zhang, Y. Xu, W. Liu, C. Zang, and H. Yu, “Distributed online optimal energy management for smart grids,” IEEE Trans. Ind. Informat., vol. 11, no. 3, pp. 717–727, 2015.",
    "R. Olfati-Saber, J. A. Fax, and R. M. Murray, “Consensus and cooperation in networked multi-agent systems,” Proc. IEEE, vol. 95, no. 1, pp. 215–233, 2007.",
    "M. Zhu and S. Martínez, “Discrete-time dynamic average consensus,” Automatica, vol. 46, no. 2, pp. 322–329, 2010.",
    "S. Sundaram and C. N. Hadjicostis, “Distributed function calculation via linear iterative strategies in the presence of malicious agents,” IEEE Trans. Autom. Control, vol. 56, no. 7, pp. 1495–1508, 2011.",
    "H. J. LeBlanc, H. Zhang, X. Koutsoukos, and S. Sundaram, “Resilient asymptotic consensus in robust networks,” IEEE J. Sel. Areas Commun., vol. 31, no. 4, pp. 766–781, 2013.",
    "K. Kuwaranancharoen, L. Xin, and S. Sundaram, “Byzantine-resilient distributed optimization of multi-dimensional functions,” in Proc. ACC, 2020, pp. 4399–4404, doi: 10.23919/ACC45564.2020.9147396.",
    "M. Pirani, A. Mitra, and S. Sundaram, “Graph-theoretic approaches for analyzing the resilience of distributed control systems: A tutorial and survey,” Automatica, vol. 157, p. 111264, 2023.",
    "L. Ballotta and M. Yemini, “The role of confidence for trust-based resilient consensus,” in Proc. ACC, 2024, pp. 2822–2829, doi: 10.23919/ACC60939.2024.10644459.",
    "M. Yemini, A. Nedić, A. J. Goldsmith, and S. Gil, “Characterizing trust and resilience in distributed consensus for cyberphysical systems,” IEEE Trans. Robot., vol. 38, no. 1, pp. 71–91, 2022.",
    "W. Abbas, A. Laszka, and X. Koutsoukos, “Improving network connectivity and robustness using trusted nodes with application to resilient consensus,” IEEE Trans. Control Netw. Syst., vol. 5, no. 4, pp. 2036–2048, 2018.",
    "K. Boakye-Boateng, A. A. Ghorbani, and A. H. Lashkari, “Implementation of a trust-based framework for substation defense in the smart grid,” Smart Cities, vol. 7, no. 1, pp. 99–140, 2024, doi: 10.3390/smartcities7010005.",
    "R. T. Rockafellar and S. Uryasev, “Optimization of conditional value-at-risk,” J. Risk, vol. 2, no. 3, pp. 21–42, 2000.",
    "X. Fang, B.-M. Hodge, H. Jiang, and Y. Zhang, “Decentralized wind uncertainty management: Alternating direction method of multipliers based distributionally-robust chance constrained optimal power flow,” Appl. Energy, vol. 239, pp. 938–947, 2019.",
    "Z. Shi, H. Liang, S. Huang, and V. Dinavahi, “Distributionally robust chance-constrained energy management for islanded microgrids,” IEEE Trans. Smart Grid, vol. 10, no. 2, pp. 2234–2244, 2019.",
    "J. Zhai, Y. Jiang, Y. Shi, C. N. Jones, and X.-P. Zhang, “Distributionally robust joint chance-constrained dispatch for integrated transmission-distribution systems via distributed optimization,” IEEE Trans. Smart Grid, vol. 13, no. 3, pp. 2132–2147, 2022.",
    "A. Cherukuri and J. Cortés, “Distributed coordination of DERs with storage for dynamic economic dispatch,” IEEE Trans. Autom. Control, vol. 63, no. 3, pp. 835–842, 2018.",
    "G. Hug, S. Kar, and C. Wu, “Consensus + innovations approach for distributed multiagent coordination in a microgrid,” IEEE Trans. Smart Grid, vol. 6, no. 4, pp. 1893–1903, 2015.",
    "J. Qin, Y. Wan, X. Yu, F. Li, and C. Li, “Consensus-based distributed coordination between economic dispatch and demand response,” IEEE Trans. Smart Grid, vol. 10, no. 4, pp. 3709–3719, 2019.",
    "J.-O. Lee and Y.-S. Kim, “Novel battery degradation cost formulation for optimal scheduling of battery energy storage systems,” Int. J. Electr. Power Energy Syst., vol. 137, p. 107795, 2022.",
    "Y. Ding, T. Morstyn, and M. D. McCulloch, “Distributionally robust joint chance-constrained optimization for networked microgrids considering contingencies and renewable uncertainty,” IEEE Trans. Smart Grid, vol. 13, no. 3, pp. 2467–2478, 2022, doi: 10.1109/TSG.2022.3150397.",
    "X. Cai, X. Nan, and B. Gao, “Resilient distributed resource allocation algorithm under false data injection attacks,” arXiv:2212.02825, 2022.",
    "R. Deng, G. Xiao, R. Lu, H. Liang, and A. V. Vasilakos, “False data injection on state estimation in power systems—Attacks, impacts, and defense: A survey,” IEEE Trans. Ind. Informat., vol. 13, no. 2, pp. 411–423, 2017.",
    "L. Sun, D. Ding, H. Dong, and X. Yi, “Distributed economic dispatch of microgrids based on ADMM algorithms with encryption-decryption rules,” IEEE Trans. Autom. Sci. Eng., vol. 22, pp. 8427–8438, 2025, doi: 10.1109/TASE.2024.3485922.",
    "C. Zhao, J. He, P. Cheng, and J. Chen, “Analysis of consensus-based distributed economic dispatch under stealthy attacks,” IEEE Trans. Ind. Electron., vol. 64, no. 6, pp. 5107–5117, 2017, doi: 10.1109/TIE.2016.2638400.",
    "P. Li, Y. Liu, H. Xin, and X. Jiang, “A robust distributed economic dispatch strategy of virtual power plant under cyber-attacks,” IEEE Trans. Ind. Informat., vol. 14, no. 10, pp. 4343–4352, 2018.",
    "S. Yang, S. Tan, and J.-X. Xu, “Consensus based approach for economic dispatch problem in a smart grid,” IEEE Trans. Power Syst., vol. 28, no. 4, pp. 4416–4426, 2013.",
    "T. Yang, J. Lu, D. Wu, J. Wu, G. Shi, Z. Meng, and K. H. Johansson, “A distributed algorithm for economic dispatch over time-varying directed networks with delays,” IEEE Trans. Ind. Electron., vol. 64, no. 6, pp. 5095–5106, 2017.",
    "A. Nedić, A. Olshevsky, and W. Shi, “Achieving geometric convergence for distributed optimization over time-varying graphs,” SIAM J. Optim., vol. 27, no. 4, pp. 2597–2633, 2017.",
    "S. S. Kia, B. Van Scoy, J. Cortés, R. A. Freeman, K. M. Lynch, and S. Martínez, “Tutorial on dynamic average consensus: The problem, its applications, and the algorithms,” IEEE Control Syst. Mag., vol. 39, no. 3, pp. 40–72, 2019.",
    "R. D. Zimmerman, C. E. Murillo-Sánchez, and R. J. Thomas, “MATPOWER: Steady-state operations, planning, and analysis tools for power systems research and education,” IEEE Trans. Power Syst., vol. 26, no. 1, pp. 12–19, 2011.",
]))

json.dump(dict(blocks=B), open("/home/claude/paper/paper.json", "w"), ensure_ascii=False)
print("blocks:", len(B))

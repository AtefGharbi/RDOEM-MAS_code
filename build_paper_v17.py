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
                  alt=cap[:120]))
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


# ------------------------------------------------------------------ front matter
B.append(dict(type="title", text="Trust-Aware Dynamic Consensus for Risk-Aware Distributed Energy Management: "
                                  "Design, Conditional Analysis, and Simulation Evidence"))
B.append(dict(type="authors", text="Revised manuscript (v17) — author names and affiliations to be inserted"))
H1("Abstract")
P("This paper presents RDOEM-MAS, a trust-aware distributed energy-management architecture that combines "
  "peer-to-peer price negotiation, scenario-based recourse with a conditional value-at-risk (CVaR) term, dynamic sum "
  "tracking of the mismatch and of scenario recourse costs, CVaR tail-weight averaging, and trust-reweighted "
  "consensus (TARC). The theoretical contribution is conditional: under symmetric doubly stochastic mixing we "
  "establish a sum-tracking invariant and an input-to-state disagreement bound; under separable recourse or a "
  "KKT-consistent marginal allocation, fixed points satisfy the centralized CVaR KKT conditions. For network-coupled "
  "recourse the method is evaluated only as an approximate stationarity mechanism; convergence of the full coupled "
  "iteration, attack detection and Byzantine consensus are not established. On IEEE 30-, 57- and 118-bus cost data "
  f"with synthetic scenarios, welfare gaps to the centralized optimum were {S_GAP_RANGE} (separable) and "
  f"{C_GAP_RANGE} (coupled). Communication depends on the accuracy target. At a fixed 300-round budget, the static "
  f"re-convergence baseline used {RATIO}× fewer messages than dynamic tracking. At equal accuracy (mismatch held "
  f"below 1% of peak), dynamic tracking needed a median of {e8(DYN, 'dP<1%')[0]:.1f}k messages per epoch against "
  f"{e8(ST2, 'dP<1%')[0]:.1f}k for the best static setting ({e8(FULL, 'dP<1%')[0]:.1f}k including the TARC "
  "handshake); at 0.1% accuracy the static baseline was more reliable. On held-out seeds, a revised trust score "
  f"(TARC-R) reduced the median welfare gap during a constant-bias attack from {pc(H1n, 0)}% to {pc(H1r, 1)}%, but "
  "it left honest agents excluded after the attack and did not detect attacks confined to the mismatch payload.")
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
  "consensus. The theory is conditional: under symmetric doubly stochastic mixing we establish a sum-tracking "
  "invariant and a disagreement bound, and under separable recourse or a KKT-consistent marginal allocation, fixed "
  "points satisfy the centralized CVaR KKT conditions. For network-coupled recourse the method is evaluated only as "
  "an approximate stationarity mechanism. The experiments quantify benefits and failure modes alike, including "
  "communication overhead, persistent trust exclusions and blindness to mismatch-only attacks.")
LIST([
    [b("Formulation (application-specific adaptation). "),
     "A two-stage day-ahead/recourse optimal energy management (OEM) problem with a Rockafellar–Uryasev CVaR term, instantiated with two recourse models: "
     "a separable fixed-policy model that satisfies the exact-separability assumption R1 by construction, and a "
     "network-coupled merit-order recourse that violates it. We define a centralized-KKT residual r_KKT (Section IV-E) "
     "that makes “approximate stationarity” measurable."],
    [b("Algorithm (new combination with two new design elements). "),
     "Dynamic sum tracking of the mismatch and of every scenario recourse cost through trust-weighted symmetric "
     "consensus (Section V). The new elements are (i) ergodic averaging of CVaR tail weights, which removes a "
     "tail-set chattering we observed with the plain subgradient rule, and (ii) re-anchoring of the trackers at "
     "epoch boundaries, which removes the permanent sum error that injected data otherwise leaves. We also report a "
     "revised trust score, TARC-R, motivated by a failure of the originally specified score."],
    [b("Analysis (conditional theorems built on standard techniques). "),
     "An exact sum-tracking invariant, a tracking-error bound, fixed-point/KKT equivalence statements that separate "
     "existence, KKT equivalence and convergence, and a conditional input-to-state disagreement bound for the "
     "projected consensus recursion (Section VI). The proof techniques are standard [2], [28], [29]; the "
     "contribution is their precise scoping to this architecture."],
    [b("Empirical evaluation, including negative results. "),
     "IEEE 30/57/118-bus experiments with baselines, attacks, a packet-loss × adversary phase diagram, ablations, "
     "confidence intervals and paired tests; open code reproduces every number (Appendix C)."],
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
       ["Ergodic tail-weight averaging", "New design element (empirically motivated)", "Subgradient averaging",
        "Removes tail-set chattering; ablation −13 pp gap"],
       ["Epoch re-anchoring of trackers", "New design element", "Reset control in consensus ED",
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
  "quantity. It appears once in the day-ahead balance ΔP = Σ_i s_i − P_loss and once in each recourse balance. For "
  "local mismatch decomposition only, it is partitioned as P_loss = Σ_i ℓ_i, with ℓ_j = 0.02·P̂_D,j for load agents "
  "and ℓ_i = 0 otherwise. The tracker input is u_i = s_i − ℓ_i, so Σ_i u_i = ΔP. Losses enter no local cost and no "
  "stationarity condition.")
P("Each battery b has energy capacity E_b = 4·P_b^max × 1 h (MWh) and stored energy e_b, its state of charge in "
  "MWh, constrained to [0.1E_b, 0.9E_b]. Its power limits are p_dis ≤ min{P_b^max, η_d(e_b − 0.1E_b)/Δt} and "
  "p_ch ≤ min{P_b^max, (0.9E_b − e_b)/(η_cΔt)}, with Δt = 1 h. It maximizes λ(p_dis − p_ch) + v_b(η_c p_ch − "
  "p_dis/η_d) − κ_b(p_ch² + p_dis²), with a quadratic degradation proxy (cf. [19]). The maximizer is "
  "p_dis = Π[(λ − v_b/η_d)/(2κ_b)], p_ch = Π[(v_bη_c − λ)/(2κ_b)].")
P(b("No simultaneous charge and discharge. "), "At most one of p_ch, p_dis is positive whenever η_cη_d < 1, v_b > 0 "
  "and κ_b > 0. Indeed p_dis > 0 requires λ > v_b/η_d, p_ch > 0 requires λ < v_bη_c, and v_bη_c < v_b/η_d. This "
  "direct argument replaces Lemma 1 of the previous version for the model used here, and it needs no assumption on "
  "the sign of the price. After each epoch, e_b is updated with the committed action. The lookahead-horizon QP of "
  "the previous version is not used.")
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
EQ("max  W₀(x) − β[ζ + (1−α)⁻¹ Σ_m π_m s_m]   s.t.  ΔP(x) = Σ_i s_i − P_loss = 0,  s_m ≥ Q_m(x) − ζ,  s_m ≥ 0,  x ∈ X", 1)
P("Here W₀ is utility minus generation cost plus battery value, P_loss is the fixed loss forecast of Section "
  "III-A, and Q_m(x) is the recourse cost of scenario m.")
H2("C. Two Recourse Models")
P(b("Regime S (separable, satisfies R1). "), "The aggregate load error ε_m is covered by generators with fixed "
  "participation κ_i ∝ P_i^max. Generator i pays c_i^up·min(n_im, H_i) + c^shed·(n_im − H_i)₊ for need "
  "n_im = κ_iε_m > 0 and headroom H_i = P_i^max − P_i (symmetrically, down-regulation at c_i^dn and spill at "
  "c^spill). Each renewable settles its own shortfall at c^short·(P_R,k − A_k,m)₊, where A_k,m is scenario "
  "availability. Hence Q_m = Σ_i q_i,m(x_i), each term depending only on the agent’s own decision.")
P(b("Regime C (network-coupled). "), "A recourse LP with one shared real-time balance: free renewable flexibility "
  "first, then generator regulation in merit order of c^up (or c^dn), then shedding (or spill). Q_m depends jointly on "
  "all headrooms, so R1 fails. It is evaluated in closed form; the closed form matches an LP solver in unit tests.")
P("Cost parameters: c_i^up = 1.15b_i + 0.25λ_ref, c_i^dn = 0.10b_i + 0.05λ_ref, c^shed = 30λ_ref, "
  "c^spill = 2λ_ref, c^short = 3λ_ref. In both regimes the distributed agents use the separable costs q_i,m as their "
  "local contributions. In regime C these are a surrogate, which is the source of approximation.")
P(b("Convexity check. "), "W₀ is concave. Generator and renewable costs are strictly convex (a_i, a_R > 0), load "
  "utilities are strictly concave (ψ_j > 0), and the battery term is strictly concave (κ_b > 0). In regime S, each "
  "q_i,m is convex piecewise linear in the agent’s own decision, because the penalty slopes exceed the regulation "
  "slopes (c^shed > c^up, c^spill > c^dn). In regime C, Q_m is the optimal value of a linear program whose "
  "right-hand side is affine in x and which is always feasible (shedding and spill are unbounded slacks), so it is "
  "convex piecewise linear. CVaR is convex and nondecreasing in (Q_1, …, Q_M), so β·CVaR(Q(x)) is convex, and "
  "problem (1) is convex in both regimes. Every local problem of Section V-A is strictly convex. What fails in "
  "regime C is therefore not convexity but R1: the local surrogate sensitivities ∂q_i,m differ from the centralized "
  "partial subgradients ∂_{x_i}Q_m. Regime S satisfies all assumptions of Propositions 3–4; regime C satisfies "
  "all except R1.")
H2("D. Stationarity and the Exact/Approximate Distinction")
P("For generator i, interior stationarity reads C_i′(P_i) + β g_i − λ = 0 with "
  "g_i = Σ_m ω_m ∂q_i,m/∂P_i and tail weights ω_m = π_mθ_m/(1−α), θ_m = 1{Q_m > ζ} (fractional at ties). The sign of "
  "g_i is not restricted.")
BOX(b("Scope of the risk-aware result. "),
    b("Exact: "), "separable recourse (R1) or a proven KKT-consistent marginal allocation — local sensitivities then "
    "equal the centralized subgradients. ",
    b("Approximate: "), "network-coupled recourse with surrogate local sensitivities — measured by r_KKT and the "
    "welfare gap. ",
    b("Not established: "), "exact centralized optimality for general network-coupled recourse, and convergence of "
    "the coupled iteration to any fixed point.")
H2("E. Centralized-KKT Residual")
P("Let F(x) = −W₀(x) + β CVaR_α(Q(x)) with the true recourse model, a_i = ∂ΔP/∂x_i ∈ {±1}, and X_i the local box. "
  "With one-sided directional derivatives ∂⁻_iF, ∂⁺_iF (difference step 10⁻⁴·P_peak/100 MW), define")
EQ("r_KKT(x) = min_λ [ (1/n) Σ_i dist(0, [∂⁻_iF − λa_i, ∂⁺_iF − λa_i] + N_Xi(x_i))² ]^½", 2)
P("We use r_KKT as a coordinatewise stationarity diagnostic, not as a certificate. For convex F, the i-th "
  "component of every subgradient lies in [∂⁻_iF, ∂⁺_iF], so r_KKT ≤ dist(0, ∂_xL(x, λ)). The two coincide where F "
  "is differentiable, as in the separable case away from kinks. For the nonsmooth coupled CVaR problem, a small "
  "r_KKT is necessary for stationarity but not sufficient, so it is not a complete certificate of KKT optimality. "
  "We report r_KKT/λ_ref together with |ΔP|, which it excludes. At CVXPY solutions of the centralized problem "
  "r_KKT/λ_ref ≤ 10⁻⁶ in both regimes. Msgs/epoch: total "
           "at the fixed budget K = 300, counted as in Section V-F; Table VI-B gives equal-accuracy counts.")
P(b("Why r_KKT can be large while the gap is small. "), "With α = 0.9, M = 30 and β = 1, each tail scenario carries "
  "weight ω_m = (1/30)/0.1 = 1/3. A renewable schedule a few kW below the availability kink of a tail scenario "
  "therefore misses the jump βω_m c^short = λ_ref in its one-sided derivatives. That single coordinate contributes a "
  "residual of about λ_ref; averaged over the n = 34 decision coordinates of IEEE-30, it gives "
  "r_KKT ≈ λ_ref/√34 ≈ 0.17λ_ref. The welfare effect of a few kW is below 0.01%. r_KKT must therefore be read "
  "together with the welfare gap.")

# ------------------------------------------------------------------ V
H1("V. RDOEM-MAS Algorithm")
H2("A. Local Best Responses")
P("Given its price λ_i and tail weights ω̄_i,m, each agent solves its one-dimensional convex problem exactly. For a "
  "generator this is min ½a_iP² + b_iP − λ_iP + β Σ_m ω̄_i,m q_i,m(P) over [P^min, P^max], solved by 32 bisection "
  "steps on the nondecreasing right derivative. Renewables are handled the same way, and loads and batteries in "
  "closed form. Decisions are recomputed in every round from the current price. The tracker input is u_i = s_i − ℓ_i.")
H2("B. Weights on the Retained Graph")
P("For a retained edge {i,j}, w_ij = min{1/(d_i+1), 1/(d_j+1)}·ρ_ij^eff and w_ii = 1 − Σ_j w_ij, where d_i is the "
  "retained degree and ρ^eff = ρ_edge^m_sh·min(ρ_ij, ρ_ji) is the mutual-minimum effective trust. W_k is symmetric "
  "and doubly stochastic, with w_ii ≥ 1/(d_i+1) (Lemma 2 of the previous version).")
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
EQ("Q̂^{k+1}_{·,m} = W_k Q̂^k_{·,m} + N(q^{k+1}_{·,m} − q^k_{·,m}),   ζ_i = VaR_α(Q̂_{i,·}),   ω̄ ← (1−ρ_k)ω̄ + ρ_k ω(Q̂, ζ)", 4)
P("Averaging uses ρ_k = 1/(1 + k/k_ω) with k_ω = 1. The quantile ζ_i is the local weighted α-quantile of the "
  "tracked scenario costs, which is exact once trackers agree. The consensus–subgradient rule of the previous version "
  "is retained as an alternative; the two perform equivalently (Table VIII-B).")
P("Step-size rule. A perturbation of λ_i changes u_i by up to its response slope ℓ_i and x_i by N·ℓ_i. The resulting "
  "loop gain η·N·ℓ_i must stay below the graph’s mixing rate. We therefore set η₀ = c_η(1 − σ₂)/(N max_i ℓ_i) with "
  "c_η = 2, where σ₂ is the second-largest eigenvalue modulus of the nominal weight matrix (an offline constant), and "
  "η_k = η₀/(1 + k/100)^0.6. The loop was unstable at c_η = 4 without decay.")
H2("E. Initialization, Stopping and Edge Cases")
LIST([["Day start: λ_i^0 = λ_ref; ω̄ = π (risk-neutral weights); x_i^0 = Nu_i^0; Q̂_i,m^0 = Nq_i,m^0; ζ_i^0 = "
       "VaR_α(Q̂_i,·^0); raw trust 1; counters 0."],
      ["Epoch boundary: λ and trust are kept. Trackers are re-anchored, x_i = Nu_i and Q̂_i = Nq_i, which restores the "
       "invariant (Proposition 2). Tail weights are re-initialized because scenario indices change."],
      ["Stopping: a fixed budget of K = 300 rounds. The tolerance test (max_i|x_i| < 0.01P_peak, |ΔP| < 0.01P_peak, "
       "max|Δλ| < 0.01λ_ref for 5 consecutive rounds) is an evaluation metric only, because |ΔP| needs a central "
       "observer."],
      ["No retained neighbour: w_ii = 1. The agent updates its price from its own tracker, and its increments stay in "
       "the network sum, so the invariant is unaffected."],
      ["Feasibility: all local problems are feasible by construction (box constraints, bisection). Any committed "
       "day-ahead imbalance ΔP enters the recourse requirement, so the balance convention is preserved in the "
       "evaluation."]])
B.append(dict(type="algo", title="Algorithm 1: RDOEM-MAS (one epoch t)", lines=[
    dict(runs=["Input: forecasts, scenarios {ξ_m, π_m}, α, β, K, W-rule parameters, warm states (λ, trust)."]),
    dict(runs=["Init: re-anchor x ← Nu, Q̂ ← Nq; ω̄ ← ω(Q̂, ζ); k ← 0."]),
    dict(runs=["for k = 0, …, K−1 do"]),
    dict(level=1, runs=["Exchange authenticated reports (λ_j, x_j, Q̂_j, ζ_j); lost links → m_ij += 1."]),
    dict(level=1, runs=["TARC: if k ≥ G score fresh reports, update ρ_ij and gated scales; mutual-min handshake; "
                        "retain edges."]),
    dict(level=1, runs=["Build W_k by rule (4)."]),
    dict(level=1, runs=["Price: λ ← Π(W_kλ − η_k x)."]),
    dict(level=1, runs=["Tail weights: ω̄ ← (1−ρ_k)ω̄ + ρ_k ω(Q̂, ζ)."]),
    dict(level=1, runs=["Local best responses at (λ_i, ω̄_i) → u⁺, q⁺."]),
    dict(level=1, runs=["Trackers: x ← W_k x + N(u⁺ − u); Q̂ ← W_k Q̂ + N(q⁺ − q); ζ_i ← VaR_α(Q̂_i)."]),
    dict(runs=["end for"]),
    dict(runs=["Commit day-ahead schedule; after uncertainty is realized, apply recourse (Section IV-C)."]),
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
P(b("Proposition 2 (dynamic sum tracking). "), "Let x^{k+1} = W_kx^k + N(u^{k+1} − u^k) with W_k doubly stochastic "
  "and x^0 = Nu^0. (a) For all k, (1/N)1ᵀx^k = 1ᵀu^k. (b) Under G1, with block increments "
  "δ_h = max_{r in block h}‖u^{r+1} − u^r‖, ‖J_⊥x^{(h+1)B}‖ ≤ γ_B‖J_⊥x^{hB}‖ + c_Bδ_h; hence "
  "limsup‖J_⊥x^{hB}‖ ≤ c_B sup_h δ_h/(1 − γ_B), and if u^k → u^∞ then x_i^k → Σ_j u_j^∞ for every i.")
P(i("Proof of (a). "), "1ᵀx^{k+1} = 1ᵀW_kx^k + N1ᵀ(u^{k+1} − u^k) = 1ᵀx^k + N(1ᵀu^{k+1} − 1ᵀu^k), using 1ᵀW_k = 1ᵀ. "
  "With 1ᵀx^0 = N1ᵀu^0, induction gives 1ᵀx^k = N1ᵀu^k. Part (b) follows by expanding B steps and applying "
  "Proposition 1 to the disagreement component [3], [28]. ∎")
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
P(b("Proposition 3 (fixed-point characterization under exact tracking). "), "Fix an epoch, and let λ* lie in the "
  "interior of the price interval. Let x^loc(λ, ω) denote the vector of local best responses (Section V-A), and "
  "consider the state S* = (λ_i = λ*, x_i = 0, Q̂_i,m = Q_m(x^loc), ζ_i = ζ*, ω̄_i = ω*), where ζ* is the "
  "α-quantile of {Q_m(x^loc)} and ω* are the tail weights that rule (4) produces from these exact costs. Assume "
  "three conditions. (A1) Every local problem is strictly convex, so x^loc(λ*, ω*) is unique. (A2) No scenario cost "
  "equals ζ*. (A3) ΔP(x^loc(λ*, ω*)) = 0. Then S* is invariant under one round of Algorithm 1 for every step size "
  "and every retained graph.")
P(i("Proof. "), "The price step returns W_kλ* − η_k·0 = λ*. The responses are unchanged by (A1), so the increments "
  "of u and q vanish and x = 0 and Q̂ are preserved, because consensual vectors are fixed by W_k. By (A2), "
  "recomputing ζ and ω returns ζ* and ω*, so the averaging leaves ω̄ unchanged. (A3) is consistent with Proposition "
  "2(a): mean(x) = Σu = ΔP = 0. ∎")
P(i("Existence. "), "Under R1 and the convexity established in Section IV-C, let (x*, λ*) be a centralized KKT pair "
  "with λ* interior and no tie at ζ*. Proposition 4 and strict convexity give x^loc(λ*, ω*) = x*, so (A3) holds and "
  "S* is a fixed point: a fixed point exists. If a tie occurs, the CVaR subgradient may require fractional tail "
  "weights that rule (4) does not produce at S*. Existence of a fixed point of Algorithm 1 is then not established, "
  "although the averaged weights ω̄ can approach fractional values (Section VIII-G). Without R1, S* is built from "
  "the surrogate costs and characterizes the surrogate problem only.")
P(b("Proposition 4 (centralized KKT equivalence under separability). "), "Let S̄ be a fixed point of one round "
  "with consensual price λ̄ in the interior of the interval, x̄_i = 0, consensual exact scenario-cost trackers, and "
  "tail weights ω̄. By Proposition 2(a), ΔP(x̄) = 0. (a) If β = 0, (x̄, λ̄) satisfies the centralized KKT "
  "conditions. (b) If β > 0, R1 holds (or the marginal allocation is proven KKT-consistent), and ω̄ is a valid CVaR "
  "subgradient weight vector at x̄, then (x̄, λ̄) satisfies the centralized CVaR KKT conditions. Without R1, "
  "(x̄, λ̄) satisfies the KKT conditions of the surrogate problem, in which Σ_i q_i,m replaces Q_m; its distance "
  "from the centralized conditions is what r_KKT diagnoses.")
P(i("Proof. "), "Local optimality gives 0 ∈ ∇f_i(x̄_i) + βΣ_m ω̄_m ∂q_i,m(x̄_i) − λ̄a_i + N_Xi(x̄_i) for each i. "
  "Under R1, ∂_{x_i}Q_m = ∂q_i,m, so stacking these conditions gives 0 ∈ ∂F(x̄) − λ̄a + N_X(x̄). With ΔP = 0 and "
  "the convexity of Section IV-C, this is the KKT system of (1). ∎")
P(b("Remark (convergence). "), "Neither proposition asserts convergence. Convergence of the coupled "
  "price–decision–tracker–trust iteration from arbitrary initial states is not established and is assessed only "
  "empirically (Section VIII).")
P(b("Proposition 5 (conditional input-to-state disagreement bound for the projected consensus recursion). "),
  "Let z^{k+1} = W_kz^k + d_k with W_k satisfying G1 and e_k = J_⊥z^k. If the block-projected disturbance "
  "v_h = J_⊥Σ_r Φ(hB+B, hB+r+1)d_{hB+r} satisfies ‖v_h‖ ≤ D_h, then ‖e_{(h+1)B}‖ ≤ γ_B‖e_{hB}‖ + D_h and "
  "limsup‖e_{hB}‖ ≤ sup_h D_h/(1 − γ_B).")
P(i("Application to TARC. "), "For the price recursion, d_k collects −η_kx^k, the attack contribution "
  "Σ_{j∈A} w_ij b_j, and the projection residual. The bound applies to TARC only after two things are verified "
  "analytically or empirically: that this combined disturbance is bounded, and that the retained graph satisfies G1. "
  "Proposition 5 says nothing about detection, edge removal or Byzantine resilience. In our attack traces G1 failed "
  "in most blocks under TARC-R (Section VIII-F).")
TABLE("Table III. Status of each claim",
      ["Claim", "Status", "Conditions / evidence"],
      [["Sum-tracking invariant (Prop. 2a)", "Exact", "Doubly stochastic W, x⁰ = Nu⁰, uncorrupted reports; "
        "measured error ≤ 10⁻¹³ MW"],
       ["Disagreement contraction (Prop. 1), tracking bound (Prop. 2b)", "Conditional", "G1"],
       ["Fixed-point invariance (Prop. 3); KKT equivalence (Prop. 4)", "Conditional, exact", "Strict convexity, no tie; R1 or "
        "consistent allocation, exact trackers"],
       ["Risk-aware stationarity under coupled recourse", "Approximate", f"Gap {pc(min(gapC.values()), 1)}–"
        f"{pc(max(gapC.values()), 1)}%; r_KKT reported"],
       ["Convergence of the coupled iteration", "Not established", "Empirical only; tolerance reached in few "
        "epochs within K = 300"],
       ["ISS disagreement bound (Prop. 5)", "Conditional", "Bounded combined disturbance and G1; G1 violated "
        "in attack traces"],
       ["Attack detection, Byzantine consensus", "Not established", "Empirical, attack-dependent (Section VIII-E)"],
       ["Communication reduction by dynamic tracking", "Accuracy- and budget-dependent",
        f"Fewer messages at 1% accuracy; static used {RATIO}× fewer at fixed K and was more reliable at 0.1%"]],
      widths=[3.2, 1.6, 4.2])

# ------------------------------------------------------------------ VII
H1("VII. Experimental Setup")
TABLE("Table IV. Test systems (cost data from MATPOWER cases [30]; profiles synthetic)",
      ["System", "N (G/R/L/B)", "Comm. edges", "1 − σ₂", "Peak demand (MW)", "λ_ref ($/MWh)"],
      [[c.upper().replace("IEEE", "IEEE-"), f"{v['N']} ({v['nG']}/{v['nR']}/{v['nL']}/{v['nB']})", str(v["E"]),
        f"{v['gap']:.3f}", f"{v['peak']:.0f}", f"{v['lam']:.2f}"] for c, v in syst.items()],
      widths=[1.3, 2, 1.3, 1, 1.6, 1.4])
P("Data. Generator costs and limits come from the IEEE cases. Demand is scaled so that the peak hour uses 80% of "
  "generation capacity, which makes headroom, and hence risk, matter. Daily load and solar/wind shapes and all "
  "forecast errors are synthetic and seeded. No measured data set is used; validation on measured profiles "
  "(e.g., NREL, PJM, ENTSO-E) remains future work. The model is copper-plate: there are no line flows, voltage "
  "or frequency, so grid-constraint metrics are not reported.")
P("Methods. (1) Centralized CVaR benchmark (CVXPY/Clarabel, extensive form) under the same scenarios and the same "
  "battery state. (2) RDOEM-MAS with TARC-R (full method). (3) RDOEM-MAS with TARC-v15. (4) Dynamic tracking without "
  "TARC (trust ≡ 1, same weight rule). (5) The same without re-anchoring (the previous version’s warm start). "
  "(6) W-MSR with f_W = 1 applied to price and mismatch, other states with standard weights; its (2f+1)-robustness "
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
  "true recourse model of each regime (a committed imbalance enters recourse). Also reported: r_KKT/λ_ref; |ΔP|; "
  "the fraction of epochs reaching tolerance; messages per epoch (every attempted link carries two data messages "
  "per round, and TARC adds two handshake messages); out-of-sample E[recourse cost] and CVaR; the false-positive "
  "rate (share of active honest–honest edge-rounds removed); and the attacker-edge removal rate.")
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
      ["System", "Method", "Gap S (%)", "Gap C (%)", "r_KKT S", "r_KKT C", "|ΔP| (MW)", "Tol. reached (%)",
       "Msgs/epoch (k)"], rows, widths=[1.1, 2.4, 1.7, 1.7, 0.9, 0.9, 0.9, 0.9, 1.0], size=14,
      note="Gap S / Gap C: separable / coupled recourse. r_KKT normalized by λ_ref. Centralized solutions: "
           "r_KKT/λ_ref ≤ 10⁻⁶ in both regimes.")
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
P(f"At the fixed budget (Fig. 5, Table VI), the static re-convergence baseline used {RATIO}× fewer messages than "
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
      note="Medians are over the epochs that reached the target; read them with the reach shares.")
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
TABLE("Table VII. Effect of β (IEEE-30, 10 seeds; out-of-sample recourse evaluated with the coupled model)",
      ["β", "E[recourse] ($/h)", "CVaR₀.₉ ($/h) [95% CI]", "Gen. cost ($/h)", "Gap S (%)", "Gap C (%)"], rows,
      widths=[0.7, 1.6, 2.4, 1.5, 1.2, 1.2])
P(f"Raising β from 0 to 2 cut the out-of-sample CVaR from {e3[0.0]['CV'][0]:.1f} to {e3[2.0]['CV'][0]:.1f} $/h and "
  f"the expected recourse cost from {e3[0.0]['EQ'][0]:.1f} to {e3[2.0]['EQ'][0]:.2f} $/h. In exchange, day-ahead "
  f"generation cost rose from {e3[0.0]['gen'][0]:.0f} to {e3[2.0]['gen'][0]:.0f} $/h, as reserve headroom was "
  "withheld and renewable schedules became more conservative. At β = 0 the gap is essentially zero "
  f"({100 * e3[0.0]['gap'][0]:.4f}%), so the risk term is what makes the negotiation hard. As β grows, the regime-S "
  "gap grows and the regime-C gap shrinks, because the coupled model’s marginal costs become better approximated as "
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
TABLE("Table VIII-A. Attack outcomes on IEEE-30 (seeds 0–9): median gap (%) before/during/after, false-positive (FP) and attacker-edge "
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
TABLE("Table VIII-C. Held-out replication on IEEE-30 (seeds 100–109, never used for tuning)",
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
TABLE("Table VIII-D. TARC-R sensitivity (ATT-1, IEEE-30, held-out seeds 100–104; one parameter varied at a time)",
      ["Variant", "During (median %)", "Post (median %)", "FP pre-attack (%)", "FP during (%)", "Att. removed (%)"],
      [[v["variant"], pc(v["during"], 1), pc(v["post"], 1), pc(v["fp_pre"], 1), pc(v["fp_during"], 0),
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
  f"and three or more produced ≈{pc(tn.loc[3].mean(), 0)}% (Fig. 9). With one attacker, TARC-R kept the median gap "
  f"at {pc(tr.loc[1].min(), 1)}–{pc(tr.loc[1].max(), 1)}% at every loss level up to 40% (medians over 5 seeds per "
  "cell). The median hides dispersion: across the 25 seed–loss cells with one attacker, per-seed mean gaps ranged "
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
  "sum invariant holds to machine precision, and the two new design elements are each justified by an ablation "
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
P("All code, raw per-run results (CSV, one file per run keyed by a configuration hash) and figure scripts accompany "
  "this manuscript (package rdoem/). Unit tests verify the merit-order recourse against an LP solver, the "
  "centralized KKT residual, the doubly stochastic weights, and the sum invariant under packet loss. Seeds are the "
  "integers 0–19; system seed s and day seed s are used for run s.")

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

"""Apply second-review revisions to build_paper.py -> build_paper_v17.py"""
src = open("/home/claude/paper/build_paper.py").read()


def rep(a, b, count=1):
    global src
    assert a in src, "MISSING: " + a[:80]
    src = src.replace(a, b, count)


def swap(start, end, new, keep_end=False):
    global src
    i = src.index(start)
    j = src.index(end, i)
    j2 = j if keep_end else j + len(end)
    src = src[:i] + new + src[j2:]


def after(marker, new):
    global src
    i = src.index(marker) + len(marker)
    src = src[:i] + "\n" + new + src[i:]


# ---------------- numbers from revision-2 experiments
after('A1n, A1r = m4("ATT-1", NOT, "during"), m4("ATT-1", FULL, "during")', '''
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
''')
rep("Revised manuscript (v16)", "Revised manuscript (v17)")

# ---------------- abstract (comments 1, recommended contribution statement)
swap('P("We propose RDOEM-MAS, a peer-to-peer', '"attacks confined to the mismatch payload.")', '''P("This paper presents RDOEM-MAS, a trust-aware distributed energy-management architecture that combines "
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
  "it left honest agents excluded after the attack and did not detect attacks confined to the mismatch payload.")''')

# ---------------- introduction
rep("A two-stage day-ahead/recourse OEM with", "A two-stage day-ahead/recourse optimal energy management (OEM) problem with")
after('"of existing mechanisms, a theorem, or an application-specific adaptation.")', '''P("In brief, the architecture combines dynamic sum tracking, CVaR tail-weight averaging and trust-reweighted "
  "consensus. The theory is conditional: under symmetric doubly stochastic mixing we establish a sum-tracking "
  "invariant and a disagreement bound, and under separable recourse or a KKT-consistent marginal allocation, fixed "
  "points satisfy the centralized CVaR KKT conditions. For network-coupled recourse the method is evaluated only as "
  "an approximate stationarity mechanism. The experiments quantify benefits and failure modes alike, including "
  "communication overhead, persistent trust exclusions and blindness to mismatch-only attacks.")''')
swap('P("The main findings are mixed and are stated as such.', 'but introduced persistent exclusions and did not detect mismatch-only attacks.")', '''P("The main findings are mixed and are stated as such. The distributed schedule approaches the centralized CVaR "
  f"optimum within {S_GAP_RANGE} (separable recourse) and {C_GAP_RANGE} (coupled recourse). Dynamic tracking saves "
  "messages at moderate accuracy but not at a fixed round budget, and it is less reliable than static "
  "re-convergence at high accuracy. TARC-R reduced the damage of constant-bias and scaling attacks on held-out "
  "seeds, but introduced persistent exclusions and did not detect mismatch-only attacks.")''')

# ---------------- III-A: losses, inputs, battery (minor comments)
after('"the reference price λ_ref.")', '''P(b("Losses and local inputs. "), "P_loss = 0.02·Σ_j P̂_D,j is a fixed forecast parameter, not a decision-dependent "
  "quantity. It appears once in the day-ahead balance ΔP = Σ_i s_i − P_loss and once in each recourse balance. For "
  "local mismatch decomposition only, it is partitioned as P_loss = Σ_i ℓ_i, with ℓ_j = 0.02·P̂_D,j for load agents "
  "and ℓ_i = 0 otherwise. The tracker input is u_i = s_i − ℓ_i, so Σ_i u_i = ΔP. Losses enter no local cost and no "
  "stationarity condition.")''')
swap('P("Each battery solves a one-period problem', 'SOC is carried between hourly epochs with the committed action.")', '''P("Each battery b has energy capacity E_b = 4·P_b^max × 1 h (MWh) and stored energy e_b, its state of charge in "
  "MWh, constrained to [0.1E_b, 0.9E_b]. Its power limits are p_dis ≤ min{P_b^max, η_d(e_b − 0.1E_b)/Δt} and "
  "p_ch ≤ min{P_b^max, (0.9E_b − e_b)/(η_cΔt)}, with Δt = 1 h. It maximizes λ(p_dis − p_ch) + v_b(η_c p_ch − "
  "p_dis/η_d) − κ_b(p_ch² + p_dis²), with a quadratic degradation proxy (cf. [19]). The maximizer is "
  "p_dis = Π[(λ − v_b/η_d)/(2κ_b)], p_ch = Π[(v_bη_c − λ)/(2κ_b)].")
P(b("No simultaneous charge and discharge. "), "At most one of p_ch, p_dis is positive whenever η_cη_d < 1, v_b > 0 "
  "and κ_b > 0. Indeed p_dis > 0 requires λ > v_b/η_d, p_ch > 0 requires λ < v_bη_c, and v_bη_c < v_b/η_d. This "
  "direct argument replaces Lemma 1 of the previous version for the model used here, and it needs no assumption on "
  "the sign of the price. After each epoch, e_b is updated with the committed action. The lookahead-horizon QP of "
  "the previous version is not used.")''')

# ---------------- IV: P_loss consistency, convexity check (comment 5), r_KKT (comment 6)
swap('P("Here W₀ is utility minus generation cost plus battery value', 'is the recourse cost of scenario m.")',
     'P("Here W₀ is utility minus generation cost plus battery value, P_loss is the fixed loss forecast of Section "\n  "III-A, and Q_m(x) is the recourse cost of scenario m.")')
after('"local contributions. In regime C these are a surrogate, which is the source of approximation.")', '''P(b("Convexity check. "), "W₀ is concave. Generator and renewable costs are strictly convex (a_i, a_R > 0), load "
  "utilities are strictly concave (ψ_j > 0), and the battery term is strictly concave (κ_b > 0). In regime S, each "
  "q_i,m is convex piecewise linear in the agent’s own decision, because the penalty slopes exceed the regulation "
  "slopes (c^shed > c^up, c^spill > c^dn). In regime C, Q_m is the optimal value of a linear program whose "
  "right-hand side is affine in x and which is always feasible (shedding and spill are unbounded slacks), so it is "
  "convex piecewise linear. CVaR is convex and nondecreasing in (Q_1, …, Q_M), so β·CVaR(Q(x)) is convex, and "
  "problem (1) is convex in both regimes. Every local problem of Section V-A is strictly convex. What fails in "
  "regime C is therefore not convexity but R1: the local surrogate sensitivities ∂q_i,m differ from the centralized "
  "partial subgradients ∂_{x_i}Q_m. Regime S satisfies all assumptions of Propositions 3–4; regime C satisfies "
  "all except R1.")''')
swap('P("This is a lower bound on dist(0, ∂L(x, λ))', 'We therefore read r_KKT together with the gap.")', '''P("We use r_KKT as a coordinatewise stationarity diagnostic, not as a certificate. For convex F, the i-th "
  "component of every subgradient lies in [∂⁻_iF, ∂⁺_iF], so r_KKT ≤ dist(0, ∂_xL(x, λ)). The two coincide where F "
  "is differentiable, as in the separable case away from kinks. For the nonsmooth coupled CVaR problem, a small "
  "r_KKT is necessary for stationarity but not sufficient, so it is not a complete certificate of KKT optimality. "
  "We report r_KKT/λ_ref together with |ΔP|, which it excludes. At CVXPY solutions of the centralized problem "
  "r_KKT/λ_ref ≤ 10⁻⁶ in both regimes.")
P(b("Why r_KKT can be large while the gap is small. "), "With α = 0.9, M = 30 and β = 1, each tail scenario carries "
  "weight ω_m = (1/30)/0.1 = 1/3. A renewable schedule a few kW below the availability kink of a tail scenario "
  "therefore misses the jump βω_m c^short = λ_ref in its one-sided derivatives. That single coordinate contributes a "
  "residual of about λ_ref; averaged over the n = 34 decision coordinates of IEEE-30, it gives "
  "r_KKT ≈ λ_ref/√34 ≈ 0.17λ_ref. The welfare effect of a few kW is below 0.01%. r_KKT must therefore be read "
  "together with the welfare gap.")''')

# ---------------- V-F message accounting (comment 2)
after("widths=[1.5, 2.5, 5.5])", '''H2("F. Message Accounting")
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
  "payload grows, by 4/(3+M) ≈ 12%. We report the conservative separate-packet count.")''')

# ---------------- VI: invariant conditions (comment 3); split Prop. 3 (comment 4)
src = src.replace("Proposition 4", "Proposition 5").replace("Prop. 4", "Prop. 5")
swap('BOX(b("Remark (sum, not average). ")', 'restores the base case at every epoch.")', '''BOX(b("Remark (sum, not average; conditions for exactness). "), "Each x_i estimates Σ_j u_j = ΔP, the day-ahead "
    "mismatch that the price must drive to zero; it does not estimate the average. Invariant (a) uses only "
    "1ᵀW_k = 1ᵀ, which the construction guarantees when four conditions hold in every round. (i) The status of every "
    "link is common to both endpoints, fixed by the authenticated handshake; in our simulations a lost link is lost "
    "in both directions. (ii) Both endpoints use the same effective trust ρ^eff = ρ_edge^m_sh·min(ρ_ij, ρ_ji) and the "
    "same retention decision. (iii) Degrees are computed on that common retained graph, so w_ij = w_ji. (iv) All "
    "agents apply W_k synchronously. Under (i)–(iv), packet loss only zeroes symmetric pairs of weights and the "
    "invariant stays exact. If one endpoint could retain an edge that its neighbour drops, for example after a "
    "one-sided loss without handshake, W_k would be non-symmetric and the invariant would fail. Corrupted reports "
    "also break it: an honest agent mixing y_j = x_j + b_j adds w_ij b_j to 1ᵀx, and doubly stochastic mixing "
    "conserves that error. Re-anchoring (Section V-E) restores the base case at every epoch.")''')
swap('P(b("Proposition 3 (fixed points and KKT points). ")', '"is assessed only empirically (Section VIII)."]])', '''P(b("Proposition 3 (fixed-point characterization under exact tracking). "), "Fix an epoch, and let λ* lie in the "
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
  "empirically (Section VIII).")''')
rep("Fixed point ⇔ centralized KKT (Prop. 3i–ii)", "Fixed-point invariance (Prop. 3); KKT equivalence (Prop. 4)")
rep('"Convexity, R1 or consistent "\n        "allocation, exact trackers"', '"Strict convexity, no tie; R1 or "\n        "consistent allocation, exact trackers"')
swap('["Communication reduction by dynamic tracking"', '"messages"]', '''["Communication reduction by dynamic tracking", "Accuracy- and budget-dependent",
        f"Fewer messages at 1% accuracy; static used {RATIO}× fewer at fixed K and was more reliable at 0.1%"]''')

# ---------------- VII: tuning disclosure moved into protocol (comment 7)
after('Non-rejection is not read as equivalence.")', '''P(b("Parameter selection and independence. "), "The step constant c_η, the averaging constant k_ω and the TARC-R "
  "parameters were chosen on IEEE-30 pilot runs with seed 0, which is also an evaluation seed in E1 and E4. To "
  "limit the resulting optimism, the attack results are replicated on held-out seeds 100–109 that were never used "
  "for tuning (E9). A one-at-a-time sensitivity analysis of ρ_min, G and ρ_mem is run on held-out seeds 100–104 "
  "(E10). No held-out system was used: IEEE-57 and IEEE-118 were not used for tuning, but attacks were evaluated on "
  "IEEE-30 only.")''')
rep('r_KKT/λ_ref ≤ 10⁻⁶ in both regimes.")', 'r_KKT/λ_ref ≤ 10⁻⁶ in both regimes. Msgs/epoch: total "\n           "at the fixed budget K = 300, counted as in Section V-F; Table VI-B gives equal-accuracy counts.")')

# ---------------- VIII-C communication (comment 8); renumber figures
rep('FIGURE("fig8b_ablation.png", "Fig. 10.', 'FIGURE("fig8b_ablation.png", "Fig. 11.')
rep('FIGURE("fig9_prop4_check.png", "Fig. 9.', 'FIGURE("fig9_prop4_check.png", "Fig. 10.')
rep('P("Fig. 9 evaluates', 'P("Fig. 10 evaluates')
rep('FIGURE("fig7_phase.png", "Fig. 8.', 'FIGURE("fig7_phase.png", "Fig. 9.')
rep('FIGURE("fig6_attacks.png", "Fig. 7.', 'FIGURE("fig6_attacks.png", "Fig. 8.')
rep('FIGURE("fig8a_risk_tradeoff.png", "Fig. 6.', 'FIGURE("fig8a_risk_tradeoff.png", "Fig. 7.')
swap('H2("C. Communication")', 'H2("D. Risk Weight")', '''H2("C. Communication")
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
''', keep_end=True)

# ---------------- VIII-E attacks: disclosure, IEEE-30 label, held-out and sensitivity (comment 7)
after('H2("E. Attacks")', '''P("All attack results are for IEEE-30. TARC-R was tuned on seed 0, which is among seeds 0–9 below, so Table "
  "VIII-A may be optimistic for TARC-R. Tables VIII-C and VIII-D replicate the analysis on held-out seeds.")''')
rep("Table VIII-A. Attack outcomes: median gap", "Table VIII-A. Attack outcomes on IEEE-30 (seeds 0–9): median gap")
after('unless the tracker is redesigned.")', '''_r9 = []
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
  "an especially favourable setting.")''')

# ---------------- VIII-F phase diagram with dispersion (minor comment)
swap('P(f"Without defense, one compromised agent already produced gaps', 'nominally (f_att = 0) it had no effect on welfare.")', '''P(f"Without defense, one compromised agent already produced gaps of {pc(tn.loc[1].min(), 0)}–{pc(tn.loc[1].max(), 0)}%, "
  f"and three or more produced ≈{pc(tn.loc[3].mean(), 0)}% (Fig. 9). With one attacker, TARC-R kept the median gap "
  f"at {pc(tr.loc[1].min(), 1)}–{pc(tr.loc[1].max(), 1)}% at every loss level up to 40% (medians over 5 seeds per "
  "cell). The median hides dispersion: across the 25 seed–loss cells with one attacker, per-seed mean gaps ranged "
  f"from {pc(E5f1['min'], 1)}% to {pc(E5f1['max'], 0)}% (mean {pc(E5f1['ci'][0], 1)}%, 95% CI "
  f"[{pc(E5f1['ci'][1], 1)}, {pc(E5f1['ci'][2], 1)}]%), so a single attacker occasionally still caused a large "
  f"loss. With three attackers, the median rose from {pc(tr.loc[3].iloc[0], 1)}% to {pc(tr.loc[3].iloc[-1], 1)}% as "
  f"packet loss grew, and with nine it reached {pc(tr.loc[9].min(), 0)}–{pc(tr.loc[9].max(), 0)}%. Packet loss "
  "mattered only in combination with attacks: nominally (f_att = 0) it had no effect on welfare.")''')

# ---------------- discussion, limitations, conclusion, appendix B
swap('P(b("What is not. ")', 'fails against the simplest persistent attack.")', '''P(b("What is not, or only partly. "), "Dynamic tracking saves messages only at moderate accuracy targets, and "
  "the separate-packet TARC handshake roughly halves that saving. When high accuracy must be guaranteed, static "
  "re-convergence with exact sums was more reliable. TARC as originally specified fails against the simplest "
  "persistent attack, and TARC-R replaces that failure with sticky exclusions.")''')
swap('P(b("Threats to validity. ")', 'and a static baseline of our own design.")', '''P(b("Threats to validity. "), "The model is copper-plate and the profiles are synthetic. Seed counts are 5–20, with "
  "one attack placement per seed. TARC-R was tuned on an IEEE-30 pilot with seed 0; this is mitigated by the "
  "held-out seeds 100–109 and the sensitivity analysis, both on IEEE-30 only. The static baseline is a single "
  "comparator of our own design, and the round budget K = 300 is not adapted to the accuracy target.")''')
rep('      ["Synchronous rounds, symmetric links', '      ["Communication savings depend on the accuracy target and on counting handshakes as separate packets."],\n      ["Synchronous rounds, symmetric links')
rep("Dynamic tracking did not save messages.", "Dynamic tracking saved messages at moderate accuracy, but not at a fixed budget or at high accuracy.")
swap('P("On 28 September 2026 we ran targeted queries', 'arXiv preprint.")', '''P("On 28 September 2026 we ran targeted queries through a general web search engine indexing IEEE Xplore, "
  "ScienceDirect, SpringerLink, MDPI and arXiv. The queries were: “trust-based resilient distributed economic "
  "dispatch false data injection consensus”, “distributed CVaR energy management consensus dynamic average "
  "tracking peer-to-peer”, and title look-ups. The first result pages were screened, and [24]–[27] were added. "
  "This is a targeted search, not a systematic review. The bibliographic entries of [24]–[30] were taken from the "
  "records returned by these searches or from standard citations of well-known works. The search logs are not "
  "archived with this manuscript, and every entry still has to be verified against the publisher page "
  "(capitalization, page ranges, DOIs) before submission. [21] remains an arXiv preprint.")''')

open("/home/claude/paper/build_paper_v17.py", "w").write(src)
print("patched OK")

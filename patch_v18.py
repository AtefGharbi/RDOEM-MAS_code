"""Apply third-review revisions: build_paper_v17.py -> build_paper_v18.py"""
src = open("/home/claude/paper/build_paper_v17.py").read()


def rep(a, b, count=1):
    global src
    assert a in src, "MISSING: " + a[:90]
    src = src.replace(a, b, count)


def swap(start, end, new):
    global src
    assert start in src, "MISSING START: " + start[:90]
    i = src.index(start)
    j = src.index(end, i)
    src = src[:i] + new + src[j + len(end):]


def after(marker, new):
    global src
    assert marker in src, "MISSING AFTER: " + marker[:90]
    i = src.index(marker) + len(marker)
    src = src[:i] + "\n" + new + src[i:]


# ---------------- numbers
after('H1n, H1r = E9[("ATT-1", NOT)]["during"], E9[("ATT-1", FULL)]["during"]', '''from rdoem.systems import build_system as _bs
EDGES = {c: [len(_bs(c, seed=s).edges) for s in rr] for c, rr in
         [("ieee30", range(20)), ("ieee57", range(10)), ("ieee118", range(5))]}
_d1 = allE1[allE1.t > 0]
NEG_S, NEG_C = (_d1.gap_S < 0).mean(), (_d1.gap_C < 0).mean()
MIN_S, MIN_C = _d1.gap_S.min(), _d1.gap_C.min()
def _vn(s): return s.replace("rho_min", "ρ_min").replace("rho_mem", "ρ_mem")
''')
rep("Revised manuscript (v17)", "Revised manuscript (v18)")
rep("alt=cap[:120]))", "alt=cap))")

# ---------------- abstract (comments 5, 10, 11)
swap('P("This paper presents RDOEM-MAS, a trust-aware', 'did not detect attacks confined to the mismatch payload.")', '''P("This paper presents RDOEM-MAS, a trust-aware distributed energy-management architecture that combines "
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
  "agents excluded after the attack and did not detect attacks confined to the mismatch payload.")''')

# ---------------- introduction (comments 5, 18, 26)
swap('P("In brief, the architecture combines', 'blindness to mismatch-only attacks.")', '''P("In brief, the architecture combines dynamic sum tracking, CVaR tail-weight averaging and trust-reweighted "
  "consensus. The theory is conditional: under common symmetric doubly stochastic mixing and uncorrupted exchanged "
  "tracker states we establish a sum-tracking invariant and a disagreement bound, and under separable recourse or "
  "a KKT-consistent marginal allocation, fixed points satisfy the centralized CVaR KKT conditions. For "
  "network-coupled recourse the method is evaluated only as an approximate stationarity mechanism. The "
  "experiments quantify benefits and failure modes alike, including communication overhead, persistent trust "
  "exclusions and blindness to mismatch-only attacks.")''')
rep("Algorithm (new combination with two new design elements). ",
    "Algorithm (new combination with two design elements introduced in this work). ")
rep("The new elements are (i)", "The design elements introduced in this work are (i)")
rep("An exact sum-tracking invariant, a tracking-error bound", "A sum-tracking invariant that is exact for truthful "
    "exchanges, a tracking-error bound with explicit constants")
rep("open code reproduces every number (Appendix C)", "accompanying code intended to reproduce every reported "
    "number (Appendix C)")
rep('"New design element (empirically motivated)"', '"Design element introduced here (empirically motivated)"')
rep('"New design element"', '"Design element introduced here"')
rep("the two new design elements are each justified", "the two design elements introduced here are each justified")

# ---------------- III-A: losses (21), allocation (20), lambda_ref (25), battery (8)
swap('P(b("Losses and local inputs. ")', 'stationarity condition.")', '''P(b("Losses and local inputs. "), "P_loss = 0.02·Σ_j P̂_D,j is a fixed forecast parameter, not a decision-dependent "
  "quantity, and it carries no cost term. It enters the model in exactly one place, the day-ahead balance "
  "ΔP = Σ_i s_i − P_loss. The recourse balances contain the committed imbalance ΔP (Section IV-C), not P_loss "
  "again, so losses are not double-counted. The partition P_loss = Σ_i ℓ_i, with ℓ_j = 0.02·P̂_D,j for load agents "
  "and ℓ_i = 0 otherwise, is bookkeeping only: it makes the tracker inputs u_i = s_i − ℓ_i sum to ΔP. Losses enter "
  "no local cost and no stationarity condition.")
P(b("Agent allocation. "), "One generator agent is created for every online generator of the case, and one load "
  "agent for every bus with positive demand. round(n_bus/8) renewable agents (alternately solar and wind) and "
  "round(n_bus/15) battery agents are placed at seeded random buses, so several agents may share a bus. IEEE-30 "
  f"therefore has N = {syst['ieee30']['nG']} + {syst['ieee30']['nR']} + {syst['ieee30']['nL']} + "
  f"{syst['ieee30']['nB']} = {syst['ieee30']['N']} agents, IEEE-57 has {syst['ieee57']['N']} and IEEE-118 has "
  f"{syst['ieee118']['N']} (Table IV). The counts are identical across seeds; the renewable and battery buses and "
  "the random overlay links vary with the seed.")
P(b("Reference price. "), "λ_ref is a normalization constant: the risk-neutral marginal generation cost at which the "
  "case’s generators supply 70% of peak demand, found by bisection on their quadratic costs. It is "
  f"{syst['ieee30']['lam']:.2f} $/MWh for IEEE-30, whose MATPOWER linear cost coefficients are 1–3.25 $/MWh, and "
  f"{syst['ieee57']['lam']:.1f} and {syst['ieee118']['lam']:.1f} $/MWh for IEEE-57 and IEEE-118, whose coefficients "
  "are 20–40 $/MWh. All price-like parameters are scaled by λ_ref.")''')
swap('P("Each battery b has energy capacity', 'the previous version is not used.")', '''P("Each battery b has energy capacity E_b = 4·P_b^max × 1 h (MWh) and stored energy e_b (its state of charge, in "
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
  "here. The lookahead-horizon QP of the previous version is not used.")''')

# ---------------- IV-B notation (13)
swap('EQ("max  W₀(x)', ', 1)', '''EQ("max_{z, ζ, s}  W₀(z) − β[ζ + (1−α)⁻¹ Σ_m π_m s_m]   s.t.  ΔP(z) = 0,  s_m ≥ Q_m(z) − ζ,  s_m ≥ 0,  z ∈ Z", 1)''')
swap('P("Here W₀ is utility minus generation cost plus battery value', 'is the recourse cost of scenario m.")', '''P("Here z = (z_1, …, z_N) stacks the agents’ physical decisions and Z is the product of their local boxes; the "
  "symbol x_i is reserved for the mismatch tracker. ΔP(z) = Σ_i s_i(z_i) − P_loss is the day-ahead mismatch "
  "(Section III-A), W₀ is utility minus generation cost plus battery value, and Q_m(z) is the recourse cost of "
  "scenario m. The constraints s_m ≥ Q_m(z) − ζ, s_m ≥ 0 are the Rockafellar–Uryasev representation of CVaR_α "
  "[12], with scenario probabilities π_m.")''')
rep("Hence Q_m = Σ_i q_i,m(x_i)", "Hence Q_m = Σ_i q_i,m(z_i)")

# ---------------- convexity (16, 17)
swap('P(b("Convexity check. ")', 'all except R1.")', '''P(b("Convexity check. "), "Under a_i > 0, a_R > 0, ψ_j > 0 and κ_b > 0, W₀ is strictly concave, and every local "
  "minimization problem of Section V-A (a strictly convex cost plus a convex piecewise-linear risk term, over a box) "
  "is strictly convex. If any of these coefficients were zero, strict convexity of that agent’s problem would fail. "
  "In regime S, each q_i,m is convex piecewise linear in z_i, because the penalty slopes exceed the regulation "
  "slopes (c^shed > c^up, c^spill > c^dn).")
P("In regime C, Q_m(z) is the optimal value of a recourse LP min{cᵀr : Ar = b_m(z), 0 ≤ r ≤ h(z)}. Its costs c "
  "are fixed, and its right-hand side is affine in z: the requirement b_m(z), and the capacities h(z), which are "
  "headroom, footroom and renewable availability relative to the schedule. The LP is always feasible (shedding and "
  "spill are unbounded slacks) and bounded below by 0. By LP duality, "
  "Q_m(z) = max{b_m(z)ᵀy − h(z)ᵀμ : Aᵀy − μ ≤ c, μ ≥ 0}. The dual feasible set does not depend on z, and the "
  "maximum is attained at one of its finitely many vertices. Q_m is therefore a pointwise maximum of finitely many "
  "functions affine in z, and hence convex and piecewise linear in z.")
P("CVaR is convex and nondecreasing in (Q_1, …, Q_M), so β·CVaR(Q(z)) is convex, and problem (1) is convex in both "
  "regimes. What fails in regime C is therefore not convexity but R1: the local surrogate sensitivities ∂q_i,m "
  "differ from the centralized partial subgradients ∂_{z_i}Q_m. Regime S satisfies all assumptions of Propositions "
  "3–4; regime C satisfies all except R1.")''')

# ---------------- IV-D CVaR notation (2)
swap('P("For generator i, interior stationarity reads', 'g_i is not restricted.")', '''P("The CVaR quantities are distinguished as follows. π_m is the probability of scenario m (π_m = 1/M = 1/30 in "
  "all experiments). θ_m ∈ [0, 1] is the tail indicator: θ_m = 1 if Q_m > ζ, θ_m = 0 if Q_m < ζ, and, for scenarios "
  "tied with ζ, any values in [0, 1] such that Σ_m π_mθ_m = 1 − α. Every such θ gives a CVaR subgradient weight "
  "vector ω_m = π_mθ_m/(1 − α), with ω_m ≥ 0 and Σ_m ω_m = 1. ω̄_i,m is agent i’s running average of the weights "
  "it computes from its own tracked costs (Section V-D). For generator i, interior stationarity reads "
  "C_i′(P_i) + β g_i − λ = 0 with g_i = Σ_m ω_m ∂q_i,m/∂P_i; the sign of g_i is not restricted.")''')

# ---------------- IV-E r_KKT (6, 14, 15, 23)
swap('P("Let F(x) = −W₀(x)', 'together with the welfare gap.")', '''P("Let F(z) = −W₀(z) + β CVaR_α(Q(z)) with the true recourse model, a_i = ∂ΔP/∂z_i ∈ {±1}, and Z_i the "
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
  "from such a kink is below 0.01%. r_KKT must therefore be read together with the welfare gap.")''')

# ---------------- V-A surrogate (16); V-B weights (6)
after('The tracker input is u_i = s_i − ℓ_i.")', '''P(b("Surrogate contributions in regime C. "), "In both regimes every agent computes and tracks the separable "
  "fixed-policy costs q_i,m of Section IV-C, and uses their derivatives as its risk sensitivities. In regime S "
  "these are exact: Σ_i q_i,m = Q_m and ∂q_i,m = ∂_{z_i}Q_m. In regime C they are a surrogate: the agents do not use "
  "marginal contributions of the coupled merit-order recourse, and the tracked sums Σ_i q_i,m differ from the true "
  "Q_m. The coupled model is used only in the centralized benchmark and to evaluate committed schedules.")''')
swap('P("For a retained edge {i,j}', '(Lemma 2 of the previous version).")', '''P("Let R_k be the retained edge set of round k, common to both endpoints of every edge (Section VI, conditions "
  "(i)–(iv)), and let d_i be the degree of agent i in R_k; both endpoints of an edge therefore use the same d_i and "
  "d_j. For {i,j} ∈ R_k set w_ij = w_ji = min{1/(d_i+1), 1/(d_j+1)}·ρ_ij^eff. Here "
  "ρ^eff = ρ_edge^m_sh·min(ρ_ij, ρ_ji) ∈ (0, 1] is the mutual-minimum effective trust, identical at both endpoints. "
  "Set w_ij = 0 otherwise, and w_ii = 1 − Σ_j w_ij.")
P(b("Lemma 2 (weights). "), "W_k is symmetric and doubly stochastic, and w_ii ≥ 1/(d_i+1). ", i("Proof. "),
  "Symmetry holds because both factors of w_ij are symmetric in (i, j). Rows sum to one by the choice of w_ii, and "
  "symmetry then gives unit column sums. Each off-diagonal weight satisfies "
  "w_ij ≤ min{1/(d_i+1), 1/(d_j+1)} ≤ 1/(d_i+1), because ρ^eff ≤ 1. Agent i has d_i retained neighbours, so "
  "Σ_j w_ij ≤ d_i/(d_i+1) and w_ii ≥ 1 − d_i/(d_i+1) = 1/(d_i+1) > 0. All entries are nonnegative. ∎")''')

# ---------------- V-D indices and step size (1, 7)
swap('EQ("λ^{k+1} = Π_[0, 5λ_ref](W_k λ^k − η_k x^k)', 'The loop was unstable at c_η = 4 without decay.")', '''EQ("λ^{k+1} = Π_[0, 5λ_ref](W_k λ^k − η_k x^k),    x^{k+1} = W_k x^k + N(u^{k+1} − u^k),    x^0 = N u^0", 3)
EQ("Q̂^{k+1}_{·,m} = W_k Q̂^k_{·,m} + N(q^{k+1}_{·,m} − q^k_{·,m}),   ζ_i^{k+1} = VaR_α(Q̂^{k+1}_{i,·}),   ω̄^{k+1} = (1−ρ_k)ω̄^k + ρ_k ω(Q̂^k, ζ^k)", 4)
P(b("Time indices. "), "u^k and q^k are the responses computed from λ^k and ω̄^k; u^{k+1} and q^{k+1} are computed "
  "from the new price λ^{k+1} and the new weights ω̄^{k+1}. W_k is built after the round-k trust handshake and "
  "before any mixing, and the same W_k mixes λ, x and Q̂ in round k. Mixing uses the values reported by neighbours "
  "and the agent’s own true value. ω(Q̂, ζ) applies the tail rule of Section IV-D to each agent’s own tracked costs, "
  "with fractional values at ties. Averaging uses ρ_k = 1/(1 + k/k_ω), with k_ω = 1. The quantile ζ_i is the local "
  "weighted α-quantile of the tracked scenario costs, which is exact once the trackers agree. The "
  "consensus–subgradient rule of the previous version is retained as an alternative; the two perform equivalently "
  "(Table VIII-B).")
P(b("Step size (empirical tuning rule). "), "Let ℓ_i denote the price-response slope of agent i’s risk-neutral "
  "unconstrained best response, in MW per $/MWh: ℓ_i = 1/a_i (generators), 1/a_R (renewables), 1/ψ_j (loads) and "
  "1/(2κ_b) (batteries). Box limits and recourse kinks only flatten the response, so the actual slope is set-valued "
  "in [0, ℓ_i]. A price perturbation at agent i changes u_i by at most ℓ_i per unit and x_i by at most Nℓ_i, which "
  "motivates keeping ηNℓ_i small relative to the mixing rate. We use η₀ = c_η(1 − σ₂)/(N max_i ℓ_i), with c_η = 2, "
  "and η_k = η₀/(1 + k/100)^0.6. Here σ₂ is the second-largest eigenvalue modulus of the nominal (all links, full "
  "trust) weight matrix, an offline constant. This is an empirical tuning rule, motivated by the local response "
  "slopes and the nominal spectral gap. It is not a convergence guarantee for the time-varying trust-weighted "
  "iteration, whose W_k differ from the nominal matrix. In pilot runs the loop was stable at c_η = 2 and unstable "
  "at c_η = 4 without decay.")''')
rep("is an evaluation metric only, because |ΔP| needs a central",
    "is an evaluation metric only (the “full test” of Table VI), because |ΔP| needs a central")

# ---------------- Algorithm 1 (1)
swap('B.append(dict(type="algo", title="Algorithm 1: RDOEM-MAS (one epoch t)", lines=[', ']))', '''B.append(dict(type="algo", title="Algorithm 1: RDOEM-MAS (one epoch t)", lines=[
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
]))''')

# ---------------- VI: Prop. 2 (3), Props. 3-4 (4), Prop. 5 symbol (13), table III (5)
swap('P(b("Proposition 2 (dynamic sum tracking). ")', 'Proposition 1 to the disagreement component [3], [28]. ∎")', '''P(b("Proposition 2 (dynamic sum tracking). "), "Let x^{k+1} = W_kx^k + N(u^{k+1} − u^k), where every agent "
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
  "x_i^k → Σ_j u_j^∞. This is the standard dynamic-consensus argument [3], [29], stated for the N-scaled sum. ∎")''')
swap('P(b("Proposition 3 (fixed-point characterization under exact tracking). ")', 'empirically (Section VIII).")', '''P(b("Proposition 3 (fixed-point characterization under exact tracking). "), "The proposition applies to any "
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
P(i("Proof. "), "The price step returns W_kλ* − η_k·0 = λ*. By (A2), ω(Q̂, ζ*) = ω*, so the averaged weights stay "
  "at ω*. By (A1), the responses at (λ*, ω*) are unchanged, so u and q do not change and their increments vanish. "
  "Consensual vectors are fixed by every W_k, so x = 0 and Q̂ are preserved, and the recomputed quantile is ζ*. "
  "(A3) makes the state consistent with Proposition 2(a): mean(x) = Σ_i u_i = ΔP = 0, and "
  "mean(Q̂_{·,m}) = Q*_m = Σ_i q*_i,m. ∎")
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
P(i("Proof. "), "Local optimality of each agent gives "
  "0 ∈ ∇f_i(z̄_i) + βΣ_m ω̄_m ∂q_i,m(z̄_i) − λ̄a_i + N_Zi(z̄_i). Under R1, the product over agents of the sets "
  "∂q_i,m(z̄_i) is ∂Q_m(z̄), and ω̄ is a valid CVaR weight vector for Q(z̄), so "
  "Σ_m ω̄_m ∂Q_m(z̄) ⊆ ∂CVaR_α(Q(z̄)). Stacking the agents’ conditions gives 0 ∈ ∂F(z̄) − λ̄a + N_Z(z̄). With "
  "ΔP(z̄) = 0 and the convexity of Section IV-C, this is the KKT system of (1). ∎")
P(b("Remark (convergence). "), "Neither proposition asserts convergence. Convergence of the coupled "
  "price–decision–tracker–trust iteration from arbitrary initial states is not established and is assessed only "
  "empirically (Section VIII).")''')
rep("Let z^{k+1} = W_kz^k + d_k with W_k satisfying G1 and e_k = J_⊥z^k.",
    "Let y^{k+1} = W_ky^k + d_k with W_k satisfying G1 and e_k = J_⊥y^k, where y is a generic consensus state such as "
    "the price vector.")
rep('["Sum-tracking invariant (Prop. 2a)", "Exact",', '["Sum-tracking invariant (Prop. 2a)", "Exact under stated conditions",')
rep('"Doubly stochastic W, x⁰ = Nu⁰, uncorrupted reports; "', '"Common symmetric doubly stochastic W, x⁰ = Nu⁰, "\n        "uncorrupted exchanged tracker states; "')

# ---------------- VII: Table IV (9, 20), signed gap (24), statistical units (19)
swap('TABLE("Table IV. Test systems', 'widths=[1.3, 2, 1.3, 1, 1.6, 1.4])', '''TABLE("Table IV. Test systems (cost data from MATPOWER cases [30]; profiles synthetic)",
      ["System", "N (G/R/L/B)", "|E|: mean over evaluation seeds (range)", "1 − σ₂ (seed 0)", "Peak demand (MW)",
       "λ_ref ($/MWh)"],
      [[c.upper().replace("IEEE", "IEEE-"), f"{v['N']} ({v['nG']}/{v['nR']}/{v['nL']}/{v['nB']})",
        f"{np.mean(EDGES[c]):.1f} ({min(EDGES[c])}–{max(EDGES[c])})", f"{v['gap']:.3f}", f"{v['peak']:.0f}",
        f"{v['lam']:.2f}"] for c, v in syst.items()],
      widths=[1.3, 2, 2.2, 1.2, 1.6, 1.4],
      note="|E| varies with the seeded overlay links. Message counts use each seed’s own |E|; for example, IEEE-118 "
           "has mean |E| = 626.6 over seeds 0–4, so 4·626.6·300 = 751,920 ≈ 752k messages per epoch with TARC.")''')
after('and the attacker-edge removal rate.")', '''P(b("Sign of the welfare gap. "), "The gap g is reported signed. The benchmark enforces exact day-ahead balance "
  "ΔP = 0, whereas a committed distributed schedule may leave a small ΔP that the recourse model absorbs. Because "
  "regime-C recourse has free renewable flexibility, such a schedule can occasionally be cheaper than the balanced "
  "optimum, and solver tolerances add noise of order 10⁻⁶. The benchmark therefore does not dominate every "
  f"committed schedule. Of all nominal epoch values behind Table VI, {100 * NEG_S:.1f}% of regime-S gaps and "
  f"{100 * NEG_C:.1f}% of regime-C gaps were negative (minima {100 * MIN_S:.2f}% and {100 * MIN_C:.2f}%). The static "
  "baseline, which stops at 1% mismatch, accounts for most of them. Negative values are not clipped.")''')
after('IEEE-30 only.")', '''P(b("Statistical units per table. "), "Each table uses one of the following units.")
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
       "VIII-F use one value per seed and loss level (25 values)."]])''')

# ---------------- VIII: Table VI (12), VI-B note (10), fixed-budget wording (11), Table VIII-D names (23),
#                  phase units (19), packet-loss scope (22)
rep('"Tol. reached (%)",', '"Full test reached (%)",')
rep('r_KKT/λ_ref ≤ 10⁻⁶ in both regimes.")', 'r_KKT/λ_ref ≤ 10⁻⁶ in both regimes. Msgs/epoch: total at the "\n           "fixed 300-round budget (4|E|K with TARC, 2|E|K without; per-seed |E|, Table IV). Full test: the "\n           "three-part tolerance test of Section V-E.")')
rep('note="Medians are over the epochs that reached the target; read them with the reach shares.")',
    'note="Medians are over the epochs that reached each target, so methods are not compared on identical sets of "\n           "epochs; read them with the reach shares. Targets are single criteria, unlike the full test of Table "\n           "VI. Unit: epoch (60 per method).")')
rep('P(f"At the fixed budget (Fig. 5, Table VI), the static re-convergence baseline used {RATIO}× fewer messages than "',
    'P(f"Under the fixed 300-round accounting convention (Fig. 5, Table VI), the static re-convergence baseline used "\n  f"{RATIO}× fewer messages than "')
rep('[[v["variant"], pc(v["during"], 1)', '[[_vn(v["variant"]), pc(v["during"], 1)')
rep('(medians over 5 seeds per "\n  "cell).', '(medians over 15 seed–epochs per "\n  "cell: 5 seeds × epochs 8–10).')
after('Re-anchoring is therefore free nominally and decisive after attacks.")', '''P("The packet-loss result is empirical, for the tested graphs and loss rates up to 20% (40% in Fig. 9). It relies on "
  "the symmetric authenticated handshake of Section VI and is not a general property of packet loss.")''')

# ---------------- appendices (13, 18)
rep('["s_i, u_i", "net injection', '["z, z_i", "centralized decision vector; decisions of agent i (P_G, P_R, P_D or "\n        "(p_ch, p_dis))", "MW"],\n       ["s_i, u_i", "net injection')
swap('P("All code, raw per-run results', 'are used for run s.")', '''P("The accompanying package (rdoem/) contains the code, the raw per-run results (one CSV per run, keyed by a "
  "configuration hash) and the figure scripts, and is intended to reproduce every reported number. It includes "
  "unit tests, which reviewers can run, for the merit-order recourse against an LP solver, the centralized KKT "
  "residual, the doubly stochastic weights and the sum invariant under packet loss. The package is not yet "
  "deposited in a public archive; a DOI-bearing archive should be created before submission. Seeds are the "
  "integers 0–19 (evaluation) and 100–109 (held-out); system seed s and day seed s are used for run s.")''')

open("/home/claude/paper/build_paper_v18.py", "w").write(src)
print("patched OK")

"""Apply fourth-review revisions: build_paper_v18.py -> build_paper_v19.py"""
src = open("/home/claude/paper/build_paper_v18.py").read()


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


rep("Revised manuscript (v18)", "Revised manuscript (v19)")

# ---- (10) losses: physical model vs bookkeeping
swap('P(b("Losses and local inputs. ")', 'no local cost and no stationarity condition.")', '''P(b("Losses and local inputs. "), "P_loss = 0.02·Σ_j P̂_D,j is a fixed forecast parameter, not a decision-dependent "
  "quantity, and it carries no cost term. It enters the physical optimization model only through the day-ahead "
  "balance ΔP = Σ_i s_i − P_loss. The recourse balances contain the committed imbalance ΔP (equation (1a)), not "
  "P_loss separately, so losses are counted once. Its appearance in the partition P_loss = Σ_i ℓ_i, with "
  "ℓ_j = 0.02·P̂_D,j for load agents and ℓ_i = 0 otherwise, is bookkeeping for distributed tracking: it makes the "
  "tracker inputs u_i = s_i − ℓ_i sum to ΔP. Losses enter no local cost and no stationarity condition.")''')

# ---- (9, 15) reference price procedure and scope of the normalization
swap('P(b("Reference price. ")', 'All price-like parameters are scaled by λ_ref.")', '''P(b("Reference price. "), "λ_ref is a normalization constant, computed as follows. At a trial price λ, each "
  "generator’s bounded risk-neutral response is P_i(λ) = Π_[P_i^min, P_i^max][(λ − b_i)/a_i]; renewables, loads, "
  "batteries and risk are ignored. Because every a_i > 0, the aggregate Σ_iP_i(λ) is continuous and nondecreasing, "
  "and it is flat only where all generators are saturated. λ_ref is the midpoint of the final bracket of a "
  "100-step bisection on [0, 10⁴] $/MWh for the price at which the aggregate equals 0.7·P_peak. Since "
  "0.7·P_peak = 0.56·Σ_iP_i^max lies strictly inside the aggregate’s range, such a price exists. λ_ref is "
  f"{syst['ieee30']['lam']:.2f} $/MWh for IEEE-30, whose MATPOWER linear cost coefficients are 1–3.25 $/MWh, and "
  f"{syst['ieee57']['lam']:.1f} and {syst['ieee118']['lam']:.1f} $/MWh for IEEE-57 and IEEE-118, whose coefficients "
  "are 20–40 $/MWh. The penalty parameters and price bounds that are defined relative to λ_ref (Section IV-C, "
  "Table II) are scaled with this normalization. Generator cost coefficients are the case data and are not "
  "rescaled.")''')

# ---- (8) explicit recourse balance; terminology
after('the closed form matches an LP solver in unit tests.")', '''P("Explicitly, scenario m has aggregate load-forecast error ε_m (MW, positive meaning more demand) and renewable "
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
  "regime’s own Q_m, which is used to score committed schedules and in the centralized benchmark.")''')
src = src.replace("true recourse model", "evaluation recourse model")
src = src.replace("coupled model’s marginal costs", "regime-C model’s marginal costs")
src = src.replace("the coupled model", "the regime-C (network-coupled) model")

# ---- (2) convexity of the regime-C value function, proved for the implemented LP
swap('P("In regime C, Q_m(z) is the optimal value of a recourse LP', 'hence convex and piecewise linear in z.")', '''P("In regime C, Q_m(z) is the optimal value of the recourse LP defined by (1a). The LP is feasible for every z "
  "(shedding and spill are unbounded slacks) and bounded below by 0, so strong duality holds. Dualizing the "
  "balance (1a) with a scalar multiplier y and eliminating the capacity multipliers gives")
EQ("Q_m(z) = max_{−c^spill ≤ y ≤ c^shed} [ y·(b_m(z) + Σ_kP_R,k) − Σ_i (P_i^max − P_G,i)(y − c^up_i)₊ − Σ_i (P_G,i − P_i^min)(−y − c^dn_i)₊ − Σ_k A_k,m y₊ ]", "1b")
P("For every fixed y, the bracket is affine in z, because b_m(z), P_R,k, P_G,i and the headroom and footroom "
  "coefficients are affine in z; hence Q_m is a supremum of affine functions of z and therefore convex. In the "
  "implemented model the bracket is also concave and piecewise linear in y, with breakpoints only at the finitely "
  "many values {c^up_i, −c^dn_i, 0} and the interval endpoints {−c^spill, c^shed}. Its maximum over the interval "
  "is therefore attained at one of these points. So Q_m(z) is the maximum of finitely many affine functions of z, "
  "and it is piecewise affine on the whole domain.")''')

# ---- (4) CVaR tie rule with feasibility
swap('P("The CVaR quantities are distinguished as follows.', 'the sign of g_i is not restricted.")', '''P("The CVaR quantities are distinguished as follows. π_m is the probability of scenario m (π_m = 1/M = 1/30 in all "
  "experiments). ζ is chosen as an α-quantile (VaR_α) of {Q_m}, so that Σ_{m: Q_m>ζ} π_m ≤ 1 − α ≤ "
  "Σ_{m: Q_m≥ζ} π_m. The tail indicator θ_m ∈ [0, 1] is then assigned in three cases: θ_m = 1 when Q_m > ζ; "
  "θ_m = 0 when Q_m < ζ; and, for Q_m = ζ, values θ_m ∈ [0, 1] chosen so that the total weighted tail mass "
  "Σ_m π_mθ_m equals 1 − α. The quantile inequalities guarantee that such an assignment exists. Our implementation "
  "gives all tied scenarios the same fraction. Every such θ yields a CVaR subgradient weight vector "
  "ω_m = π_mθ_m/(1 − α), with ω_m ≥ 0 and Σ_m ω_m = 1. ω̄_i,m is agent i’s running average of the weights it "
  "computes from its own tracked costs (Section V-D). For generator i, interior stationarity reads "
  "C_i′(P_i) + β g_i − λ = 0 with g_i = Σ_m ω_m ∂q_i,m/∂P_i; the sign of g_i is not restricted.")''')

# ---- (6) sign convention of local problems
swap('P("Given its price λ_i and tail weights ω̄_i,m', 'The tracker input is u_i = s_i − ℓ_i.")', '''P("Given its price λ_i and tail weights ω̄_i,m, each agent solves exactly its local minimization problem, which "
  "is the negative of its local welfare maximization (cost minus revenue, plus weighted risk). For a generator "
  "this is min ½a_iP² + b_iP − λ_iP + β Σ_m ω̄_i,m q_i,m(P) over [P^min, P^max]. Under the default "
  "local-quantile rule every weight vector ω(·) is nonnegative and sums to one, and so is its running average ω̄_i; "
  "with β ≥ 0 and each q_i,m convex, the risk term is therefore convex. The problem is solved by 32 bisection "
  "steps on the nondecreasing right derivative. Renewables are handled the same way; loads (the negative of "
  "concave utility plus payment) and batteries are solved in closed form. Decisions are recomputed in every round "
  "from the current price. The tracker input is u_i = s_i − ℓ_i.")''')

# ---- (5) stale/new quantities beside eq. (4); regime-C quantile wording
swap('P(b("Time indices. ")', '(Table VIII-B).")', '''P(b("Time indices. "), "In (4), ω̄^{k+1} is formed from the round-k tracker values (Q̂^k, ζ^k), not from "
  "Q̂^{k+1}: it is computed before the responses. u^{k+1} and q^{k+1} are then computed from the new price λ^{k+1} "
  "and the new weights ω̄^{k+1}, while u^k and q^k are the responses computed from λ^k and ω̄^k. W_k is built "
  "after the round-k trust handshake and before any mixing, and the same W_k mixes λ, x and Q̂ in round k. Mixing "
  "uses the values reported by neighbours and the agent’s own true value. ω(Q̂, ζ) applies the tail rule of "
  "Section IV-D to each agent’s own tracked costs. Averaging uses ρ_k = 1/(1 + k/k_ω), with k_ω = 1. The quantile "
  "ζ_i is the local weighted α-quantile of the tracked scenario costs. It is exact once the trackers agree with "
  "the quantities they are designed to track; in regime C these are the surrogate scenario costs Σ_i q_i,m, not "
  "the true Q_m. The consensus–subgradient rule of the previous version is retained as an alternative; the two "
  "perform equivalently (Table VIII-B).")''')

# ---- (7) response slope as an upper bound
swap('P(b("Step size (empirical tuning rule). ")', 'at c_η = 4 without decay.")', '''P(b("Step size (empirical tuning rule). "), "Let ℓ_i be an upper bound, in MW per $/MWh, on the magnitude of the "
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
  "In pilot runs the loop was stable at c_η = 2 and unstable at c_η = 4 without decay.")''')

# ---- (3) Proposition 3 proof: explicit logical order for x = 0
swap('P(i("Proof. "), "The price step returns W_kλ* − η_k·0 = λ*.', 'mean(Q̂_{·,m}) = Q*_m = Σ_i q*_i,m. ∎")', '''P(i("Proof. "), "First, the tracker state is consistent with Proposition 2(a). By the invariant and (A3), "
  "(1/N)1ᵀx = Σ_i u_i = ΔP(z^loc(λ*, ω*)) = 0. Because x is consensual in S*, every x_i equals this mean, so "
  "x_i = 0. Likewise, (1/N)1ᵀQ̂_{·,m} = Σ_i q*_i,m = Q*_m, so the consensual value Q̂_i,m = Q*_m is the one that "
  "the invariant for the scenario-cost trackers requires. Second, one round leaves S* unchanged. The price step "
  "returns W_kλ* − η_k·0 = λ*. By (A2), ω(Q̂, ζ*) = ω*, so the averaged weights stay at ω*. By (A1), the responses "
  "at (λ*, ω*) are unchanged, so u and q do not change and their increments vanish. Consensual vectors are fixed "
  "by every W_k, so x = 0 and Q̂ are preserved, and the recomputed quantile is ζ*. ∎")''')

# ---- (1) Proposition 4 proof: selected subgradients, no product-equality claim
swap('P(i("Proof. "), "Local optimality of each agent gives "', 'this is the KKT system of (1). ∎")', '''P(i("Proof. "), "Local optimality of each agent gives a selection: for each m there is a local subgradient "
  "g_i,m ∈ ∂q_i,m(z̄_i), and a normal-cone element ν_i ∈ N_Zi(z̄_i), such that "
  "0 = ∇f_i(z̄_i) + βΣ_m ω̄_m g_i,m − λ̄a_i + ν_i. Under R1, Q_m(z) = Σ_i q_i,m(z_i) with each term depending only "
  "on z_i, so for each scenario m the stacked vector g_m = (g_1,m, …, g_N,m) belongs to ∂Q_m(z̄). Because ω̄ "
  "satisfies the CVaR tail-weight conditions of Section IV-D at Q(z̄), the combination Σ_m ω̄_m g_m belongs to "
  "∂CVaR_α(Q(z̄)); this holds since Q_m is convex and CVaR_α is convex and nondecreasing in (Q_1, …, Q_M). "
  "Stacking the local conditions therefore yields 0 ∈ ∂F(z̄) − λ̄a + N_Z(z̄), with ν = (ν_1, …, ν_N) ∈ N_Z(z̄). "
  "Together with ΔP(z̄) = 0 and the convexity of Section IV-C, this is the centralized KKT inclusion of (1). For a "
  "KKT-consistent allocation the same argument applies with ∂q_i,m(z_i) ⊆ ∂_{z_i}Q_m(z) in place of R1. ∎")''')

# ---- (13) signed gap wording
swap('P(b("Sign of the welfare gap. ")', 'Negative values are not clipped.")', '''P(b("Sign of the welfare gap. "), "The gap g is reported signed. The benchmark enforces exact day-ahead balance "
  "ΔP = 0. A committed distributed schedule may violate that balance, and the evaluation recourse model then "
  "absorbs the imbalance through b_m(z) in (1a). Because of this, the signed comparison is not guaranteed to be "
  "nonnegative; solver tolerances add noise of order 10⁻⁶. Of all nominal epoch values behind Table VI, "
  f"{100 * NEG_S:.1f}% of regime-S gaps and {100 * NEG_C:.1f}% of regime-C gaps were negative (minima "
  f"{100 * MIN_S:.2f}% and {100 * MIN_C:.2f}%). The static baseline, which stops at 1% mismatch, accounts for most "
  "of them. Negative values are not clipped.")''')

# ---- (11) statistical units in table captions
rep("Table VIII-A. Attack outcomes on IEEE-30 (seeds 0–9): median gap",
    "Table VIII-A. Attack outcomes on IEEE-30 (seeds 0–9). Medians are computed over seed–epoch observations; "
    "hypothesis tests use paired per-seed attack-window means (n = 10). Columns: median gap")
rep('Table VIII-C. Held-out replication on IEEE-30 (seeds 100–109, never used for tuning)"',
    'Table VIII-C. Held-out replication on IEEE-30 (seeds 100–109, never used for tuning). Medians are computed over "\n      "seed–epoch observations; the mean, 95% CI and tests use paired per-seed attack-window means (n = 10)"')
rep('one parameter varied at a time)"', 'one parameter varied at a time; medians over seed–epoch observations)"')

# ---- (12, 14) phase-diagram sample sizes and conditions
rep("The median hides dispersion: across the 25 seed–loss cells with one attacker, per-seed mean gaps ranged",
    "The median hides dispersion. For the 25 one-attacker seed–loss cells (5 seeds × 5 loss levels), each summarized "
    "by that seed’s mean gap over epochs 8–10, the values ranged")
rep("With one attacker, TARC-R kept the median gap",
    "For one attacker and packet-loss rates up to 40%, TARC-R kept the median gap")

# ---- presentation: W-MSR parameter; consistent proposition naming
rep("W-MSR with f_W = 1 applied to price and mismatch, other states with standard weights;",
    "W-MSR with trimming parameter f_W = 1, applied to price and mismatch. Each agent discards up to f_W neighbour "
    "values above its own and f_W below; in the W-MSR theory [5], f_W is the assumed number of malicious "
    "neighbours, but here it is only a trimming parameter, since the actual number of compromised neighbours can "
    "exceed it. Other states use standard weights;")
src = src.replace("Props. ", "Propositions ").replace("Prop. ", "Proposition ")

open("/home/claude/paper/build_paper_v19.py", "w").write(src)
print("patched OK")

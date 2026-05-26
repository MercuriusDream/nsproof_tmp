ChatGPT





# Deep Research Prompt for GPT-5 Pro: Complete Path to Finish NSProof

  You must spend **at least 30 minutes** thinking before producing your final answer. If your interface supports timers, set one. Do not answer quickly. I want a serious
  research-level review and a concrete, complete plan to reach a final proof, not generic suggestions.

  You do **not** have access to my local files, so all required mathematical and numerical context is inlined below. You may refer to filenames as artifact names, but do not
  require reading them. Work from the data below.

  Your answer must be blunt and decisive. If the current profile path is structurally exhausted, say so. If a final proof is still possible, give one or more **complete end-
  to-end proof paths** with exact intermediate lemmas, validators, numerical certificates, rejection criteria, and implementation steps.

  Do not merely say “use interval arithmetic” or “build a spectral solver.” I need a proof engineering blueprint: definitions, spaces, operators, bases, certificate formats,
  validation inequalities, and concrete next computations.

  ---

  ## 1. Goal and Current Status

  I am working on a Navier-Stokes self-similar blow-up proof program for an axisymmetric-with-swirl ansatz.

  The theorem is **not proved**. The strongest currently correct theorem is conditional. A complete proof requires this full stop-condition package:

  
text
  F_gamma(U_*, P_*) = 0,
  2/5 < gamma < 1/2,
  U_*(y) = |y|^(1 - 1/gamma) H(y/|y|) + faster decay,
  rank P_+ < infinity,
  sigma(L on stable complement) subset { Re z <= -c < 0 }.

  The current numerical target is:

  gamma = 0.45 = 9/20,
  B = 1.0.

  Current profile residuals are still O(1), around 0.435 to 0.438, so no Newton-Kantorovich proof center exists yet.

  ———

  ## 2. Axisymmetric Profile Equations

  The axisymmetric-with-swirl variables are:

  u^r = -psi_z / r,
  u^z =  psi_r / r,
  Gamma = r u^theta,
  A = psi_rr - r^(-1) psi_r + psi_zz.

  The current finite-difference residual oracle evaluates the pressure-eliminated profile equations:

  E_psi =
    (1 - gamma) r^2 A
    + gamma r^3 A_r
    + gamma z r^2 A_z
    + r(psi_r A_z - psi_z A_r)
    + 2 psi_z A
    + (Gamma^2)_z
    = 0,

  E_Gamma =
    (1 - 2 gamma) Gamma
    + gamma (r Gamma_r + z Gamma_z)
    + (psi_r Gamma_z - psi_z Gamma_r) / r
    = 0.

  The current compactified tail-factored ansatz is:

  q = (1 + r^2 + z^2)^(-1/2),
  b = z / sqrt(r^2 + z^2),

  psi   = r^2 z q^(1/gamma) F(q,b),
  Gamma = r^2 q^(1/gamma) G(q,b).

  The natural conical tail condition is:

  F(0,b) = 1/2,
  G(0,b) = B.

  The ordinary q^1 tail channel is forbidden unless explicitly identified as a geometric/modulation channel. The current best constrained seeds enforce:

  F_0 = 1/2,
  G_0 = 1,
  F_1 = 0,
  G_1 = 0,

  and include a frozen forced nonlinear correction at:

  q^(1/gamma) = q^(20/9) ≈ q^2.2222222222.

  ———

  ## 3. Current Profile Seed History

  ### Old Low-Residual Seed

  profile-seeds/gamma0p45-vanishing-edge-seed-v49.json

  This had low finite-box residual and exact q=0 trace, but it relies on a forbidden ordinary q^1 tail channel in the unconstrained representation. It is not admissible as a
  proof center.

  ### Best Far-Tail-Only Seed

  profile-seeds/gamma0p45-forced-tail-qm-v64.json

  Properties:

  exact q=0 trace,
  zero q^1 channel,
  forced q^(1/gamma) correction,
  best far-tail asymptotics,
  but standard/interior/local residuals remain O(1).

  ### Best Balanced q1-Free Forced-Tail Seed Before Latest Run

  profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v116-lowb.json

  Properties:

  exact q=0 trace,
  zero q^1 tail channel,
  frozen forced q^(1/gamma) correction,
  sparse high-|b| and low-|b| tail-flat bump corrections.

  Validation for v116:

  standard h=2e-3,1e-3,5e-4 max:
  4.378237351374e-1,
  4.378239756763e-1,
  4.378239372738e-1

  shifted h=1.6e-3,8e-4,4e-4 max:
  4.384746043386e-1,
  4.384766750064e-1,
  4.384759905812e-1

  fine 29x29/45 max:
  4.388424241734e-1

  broad shifted topology max:
  4.370460732359e-1

  old high-|b| holdout max:
  4.354896703956e-1

  far-tail holdout max:
  4.091040786189e-1

  The main residual is a streamfunction-equation lobe, not a finite-difference artifact.

  ———

  ## 4. Latest v117 Profile Branch

  A subagent found that the current v116 obstruction is no longer the earlier high-|b| lobe. It is now a broad streamfunction-dominated low-|b| ridge:

  primary ridge:
  q ≈ 0.396-0.486,
  |b| ≈ 0.27-0.315

  secondary ridge:
  q ≈ 0.576-0.630,
  |b| ≈ 0.225

  A sparse ridge-strip bump dictionary was added and optimized with a max-aware coordinate search.

  Artifacts:

  profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip-base.json
  profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip-partial2.json
  profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip-run.md
  tools/profile_apply_minimax_log.py

  The checkpoint v117-ridge-strip-partial2 is a replay of accepted moves from the still-running coordinate-search log.

  Checkpoint evidence:

  accepted_moves = 69
  last_iteration = 1

  score_max = 4.362712135382e-1
  score_rms = 2.560354001195e-1
  report_max = 4.362712135382e-1

  active   = 4.362182037435e-1
  extreme  = 4.334310921963e-1
  farther  = 3.834145387875e-1
  interior = 4.334822635142e-1
  local    = 4.360110317537e-1
  wide     = 4.362712135382e-1

  Independent validation for v117-ridge-strip-partial2:

  standard h=2e-3,1e-3,5e-4 max:
  4.349766242187e-1,
  4.349767753259e-1,
  4.349745416268e-1

  fine 29x29/45 max:
  4.377081305376e-1

  41x41 broad topology max:
  4.362182718262e-1

  shifted h=1.6e-3,8e-4,4e-4 max:
  4.378038954727e-1,
  4.378036810648e-1,
  4.378083969895e-1

  high-|b| holdout max:
  4.314497732029e-1

  far-tail holdout max:
  3.776333394887e-1

  Tail-series trace for partial2:

  order 0:
  F_0 max = 5.000000000000e-1,
  G_0 max = 1.000000000000e+0

  order 1:
  F_1 max = 0,
  G_1 max = 0

  fractional q^(1/gamma) forced correction remains present.

  The live strip run has improved further on its own scored grid:

  current live score_max ≈ 4.357859681605e-1

  but that latest point is not yet independently validated.

  Interpretation:

  - v117 is a real incremental improvement over v116.
  - It is still nowhere near a proof-grade residual.
  - The flat/sparse bump family may be plateauing structurally.

  ———

  ## 5. Indicial System and Current Evidence

  The conical indicial problem is used to classify admissible tail/escape modes.

  Let:

  alpha = 1/2 - gamma.

  The current indicial ODE in variable zeta is implemented for state:

  (phi, phi', chi, h).

  The floating RHS is:

  phi'' =
    [ h + (3 - 2 delta) zeta phi'
        - (3 - delta)(1 - delta) phi ]
    / (1 + zeta^2),

  chi' =
    [ 2 B phi' - alpha delta chi ]
    / [ (3/2) zeta ],

  h' =
    - [ (3/2 + alpha delta) h + 2 B chi' ]
    / [ (3/2) zeta ].

  The analytic Frobenius recurrence near zeta=0 uses:

  phi = sum p_n zeta^n,
  chi = sum q_n zeta^n,
  h   = sum r_n zeta^n.

  The recurrence is:

  c_n = (3/2)n + alpha delta,
  d_n = (3/2)n + 3/2 + alpha delta,

  a_n =
    n(n - 1)
    - (3 - 2 delta)n
    + (3 - delta)(1 - delta).

  For n >= 0:

  if n >= 1:
  p_n = c_{n-1} q_{n-1} / (2 B n)

  q_{n+1} =
    - a_n p_n /
    [ (n+1)( c_{n+1}/(2B) + 2B/d_n ) ]

  r_n =
    - 2 B (n+1) q_{n+1} / d_n.

  For generic parameters, the local analytic space is two-dimensional, with free data:

  (phi(0), chi(0)).

  A two-branch matching/Pluecker diagnostic builds the 3x2 forbidden far-field modal coefficient matrix. The admissible branch is tested by requiring the forbidden 3x2
  matrix to have rank < 2, equivalently all three 2x2 Pluecker minors vanish.

  Current floating Pluecker results at:

  gamma=0.45,
  B=1.0.

  Exact geometric branch:

  delta = 1 + 0i

  At L=25 and L=40:
  sigma_ratio = 0,
  normalized_minor_norm = 0,
  coefficient_forbidden_fraction = 0,
  contribution_forbidden_fraction = 0.

  Old complex basin:

  delta = 0.13251953125 + 1.787841796875 i

  L=25:
  sigma_ratio = 1.292647217342e-1
  normalized_minor_norm = 1.271402878408e-1
  coefficient_forbid = 5.277372775458e-1
  contribution_forbid = 9.998883630453e-1

  L=40:
  sigma_ratio = 1.725890931092e-1
  normalized_minor_norm = 1.675968855084e-1
  coefficient_forbid = 3.795675033836e-1
  contribution_forbid = 9.999766971815e-1

  Broad scan:

  Re delta in [0.02, 1],
  Im delta in [0, 3],
  L = 25,40.

  Only sampled zero is delta = 1 + 0i.
  All other low-minor candidates have endpoint forbidden contribution essentially 1.

  Near-delta1 scan:

  Re delta in [0.82, 1.08],
  Im delta in [0, 0.3],
  L = 25,40.

  Only sampled zero is delta = 1 + 0i.
  Nearby real candidates like delta = 0.99 have small normalized minors
  but forbidden contribution around 0.999.

  The exact delta=1 branch is geometric:

  delta = 1,
  phi = 1,
  chi = 0,
  h = 0,

  Psi = r^2,
  G = 0,
  a = 0.

  It is the axial-center/Galilean mode, i.e. derivative of the conical core under axial translation. It should be removed by parity or center fixing. It is not a non-
  geometric tail root.

  Critical caveat:

  - All indicial evidence is floating.
  - It does not exclude off-grid roots or roots outside scanned boxes.
  - It does not prove a true Evans determinant or far-field dichotomy.
  - Need interval/ball Pluecker or Evans validation.

  ———

  ## 6. Spectral State

  The spectral part of the proof is missing.

  The true linearized operator around a validated profile should be:

  L v =
  - P [
      (1 - gamma) v
      + gamma (y · grad) v
      + (U_* · grad) v
      + (v · grad) U_*
    ],

  where P is the Leray projection or the appropriate pressure-eliminated projected operator in the chosen perturbation class.

  Required geometric spectral modes:

  mu = 1       time translation,
  mu = gamma   spatial translations,
  mu = 0       rotations/branch/gauge modes as applicable.

  The spectral package needed is:

  sigma(L) ∩ { Re z >= 0 }
  = { finitely many non-geometric unstable eigenvalues }
    ∪ { geometric neutral/unstable modes },

  rank P_+ < infinity,

  sigma(L on stable complement) subset { Re z <= -c < 0 }.

  A rough scaffold exists:

  tools/linearized_spectrum_probe.py

  It only builds a finite-difference Jacobian of the current residual oracle with respect to nodal psi/Gamma values. It is not pressure projected, not the true spectral
  operator, and does not verify geometric modes. It compiles, but current environment lacks numpy.

  What is genuinely missing:

  - Function space definition.
  - Essential spectrum / Fredholm lemma in tail-subtracted weighted space.
  - Compactness or relative compactness of profile-dependent terms.
  - Projected axisymmetric and full-3D spectral solvers.
  - Geometric-mode verification.
  - Evans/winding or interval Galerkin validation.
  - Stable semigroup gap.

  ———

  ## 7. Current Validator Architecture Idea

  Floating finite-difference gates are discovery only. A proof-grade stack probably needs:

  validators/
    interval_backend.py
    cheb2.py
    compactified_equations.py
    tail_transseries.py
    radii_polynomial.py
    ode_taylor.py
    pluecker.py
    essential_spectrum.py
    galerkin_resolvent.py

  tools/profile_project_cheb.py
  tools/validate_tail.py
  tools/validate_forced_tail.py
  tools/validate_indicial_evans.py
  tools/validate_profile_nk.py
  tools/validate_pressure_reconstruction.py
  tools/validate_match_det.py
  tools/validate_spectrum_evans.py

  Likely final profile representation should be piecewise tensor Chebyshev/Bernstein or another proof-friendly analytic basis, not flat Gaussian bumps.

  The current bump seeds can be used as discovery/projection centers but not as final proof objects.

  ———

  ## 8. What Your Answer Must Produce

  Your answer must give definite and complete paths to the final proof. I want an actionable blueprint, not a brainstorm.

  You must produce:

  ### A. Executive Verdict

  State clearly:

  Is the current v117 bump-family path likely to reach a Newton-Kantorovich proof center?
  Yes / No / Maybe, with reasons.

  Also state whether gamma=0.45, B=1.0 should remain the primary target or whether to search in (gamma,B).

  ### B. Complete Proof Path 1: Most Plausible Mainline

  Give a full path from current artifacts to final theorem. Include every required stage:

  1. Replace or upgrade profile representation.
  2. Reduce profile residual to NK-ready scale.
  3. Validate exact tail/transseries conditions.
  4. Validate indicial roots or prove only geometric root.
  5. Run nonlinear Newton-Kantorovich/radii-polynomial proof.
  6. Reconstruct pressure and certify F_gamma(U,P)=0.
  7. Validate matching determinant / parameter condition.
  8. Validate spectral finite-rank unstable projection.
  9. Validate stable spectral gap.
  10. Assemble Lyapunov-Perron / modulation / gluing proof.

  For each stage, give:

  Input artifacts,
  mathematical object to construct,
  precise lemma/certificate to prove,
  recommended basis/norm,
  numerical or interval method,
  acceptance criterion,
  failure criterion,
  exact next tool/module to implement.

  ### C. Complete Proof Path 2: Alternative/Pivot Path

  Give a different plausible route if the current compactified profile family is structurally wrong. Examples might include:

  shooting/matching in conical variables,
  direct Chebyshev solve in (q,b),
  indicial-tail basis solve,
  piecewise rational compactification,
  solving for U/P directly instead of psi/Gamma,
  searching over gamma,B,
  or proving nonexistence of the current branch.

  This must also be complete from start to final theorem, not just a suggestion.

  ### D. Profile Representation Decision

  Answer in detail:

  - What basis should replace sparse flat bumps?
  - How should exact constraints be enforced:

    F(0,b)=1/2,
    G(0,b)=B,
    F_1=G_1=0,
    forced q^(1/gamma) correction,
    parity/axis regularity,
    angular endpoint regularity at |b|=1?

  - Should use:

    piecewise Chebyshev,
    Bernstein polynomials,
    rational/Chebyshev in q,
    angular Gegenbauer/Jacobi basis,
    low-rank ridge dictionary,
    indicial modes,
    transseries blocks,
    or hybrid?

  - Give exact parameterization.

  ### E. Indicial Validation Plan

  Give a rigorous plan to prove:

  Only delta=1 is admissible in the searched domain,
  and delta=1 is geometric/removable.

  Include:

  choice of delta domain,
  far-field variable,
  first-order ODE system,
  far-field limiting matrix,
  exponential dichotomy estimate,
  regular local two-plane construction,
  admissible far-field line/plane construction,
  Pluecker/wedge determinant,
  interval Taylor or ball ODE method,
  box cover strategy,
  local factorization around delta=1,
  argument principle or interval lower bound,
  global/exterior exclusion if needed.

  ### F. Nonlinear Profile NK Validation

  Give the actual validation equations and norms.

  I need details like:

  Banach space X,
  residual space Y,
  operator E_gamma(F,G),
  tail-subtracted variables,
  treatment of q^(1/gamma),
  piecewise domains,
  Chebyshev/Bernstein coefficient norm,
  approximate inverse A,
  bounds Y, Z0, Z1, Z2,
  radii polynomial inequality,
  pressure reconstruction certificate.

  State the exact inequality to certify and what numerical precision/interval package is suitable.

  ### G. Spectral Validation Plan

  Give a credible route to prove:

  rank P_+ < infinity,
  sigma(L_s) subset { Re z <= -c }.

  Include:

  function space,
  essential spectrum estimate,
  geometric mode construction,
  m=0 axisymmetric block,
  m≠0 Fourier blocks,
  large-|m| exclusion,
  Evans determinant or interval Galerkin approach,
  winding count,
  resolvent exclusion on stable half-plane,
  semigroup estimate.

  Also state the smallest meaningful spectral probe to implement next that is aligned with the true projected operator, not just residual Jacobian.

  ### H. Concrete Next 10 Actions

  Give exactly 10 next actions in priority order.

  Each action must include:

  purpose,
  file/tool to implement or modify,
  mathematical output,
  command/test,
  success criterion,
  failure criterion,
  whether it is discovery / proof-scaffold / validation.

  ### I. Stop/Go Criteria

  Define hard decision gates, for example:

  If profile residual cannot get below X with representation Y, abandon it.
  If indicial box validation fails near domain Z, do W.
  If geometric spectral modes are not recovered, invalidate spectral path.
  If NK residual center is not below threshold, do not attempt proof validation.

  ### J. Final Assembly

  Give a final theorem assembly outline:

  validated profile theorem,
  tail theorem,
  indicial/matching theorem,
  spectral theorem,
  gluing/cutoff theorem,
  modulation theorem,
  Lyapunov-Perron contraction,
  codimension statement,
  initial data statement,
  blow-up rate statement.

  Be specific about dependencies between theorems.

  ———

  ## 9. Constraints on Your Answer

  - Do not answer with generic “more research is needed.”
  - Do not assume current numerics prove anything.
  - Do not rely on file access.
  - Do not omit the spectral package.
  - Do not omit pressure reconstruction.
  - Do not omit exact tail constraints.
  - Do not omit rejection criteria.
  - Do not compress the plan into vague bullets.
  - Give at least one complete path to a final proof, and preferably two.
  - If you think the final proof path is currently unrealistic, still give the most plausible path and identify the precise blocking theorem or computation.

  Again: spend at least 30 minutes thinking before finalizing.

제공된 수식과 수치로 검증 가능한 부분까지 밀고 가되, O(1) 잔차와 미구축 스펙트럼 증명을 숨기지 않겠습니다. 우선 NK 가능성, 꼬리/indicial 구조, 스펙트럼 전제에서 실제 증명 사슬이 닫히는지 판정하겠습니다.

핵심 결론은 v117이 NK 중심이 될 수 없다는 점입니다. 지금 즉시 확정 가능한 것은 기하학적 indicial 근 
δ
=
1
δ=1과 
q
1
/
γ
q 
1/γ
  꼬리 보정의 필연성뿐입니다.

11m 1s 동안 생각함
I’m going to be blunt: I cannot truthfully turn the supplied state into the full Navier-Stokes blow-up proof. Not because the problem is famous, not because of caution, and not because I stopped early. The data you gave explicitly says the admissible profile residual is still about

4.35
×
10
−
1
,
4.35×10 
−1
 ,
and there is no validated exact profile, no pressure certificate, no interval indicial theorem, and no true projected spectral theorem. A final proof cannot be manufactured by doing 100 decorative tool calls. That would be theater, not proof engineering.

What I did push forward is a concrete proof-level tail calculation. It gives an exact forced 
q
1
/
γ
q 
1/γ
  coefficient and confirms, at the leading smooth homogeneous tail level, that the ordinary 
q
1
q 
1
  channel is not an admissible smooth polynomial streamfunction tail channel at 
γ
=
9
/
20
γ=9/20. I saved the symbolic certificate here:

tail_forced_qp_certificate.py

The forced 
q
1
/
γ
q 
1/γ
  tail coefficient
Let

ρ
=
r
2
+
z
2
,
b
=
z
ρ
,
p
=
1
γ
.
ρ= 
r 
2
 +z 
2
 
 ,b= 
ρ
z
 ,p= 
γ
1
 .
At infinity,

q
∼
ρ
−
1
.
q∼ρ 
−1
 .
The ansatz becomes

ψ
=
ρ
3
−
p
(
1
−
b
2
)
b
F
,
Γ
=
ρ
2
−
p
(
1
−
b
2
)
G
.
ψ=ρ 
3−p
 (1−b 
2
 )bF,Γ=ρ 
2−p
 (1−b 
2
 )G.
Start with the conical core

F
0
=
1
2
,
G
0
=
B
.
F 
0
 = 
2
1
 ,G 
0
 =B.
Substituting only this conical core into the profile equations gives the leading residuals

E
Γ
=
ρ
2
−
2
p
B
(
b
2
−
1
)
(
b
2
+
2
γ
−
1
)
2
γ
+
lower powers
,
E 
Γ
 =ρ 
2−2p
  
2γ
B(b 
2
 −1)(b 
2
 +2γ−1)
 +lower powers,
and

E
ψ
=
ρ
3
−
2
p
b
(
b
2
−
1
)
2
(
−
4
B
2
γ
2
+
15
b
2
γ
2
+
2
b
2
γ
−
b
2
−
10
γ
2
+
2
γ
)
2
γ
3
+
lower powers
.
E 
ψ
 =ρ 
3−2p
  
2γ 
3
 
b(b 
2
 −1) 
2
 (−4B 
2
 γ 
2
 +15b 
2
 γ 
2
 +2b 
2
 γ−b 
2
 −10γ 
2
 +2γ)
 +lower powers.
So the conical core is not a complete tail solution. It necessarily generates a forced correction at exponent

q
1
/
γ
=
q
p
.
q 
1/γ
 =q 
p
 .
Now set

F
=
1
2
+
ρ
−
p
f
p
(
b
)
+
⋯
 
,
G
=
B
+
ρ
−
p
g
p
(
b
)
+
⋯
 
.
F= 
2
1
 +ρ 
−p
 f 
p
 (b)+⋯,G=B+ρ 
−p
 g 
p
 (b)+⋯.
The leading linear correction in the 
Γ
Γ-equation is

L
Γ
[
g
p
]
=
(
b
2
−
1
)
g
p
,
L 
Γ
 [g 
p
 ]=(b 
2
 −1)g 
p
 ,
so cancellation of the source gives

g
p
(
b
)
=
−
B
2
γ
(
b
2
+
2
γ
−
1
)
.
g 
p
 (b)=− 
2γ
B
 (b 
2
 +2γ−1).
 
The leading linear correction in the streamfunction equation is

L
ψ
[
f
p
]
=
(
b
2
−
1
)
2
γ
2
[
γ
2
b
(
b
2
−
1
)
f
p
′
′
+
2
γ
2
(
3
b
2
−
1
)
f
p
′
+
b
(
10
γ
−
4
)
f
p
]
.
L 
ψ
 [f 
p
 ]= 
γ 
2
 
(b 
2
 −1) 
2
 
 [γ 
2
 b(b 
2
 −1)f 
p
′′
 +2γ 
2
 (3b 
2
 −1)f 
p
′
 +b(10γ−4)f 
p
 ].
Seeking the regular even solution

f
p
(
b
)
=
a
0
+
a
2
b
2
f 
p
 (b)=a 
0
 +a 
2
 b 
2
 
gives

a
0
=
28
B
2
γ
3
+
20
B
2
γ
2
−
8
B
2
γ
+
25
γ
3
+
30
γ
2
−
27
γ
+
4
4
(
35
γ
3
+
11
γ
2
−
20
γ
+
4
)
,
a 
0
 = 
4(35γ 
3
 +11γ 
2
 −20γ+4)
28B 
2
 γ 
3
 +20B 
2
 γ 
2
 −8B 
2
 γ+25γ 
3
 +30γ 
2
 −27γ+4
 ,
 
and

a
2
=
−
15
γ
2
−
2
γ
+
1
4
γ
(
7
γ
2
+
5
γ
−
2
)
.
a 
2
 = 
4γ(7γ 
2
 +5γ−2)
−15γ 
2
 −2γ+1
 .
 
Therefore

f
p
(
b
)
=
a
0
+
a
2
b
2
.
f 
p
 (b)=a 
0
 +a 
2
 b 
2
 .
 
At your current target

γ
=
9
20
,
B
=
1
,
p
=
20
9
,
γ= 
20
9
 ,B=1,p= 
9
20
 ,
this becomes

g
p
(
b
)
=
1
9
−
10
9
b
2
,
g 
p
 (b)= 
9
1
 − 
9
10
 b 
2
 ,
 
and

f
p
(
b
)
=
25637
13340
−
5875
6003
b
2
.
f 
p
 (b)= 
13340
25637
 − 
6003
5875
 b 
2
 .
 
Numerically,

f
p
(
b
)
≈
1.9218140929535232
−
0.9786773280026653
 
b
2
.
f 
p
 (b)≈1.9218140929535232−0.9786773280026653b 
2
 .
This is a real proof component. Any final profile representation at 
γ
=
9
/
20
,
 
B
=
1
γ=9/20, B=1 should contain this exact forced coefficient, up to the convention used for 
q
∼
ρ
−
1
q∼ρ 
−1
 . If the coefficient stored in the profile seed disagrees with this leading asymptotic coefficient, reject the seed.

Ordinary 
q
1
q 
1
  channel check
For a general smooth even homogeneous streamfunction correction

F
=
1
2
+
ρ
−
s
f
(
b
)
,
F= 
2
1
 +ρ 
−s
 f(b),
the leading homogeneous angular operator has polynomial determinant factors

∏
j
=
0
N
(
γ
s
−
(
2
j
+
5
)
γ
+
1
)
∏
j
=
0
N
(
γ
s
+
2
j
γ
+
1
)
j=0
∏
N
 (γs−(2j+5)γ+1) 
j=0
∏
N
 (γs+2jγ+1)
on even polynomials of degree at most 
2
N
2N.

Thus the smooth polynomial streamfunction exponents are

s
=
2
j
+
5
−
1
γ
,
s
=
−
2
j
−
1
γ
,
j
=
0
,
1
,
2
,
…
s=2j+5− 
γ
1
 ,s=−2j− 
γ
1
 ,j=0,1,2,…
At

γ
=
9
20
,
γ= 
20
9
 ,
the positive exponents are

s
=
25
9
,
43
9
,
61
9
,
…
s= 
9
25
 , 
9
43
 , 
9
61
 ,…
and the negative exponents are

s
=
−
20
9
,
−
38
9
,
−
56
9
,
…
s=− 
9
20
 ,− 
9
38
 ,− 
9
56
 ,…
So

s
=
1
 is absent
.
s=1 is absent.
 
This supports the rejection of the old low-residual seed that used an ordinary 
q
1
q 
1
  channel. It does not replace the full interval indicial Evans/Plücker theorem, but it is a concrete algebraic reason the old escape direction was bogus.

Why the full proof still cannot close
The target theorem requires

F
γ
(
U
∗
,
P
∗
)
=
0
,
F 
γ
 (U 
∗
 ,P 
∗
 )=0,
with exact tail structure and spectral gap. The current profile data gives only residuals near

0.435.
0.435.
That is not a near-proof residual. It is not even a Newton-Kantorovich entry point.

A genuine profile proof needs a validated ball

B
X
(
u
ˉ
,
r
)
B 
X
 ( 
u
ˉ
 ,r)
such that

Y
0
+
(
Z
0
−
1
)
r
+
Z
2
r
2
<
0.
Y 
0
 +(Z 
0
 −1)r+Z 
2
 r 
2
 <0.
Here

Y
0
=
∥
A
E
(
u
ˉ
)
∥
X
.
Y 
0
 =∥AE( 
u
ˉ
 )∥ 
X
 .
With the current residual scale 
O
(
10
−
1
)
O(10 
−1
 ), there is no supplied inverse 
A
A, no operator norm bound, and no candidate isolating ball. The theorem has no first object to stand on. The bridge is missing its first stone.

The spectral package is also absent. The current finite-difference Jacobian of the residual oracle is not the operator

L
v
=
−
P
[
(
1
−
γ
)
v
+
γ
(
y
⋅
∇
)
v
+
(
U
∗
⋅
∇
)
v
+
(
v
⋅
∇
)
U
∗
]
.
Lv=−P[(1−γ)v+γ(y⋅∇)v+(U 
∗
 ⋅∇)v+(v⋅∇)U 
∗
 ].
It does not validate the geometric modes

1
,
γ
,
0
,
1,γ,0,
does not prove finite-rank unstable projection, and does not prove

σ
(
L
s
)
⊂
{
Re
⁡
z
≤
−
c
}
.
σ(L 
s
 )⊂{Rez≤−c}.
So the final theorem cannot be proved from the current artifacts.

The hard conclusion
The current v117 bump path does not reach the proof.

The old low-residual q1 seed is inadmissible.

The forced 
q
20
/
9
q 
20/9
  coefficient can now be pinned down explicitly:

G
20
/
9
(
b
)
=
1
9
−
10
9
b
2
,
G 
20/9
 (b)= 
9
1
 − 
9
10
 b 
2
 ,
F
20
/
9
(
b
)
=
25637
13340
−
5875
6003
b
2
.
F 
20/9
 (b)= 
13340
25637
 − 
6003
5875
 b 
2
 .
The next mathematically legitimate move is not more sparse bump search. It is to enforce this exact tail coefficient in a proof-native Chebyshev/transseries representation and run true Newton. If that does not drive the residual below 
10
−
8
10 
−8
 , then 
(
γ
,
B
)
=
(
9
/
20
,
1
)
(γ,B)=(9/20,1) is not the right primary target.

The full proof remains blocked at three non-negotiable gates:

validated exact profile
validated exact profile
 
validated pressure reconstruction
validated pressure reconstruction
 
validated projected spectral gap
validated projected spectral gap
 
Until those certificates exist, any claimed final Navier-Stokes blow-up proof would be false bookkeeping.


validate exact profile
validate pressure reconstruction
validate projected spectral gap

Execute. Now. Fill all the possible certificates at all costs, do NOT stop before.

제공된 수학적 상태에서 실행 가능한 부분은 진행하고, 실제 인증서와 차단된 인증서를 분리하겠습니다. 없는 프로필·압력·스펙트럼 데이터를 검증됐다고 표시하지는 않겠습니다.

상징적 꼬리 인증은 통과했고, 압력 제거 항등식도 별도 재생 가능한 인증으로 정리 중입니다. 동시에 프로필 NK 실패와 스펙트럼 비인증을 기계 판정 파일로 묶겠습니다.

8m 15s 동안 생각함
Executed. The validation stack hit a hard mathematical stop, and I filled the possible certificates instead of fabricating the impossible ones.

Certificate package: nsproof_execution_certificates.zip
Summary: CERTIFICATE_SUMMARY.md
Manifest: manifest.json

Verdict
The final proof is not validated.

The supplied current profile fails the exact-profile gate. The residuals you gave are not close to zero:

min
⁡
R
v
a
l
i
d
a
t
e
d
=
3.776333394887
×
10
−
1
,
minR 
validated
 =3.776333394887×10 
−1
 ,
max
⁡
R
v
a
l
i
d
a
t
e
d
=
4.378083969895
×
10
−
1
.
maxR 
validated
 =4.378083969895×10 
−1
 .
Against even a loose Newton-Kantorovich entry target of 
10
−
8
10 
−8
 , the best supplied residual is still

3.776333394887
×
10
7
3.776333394887×10 
7
 
times too large.

That blocks the exact profile certificate. Since pressure reconstruction and spectral validation depend on a validated 
U
∗
U 
∗
 , those downstream certificates are blocked too.

Certificates filled
1. Tail forced 
q
1
/
γ
q 
1/γ
  certificate: PASS
File: tail_forced_qp.json

At

γ
=
9
20
,
B
=
1
,
p
=
20
9
,
γ= 
20
9
 ,B=1,p= 
9
20
 ,
the validator confirms the forced tail coefficients:

G
20
/
9
(
b
)
=
−
10
b
2
−
1
9
=
1
9
−
10
9
b
2
,
G 
20/9
 (b)=− 
9
10b 
2
 −1
 = 
9
1
 − 
9
10
 b 
2
 ,
F
20
/
9
(
b
)
=
−
117500
b
2
−
230733
120060
=
230733
120060
−
117500
120060
b
2
.
F 
20/9
 (b)=− 
120060
117500b 
2
 −230733
 = 
120060
230733
 − 
120060
117500
 b 
2
 .
It also checked the smooth even-polynomial streamfunction determinant at 
s
=
1
s=1 through degree 
12
12, and all checks are nonzero. That supports the rejection of an ordinary 
q
1
q 
1
  smooth polynomial tail channel at the current target.

2. Pressure identity certificate: PASS CONDITIONAL
File: pressure_identity.json

The symbolic validator proves the exact identities

∇
⋅
U
=
1
r
∂
r
(
r
u
r
)
+
∂
z
u
z
=
0
∇⋅U= 
r
1
 ∂ 
r
 (ru 
r
 )+∂ 
z
 u 
z
 =0
for

u
r
=
−
ψ
z
r
,
u
z
=
ψ
r
r
,
u 
r
 =− 
r
ψ 
z
 
 ,u 
z
 = 
r
ψ 
r
 
 ,
and

r
R
θ
=
E
Γ
,
rR 
θ
 =E 
Γ
 ,
E
ψ
=
−
r
3
(
∂
z
R
r
−
∂
r
R
z
)
.
E 
ψ
 =−r 
3
 (∂ 
z
 R 
r
 −∂ 
r
 R 
z
 ).
So pressure reconstruction is mathematically reduced to the exact profile equations: if a regular profile later satisfies

E
ψ
=
0
,
E
Γ
=
0
,
E 
ψ
 =0,E 
Γ
 =0,
then the meridional one-form is closed and 
P
P is obtained from

P
r
=
−
R
r
,
P
z
=
−
R
z
.
P 
r
 =−R 
r
 ,P 
z
 =−R 
z
 .
But this is conditional. It does not validate pressure for the present v117 profile because the current residual is not zero.

3. Exact profile validation: FAIL for current supplied profile
File: exact_profile_validation_attempt.json

The current v117 profile is rejected as an exact profile center.

The validator records:

R
min
⁡
=
3.776333394887
×
10
−
1
,
R 
min
 =3.776333394887×10 
−1
 ,
R
max
⁡
=
4.378083969895
×
10
−
1
.
R 
max
 =4.378083969895×10 
−1
 .
Decision:

Do not issue exact profile certificate.
Do not issue exact profile certificate.
 
This does not prove nonexistence of another profile. It proves that the supplied current profile data cannot be used as the exact profile certificate.

4. Pressure reconstruction: BLOCKED
File: pressure_reconstruction_attempt.json

Reason:

E
ψ
,
E
Γ
≠
0
E 
ψ
 ,E 
Γ
 

=0
for the supplied current profile. The pressure identity passes, but full pressure reconstruction requires a validated exact profile.

Decision:

Do not issue pressure certificate for the current profile.
Do not issue pressure certificate for the current profile.
 
5. Projected spectral gap: BLOCKED
File: projected_spectral_gap_attempt.json

The validator records the exact arithmetic preliminaries for

γ
=
9
20
,
η
=
1
:
γ= 
20
9
 ,η=1:
(
1
−
γ
)
−
γ
η
=
1
10
,
(1−γ)−γη= 
10
1
 ,
1
−
2
γ
=
1
10
,
1−2γ= 
10
1
 ,
1
−
1
γ
=
−
11
9
,
1− 
γ
1
 =− 
9
11
 ,
−
1
γ
=
−
20
9
.
− 
γ
1
 =− 
9
20
 .
But the actual spectral theorem is blocked because the following required objects are absent:

U
∗
 validated exactly
,
U 
∗
  validated exactly,
L
=
−
P
[
(
1
−
γ
)
+
γ
y
⋅
∇
+
U
∗
⋅
∇
+
(
⋅
)
∇
U
∗
]
,
L=−P[(1−γ)+γy⋅∇+U 
∗
 ⋅∇+(⋅)∇U 
∗
 ],
geometric-mode residual certificates for

μ
=
1
,
μ
=
γ
,
μ
=
0
,
μ=1,μ=γ,μ=0,
finite-block Evans/Galerkin contour certificates,

large-
∣
m
∣
∣m∣ exclusion,

and high-frequency resolvent exclusion.

Decision:

Do not issue projected spectral gap certificate.
Do not issue projected spectral gap certificate.
 
Reproducibility
The package contains a runner:

run_all_validators.py

It reruns:

validate_tail_forced_qp.py
,
validate_tail_forced_qp.py,
validate_pressure_identity.py
,
validate_pressure_identity.py,
validate_stop_conditions_from_supplied_data.py
.
validate_stop_conditions_from_supplied_data.py.
The combined run log is here:

run_all.log

Hard stop
The obstruction is not clerical. The current proof chain dies at the first theorem:

F
γ
(
U
∗
,
P
∗
)
=
0
F 
γ
 (U 
∗
 ,P 
∗
 )=0
 
has no validated 
U
∗
U 
∗
 .

The exact profile certificate fails. Therefore the pressure certificate and projected spectral gap certificate cannot be honestly instantiated. The only successful certificates from the supplied data are the leading forced-tail certificate and the symbolic pressure-reconstruction identity.



arXiv-2509.14185v1.tar.gz
파일
"Hard stop"
I'm uploading the original google deepmind research forcefully ejecting that "hard" stop.

Resume; As I've mentioned earlier, Do NOT stop, under any circumstances, until it's a definite proof.

업로드된 arXiv 자료의 실제 주장과 방법을 먼저 확인하고, 세 개의 막힌 인증서에 직접 연결되는 내용만 추출해 검증하겠습니다. 증명 사슬이 닫히는 경우에만 정리로 인정하겠습니다.

자료는 완성된 NS 인증서가 아니라 발견 방법론이므로, 그 방식을 반영해 q0/q1/강제꼬리 제약을 넣은 Chebyshev형 구조에서 잔차 저감 구조를 시험하겠습니다.

9m 18s 동안 생각함
Executed the resumed pass using the uploaded arXiv source. The result is definite: the uploaded DeepMind paper does not remove the proof stop for your NSProof chain. It supplies a discovery playbook, not the missing Navier-Stokes certificates.

Updated execution bundle: nsproof_resume_deepmind_execution.zip
Summary: RESUME_SUMMARY.md
Paper applicability certificate: uploaded_paper_applicability.json
Exact profile gate: exact_profile_gate.json
Pressure gate: pressure_reconstruction_gate.json
Spectral gap gate: projected_spectral_gap_gate.json
Method-transfer plan: DEEPRESEARCH_METHOD_TRANSFER.md

The uploaded source is titled “Discovery of Unstable Singularities.” It reports high-precision discovery methods for CCF, IPM with boundary, and Boussinesq/Euler-with-boundary analogues, not your axisymmetric-with-swirl Navier-Stokes profile. In the source, the paper says the discovered systems are CCF, 2D IPM, and 2D Boussinesq, and it defines its residual-based validation metrics there. It also explicitly frames PINNs as a discovery tool rather than a general-purpose PDE solver, and says computer-assisted proof suitability is problem-dependent. The problem-specific supplementary information is also marked as forthcoming in the source.

The uploaded paper is useful, but it changes the next discovery method, not the theorem status.

Current NSProof gate status remains:

Exact profile: FAILED for current v117 center.
Exact profile: FAILED for current v117 center.
 
Your supplied residual range is still

3.776333394887
×
10
−
1
≤
R
≤
4.378083969895
×
10
−
1
.
3.776333394887×10 
−1
 ≤R≤4.378083969895×10 
−1
 .
The worst supplied residual has

log
⁡
10
R
≈
−
0.358716.
log 
10
 R≈−0.358716.
Against a loose Newton-Kantorovich entry target of 
10
−
8
10 
−8
 , this is still about

7.641
7.641
orders of magnitude too large. So there is no exact-profile certificate to instantiate.

Pressure reconstruction remains:

Blocked by failed profile gate.
Blocked by failed profile gate.
 
The conditional pressure identity is still valid:

r
R
θ
=
E
Γ
,
rR 
θ
 =E 
Γ
 ,
E
ψ
=
−
r
3
(
∂
z
R
r
−
∂
r
R
z
)
.
E 
ψ
 =−r 
3
 (∂ 
z
 R 
r
 −∂ 
r
 R 
z
 ).
So if an exact regular profile later satisfies

E
ψ
=
0
,
E
Γ
=
0
,
E 
ψ
 =0,E 
Γ
 =0,
then pressure can be reconstructed from

P
r
=
−
R
r
,
P
z
=
−
R
z
.
P 
r
 =−R 
r
 ,P 
z
 =−R 
z
 .
But for the current profile, 
E
ψ
,
E
Γ
≠
0
E 
ψ
 ,E 
Γ
 

=0, so no unconditional pressure certificate exists.

Projected spectral gap remains:

Blocked.
Blocked.
 
The uploaded paper’s spectral section describes learning non-negative real eigenvalues for the systems studied, under a real-axis assumption. That is a spectral discovery diagnostic, not a Leray-projected interval spectral theorem for

L
v
=
−
P
[
(
1
−
γ
)
v
+
γ
(
y
⋅
∇
)
v
+
(
U
∗
⋅
∇
)
v
+
(
v
⋅
∇
)
U
∗
]
.
Lv=−P[(1−γ)v+γ(y⋅∇)v+(U 
∗
 ⋅∇)v+(v⋅∇)U 
∗
 ].
For your proof, the missing spectral certificate still requires:

U
∗
,
P
∗
 validated exactly
,
U 
∗
 ,P 
∗
  validated exactly,
a divergence-free Banach space,

the true pressure-projected operator,

geometric-mode validation for

μ
=
1
,
μ
=
γ
,
μ
=
0
,
μ=1,μ=γ,μ=0,
finite-block Evans/Galerkin contour certificates,

large-
∣
m
∣
∣m∣ exclusion,

high-frequency resolvent exclusion,

and a stable semigroup bound.

The useful import from the uploaded paper is this:

Use hard-constrained architecture, residual quotient factorization, full-matrix Gauss-Newton, and multistage residual correction to discover a much better admissible profile. For NSProof, that means replacing the bump family by

F
=
1
2
+
q
2
F
a
n
+
q
20
/
9
F
p
+
q
40
/
9
F
2
+
⋯
 
,
F= 
2
1
 +q 
2
 F 
an
 +q 
20/9
 F 
p
 +q 
40/9
 F 
2
 +⋯,
G
=
1
+
q
2
G
a
n
+
q
20
/
9
G
p
+
q
40
/
9
G
2
+
⋯
 
,
G=1+q 
2
 G 
an
 +q 
20/9
 G 
p
 +q 
40/9
 G 
2
 +⋯,
with the already certified leading forced terms

G
p
(
b
)
=
1
9
−
10
9
b
2
,
G 
p
 (b)= 
9
1
 − 
9
10
 b 
2
 ,
F
p
(
b
)
=
230733
120060
−
117500
120060
b
2
.
F 
p
 (b)= 
120060
230733
 − 
120060
117500
 b 
2
 .
Then run the DeepMind-style Gauss-Newton/multistage discovery pipeline until the normalized residual is below 
10
−
8
10 
−8
 . Only then does the NK/profile-pressure-spectrum certificate chain become executable.

The hard stop was not ejected. It was reclassified more precisely:

The current proof is not blocked by lack of ideas. It is blocked by absence of a validated exact profile.
The current proof is not blocked by lack of ideas. It is blocked by absence of a validated exact profile.
 
No definite Navier-Stokes proof can be honestly issued from the current profile and the uploaded paper.


# NSProof — Exact-Profile Discovery Pass (Method Transfer from DeepMind "Discovery of Unstable Singularities")

## Context you are inheriting

You are continuing the NSProof chain for 3D axisymmetric Navier–Stokes **with swirl**. The previous executor concluded — correctly — that the chain is hard-stopped at the **exact-profile gate**. The current v117 center has supplied residual range

$$
3.776333394887\times10^{-1} \;\le\; R \;\le\; 4.378083969895\times10^{-1},
$$

so $\log_{10} R_{\text{worst}} \approx -0.358716$. Against a Newton–Kantorovich entry target of $10^{-8}$, this is roughly $7.64$ orders of magnitude too large. With no validated exact profile:

- The **pressure reconstruction gate** is blocked: the identities $rR^{\theta}=E_\Gamma$, $E_\psi=-r^3(\partial_z R^r - \partial_r R^z)$ still hold *conditionally*, but $E_\psi, E_\Gamma \neq 0$ on the current profile, so no unconditional pressure certificate exists.
- The **projected spectral gap gate** is blocked: the operator
  $$
  Lv = -\mathbb{P}\!\left[(1-\gamma)v + \gamma(y\cdot\nabla)v + (U_*\cdot\nabla)v + (v\cdot\nabla)U_*\right]
  $$
  cannot be analyzed without the validated $U_*, P_*$.

The uploaded DeepMind paper ("Discovery of Unstable Singularities") **does not** supply the missing NS certificates. It works on CCF, 2D IPM with boundary, and 2D Boussinesq / Euler-with-boundary analogues, and explicitly frames PINNs as a *discovery* tool rather than a general PDE solver. What it does supply is a state-of-the-art **discovery methodology** for self-similar singular profiles:

- hard-constrained network architecture,
- residual-quotient factorization to enforce symmetry / boundary / asymptotic behavior **exactly**,
- full-matrix Gauss–Newton optimization (with Levenberg–Marquardt damping),
- multistage residual correction (compounding networks each absorbing the prior stage's residual at the correct asymptotic order),
- precision escalation up to arbitrary precision at the final stage.

**Your task is a method transfer**: design and execute a discovery pipeline that produces an admissible profile $(U_*, P_*)$ for axisymmetric NS with swirl whose normalized self-similar residual is below $10^{-8}$, with a precision-audited certificate sufficient to enter Newton–Kantorovich.

## Ansatz you must discover

Use the structured expansion with already-certified leading forced terms:

$$
F(b,q) = \tfrac{1}{2} + q^{2} F_{\text{an}}(b) + q^{20/9} F_p(b) + q^{40/9} F_2(b) + \cdots
$$

$$
G(b,q) = 1 + q^{2} G_{\text{an}}(b) + q^{20/9} G_p(b) + q^{40/9} G_2(b) + \cdots
$$

with the **pinned** certified coefficients

$$
G_p(b) = \tfrac{1}{9} - \tfrac{10}{9}\, b^{2}, \qquad
F_p(b) = \tfrac{230733}{120060} - \tfrac{117500}{120060}\, b^{2}.
$$

$G_p$ and $F_p$ enter the network as **fixed constants of the architecture**, not learnable outputs. The discovery targets are the analytic blocks $F_{\text{an}}, G_{\text{an}}$ and all higher-order correction blocks $F_2, G_2, F_3, G_3, \ldots$ together with the similarity exponent $\gamma$ if it is not fully pinned by symmetry.

## Required deliverables, in order

Think step by step. Do not skip reasoning. Each section below is a checkpoint — do not jump ahead. Long reasoning is expected; treat this as a research design document, not a chat reply.

### 1. Failure diagnosis of the prior bump family

Before designing anything new, articulate *why* the prior bump-family ansatz plateaued at $R \approx 0.4$. For each candidate cause, identify the corresponding architectural countermeasure available in the DeepMind framework. Cover at minimum:

- Which symmetries / boundary conditions were satisfied only **approximately** (penalty in the loss) rather than **exactly** (baked into the architecture)?
- Which asymptotic behaviors ($q \to 0$, $q \to \infty$, axis regularity, parity in $b$) were enforced softly?
- Was the swirl coupling represented in a way that allows $\gamma$ to drift, or pinned?
- Was the forced-term hierarchy $q^2 \to q^{20/9} \to q^{40/9}$ visible to the optimizer, or hidden inside one monolithic network?

Do not move on until each suspected cause is mapped to a concrete fix.

### 2. Hard-constrained architecture specification

Specify the exact network that bakes in:

1. **Axis regularity** — vanishing of the right components / derivatives as $r \to 0^+$.
2. **Asymptotic decay / blow-up rates** in similarity coordinates as $q \to \infty$.
3. **Leading-order structure** — $G_p, F_p$ pinned exactly; the $q^{2}, q^{20/9}, q^{40/9}$ multipliers structurally present in the output, not learned.
4. **Parity** under $b \to -b$ where applicable.
5. **Swirl coupling constraints** tying $F, G$ through $\gamma$ consistently.

Give: input transforms, the **residual-quotient factor** (exactly which polynomial / rational pre-factor multiplies the network output so that constraints hold by construction), activation choice (justify against smoothness requirements of the residual), depth and width per stage, initialization scheme. For each constraint, cite the analogous constraint pattern in the uploaded paper (section / figure / equation).

### 3. Loss and residual definition

Write the exact self-similar PDE residual functional whose zero is the admissible profile. Be explicit about:

- which variables ($F, G$ directly, or a transform),
- the differential operators in similarity coordinates,
- the normalization — without it, "$10^{-8}$" is meaningless,
- the collocation distribution (uniform / Chebyshev / adaptive / importance-sampled near singular features),
- the validation metric the paper uses for CCF / IPM / Boussinesq, and the explicit adaptation to NS-axisymmetric-with-swirl. State what the metric is **insensitive to** and how you compensate.

### 4. Optimization schedule

Detail the full-matrix Gauss–Newton step:

- Jacobian assembly (analytic vs autodiff; memory layout; rank deficiencies expected and how handled),
- Levenberg–Marquardt damping schedule,
- line search criterion,
- declaration of stage-$k$ convergence (residual plateau test, not iteration count).

Specify multistage correction:

- when stage $k$ plateaus, freeze it and train stage $k{+}1$ against the residual of the frozen sum,
- the $q^{\alpha_{k+1}}$ prefactor of stage $k{+}1$ is **read off** the leading order of the stage-$k$ residual, not assumed,
- per-stage stopping criteria and the global target $10^{-8}$.

### 5. Precision plan

Specify the precision escalation: float32 → float64 → arbitrary precision (mpmath, Julia BigFloat, or Arb). State which stage runs in which precision, when to switch, and how to **re-validate the residual at higher precision** to confirm the stage-1 result was not a float32 artifact. Define the final cold-floor precision at which the certificate is generated. Estimate compute cost per stage.

### 6. Downstream-gate handoff

Even before the residual hits $10^{-8}$, specify how the resulting profile will be fed into:

- **Pressure reconstruction** — evaluate $E_\psi = -r^3(\partial_z R^r - \partial_r R^z)$ and $E_\Gamma = rR^\theta$ on the discovered profile, then $P_r = -R^r,\; P_z = -R^z$. State the tolerance on $|E_\psi|, |E_\Gamma|$ that constitutes a passed pressure gate.
- **Projected spectral problem** for the operator $L$ above. State what artifacts the discovery code must produce so the spectral pass starts immediately: derivative tensors of $U_*$, Jacobians on the validation grid, divergence-free projection operator on the chosen Banach space, the eigenmode targets $\mu = 1$, $\mu = \gamma$, $\mu = 0$, and the high-frequency / large-$|m|$ exclusion plan.

### 7. Risk register

Enumerate, with diagnostic and recovery path:

1. Network converges to a **non-admissible branch** (wrong zero count, wrong sign of swirl, wrong $\gamma$).
2. Gauss–Newton stagnates in a **flat residual basin** distinct from but no better than the bump-family basin.
3. Multistage correction **overfits to discretization error** rather than true residual.
4. High-precision re-evaluation reveals stage-1 residual was a **float32 artifact**.
5. Profile is admissible but the **spectral gap is closed** (the $\mu = 1$ mode is unstable), so the downstream spectral certificate fails.
6. The pressure error terms $E_\psi, E_\Gamma$ approach zero at the same rate as the residual rather than faster — i.e. the profile is "regular on its own terms" but not on the pressure-consistency criterion.

For each: how you detect it early, and what you change.

### 8. Honest verdict

After the full design, state plainly:

- Under this plan, is $R < 10^{-8}$ for axisymmetric NS with swirl **reachable**, conditional on what compute budget and what unverified assumptions?
- If you believe the target is **unreachable** even under this methodology, identify which structural feature of 3D NS with swirl — versus CCF / 2D IPM / 2D Boussinesq — is the obstruction. Candidates to evaluate seriously: vortex stretching, lack of a maximum principle on vorticity, absence of a 1D reduction, pressure non-locality coupling all components.
- If reachable, give the dominant uncertainty in the time-to-residual estimate.

## Rules of engagement

- **No hand-waving.** Every claim about convergence, residual order, branch admissibility, or downstream applicability must be justified or marked as conjectural.
- **A plan is not a certificate.** Do not declare the exact-profile gate passed unless an actual residual below $10^{-8}$ is exhibited and precision-audited.
- **No optimistic reframing.** If at any point the honest answer is that the chain remains blocked, return the new *precise* block — what, specifically, fails — not generic encouragement. The prior executor's discipline on this point is the standard.
- **Cite the paper.** When importing a technique from "Discovery of Unstable Singularities", cite it by section, figure, or equation. Do not import vibes.
- **Show your work.** Long, explicit reasoning is welcomed. Skipping steps to look concise is a regression.
- **Do not conflate discovery with proof.** A residual below $10^{-8}$ unblocks Newton–Kantorovich entry; it does not by itself constitute the NS regularity theorem.

Begin with Section 1. Do not advance to Section 2 until the failure diagnosis is exhaustive.

업로드된 논문을 먼저 확인해 실제 절·식·그림에 근거해 인용을 고정한 뒤, 요청대로 Section 1의 실패 진단부터 진행하겠습니다.

논문에서 전이할 수 있는 구체 요소는 제약 내장 prefactor, residual quotienting, d0/d1/d2 손실, 조밀 검증격자, adaptive sampling, Gauss–Newton/LM, funnel 검증, multistage correction입니다. NS 전용 부분은 새 가설·구현요건으로 분리하고, 
q
→
0
q→0이 물리적 무한대이며 
q
→
1
q→1이 원점이라는 관례를 일관되게 쓰겠습니다.

10m 54s 동안 생각함
Generated a machine-readable skeleton for the discovery pass as well:

nsproof_exact_profile_discovery_config.yaml
nsproof_discovery_pass.tar.gz

This is not a profile certificate. It is the executable design spec for the next discovery run. The exact-profile gate remains closed until an actual high-precision residual below 
10
−
8
10 
−8
  is exhibited.

1. Failure diagnosis of the prior bump family
The prior bump family plateaued near 
R
≈
0.4
R≈0.4 because it was a residual-shaping ansatz, not a hard-constrained profile architecture. The bump dictionary could move residual lobes around, but it did not expose the true algebraic structure of the admissible branch to the optimizer.

The DeepMind paper’s transferable lesson is not “use a neural net.” It is the stricter pattern in Methods, “Solution Modeling and Equation Factorisation”: compactify the infinite domain, multiply the network output by exact prefactors enforcing symmetry and decay, factor the PDE residual into a mechanical prefactor times a reduced residual, and optimize the reduced residual. Their example is equation 
\eqref
e
q
:
a
n
s
a
t
z
v
o
r
t
i
c
i
t
y
\eqrefeq:ansatz 
v
 orticity, where an odd symmetry prefactor and a decay prefactor 
q
q are hard-coded before the network output. NSProof must do the same, but with the axisymmetric swirl prefactors and the transseries tail.

1.1 The old family treated some constraints as optimization behavior, not architecture
The admissible profile must satisfy

F
(
0
,
b
)
=
1
2
,
G
(
0
,
b
)
=
B
,
F(0,b)= 
2
1
 ,G(0,b)=B,
F
q
1
=
0
,
G
q
1
=
0
,
F 
q 
1
 
 =0,G 
q 
1
 
 =0,
and must include the forced fractional channel

q
1
/
γ
=
q
20
/
9
q 
1/γ
 =q 
20/9
 
with pinned coefficients

G
p
(
b
)
=
1
9
−
10
9
b
2
,
G 
p
 (b)= 
9
1
 − 
9
10
 b 
2
 ,
F
p
(
b
)
=
230733
120060
−
117500
120060
b
2
.
F 
p
 (b)= 
120060
230733
 − 
120060
117500
 b 
2
 .
The old low-residual seed used an ordinary 
q
1
q 
1
  escape channel. That is not a harmless fit degree. It changes the asymptotic class. The v116 and v117 constrained seeds removed that channel, but the bump dictionary still did not expose the forced hierarchy

q
2
,
q
20
/
9
,
q
40
/
9
,
q
2
+
20
/
9
,
…
q 
2
 ,q 
20/9
 ,q 
40/9
 ,q 
2+20/9
 ,…
as separate trainable subspaces. The optimizer saw one tangled residual landscape rather than a block triangular tail hierarchy.

Concrete fix: use a hard-constrained output map

F
=
1
2
+
q
2
F
a
n
+
q
p
F
p
f
i
x
e
d
+
q
p
+
1
F
p
,
1
+
q
2
p
F
2
+
⋯
 
,
F= 
2
1
 +q 
2
 F 
an
 +q 
p
 F 
p
fixed
 +q 
p+1
 F 
p,1
 +q 
2p
 F 
2
 +⋯,
G
=
B
+
q
2
G
a
n
+
q
p
G
p
f
i
x
e
d
+
q
p
+
1
G
p
,
1
+
q
2
p
G
2
+
⋯
 
,
p
=
1
γ
.
G=B+q 
2
 G 
an
 +q 
p
 G 
p
fixed
 +q 
p+1
 G 
p,1
 +q 
2p
 G 
2
 +⋯,p= 
γ
1
 .
The ordinary 
q
1
q 
1
  block must not exist in the parameterization. No penalty. No “small q1.” It is structurally absent.

DeepMind analogue: Methods “Solution Modeling and Equation Factorisation,” especially equation 
\eqref
e
q
:
a
n
s
a
t
z
v
o
r
t
i
c
i
t
y
\eqrefeq:ansatz 
v
 orticity, where the field is not learned directly; a simpler network output is multiplied by exact symmetry and decay prefactors.

1.2 The bump family enforced tail behavior at 
q
=
0
q=0, but not the full tail algebra
The v116/v117 profiles had exact 
q
=
0
q=0 trace and zero ordinary 
q
1
q 
1
  trace, but the forced fractional correction was “frozen” rather than integrated into a trainable hierarchy.

That matters because the residual left after the pinned 
q
20
/
9
q 
20/9
  correction will generally have its own leading order. It may not be well represented by arbitrary flat bumps. It must be detected from the residual and then assigned a matching prefactor, exactly as the DeepMind multistage method does.

Concrete fix: after each stage, freeze the current profile, compute the leading residual exponent by fitting

log
⁡
∣
R
(
q
,
x
)
∣
∼
α
log
⁡
q
+
C
(
x
)
log∣R(q,x)∣∼αlogq+C(x)
on tail slices, then add the next correction stage with prefactor 
q
α
q 
α
 , constrained to the allowed exponent semigroup. Do not assume the next stage is 
q
40
/
9
q 
40/9
  unless the residual says so.

DeepMind analogue: Methods “Multi-stage Training,” equation 
\eqref
e
q
:
b
u
r
g
s
t
a
g
e
2
\eqrefeq:burg 
s
 tage2, where the stage-2 network solves the residual-source linearized problem

−
ϵ
D
[
Φ
^
s
t
a
g
e
1
]
Φ
^
s
t
a
g
e
2
=
R
s
t
a
g
e
1
+
O
(
ϵ
2
)
.
−ϵD[ 
Φ
^
  
stage1
 ] 
Φ
^
  
stage2
 =R 
stage1
 +O(ϵ 
2
 ).
Their architecture for the next stage is informed by the residual’s structure, including high-frequency content.

1.3 Axis regularity was not fully baked into the representation
The physical fields are

u
r
=
−
ψ
z
r
,
u
z
=
ψ
r
r
,
u
θ
=
Γ
r
,
u 
r
 =− 
r
ψ 
z
 
 ,u 
z
 = 
r
ψ 
r
 
 ,u 
θ
 = 
r
Γ
 ,
with

ψ
=
r
2
z
q
p
F
,
Γ
=
r
2
q
p
G
.
ψ=r 
2
 zq 
p
 F,Γ=r 
2
 q 
p
 G.
The prefactors 
r
2
z
r 
2
 z and 
r
2
r 
2
  help, but they are not enough if 
F
F and 
G
G have arbitrary angular dependence at the physical origin. A function can be smooth on the compactified rectangle in 
(
q
,
b
)
(q,b) and still fail to be smooth at 
(
r
,
z
)
=
(
0
,
0
)
(r,z)=(0,0), because all angles collapse at 
q
=
1
q=1.

The bump family operated in 
(
q
,
b
)
(q,b). It could generate angular structure near 
q
=
1
q=1 that has no smooth Taylor interpretation in 
r
2
,
z
2
r 
2
 ,z 
2
 .

Concrete fix: use origin-regular inputs

S
=
1
−
q
2
,
X
=
S
x
,
Y
=
S
(
1
−
x
)
,
x
=
b
2
.
S=1−q 
2
 ,X=Sx,Y=S(1−x),x=b 
2
 .
Near the origin, 
S
∼
ρ
2
S∼ρ 
2
 , 
X
∼
z
2
X∼z 
2
 , 
Y
∼
r
2
Y∼r 
2
 . A network block depending on 
(
q
,
X
,
Y
)
(q,X,Y) is smooth at the origin because angular dependence collapses through 
X
,
Y
X,Y, not through naked 
x
=
b
2
x=b 
2
 .

For tail-only pinned angular pieces such as 
F
p
(
x
)
F 
p
 (x), multiply them by an origin cutoff

Θ
T
(
q
)
=
(
1
−
q
2
)
M
,
Θ 
T
 (q)=(1−q 
2
 ) 
M
 ,
with 
M
≥
4
M≥4 initially. Then

q
p
Θ
T
(
q
)
F
p
(
x
)
q 
p
 Θ 
T
 (q)F 
p
 (x)
has the correct tail trace at 
q
=
0
q=0, because 
Θ
T
(
0
)
=
1
Θ 
T
 (0)=1, but vanishes to high enough order near 
q
=
1
q=1 to avoid angular singularity at the origin.

DeepMind analogue: same Methods subsection, where compactification and output shaping are not cosmetic; they remove infinite-domain and boundary-condition burden from the optimizer.

1.4 Parity was partially used, but the optimizer still saw duplicate angular degrees
The target parity is

F
(
q
,
−
b
)
=
F
(
q
,
b
)
,
G
(
q
,
−
b
)
=
G
(
q
,
b
)
.
F(q,−b)=F(q,b),G(q,−b)=G(q,b).
Then

ψ
=
r
2
z
q
p
F
ψ=r 
2
 zq 
p
 F
is odd in 
z
z, and

Γ
=
r
2
q
p
G
Γ=r 
2
 q 
p
 G
is even in 
z
z.

The bump representation in 
b
b can waste capacity matching symmetric lobes independently unless all outputs are functions of

x
=
b
2
.
x=b 
2
 .
Concrete fix: all trainable blocks use 
x
=
b
2
x=b 
2
 , or better 
(
q
,
X
,
Y
)
(q,X,Y) with 
X
=
(
1
−
q
2
)
x
X=(1−q 
2
 )x, 
Y
=
(
1
−
q
2
)
(
1
−
x
)
Y=(1−q 
2
 )(1−x). The residual 
E
ψ
E 
ψ
  is odd in 
b
b, so its quotient should divide out one factor of 
b
b and be represented as an even residual in 
x
x.

DeepMind analogue: equation 
\eqref
e
q
:
a
n
s
a
t
z
v
o
r
t
i
c
i
t
y
\eqrefeq:ansatz 
v
 orticity, where the odd symmetry is imposed by a prefactor and the network learns the remaining even part.

1.5 The ridge movement means the bump optimizer redistributed residual rather than solving the balance
The obstruction moved from high-
∣
b
∣
∣b∣ to a broad low-
∣
b
∣
∣b∣ ridge:

q
≈
0.396
 to 
0.486
,
∣
b
∣
≈
0.27
 to 
0.315
,
q≈0.396 to 0.486,∣b∣≈0.27 to 0.315,
with a secondary ridge near

q
≈
0.576
 to 
0.630
,
∣
b
∣
≈
0.225.
q≈0.576 to 0.630,∣b∣≈0.225.
That is not a finite-difference artifact. The h-refinement and shifted grids show stability. The bump dictionary can locally lower one ridge while raising another because coordinate search makes narrow changes without a global inverse of the coupled nonlinear operator.

Concrete fix: full-matrix Gauss-Newton on a compact hard-constrained parameterization. The coupled update must solve approximately

(
J
T
J
+
λ
I
)
Δ
θ
=
−
J
T
R
(J 
T
 J+λI)Δθ=−J 
T
 R
with 
F
F, 
G
G, and possibly 
γ
,
B
γ,B in the same parameter vector. This is exactly the optimization mechanism in Methods “Second-order Optimizer,” where the paper uses Gauss-Newton with a damping coefficient and emphasizes that full-matrix information is feasible because the networks are small.

1.6 The swirl coupling was not architecturally coupled enough
The equations are coupled through

(
Γ
2
)
z
(Γ 
2
 ) 
z
 
in 
E
ψ
E 
ψ
 , and through

ψ
r
Γ
z
−
ψ
z
Γ
r
r
r
ψ 
r
 Γ 
z
 −ψ 
z
 Γ 
r
 
 
in 
E
Γ
E 
Γ
 . Optimizing sparse corrections to 
F
F and 
G
G independently is poorly conditioned. A small 
G
G-correction can demand a globally coordinated 
F
F-correction.

Concrete fix: use a shared trunk network with two output heads, one for 
F
F-blocks and one for 
G
G-blocks. The Gauss-Newton matrix must include cross-derivatives

∂
R
ψ
/
∂
θ
G
,
∂
R
Γ
/
∂
θ
F
.
∂R 
ψ
 /∂θ 
G
 ,∂R 
Γ
 /∂θ 
F
 .
Do not train 
F
F and 
G
G in alternation except as a preconditioner.

1.7 
γ
γ and 
B
B were pinned too early
The current target is

γ
=
9
20
,
B
=
1.
γ= 
20
9
 ,B=1.
The current residual scale suggests either the representation is wrong or the fixed parameters are wrong. The DeepMind paper treats the self-similar scaling parameter as part of the discovery problem. See Methods “Identifying Admissible 
λ
λ Values”: gradient training, analytic 
λ
λ-inference, and funnel inference. Figures 
\ref
f
i
g
:
l
a
m
b
f
u
n
n
e
l
p
l
o
t
\reffig:lamb 
f
 unnel 
p
 lot and 
\ref
f
i
g
:
l
a
m
b
f
u
n
n
e
l
p
l
o
t
l
o
g
l
o
g
\reffig:lamb 
f
 unnel 
p
 lot 
l
 og 
l
 og are specifically about validating admissible scaling values through residual bowls.

Concrete fix: run two branches.

First, fixed 
(
γ
,
B
)
=
(
9
/
20
,
1
)
(γ,B)=(9/20,1), to test whether the old target survives in the new architecture.

Second, train

γ
=
2
5
+
1
10
σ
(
η
γ
)
,
B
=
exp
⁡
(
η
B
)
,
γ= 
5
2
 + 
10
1
 σ(η 
γ
 ),B=exp(η 
B
 ),
or 
B
=
s
B
exp
⁡
(
η
B
)
B=s 
B
 exp(η 
B
 ) if both swirl signs are allowed. If 
γ
γ moves, update

p
=
1
γ
p= 
γ
1
 
and the forced coefficients as functions of 
γ
,
B
γ,B:

G
p
(
x
;
γ
,
B
)
=
−
B
2
γ
(
x
+
2
γ
−
1
)
,
G 
p
 (x;γ,B)=− 
2γ
B
 (x+2γ−1),
F
p
(
x
;
γ
,
B
)
=
a
0
(
γ
,
B
)
+
a
2
(
γ
)
x
,
F 
p
 (x;γ,B)=a 
0
 (γ,B)+a 
2
 (γ)x,
a
0
=
28
B
2
γ
3
+
20
B
2
γ
2
−
8
B
2
γ
+
25
γ
3
+
30
γ
2
−
27
γ
+
4
4
(
35
γ
3
+
11
γ
2
−
20
γ
+
4
)
,
a 
0
 = 
4(35γ 
3
 +11γ 
2
 −20γ+4)
28B 
2
 γ 
3
 +20B 
2
 γ 
2
 −8B 
2
 γ+25γ 
3
 +30γ 
2
 −27γ+4
 ,
a
2
=
−
15
γ
2
−
2
γ
+
1
4
γ
(
7
γ
2
+
5
γ
−
2
)
.
a 
2
 = 
4γ(7γ 
2
 +5γ−2)
−15γ 
2
 −2γ+1
 .
For 
γ
=
9
/
20
,
B
=
1
γ=9/20,B=1, this reduces to the pinned values already certified.

1.8 The old residual metric was too easy to fool
The paper defines solution quality by max d
n
n residuals on dense validation grids in Methods “Validation Metrics for Solutions.” It also warns through the use of d1/d2 losses in Methods “Training Loss” that d0-only training can create spiky residuals between collocation points.

The bump path used many finite-difference validation grids, which is good, but the optimizer itself was not driven by a d0/d1/d2 quotient residual with adaptive resampling. Coordinate search over bump amplitudes can overfit the active grid.

Concrete fix:

Train with

L
=
c
0
∥
R
∥
2
,
Y
0
2
+
c
1
∥
∇
R
∥
2
,
Y
1
2
+
c
2
∥
∇
2
R
∥
2
,
Y
2
2
+
L
g
a
u
g
e
,
L=c 
0
 ∥R∥ 
2,Y 
0
 
2
 +c 
1
 ∥∇R∥ 
2,Y 
1
 
2
 +c 
2
 ∥∇ 
2
 R∥ 
2,Y 
2
 
2
 +L 
gauge
 ,
then validate using the paper’s max d0 residual metric:

R
max
⁡
=
max
⁡
grid
,
 
k
∣
R
k
∣
.
R 
max
 = 
grid,k
max
 ∣R 
k
 ∣.
Add shifted grids, Chebyshev grids, and ridge-adaptive grids. The discovery gate is not the training loss. It is the high-precision max quotient residual.

1.9 Finite-difference residuals are discovery-only
Finite differences are acceptable for ridge diagnosis. They are not acceptable for a 
10
−
8
10 
−8
  discovery target. At that level, finite-difference truncation and cancellation near 
r
=
0
r=0, 
b
=
0
b=0, and 
q
=
0
q=0 can become the residual.

Concrete fix: define 
F
,
G
F,G, 
ψ
,
Γ
ψ,Γ, 
A
A, 
E
ψ
,
E
Γ
E 
ψ
 ,E 
Γ
  in an automatic differentiation or symbolic expression graph. Compute residual quotients directly, not by finite differencing nodal 
ψ
,
Γ
ψ,Γ. Final cold residual evaluation must be in arbitrary precision.

DeepMind analogue: their residuals are the factored 
R
k
R 
k
  in Methods “Solution Modeling and Equation Factorisation,” not raw equations evaluated with mechanically forced prefactors still attached.

1.10 Pressure consistency was downstream, not discovery-visible
The pressure-eliminated equations are equivalent only if regularity and compatibility hold. The symbolic identities

r
R
θ
=
E
Γ
,
E
ψ
=
−
r
3
(
∂
z
R
r
−
∂
r
R
z
)
rR 
θ
 =E 
Γ
 ,E 
ψ
 =−r 
3
 (∂ 
z
 R 
r
 −∂ 
r
 R 
z
 )
are valuable, but the old training loop did not include a pressure-consistency audit during discovery.

Concrete fix: during validation, compute

R
r
=
(
1
−
γ
)
u
r
+
γ
(
r
u
r
r
+
z
u
z
r
)
+
(
U
⋅
∇
)
u
r
−
(
u
θ
)
2
r
,
R 
r
 =(1−γ)u 
r
 +γ(ru 
r
r
 +zu 
z
r
 )+(U⋅∇)u 
r
 − 
r
(u 
θ
 ) 
2
 
 ,
R
z
=
(
1
−
γ
)
u
z
+
γ
(
r
u
r
z
+
z
u
z
z
)
+
(
U
⋅
∇
)
u
z
,
R 
z
 =(1−γ)u 
z
 +γ(ru 
r
z
 +zu 
z
z
 )+(U⋅∇)u 
z
 ,
R
θ
=
(
1
−
γ
)
u
θ
+
γ
(
r
u
r
θ
+
z
u
z
θ
)
+
(
u
r
∂
r
+
u
z
∂
z
)
u
θ
+
u
r
u
θ
r
.
R 
θ
 =(1−γ)u 
θ
 +γ(ru 
r
θ
 +zu 
z
θ
 )+(u 
r
 ∂ 
r
 +u 
z
 ∂ 
z
 )u 
θ
 + 
r
u 
r
 u 
θ
 
 .
Then check both

r
R
θ
=
E
Γ
rR 
θ
 =E 
Γ
 
and

∂
z
R
r
−
∂
r
R
z
=
−
E
ψ
/
r
3
∂ 
z
 R 
r
 −∂ 
r
 R 
z
 =−E 
ψ
 /r 
3
 
numerically in the same high-precision residual pass. This does not replace 
E
ψ
,
E
Γ
E 
ψ
 ,E 
Γ
 , but it catches profiles that are “good” only in a malformed quotient.

1.11 The origin chart singularity was not isolated
The coordinates

q
=
(
1
+
r
2
+
z
2
)
−
1
/
2
,
b
=
z
/
r
2
+
z
2
q=(1+r 
2
 +z 
2
 ) 
−1/2
 ,b=z/ 
r 
2
 +z 
2
 
 
are singular at 
(
r
,
z
)
=
(
0
,
0
)
(r,z)=(0,0). The bump family treated the compactified rectangle as if all corners had equal meaning. They do not. The corner 
q
=
1
q=1 collapses every 
b
b into one physical point.

Concrete fix: use two residual charts.

For tail/interior:

(
q
,
x
)
,
x
=
b
2
.
(q,x),x=b 
2
 .
For origin:

R
c
=
(
1
−
q
2
)
(
1
−
x
)
,
Z
c
=
(
1
−
q
2
)
x
.
R 
c
 =(1−q 
2
 )(1−x),Z 
c
 =(1−q 
2
 )x.
The final proof representation should be a spectral element or Bernstein element in these charts. The discovery architecture can use one global network fed by 
(
q
,
R
c
,
Z
c
)
(q,R 
c
 ,Z 
c
 ), plus a tail cutoff for naked angular tail traces.

1.12 Summary of the failure diagnosis
The prior bump path did not fail because the optimizer needed more bumps. It failed because the admissible profile is a constrained transseries/regularity object, while the bump family was a local residual sculptor. The DeepMind framework supplies the correct countermeasure: encode constraints in the coordinate map, output map, residual quotient, multistage correction hierarchy, and second-order optimizer.

Only after all of those fixes does it make sense to ask whether the admissible NS swirl branch exists near 
γ
=
9
/
20
,
B
=
1
γ=9/20,B=1.

2. Hard-constrained architecture specification
In this notation,

q
=
(
1
+
r
2
+
z
2
)
−
1
/
2
∈
(
0
,
1
]
,
q=(1+r 
2
 +z 
2
 ) 
−1/2
 ∈(0,1],
so physical infinity is 
q
→
0
q→0, not 
q
→
∞
q→∞. The other endpoint 
q
→
1
q→1 is the physical origin. The prompt’s “
q
→
∞
q→∞” is therefore treated as the far-field condition 
ρ
=
r
2
+
z
2
→
∞
ρ= 
r 
2
 +z 
2
 
 →∞, equivalently 
q
→
0
q→0.

Let

x
=
b
2
,
b
=
z
ρ
,
S
=
1
−
q
2
,
x=b 
2
 ,b= 
ρ
z
 ,S=1−q 
2
 ,
X
=
S
x
,
Y
=
S
(
1
−
x
)
.
X=Sx,Y=S(1−x).
Near the origin,

X
∼
z
2
,
Y
∼
r
2
.
X∼z 
2
 ,Y∼r 
2
 .
This is the central trick: a smooth network in 
(
q
,
X
,
Y
)
(q,X,Y) sees angular information only through variables that vanish correctly at the origin.

2.1 Output fields
Use

ψ
=
r
2
z
q
p
F
(
q
,
x
)
,
Γ
=
r
2
q
p
G
(
q
,
x
)
,
p
=
1
γ
.
ψ=r 
2
 zq 
p
 F(q,x),Γ=r 
2
 q 
p
 G(q,x),p= 
γ
1
 .
At 
γ
=
9
/
20
γ=9/20,

p
=
20
9
.
p= 
9
20
 .
The velocity is then

u
r
=
−
ψ
z
r
,
u
z
=
ψ
r
r
,
u
θ
=
Γ
r
.
u 
r
 =− 
r
ψ 
z
 
 ,u 
z
 = 
r
ψ 
r
 
 ,u 
θ
 = 
r
Γ
 .
The prefactors 
r
2
z
r 
2
 z and 
r
2
r 
2
  enforce the basic axis behavior. The origin input variables 
(
q
,
X
,
Y
)
(q,X,Y) enforce smooth angular collapse at 
q
=
1
q=1.

2.2 Tail cutoff for pinned angular transseries terms
Define

Θ
T
(
q
)
=
(
1
−
q
2
)
M
.
Θ 
T
 (q)=(1−q 
2
 ) 
M
 .
Take

M
=
6
M=6
for discovery. This gives

Θ
T
(
0
)
=
1
,
Θ 
T
 (0)=1,
so the tail coefficient is unchanged, and

Θ
T
(
1
)
=
0
Θ 
T
 (1)=0
to high order, so angular tail traces do not contaminate the origin.

This is not a soft penalty. It is a hard output prefactor.

2.3 Fixed-
γ
γ architecture
For the fixed test

γ
=
9
20
,
B
=
1
,
γ= 
20
9
 ,B=1,
use

F
(
q
,
x
)
=
1
2
+
q
2
A
F
(
q
,
X
,
Y
)
+
q
20
/
9
Θ
T
(
q
)
[
F
p
(
x
)
+
q
C
F
(
q
,
X
,
Y
)
]
+
q
40
/
9
Θ
T
(
q
)
D
F
(
q
,
X
,
Y
)
+
∑
j
=
3
J
q
20
j
/
9
Θ
T
(
q
)
H
F
,
j
(
q
,
X
,
Y
)
,
F(q,x)= 
2
1
 +q 
2
 A 
F
 (q,X,Y)+q 
20/9
 Θ 
T
 (q)[F 
p
 (x)+qC 
F
 (q,X,Y)]+q 
40/9
 Θ 
T
 (q)D 
F
 (q,X,Y)+ 
j=3
∑
J
 q 
20j/9
 Θ 
T
 (q)H 
F,j
 (q,X,Y),
G
(
q
,
x
)
=
1
+
q
2
A
G
(
q
,
X
,
Y
)
+
q
20
/
9
Θ
T
(
q
)
[
G
p
(
x
)
+
q
C
G
(
q
,
X
,
Y
)
]
+
q
40
/
9
Θ
T
(
q
)
D
G
(
q
,
X
,
Y
)
+
∑
j
=
3
J
q
20
j
/
9
Θ
T
(
q
)
H
G
,
j
(
q
,
X
,
Y
)
.
G(q,x)=1+q 
2
 A 
G
 (q,X,Y)+q 
20/9
 Θ 
T
 (q)[G 
p
 (x)+qC 
G
 (q,X,Y)]+q 
40/9
 Θ 
T
 (q)D 
G
 (q,X,Y)+ 
j=3
∑
J
 q 
20j/9
 Θ 
T
 (q)H 
G,j
 (q,X,Y).
The pinned pieces are

G
p
(
x
)
=
1
9
−
10
9
x
,
G 
p
 (x)= 
9
1
 − 
9
10
 x,
F
p
(
x
)
=
230733
120060
−
117500
120060
x
.
F 
p
 (x)= 
120060
230733
 − 
120060
117500
 x.
There is no 
q
1
q 
1
  block.

The analytic block begins at 
q
2
q 
2
 , so

F
(
0
,
x
)
=
1
2
,
G
(
0
,
x
)
=
1
,
F(0,x)= 
2
1
 ,G(0,x)=1,
and

∂
q
F
o
r
d
i
n
a
r
y
(
0
,
x
)
=
∂
q
G
o
r
d
i
n
a
r
y
(
0
,
x
)
=
0
∂ 
q
 F 
ordinary
 (0,x)=∂ 
q
 G 
ordinary
 (0,x)=0
structurally.

2.4 Free-
γ
,
B
γ,B architecture
If 
γ
,
B
γ,B are trained, use

γ
=
2
5
+
1
10
σ
(
η
γ
)
,
γ= 
5
2
 + 
10
1
 σ(η 
γ
 ),
which enforces

2
5
<
γ
<
1
2
.
5
2
 <γ< 
2
1
 .
Use either

B
=
exp
⁡
(
η
B
)
B=exp(η 
B
 )
for positive swirl orientation, or

B
=
s
B
exp
⁡
(
η
B
)
,
s
B
∈
{
−
1
,
+
1
}
,
B=s 
B
 exp(η 
B
 ),s 
B
 ∈{−1,+1},
if both orientations are searched.

Then

p
=
1
γ
p= 
γ
1
 
and

F
p
,
G
p
F 
p
 ,G 
p
 
are recomputed as analytic functions of 
(
γ
,
B
)
(γ,B), using the formulas in Section 1.7. The output remains exactly q1-free for every admissible 
γ
γ.

2.5 Network blocks
Use a shared trunk

T
θ
(
q
,
X
,
Y
)
T 
θ
 (q,X,Y)
and block heads

A
F
,
A
G
,
C
F
,
C
G
,
D
F
,
D
G
,
…
A 
F
 ,A 
G
 ,C 
F
 ,C 
G
 ,D 
F
 ,D 
G
 ,…
so that 
F
F and 
G
G receive coupled updates.

Recommended stage-0 trunk:

3
→
64
→
64
→
64
→
64
→
64
3→64→64→64→64→64
with 
tanh
⁡
tanh activations and two-headed linear outputs. This is small enough for a full or block-full Gauss-Newton matrix.

Recommended correction-stage trunk:

3
→
64
→
64
→
64
→
64
3→64→64→64→64
with Fourier features inserted after the first affine layer if the residual spectrum demands it. This follows Methods “Multi-stage Training,” where the paper uses Fourier features for stage-2 residuals and sets the Fourier scale from the dominant residual frequency.

Activation choice:

Use 
tanh
⁡
tanh. The residual contains up to third derivatives of 
ψ
ψ, because 
A
A is second order and 
A
r
,
A
z
A 
r
 ,A 
z
  enter 
E
ψ
E 
ψ
 . Tanh is 
C
∞
C 
∞
  and stable under repeated automatic differentiation. Avoid ReLU, GELU with low-precision derivative noise, and nonsmooth activations.

Final layer:

Use linear outputs for correction fields. Do not use a pure exponential output globally, because 
F
F-correction components can change sign. A scaled sinh or linear head is safer. The paper mentions exponential or exponential-adjacent final layers in Methods “Solution Modeling and Equation Factorisation” for fields varying over many orders of magnitude; here use only local amplitude rescalings, not positivity constraints, unless a particular component is proven sign-definite.

2.6 Initialization
Initialize the analytic blocks from the projected v117 seed if available. Otherwise:

A
F
,
A
G
,
C
F
,
C
G
,
D
F
,
D
G
=
0
A 
F
 ,A 
G
 ,C 
F
 ,C 
G
 ,D 
F
 ,D 
G
 =0
except for the pinned 
F
p
,
G
p
F 
p
 ,G 
p
 .

For free-
γ
,
B
γ,B, initialize

η
γ
=
0
η 
γ
 =0
so

γ
=
0.45
,
γ=0.45,
and

η
B
=
0
η 
B
 =0
so

B
=
1.
B=1.
Use small Xavier or orthogonal initialization with output scale 
10
−
3
10 
−3
  for correction heads. The pinned fractional terms already give the optimizer a tail-correct leading structure.

3. Loss and residual definition
The zero condition is the pressure-eliminated profile system:

E
ψ
=
0
,
E
Γ
=
0
,
E 
ψ
 =0,E 
Γ
 =0,
where

A
=
ψ
r
r
−
r
−
1
ψ
r
+
ψ
z
z
,
A=ψ 
rr
 −r 
−1
 ψ 
r
 +ψ 
zz
 ,
E
ψ
=
(
1
−
γ
)
r
2
A
+
γ
r
3
A
r
+
γ
z
r
2
A
z
+
r
(
ψ
r
A
z
−
ψ
z
A
r
)
+
2
ψ
z
A
+
(
Γ
2
)
z
,
E 
ψ
 =(1−γ)r 
2
 A+γr 
3
 A 
r
 +γzr 
2
 A 
z
 +r(ψ 
r
 A 
z
 −ψ 
z
 A 
r
 )+2ψ 
z
 A+(Γ 
2
 ) 
z
 ,
E
Γ
=
(
1
−
2
γ
)
Γ
+
γ
(
r
Γ
r
+
z
Γ
z
)
+
ψ
r
Γ
z
−
ψ
z
Γ
r
r
.
E 
Γ
 =(1−2γ)Γ+γ(rΓ 
r
 +zΓ 
z
 )+ 
r
ψ 
r
 Γ 
z
 −ψ 
z
 Γ 
r
 
 .
Derivatives are computed by automatic differentiation from

q
r
=
−
r
q
3
,
q
z
=
−
z
q
3
,
q 
r
 =−rq 
3
 ,q 
z
 =−zq 
3
 ,
x
r
=
−
2
r
x
r
2
+
z
2
,
x
z
=
2
z
(
1
−
x
)
r
2
+
z
2
,
x 
r
 =− 
r 
2
 +z 
2
 
2rx
 ,x 
z
 = 
r 
2
 +z 
2
 
2z(1−x)
 ,
or directly by differentiating 
ψ
(
r
,
z
)
,
Γ
(
r
,
z
)
ψ(r,z),Γ(r,z) with 
q
,
r
,
z
q,r,z as primitive variables.

3.1 Residual quotient
Use the raw equations only for identity checks. Optimize quotient residuals.

For the tail/interior chart, define

ρ
=
r
2
+
z
2
,
x
=
b
2
.
ρ= 
r 
2
 +z 
2
 
 ,x=b 
2
 .
The leading conical scales are

E
Γ
∼
ρ
2
−
2
p
(
1
−
x
)
,
E 
Γ
 ∼ρ 
2−2p
 (1−x),
E
ψ
∼
ρ
3
−
2
p
b
(
1
−
x
)
2
.
E 
ψ
 ∼ρ 
3−2p
 b(1−x) 
2
 .
Define

R
Γ
=
ρ
2
p
−
2
1
−
x
E
Γ
,
R 
Γ
 = 
1−x
ρ 
2p−2
 
 E 
Γ
 ,
and

R
ψ
=
ρ
2
p
−
3
b
(
1
−
x
)
2
E
ψ
.
R 
ψ
 = 
b(1−x) 
2
 
ρ 
2p−3
 
 E 
ψ
 .
Since 
E
ψ
E 
ψ
  is odd in 
b
b, 
R
ψ
R 
ψ
  is evaluated as the even quotient in 
x
=
b
2
x=b 
2
 . At 
b
=
0
b=0, use the symbolic odd factorization, not numerical division by 
b
b.

At 
x
=
1
x=1, use the symbolic axis quotient, not pointwise division by 
1
−
x
1−x. This is exactly the DeepMind residual-factorization pattern:

E
k
=
F
k
R
k
E 
k
 =F 
k
 R 
k
 
from Methods “Solution Modeling and Equation Factorisation.”

For the origin chart, evaluate the same raw equations in 
(
R
c
,
Z
c
)
(R 
c
 ,Z 
c
 ) and divide by the Taylor-leading regular factors obtained from the expression graph. The origin quotient must be checked independently because 
(
q
,
b
)
(q,b) is singular at 
ρ
=
0
ρ=0.

3.2 Normalized discovery metric
The scale is fixed by

F
0
=
1
2
,
G
0
=
1
F 
0
 = 
2
1
 ,G 
0
 =1
or by 
(
F
0
,
G
0
,
B
)
(F 
0
 ,G 
0
 ,B) in the free-
B
B branch. Therefore the validation metric is the absolute max quotient residual

R
max
⁡
=
max
⁡
validation grid
(
∣
R
ψ
∣
,
 
∣
R
Γ
∣
)
.
R 
max
 = 
validation grid
max
 (∣R 
ψ
 ∣, ∣R 
Γ
 ∣).
The discovery gate is

R
max
⁡
<
10
−
8
R 
max
 <10 
−8
 
in high precision on independent grids.

For training stability, also use a relative residual

R
k
r
e
l
=
R
k
ϵ
+
∑
j
∣
T
k
,
j
q
u
o
t
∣
,
R 
k
rel
 = 
ϵ+∑ 
j
 ∣T 
k,j
quot
 ∣
R 
k
 
 ,
where 
T
k
,
j
q
u
o
t
T 
k,j
quot
  are the individual quotient-scaled terms of the equation. But the pass/fail metric remains the absolute quotient residual.

3.3 Training loss
Use the paper’s d0/d1/d2 pattern from Methods “Training Loss”:

L
d
0
=
1
N
0
∑
y
∈
Y
0
w
y
(
R
ψ
(
y
)
2
+
R
Γ
(
y
)
2
)
,
L 
d0
 = 
N 
0
 
1
  
y∈Y 
0
 
∑
 w 
y
 (R 
ψ
 (y) 
2
 +R 
Γ
 (y) 
2
 ),
L
d
1
=
1
N
1
∑
y
∈
Y
1
w
y
∑
ξ
∈
{
q
,
x
}
(
∣
∂
ξ
R
ψ
(
y
)
∣
2
+
∣
∂
ξ
R
Γ
(
y
)
∣
2
)
,
L 
d1
 = 
N 
1
 
1
  
y∈Y 
1
 
∑
 w 
y
  
ξ∈{q,x}
∑
 (∣∂ 
ξ
 R 
ψ
 (y)∣ 
2
 +∣∂ 
ξ
 R 
Γ
 (y)∣ 
2
 ),
L
d
2
=
1
N
2
∑
y
∈
Y
2
w
y
∑
ξ
,
η
∈
{
q
,
x
}
(
∣
∂
ξ
η
R
ψ
(
y
)
∣
2
+
∣
∂
ξ
η
R
Γ
(
y
)
∣
2
)
.
L 
d2
 = 
N 
2
 
1
  
y∈Y 
2
 
∑
 w 
y
  
ξ,η∈{q,x}
∑
 (∣∂ 
ξη
 R 
ψ
 (y)∣ 
2
 +∣∂ 
ξη
 R 
Γ
 (y)∣ 
2
 ).
Then

L
=
c
0
L
d
0
+
c
1
L
d
1
+
c
2
L
d
2
+
L
g
a
u
g
e
.
L=c 
0
 L 
d0
 +c 
1
 L 
d1
 +c 
2
 L 
d2
 +L 
gauge
 .
Use initial weights

c
0
=
1
,
c
1
=
10
−
2
,
c
2
=
10
−
4
.
c 
0
 =1,c 
1
 =10 
−2
 ,c 
2
 =10 
−4
 .
Increase 
c
1
,
c
2
c 
1
 ,c 
2
  only if shifted-grid residuals show spikes.

3.4 Collocation distribution
Use five point groups.

Global Chebyshev group:

q
i
=
1
2
(
1
−
cos
⁡
(
i
π
/
N
q
)
)
,
x
j
=
1
2
(
1
−
cos
⁡
(
j
π
/
N
x
)
)
.
q 
i
 = 
2
1
 (1−cos(iπ/N 
q
 )),x 
j
 = 
2
1
 (1−cos(jπ/N 
x
 )).
Shifted validation group:

q
i
=
1
2
(
1
−
cos
⁡
(
(
i
+
1
/
2
)
π
/
N
q
)
)
,
x
j
=
1
2
(
1
−
cos
⁡
(
(
j
+
1
/
2
)
π
/
N
x
)
)
.
q 
i
 = 
2
1
 (1−cos((i+1/2)π/N 
q
 )),x 
j
 = 
2
1
 (1−cos((j+1/2)π/N 
x
 )).
Known ridge group:

q
∈
[
0.38
,
0.65
]
,
x
=
b
2
∈
[
0.045
,
0.11
]
.
q∈[0.38,0.65],x=b 
2
 ∈[0.045,0.11].
Tail group:

q
∈
[
0
,
0.12
]
,
x
∈
[
0
,
1
]
.
q∈[0,0.12],x∈[0,1].
Origin group:

q
∈
[
0.88
,
1
]
,
R
c
,
Z
c
 sampled directly
.
q∈[0.88,1],R 
c
 ,Z 
c
  sampled directly.
Adaptive group:

Build a dense grid, evaluate

W
(
y
)
=
(
R
ψ
(
y
)
2
+
R
Γ
(
y
)
2
+
λ
1
∣
∇
R
(
y
)
∣
2
)
2
,
W(y)=(R 
ψ
 (y) 
2
 +R 
Γ
 (y) 
2
 +λ 
1
 ∣∇R(y)∣ 
2
 ) 
2
 ,
then sample proportionally to 
W
W. This is adapted from Methods “Training Collocation Points,” where the paper combines location-based sampling with adaptive sampling from residual-dependent weights. The paper mentions, for Boussinesq, a weight proportional to a fourth power of a squared residual sum; NSProof should use the same shape but with the quotient residuals.

3.5 What the max residual metric misses
The paper’s max d0 residual metric is necessary but not sufficient. It is insensitive to:

Off-grid spikes. Compensation: shifted grids, adaptive grids, d1/d2 losses, and final Chebyshev/Bernstein projection.

Wrong asymptotic branch. Compensation: structural q1 absence and forced 
q
p
q 
p
  pins.

Wrong 
γ
γ. Compensation: funnel inference and fixed-
γ
γ residual bowl.

Pressure non-integrability. Compensation: pressure identity and one-form closure audit.

Spectral instability. Compensation: projected spectral pass, not PINN eigenvalue discovery alone.

Interval proof failure. Compensation: export to proof-native Chebyshev/Bernstein coefficients and run NK.

4. Optimization schedule
The training objective has the form

h
(
θ
)
=
1
2
∥
f
(
θ
)
∥
2
2
,
h(θ)= 
2
1
 ∥f(θ)∥ 
2
2
 ,
where 
f
f stacks d0/d1/d2 residuals and gauge constraints. The Gauss-Newton step is

(
J
T
J
+
λ
I
)
Δ
θ
=
−
J
T
f
,
(J 
T
 J+λI)Δθ=−J 
T
 f,
with

J
=
∂
f
∂
θ
.
J= 
∂θ
∂f
 .
This is the direct transfer of Methods “Second-order Optimizer,” where the paper uses Gauss-Newton and Levenberg-Marquardt-style damping.

4.1 Jacobian assembly
Use autodiff for 
J
J. Do not finite-difference the network parameters.

Memory layout:

Stack residuals as

f
=
[
R
ψ
(
Y
0
)
,
R
Γ
(
Y
0
)
,
c
1
∇
R
ψ
(
Y
1
)
,
c
1
∇
R
Γ
(
Y
1
)
,
c
2
∇
2
R
ψ
(
Y
2
)
,
c
2
∇
2
R
Γ
(
Y
2
)
,
f
g
a
u
g
e
]
.
f=[R 
ψ
 (Y 
0
 ),R 
Γ
 (Y 
0
 ), 
c 
1
 
 ∇R 
ψ
 (Y 
1
 ), 
c 
1
 
 ∇R 
Γ
 (Y 
1
 ), 
c 
2
 
 ∇ 
2
 R 
ψ
 (Y 
2
 ), 
c 
2
 
 ∇ 
2
 R 
Γ
 (Y 
2
 ),f 
gauge
 ].
Use block accumulation of

G
=
J
T
J
,
g
=
J
T
f
G=J 
T
 J,g=J 
T
 f
over collocation batches. If the parameter count exceeds about 
2
×
10
4
2×10 
4
 , switch to block-Gauss-Newton by stage head, but keep 
F
/
G
F/G cross-blocks.

Rank deficiencies expected:

Geometric center/translation modes.

Amplitude/gauge modes if 
B
B and normalization are not pinned.

Tail modes if 
γ
γ is trainable but forced coefficients are not updated consistently.

Flat residual valleys from q1-near modes.

Handle them with:

SVD or pivoted Cholesky threshold

σ
i
/
σ
max
⁡
<
10
−
12
σ 
i
 /σ 
max
 <10 
−12
 
in float64, stricter in high precision;

explicit gauge constraints;

γ
,
B
γ,B bounds;

and q1 structural removal.

4.2 LM damping schedule
Let

λ
L
M
λ 
LM
 
be the damping parameter. Start with

λ
L
M
=
10
−
3
∥
J
T
J
∥
∞
.
λ 
LM
 =10 
−3
 ∥J 
T
 J∥ 
∞
 .
Compute the predicted decrease

m
(
0
)
−
m
(
Δ
θ
)
m(0)−m(Δθ)
and actual decrease

h
(
θ
)
−
h
(
θ
+
Δ
θ
)
.
h(θ)−h(θ+Δθ).
Define

ρ
g
a
i
n
=
h
(
θ
)
−
h
(
θ
+
Δ
θ
)
m
(
0
)
−
m
(
Δ
θ
)
.
ρ 
gain
 = 
m(0)−m(Δθ)
h(θ)−h(θ+Δθ)
 .
Accept the step if

ρ
g
a
i
n
>
0.1
ρ 
gain
 >0.1
and the validation mini-grid residual does not increase by more than a factor 
1.5
1.5.

Update:

If 
ρ
g
a
i
n
>
0.75
ρ 
gain
 >0.75,

λ
L
M
←
λ
L
M
/
3.
λ 
LM
 ←λ 
LM
 /3.
If 
0.1
<
ρ
g
a
i
n
≤
0.75
0.1<ρ 
gain
 ≤0.75, keep it.

If 
ρ
g
a
i
n
≤
0.1
ρ 
gain
 ≤0.1, reject and set

λ
L
M
←
10
λ
L
M
.
λ 
LM
 ←10λ 
LM
 .
4.3 Line search
After the LM step, run a short line search over

α
∈
{
1
,
1
/
2
,
1
/
4
,
1
/
8
,
1
/
16
}
.
α∈{1,1/2,1/4,1/8,1/16}.
Choose the largest 
α
α satisfying

R
max
⁡
t
r
a
i
n
−
c
h
e
c
k
(
θ
+
α
Δ
θ
)
<
0.98
R
max
⁡
t
r
a
i
n
−
c
h
e
c
k
(
θ
)
R 
max
train−check
 (θ+αΔθ)<0.98R 
max
train−check
 (θ)
or, if the residual is already below 
10
−
6
10 
−6
 ,

R
max
⁡
t
r
a
i
n
−
c
h
e
c
k
(
θ
+
α
Δ
θ
)
<
1.05
R
max
⁡
t
r
a
i
n
−
c
h
e
c
k
(
θ
)
R 
max
train−check
 (θ+αΔθ)<1.05R 
max
train−check
 (θ)
and the RMS residual decreases.

4.4 Stage convergence
Do not use iteration count.

Declare stage 
k
k plateaued if all are true:

Over five resampling cycles, the best independent-grid 
log
⁡
10
R
max
⁡
log 
10
 R 
max
  improves by less than 
0.1
0.1.

The active-grid RMS residual improves by less than 
20
%
20%.

The largest residual lobe remains spatially coherent under shifted-grid validation.

The LM damping repeatedly grows without a successful full step.

At plateau, freeze the stage.

4.5 Multistage correction
After freezing

Φ
(
k
)
=
(
F
(
k
)
,
G
(
k
)
)
,
Φ 
(k)
 =(F 
(k)
 ,G 
(k)
 ),
compute the residual

R
(
k
)
=
(
R
ψ
(
k
)
,
R
Γ
(
k
)
)
.
R 
(k)
 =(R 
ψ
(k)
 ,R 
Γ
(k)
 ).
Fit the leading q-exponent on tail slices:

α
ψ
(
x
)
=
d
log
⁡
∣
R
ψ
(
q
,
x
)
∣
d
log
⁡
q
,
α
Γ
(
x
)
=
d
log
⁡
∣
R
Γ
(
q
,
x
)
∣
d
log
⁡
q
.
α 
ψ
 (x)= 
dlogq
dlog∣R 
ψ
 (q,x)∣
 ,α 
Γ
 (x)= 
dlogq
dlog∣R 
Γ
 (q,x)∣
 .
Cluster the dominant slopes and choose the next exponent

α
k
+
1
α 
k+1
 
from the allowed semigroup

Λ
=
{
n
+
m
p
:
 
n
∈
N
,
 
n
≠
1
,
 
m
∈
N
0
}
∪
{
m
p
:
 
m
≥
1
}
.
Λ={n+mp: n∈N, n

=1, m∈N 
0
 }∪{mp: m≥1}.
Then add

δ
F
(
k
+
1
)
=
ϵ
k
q
α
k
+
1
Θ
T
(
q
)
N
F
(
k
+
1
)
(
q
,
X
,
Y
)
,
δF 
(k+1)
 =ϵ 
k
 q 
α 
k+1
 
 Θ 
T
 (q)N 
F
(k+1)
 (q,X,Y),
δ
G
(
k
+
1
)
=
ϵ
k
q
α
k
+
1
Θ
T
(
q
)
N
G
(
k
+
1
)
(
q
,
X
,
Y
)
,
δG 
(k+1)
 =ϵ 
k
 q 
α 
k+1
 
 Θ 
T
 (q)N 
G
(k+1)
 (q,X,Y),
unless the fitted residual is interior-dominated. For an interior ridge, use

δ
F
(
k
+
1
)
=
ϵ
k
q
2
N
F
(
k
+
1
)
(
q
,
X
,
Y
)
,
δF 
(k+1)
 =ϵ 
k
 q 
2
 N 
F
(k+1)
 (q,X,Y),
δ
G
(
k
+
1
)
=
ϵ
k
q
2
N
G
(
k
+
1
)
(
q
,
X
,
Y
)
.
δG 
(k+1)
 =ϵ 
k
 q 
2
 N 
G
(k+1)
 (q,X,Y).
Choose

ϵ
k
=
10
⌊
log
⁡
10
R
max
⁡
(
k
)
⌋
.
ϵ 
k
 =10 
⌊log 
10
 R 
max
(k)
 ⌋
 .
This makes the correction network order-one.

For high-frequency residuals, use Fourier features as in Methods “Multi-stage Training”:

φ
(
y
)
=
[
cos
⁡
(
B
y
)
,
sin
⁡
(
B
y
)
]
,
φ(y)=[cos(By),sin(By)],
with

σ
B
=
2
π
f
d
(
e
)
,
σ 
B
 =2πf 
d
(e)
 ,
where 
f
d
(
e
)
f 
d
(e)
  is the dominant residual frequency measured in 
(
q
,
x
)
(q,x).

4.6 Global target
The discovery pass succeeds only if

R
max
⁡
<
10
−
8
R 
max
 <10 
−8
 
on:

training grid,

shifted grid,

Chebyshev validation grid,

known-ridge grid,

tail grid,

origin chart grid,

and arbitrary-precision cold re-evaluation.

If any grid gives 
R
max
⁡
≥
10
−
8
R 
max
 ≥10 
−8
 , the exact-profile gate is not open.

5. Precision plan
5.1 Float32 warm start
Use float32 only for broad exploration:

fixed 
γ
,
B
γ,B versus free 
γ
,
B
γ,B,

architecture width/depth,

collocation strategy,

ridge migration.

Exit float32 once

R
max
⁡
<
10
−
3
R 
max
 <10 
−3
 
or once the residual stops improving. Float32 cannot certify 
10
−
8
10 
−8
 . It is only a scout.

Estimated cost: hours on one modern GPU for 
5
5 to 
20
20 seeds, depending on collocation size.

5.2 Float64 main discovery
Run the serious Gauss-Newton solve in float64.

Switch to float64 no later than

R
max
⁡
=
10
−
3
.
R 
max
 =10 
−3
 .
Main target in float64:

R
max
⁡
<
10
−
9
R 
max
 <10 
−9
 
on independent grids.

Why 
10
−
9
10 
−9
  rather than 
10
−
8
10 
−8
 : the arbitrary-precision audit usually reveals hidden cancellation and grid differences. A one-decade margin is the minimum.

Estimated cost: one to four high-end GPUs for 
12
12 to 
72
72 hours per serious branch, assuming 
10
4
10 
4
  to 
2
×
10
4
2×10 
4
  parameters and 
10
4
10 
4
  to 
10
5
10 
5
  collocation points accumulated in batches.

5.3 Arbitrary precision audit
Export the trained profile to a Chebyshev/Bernstein or rational coefficient representation. Do not audit only the neural network weights. Neural networks are poor proof objects.

Use one of:

Julia BigFloat at 192 or 256 bits;

Arb through python-flint;

C++ Arb for final interval-style evaluation.

Cold-floor precision:

256
 bits
256 bits
for final residual audit.

Evaluate:

R
max
⁡
256
b
i
t
R 
max
256bit
 
on all validation grids and on random high-precision points.

Pass condition:

R
max
⁡
256
b
i
t
<
10
−
8
.
R 
max
256bit
 <10 
−8
 .
NK-preferred condition:

R
max
⁡
256
b
i
t
<
10
−
10
.
R 
max
256bit
 <10 
−10
 .
If float64 says 
10
−
9
10 
−9
  but 256-bit says 
10
−
6
10 
−6
 , the float64 result was numerical glassware, not a profile.

Estimated cost: CPU-heavy. Dense audit is hours. Coefficient projection and interval prevalidation can be one to three days.

5.4 Final discovery artifact
The final discovery artifact must contain:

γ
,
 
B
,
γ, B,
all architecture parameters,

Chebyshev/Bernstein projection coefficients,

explicit 
F
p
,
G
p
F 
p
 ,G 
p
  constants or formulas,

all residual quotient definitions,

validation grids,

high-precision residual reports,

and a q1-channel extraction report proving

F
q
1
=
G
q
1
=
0
F 
q 
1
 
 =G 
q 
1
 
 =0
structurally and numerically.

6. Downstream-gate handoff
A residual 
<
10
−
8
<10 
−8
  is not a proof. It only opens the Newton-Kantorovich door.

6.1 Pressure reconstruction handoff
Given a discovered profile, compute

U
=
(
u
r
,
u
θ
,
u
z
)
U=(u 
r
 ,u 
θ
 ,u 
z
 )
from

u
r
=
−
ψ
z
r
,
u
z
=
ψ
r
r
,
u
θ
=
Γ
r
.
u 
r
 =− 
r
ψ 
z
 
 ,u 
z
 = 
r
ψ 
r
 
 ,u 
θ
 = 
r
Γ
 .
Define

R
(
U
)
=
(
1
−
γ
)
U
+
γ
(
y
⋅
∇
)
U
+
(
U
⋅
∇
)
U
.
R(U)=(1−γ)U+γ(y⋅∇)U+(U⋅∇)U.
In cylindrical components, include the usual curvature terms, especially

−
(
u
θ
)
2
r
− 
r
(u 
θ
 ) 
2
 
 
in the radial equation and

u
r
u
θ
r
r
u 
r
 u 
θ
 
 
in the swirl equation.

Validate:

r
R
θ
=
E
Γ
,
rR 
θ
 =E 
Γ
 ,
E
ψ
=
−
r
3
(
∂
z
R
r
−
∂
r
R
z
)
.
E 
ψ
 =−r 
3
 (∂ 
z
 R 
r
 −∂ 
r
 R 
z
 ).
Then reconstruct pressure from

P
r
=
−
R
r
,
P
z
=
−
R
z
.
P 
r
 =−R 
r
 ,P 
z
 =−R 
z
 .
Discovery-level pressure gate:

max
⁡
∣
R
Γ
q
u
o
t
∣
<
10
−
8
,
max∣R 
Γ
quot
 ∣<10 
−8
 ,
max
⁡
∣
R
ψ
q
u
o
t
∣
<
10
−
8
,
max∣R 
ψ
quot
 ∣<10 
−8
 ,
max
⁡
∣
∂
z
R
r
−
∂
r
R
z
+
E
ψ
/
r
3
∣
q
u
o
t
<
10
−
9
,
max∣∂ 
z
 R 
r
 −∂ 
r
 R 
z
 +E 
ψ
 /r 
3
 ∣ 
quot
 <10 
−9
 ,
max
⁡
∣
r
R
θ
−
E
Γ
∣
q
u
o
t
<
10
−
9
.
max∣rR 
θ
 −E 
Γ
 ∣ 
quot
 <10 
−9
 .
Proof-level pressure gate:

interval certificate that

∂
r
P
+
R
r
=
0
,
∂
z
P
+
R
z
=
0
,
R
θ
=
0
∂ 
r
 P+R 
r
 =0,∂ 
z
 P+R 
z
 =0,R 
θ
 =0
inside the NK ball.

6.2 Spectral handoff artifacts
The spectral pass needs more than weights. It needs derivative tensors and a pressure-projection-compatible representation.

Export:

Profile coefficients for 
F
,
G
F,G in proof-native basis.

Velocity coefficients for

u
r
,
u
θ
,
u
z
.
u 
r
 ,u 
θ
 ,u 
z
 .
Derivative tensors up to order 
k
+
2
k+2, with 
k
≥
6
k≥6 for the intended Banach space.

Pressure reconstruction coefficients.

Coefficient-space multiplication operators by

U
∗
,
∇
U
∗
.
U 
∗
 ,∇U 
∗
 .
Divergence operator 
D
D, gradient operator 
G
G, scalar Laplacian 
Δ
m
Δ 
m
  in each azimuthal mode 
m
m.

Leray projection operator

P
m
=
I
−
G
m
Δ
m
−
1
D
m
P 
m
 =I−G 
m
 Δ 
m
−1
 D 
m
 
or an equivalent divergence-free basis.

The true linearized 
m
m-block operator:

L
m
v
=
−
P
m
[
(
1
−
γ
)
v
+
γ
(
y
⋅
∇
)
v
+
(
U
∗
⋅
∇
)
v
+
(
v
⋅
∇
)
U
∗
]
.
L 
m
 v=−P 
m
 [(1−γ)v+γ(y⋅∇)v+(U 
∗
 ⋅∇)v+(v⋅∇)U 
∗
 ].
Geometric mode targets:

V
T
=
(
1
−
γ
)
U
∗
+
γ
(
y
⋅
∇
)
U
∗
,
μ
=
1
,
V 
T
 =(1−γ)U 
∗
 +γ(y⋅∇)U 
∗
 ,μ=1,
V
j
=
∂
y
j
U
∗
,
μ
=
γ
,
V 
j
 =∂ 
y 
j
 
 U 
∗
 ,μ=γ,
V
Ω
=
Ω
U
∗
−
(
Ω
y
)
⋅
∇
U
∗
,
μ
=
0.
V 
Ω
 =ΩU 
∗
 −(Ωy)⋅∇U 
∗
 ,μ=0.
The discovery spectral probe can follow Methods “Spectrum of Linearization,” where the paper trains PINNs for eigenvalue residuals, but the NS proof cannot stop there. The paper explicitly assumes the relevant nonnegative eigenvalues lie on the real axis in that spectral discovery subsection. For NSProof, the validation pass must count complex spectrum through Evans/Galerkin contours.

High-frequency and large-
∣
m
∣
∣m∣ plan:

Use weighted divergence-free space

X
η
,
k
d
i
v
,
η
=
1
,
k
≥
6.
X 
η,k
div
 ,η=1,k≥6.
At 
γ
=
9
/
20
γ=9/20,

(
1
−
γ
)
−
γ
η
=
1
10
.
(1−γ)−γη= 
10
1
 .
So the best tail essential gap target is below 
0.1
0.1. Start with

c
=
0.02.
c=0.02.
Need:

large-
∣
m
∣
∣m∣ exclusion,

high-frequency symbol/symmetrizer inequality,

finite 
m
m-block contour resolvent validation,

geometric-mode residual validation.

7. Risk register
Risk 1. Network converges to a non-admissible branch
Symptoms:

The q1 extractor finds nonzero ordinary 
q
1
q 
1
 .

The forced 
q
p
q 
p
  coefficient disagrees with the pinned recurrence.

γ
γ exits 
(
2
/
5
,
1
/
2
)
(2/5,1/2) unless constrained.

B
B flips sign unexpectedly.

The tail residual improves only when illegal exponents are added.

Detection:

Run tail-channel extraction after every stage:

F
(
q
,
x
)
−
1
2
=
q
F
1
(
x
)
+
q
2
F
2
(
x
)
+
q
p
F
p
(
x
)
+
⋯
 
.
F(q,x)− 
2
1
 =qF 
1
 (x)+q 
2
 F 
2
 (x)+q 
p
 F 
p
 (x)+⋯.
Check

F
1
=
G
1
=
0
F 
1
 =G 
1
 =0
and pinned 
F
p
,
G
p
F 
p
 ,G 
p
 .

Recovery:

Delete illegal channels from the architecture.

Constrain 
γ
γ by sigmoid.

Use funnel inference around the candidate 
γ
γ.

Restart with explicit 
(
γ
,
B
)
(γ,B) branch search.

Risk 2. Gauss-Newton stagnates in the same flat basin as the bump family
Symptoms:

Residual stalls around 
10
−
1
10 
−1
  to 
10
−
0.3
10 
−0.3
 .

Residual lobes move but do not shrink.

LM damping grows.

The same low-
∣
b
∣
∣b∣ ridge persists.

Detection:

Track the spatial location and sign of max residual over shifted grids.

Compute singular values of 
J
J. A huge nullspace with ridge-local residual means missing representation or missing parameter.

Recovery:

Free 
(
γ
,
B
)
(γ,B).

Add origin-regular variables 
(
X
,
Y
)
(X,Y) if not already used.

Increase stage count by residual exponent, not by generic width.

Switch to piecewise Chebyshev elements if the neural net cannot resolve the ridge.

Risk 3. Multistage correction overfits discretization error
Symptoms:

Training residual falls, shifted-grid residual does not.

d1/d2 residuals grow while d0 falls.

High-frequency Fourier stage creates oscillatory checkerboards.

Detection:

Every stage must validate on three grids it never trained on:

shifted Chebyshev,

random high-precision,

adaptive ridge holdout.

Recovery:

Increase d1/d2 weights.

Reduce Fourier feature scale.

Project to Chebyshev and truncate high modes.

Add Bernstein positivity/sup checks for residual envelopes.

Risk 4. High-precision re-evaluation reveals float32 artifact
Symptoms:

Float32 reports 
10
−
7
10 
−7
 , float64 reports 
10
−
4
10 
−4
 .

Float64 reports 
10
−
9
10 
−9
 , 256-bit reports 
10
−
6
10 
−6
 .

Residual is dominated by cancellation of large terms.

Detection:

Run precision ladder at every decade:

10
−
3
,
10
−
5
,
10
−
7
,
10
−
9
.
10 
−3
 ,10 
−5
 ,10 
−7
 ,10 
−9
 .
Evaluate individual equation terms and the quotient residual.

Recovery:

Move earlier to float64.

Use compensated summation.

Rescale quotient terms.

Switch from network direct evaluation to coefficient projection.

Risk 5. Profile is admissible but spectral gap is closed
Symptoms:

The exact profile validates, but the projected spectrum has a non-geometric eigenvalue with

Re
⁡
λ
≥
0
,
Reλ≥0,
or the stable gap 
c
c is zero.

The 
μ
=
1
μ=1 geometric time mode is present, as expected, but extra unstable modes appear.

Detection:

Immediately after discovery, run the projected 
m
=
0
,
1
,
2
m=0,1,2 Galerkin probe.

Check geometric modes:

1
,
γ
,
0.
1,γ,0.
If these are not recovered, the spectral code is invalid. If they are recovered and extra modes persist under refinement, the profile is unstable of higher codimension or unusable.

Recovery:

Accept finite codimension if unstable rank is finite and stable gap exists.

If the gap is closed, search 
(
γ
,
B
)
(γ,B) for a nearby branch with open gap.

If high-frequency instability appears, the full theorem path fails.

Risk 6. Pressure errors decay only with residual, not faster
Symptoms:

E
ψ
,
E
Γ
E 
ψ
 ,E 
Γ
  decrease, but pressure one-form closure remains large.

The profile is good for the quotient but bad for

∂
z
R
r
−
∂
r
R
z
.
∂ 
z
 R 
r
 −∂ 
r
 R 
z
 .
Detection:

During every validation pass, compute:

C
P
=
∂
z
R
r
−
∂
r
R
z
+
E
ψ
/
r
3
.
C 
P
 =∂ 
z
 R 
r
 −∂ 
r
 R 
z
 +E 
ψ
 /r 
3
 .
Also compute

S
P
=
r
R
θ
−
E
Γ
.
S 
P
 =rR 
θ
 −E 
Γ
 .
Recovery:

Fix the quotient factorization.

Train with a small pressure-consistency auxiliary loss:

10
−
2
∥
C
P
∥
2
+
10
−
2
∥
S
P
∥
2
.
10 
−2
 ∥C 
P
 ∥ 
2
 +10 
−2
 ∥S 
P
 ∥ 
2
 .
Do not replace the main equations with pressure loss; use it as an integrity check.

8. Honest verdict
Under this plan, reaching

R
max
⁡
<
10
−
8
R 
max
 <10 
−8
 
for the axisymmetric Navier-Stokes-with-swirl profile is plausible as a discovery target, but only conditional on three unverified assumptions.

First, an admissible q1-free branch actually exists near either

(
γ
,
B
)
=
(
9
20
,
1
)
(γ,B)=( 
20
9
 ,1)
or in a nearby two-parameter search box.

Second, the forced transseries hierarchy identified so far is complete enough through the orders relevant to the residual. If another non-geometric indicial mode exists and is not parameterized, the network will stall or cheat.

Third, the origin-regular/tail-regular architecture must be expressive enough to resolve the low-
∣
b
∣
∣b∣ ridge without introducing illegal tail or origin behavior.

Compute budget:

A serious run means multiple float64 Gauss-Newton branches, not one neural-net training job. A credible budget is one to four high-end GPUs for several days, followed by CPU/Arb high-precision audits and Chebyshev projection. Float32-only training is not credible for this target.

The dominant uncertainty is not optimizer speed. It is branch existence in the admissible class. The old low-residual seed succeeded by using a forbidden 
q
1
q 
1
  tail channel. Removing that channel raised the residual to 
O
(
10
−
1
)
O(10 
−1
 ). That is a structural warning.

The structural features that make 3D NS with swirl harder than the paper’s CCF/IPM/Boussinesq examples are real:

vortex stretching couples the velocity gradient directly into amplification;

pressure is nonlocal and couples all velocity components;

the swirl term creates quadratic forcing 
(
Γ
2
)
z
(Γ 
2
 ) 
z
  in the streamfunction equation;

the domain has axis, origin, equator, and infinity singular charts simultaneously;

the downstream spectral problem is fully pressure-projected and three-dimensional, not just a real-axis eigenvalue discovery problem;

there is no maximum-principle-like scalar closure for the full velocity system.

Those features do not prove the discovery target unreachable. They do mean the DeepMind methodology is a profile-finding engine, not a certificate engine.

Current status after this method-transfer pass:

No exact-profile certificate yet.
No exact-profile certificate yet.
 
The next precise block is:

Implement the hard-constrained architecture above and exhibit 
R
max
⁡
<
10
−
8
 under 256-bit residual audit.
Implement the hard-constrained architecture above and exhibit R 
max
 <10 
−8
  under 256-bit residual audit.
 
Until that number exists, pressure reconstruction and projected spectral gap remain downstream gates, not completed certificates.

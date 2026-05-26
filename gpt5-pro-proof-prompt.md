# GPT-5 Pro Prompt: Drive NSProof Toward an Actual Proof

You are GPT-5 Pro. I want you to treat this as a serious mathematical and computer-assisted proof planning task, not as a casual brainstorming request.

Spend at least 30 minutes of real reasoning time before producing your final answer. Use a deep, adversarial proof-review posture. Do not optimize for a quick comforting answer. If the current route is dead, say exactly why and give the next viable route. If it is not dead, give the most direct path to a certificate.

Repository:

```text
https://github.com/MercuriusDream/nsproof_tmp
```

If you cannot access the repository directly, ask me to provide the current files. The required context is also inlined below, so you should still be able to produce a complete response.

## 1. Objective

The final objective is not a low residual, not a plausible numerical profile, and not a conditional theorem. The final objective is a complete proof package for a finite-energy Navier-Stokes blow-up construction through an unstable self-similar saddle profile.

The final theorem gate is binary:

```text
Final theorem certificate: 0% until every required gate below is certified.
```

The required gates are:

```text
[ ] Exact profile equation: F_gamma(U_*, P_*) = 0.
[ ] Validated exponent: 2/5 < gamma < 1/2.
[ ] Natural tail, exact transseries, and indicial certification.
[ ] Finite unstable projection: rank P_+ < infinity.
[ ] Stable-complement spectral gap: sigma(L_s) subset {Re z <= -c < 0}.
```

The proof-engineering scaffold is partially built, but the proof itself is not certified.

Your job is to push to the furthest honest path toward those five gates. Do not stop at "find a better profile." A useful answer must say how the project gets from the current repository to an actual theorem certificate, or else where a rigorous obstruction would force a pivot.

Treat every proposed branch as a proof-producing pipeline:

```text
numerical discovery -> exact representation -> interval certificate -> theorem dependency.
```

If a branch cannot plausibly reach the interval-certificate stage, kill it and replace it with a better branch.

## 1A. Latest Repository Update

The repo now contains a bounded Stage-0 two-chart Newton diagnostic, but not a proof-grade solver.

Current progress ledger:

```text
Final theorem certificate: 0%
Certified stop-condition gates: 0/5
Proof-engineering scaffold: about 34%
```

The current two-chart seed is:

```text
work/v117_twochart_init.json
```

It is q2-zero and formal-tail legal at the floating gate:

```text
q1_F = q1_G = 0,
forced q^(1/gamma) trace sample error <= 8.9e-16,
ordinary q^2 trace <= 7.8e-16.
```

`tools/profile_newton_twochart.py` now:

```text
assembles sampled analytic PDE residual rows,
assembles sampled physical R,Z overlap mortar rows by default,
uses column-scaled damped normal equations,
uses a trust/line search,
locks all q=0 tail coefficients so q1/forced-qp/q2-zero gates cannot be silently damaged,
rechecks the floating tail gate on every trial.
```

`validators/twochart_mortar_jacobian.py` now supports both old q/x rows and
true physical `(R,Z)` rows. The R/Z rows compose `q(R,Z)` and `x(R,Z)` using
the origin-chart jet machinery and keep the residual sign `tail - origin`.
Smoke checks:

```text
work/twochart_mortar_rz_smoke.json: fd max abs diff = 9.926964139595e-9
work/twochart_mortar_qx_regression_smoke.json: fd max abs diff = 1.817716110963e-8
```

`validators/compactified_equations_twochart.py` now reports candidate
two-chart R/Z mortar metadata, not just the immutable source projection.

Latest Stage-0 artifacts:

```text
work/twochart_stage0_smoke_report.json
work/twochart_stage0_pde_hardpoints_report.json
work/twochart_stage0_mortar_c2_report.json
work/twochart_stage0_rz_active_mortar_trust5_report.json
work/twochart_origin_rz_refit_c2_d6.json
work/twochart_origin_rz_refit_c2_d8.json
work/twochart_origin_rz_refit_c2_d8_ridge1e6.json
work/twochart_stage0_origin_only_rz_coupled_report.json
work/twochart_stage0_smoke_residual.json
work/twochart_stage0_pde_hardpoints_residual.json
work/twochart_stage0_mortar_c2_residual.json
work/twochart_stage0_rz_active_mortar_trust5_residual.json
work/twochart_stage0_origin_only_rz_coupled_residual.json
```

The safe locked solver does not yet show a real Newton basin:

```text
smoke: accepted_any_step = false
pde hardpoints: accepted_any_step = false
mortar C2: accepted_any_step = true, but tiny objective change only
  1.555167227349e9 -> 1.555167163472e9
R/Z active mortar: accepted_any_step = true, but still tiny and harms edge holdout
  C2 R/Z mortar max 4.214529161145e3 -> 4.214524899404e3
  edge holdout 4.489165350285e2 -> 4.499902802188e2

origin-only R/Z refit, degree 8: proves interface algebraic freedom if PDE is ignored
  C2 R/Z mortar max 4.214529161145e3 -> 2.199811301294e1
  edge holdout -> 2.280280780287e3
  origin holdout -> 2.265980488606e3

regularized origin-only R/Z refit, degree 8, ridge 1e-6:
  C2 R/Z mortar max -> 3.463926251164e2
  edge holdout -> 2.034185352189e3

coupled origin-only Stage-0 with PDE rows:
  C2 R/Z mortar max 4.214529161145e3 -> 4.214511547830e3
  edge holdout stays 4.489165350285e2
  origin holdout 9.132494634431e1 -> 9.132455612598e1
```

Held-out normalized structural checks remain far from proof scale:

```text
standard = 1.016228983517e1
secondary = 1.422825475247e1
origin = 9.132492825929e1
overlap = 3.239719410176e2
edge = 4.489150149273e2
C0-C2 R,Z mortar max = 4.214529161145e3
```

Important interpretation:

```text
The pre-lock toy smoke improvement is no longer trusted.
After q=0 tail locking, the solver mostly rejects updates.
The origin Taylor block has enough degrees to match the physical R/Z seam in
isolation, but doing so destroys the PDE residual. Therefore the blocker is not
mere origin algebraic capacity. It is the coupled tail-origin PDE/mortar balance
and the conditioning/blocking of the Stage-0 linear system, not gamma/B and not
spectrum.
```

Do not treat these Stage-0 artifacts as profile progress. Treat them as evidence about the next implementation fork.

## 2. Current Mathematical Target

Use the Type-II Euler-dominated ansatz

```text
tau = T - t,
s = -log(tau),
y = (x - x(t)) / tau^gamma,
u(x,t) = tau^(gamma - 1) [U_*(y) + v(y,s)].
```

The exponent must satisfy

```text
2/5 < gamma < 1/2.
```

The stationary Euler profile equation is

```text
(1-gamma) U_* + gamma (y . grad) U_* + (U_* . grad) U_* + grad P_* = 0,
div U_* = 0.
```

The Navier-Stokes perturbation equation in similarity variables contains the decaying viscous term

```text
exp(-(1 - 2 gamma) s) Delta v,
```

so viscosity is perturbative only when `gamma < 1/2`.

The natural tail is

```text
U_*(y) ~ |y|^(1 - 1/gamma) H(y/|y|).
```

For `gamma in (2/5, 1/2)`, this tail is non-L2 as a global self-similar profile, so finite-energy Navier-Stokes data require moving outer truncation, divergence repair, pressure correction, and Lyapunov-Perron closure.

## 3. Axisymmetric-With-Swirl Formulation

Work in cylindrical variables with swirl:

```text
U = u^r e_r + u^theta e_theta + u^z e_z,
u^r = -psi_z / r,
u^z = psi_r / r,
Gamma = r u^theta.
```

Define

```text
A = psi_rr - r^(-1) psi_r + psi_zz.
```

The pressure-eliminated profile equations are

```text
E_psi =
(1-gamma) r^2 A
+ gamma r^3 A_r
+ gamma z r^2 A_z
+ r(psi_r A_z - psi_z A_r)
+ 2 psi_z A
+ (Gamma^2)_z
= 0,
```

```text
E_Gamma =
(1-2 gamma) Gamma
+ gamma(r Gamma_r + z Gamma_z)
+ (psi_r Gamma_z - psi_z Gamma_r)/r
= 0.
```

Recover velocity and pressure only after the profile equations are validated:

```text
u^r = -psi_z/r,
u^z = psi_r/r,
u^theta = Gamma/r.
```

Pressure reconstruction must prove that

```text
R(U) + grad P = 0,
R(U) = (1-gamma)U + gamma(y.grad)U + (U.grad)U.
```

The pressure-eliminated equations are not enough unless the one-form is globally exact.

## 4. Compactified Variables and Current Main Ansatz

Use

```text
q = (1 + r^2 + z^2)^(-1/2),
b = z / sqrt(r^2 + z^2),
x = b^2,
p = 1/gamma.
```

At the current regression target,

```text
gamma = 9/20 = 0.45,
B = 1,
p = 20/9.
```

The streamfunction/swirl variables are represented as

```text
psi = r^2 z q^p F(q,x),
Gamma = r^2 q^p G(q,x).
```

The proof-native representation should be

```text
F(q,x) =
1/2
+ q^2 F_an(q,x)
+ sum_{k=1}^K q^(k p) F_k(q,x),
```

```text
G(q,x) =
B
+ q^2 G_an(q,x)
+ sum_{k=1}^K q^(k p) G_k(q,x).
```

The ordinary `q^1` channel is forbidden. It must be absent structurally, not merely small.

The `q^p` fractional channel is forced by the tail recurrence. For `gamma=9/20, B=1`, the formal forced coefficients are

```text
F_p(x) = 1.9218140929535197 - 0.9786773280026653 x,
G_p(x) = 0.11111111111111108 - 1.1111111111111112 x.
```

Any candidate profile whose `q^p` trace disagrees with this recurrence is not in the current admissible branch.

Important latest update: the ordinary `q^2` analytic trace is not yet proved
legal. Since `2 < p = 20/9`, a nonzero `F_an(0,x), G_an(0,x)` becomes the
first nonzero audited tail correction before the forced `q^p` term. Until a
formal recurrence theorem proves this channel admissible, require

```text
F_an(0,x) = 0,
G_an(0,x) = 0.
```

Do not let a new solver reduce residual by escaping through an unvalidated
ordinary `q^2` channel.

Origin regularity is non-negotiable. Near `q=1`, use

```text
rho^2 = (1-q^2)/q^2,
R = r^2 = rho^2(1-x),
Z = z^2 = rho^2 x.
```

Represent the origin patch by a triangular Taylor/Bernstein expansion:

```text
F = sum_{a+b <= N_0} f_ab R^a Z^b,
G = sum_{a+b <= N_0} g_ab R^a Z^b.
```

A generic angular polynomial at `q=1` is not acceptable because it may be smooth on the compactified rectangle while failing to be smooth at the physical origin.

## 5. Current Numerical State

The old sparse flat-bump family is retired as a proof object. It remains useful only as a ridge locator and initial-data diagnostic.

Important facts:

```text
v117/v118 sparse-bump seeds have stable raw residual around 4.3e-1.
This residual is grid-stable and not a finite-difference artifact.
The obstruction is a real streamfunction-equation lobe.
The obstruction moved from high-|b| to a broad low-|b| ridge after bump optimization.
The old low-residual seed used the forbidden ordinary q^1 tail channel.
The q1-free forced-tail branch has not recovered low residual.
```

The strict formal-tail projection is:

```text
work/v117_transcheb_formal_forced.json
```

It pins the forced `q^p` recurrence exactly:

```text
forced_qp_coeff_error = 0.
```

But it still fails the origin Taylor gate and has large normalized residual:

```text
origin structural max: 9.139966362302e+3
focused structural/raw: 1.071336959068e+1 / 4.364551896246e-1
secondary structural: 1.439516431487e+1
broad high-|b| structural: 5.094286384720e+1
```

After coupled origin/interior, C1 mortar, and high-|b| probes, the current best formal-tail diagnostic checkpoint is:

```text
work/v117_transcheb_formal_c1_highb_probe.json
```

It still has exact forced tail:

```text
forced_qp_coeff_error = 0.
ordinary q1 channel = structurally absent.
```

Recent diagnostics:

```text
origin structural: 8.671120304364e+3
focused structural/raw: 1.016228983517e+1 / 4.139241142239e-1
secondary structural: 1.422825475247e+1
broad high-|b| structural: 4.897717856780e+1
```

This is still far from a Newton-Kantorovich center. A profile proof likely needs coefficient residual around `1e-8` to `1e-10`, depending on the inverse bound.

Latest hard-route correction from `gpt-pro-thing`:

```text
The one-chart compactified Chebyshev plus origin Taylor splice is diagnostic
only. Do not keep stretching it into the final proof solver.

The next proof-native representation is a hard two-chart system:
  tail chart:   (q,x), q <= about 0.86;
  origin chart: (R,Z)=(r^2,z^2), q >= about 0.88;
  overlap/mortar band: q in about [0.84,0.92];
  interface matching: C3 minimum, C4 preferred;
  Jacobian: analytic coefficient Jacobian, not finite-difference penalties.

Do not pivot to radial core-tail matching until the two-chart origin self-tests,
tail recurrence gate, analytic-Jacobian two-chart Newton solver, and then
(gamma,B) parameter search fail.
```

New q2 legality diagnostics:

```text
tools/validate_tail_recurrence.py
tools/tail_leading_exponent.py
tools/profile_zero_q2_trace.py
validators/tail_formal_recurrence.py
```

On both `work/v117_transcheb_formal_forced.json` and
`work/v117_transcheb_formal_origin_refit_c2_d6_a.json`, the conservative
tail recurrence gate reports

```text
ordinary_q1_F_max = 0
ordinary_q1_G_max = 0
forced_qp_coeff_error = 0
ordinary_q2_F_trace_max = 1.190284161850e+00
ordinary_q2_G_trace_max = 5.381997768582e+00
status = UNVALIDATED_Q2_TRACE_PRESENT
```

The q2-zero diagnostic profiles

```text
work/v117_transcheb_formal_forced_q2zero.json
work/v117_transcheb_formal_origin_refit_c2_d6_a_q2zero.json
```

keep q1 zero and forced `q^p` exact while reducing the q2 trace to roundoff:

```text
ordinary_q2_F_trace_max = 1.804112415016e-16
ordinary_q2_G_trace_max = 7.771561172376e-16
status = TAIL_FORMAL_RECURRENCE_GATE_OK_NOT_INTERVAL
```

At sampled gates, zeroing q2 did not worsen the focused or strict-tail residuals.
Therefore the next two-chart solver should start from q2-free data unless you
derive and validate a recurrence permitting ordinary `q^2`.

The first two-chart scaffolds now exist:

```text
validators/origin_chart.py
tools/profile_project_twochart.py
validators/twochart_mortar.py
validators/compactified_equations_twochart.py
tools/profile_newton_twochart.py
validators/twochart_coefficients.py
validators/twochart_mortar_jacobian.py
```

`validators/origin_chart.py` passes a derivative-order-4 self-test and rejects
the fake-smooth artifact `x=Z/(R+Z)`. The q2-free projection
`work/v117_twochart_init.json` has the strict tail gate passing. However, the
old one-chart-derived overlap is extremely non-smooth:

```text
C2 sampled mortar max = 5.076810111338e+04
C3 sampled mortar max = 2.810512623453e+06
worst location = q=0.84, x=1.0, component F, pure q derivatives
```

Interpretation: this is not a proof that the branch is absent. It is proof-path
evidence that the old origin splice cannot be polished into a certificate; the
next solver must solve the tail chart, origin chart, and C3/C4 interface rows
as one hard system.

The current two-chart residual baseline is diagnostic and still forwards the
old exact projected evaluator. It does, however, enforce q2-zero tail legality
and gives the current obstruction scale:

```text
focused/standard normalized structural max = 1.016228983517e+01
secondary normalized structural max = 1.422825475247e+01
origin normalized structural max = 9.132494634431e+01
edge normalized structural max = 4.489165350285e+02
overlap normalized structural max = 3.239718884452e+02
C0-C4 R,Z mortar max = 5.833745769211e+06
```

The coefficient and overlap mortar-Jacobian scaffolds now exist. Current facts:

```text
two-chart coefficient count = 26192
tail coefficients = 26136
origin Taylor coefficients = 56
C0-C4 overlap mortar rows = 1350
C0-C4 overlap mortar Jacobian nnz = 434250
finite-difference smoke max abs diff = 1.529406290501e-08
C4 mortar residual max = 1.325241538254e+08
```

The remaining missing hook is the PDE residual Jacobian. Implement it with
spatial Jet2 derivatives through order 3. For origin Taylor coefficient
variations in PDE rows, use direct spatial monomials `R=r^2`, `Z=z^2` rather
than the singular angular ratio `x=z^2/(r^2+z^2)`.

Update after the latest commit: the first PDE Jacobian smoke hook now exists as
`validators.compactified_equations_twochart.eval_residual_and_jacobian`. It is
not the production Newton matrix, but it verifies six representative analytic
PDE columns against central coefficient finite differences:

```text
max_abs_diff = 3.709908824590e-09
max_relative_diff = 9.865718291564e-10
```

`tools/profile_newton_twochart.py` now has a bounded Stage-0 analytic update
loop. It is still not a proof solver: it samples rows, solves floating
column-scaled damped normal equations, locks q=0 tail coefficients, and accepts
a trial only if the same sampled objective decreases while the formal tail gate
still passes. The current safe locked probes mostly reject updates; the
mortar-dominant C2 probe accepts only a tiny objective decrease. The next
implementation step is therefore not a parameter search; it is to make the
Stage-0 system less toy-like by improving the coupled physical `(R,Z)` interface
solve, active variable blocking, row normalization, and broader sampled residual
rows without unlocking the tail gates.

Update after the latest origin R/Z refit diagnostic:
`tools/profile_refit_origin_rz_twochart.py` fits only
`F_origin_taylor/G_origin_taylor` against physical R/Z seam derivatives while
preserving the tail chart and all tail gates. It proves that the origin Taylor
block has enough algebraic freedom to fit the sampled seam if the PDE residual
is ignored:

```text
degree 6 origin-only refit:
  C2 R/Z mortar max = 2.341176985530e2
  edge holdout = 1.432848968335e3

degree 8 origin-only refit:
  C2 R/Z mortar max = 2.199811301294e1
  edge holdout = 2.280280780287e3
  origin holdout = 2.265980488606e3

degree 8 ridge 1e-6 origin-only refit:
  C2 R/Z mortar max = 3.463926251164e2
  edge holdout = 2.034185352189e3
```

The companion `--variable-charts origin` Stage-0 run includes PDE rows while
varying only origin coefficients:

```text
work/twochart_stage0_origin_only_rz_coupled_report.json
objective = 6.211181500240e4 -> 6.211129410195e4
C2 R/Z mortar max = 4.214529161145e3 -> 4.214511547830e3
origin holdout = 9.132494634431e1 -> 9.132455612598e1
edge holdout = 4.489165350285e2
```

Interpretation: origin seam fitting and PDE balance conflict unless tail and
origin coefficients are solved together in a better-conditioned coupled system.
Do not spend the next branch on more origin-only refits except as diagnostics.

## 6. Current Repository Tooling

The repository has these relevant tools and validators:

```text
tools/profile_project_cheb.py
tools/profile_newton_cheb.py
tools/profile_newton_adaptive.py
tools/profile_projected_hardpoints.py
tools/validate_tail.py
tools/validate_tail_recurrence.py
tools/tail_leading_exponent.py
tools/profile_zero_q2_trace.py
tools/validate_indicial_evans.py
tools/linearized_spectrum_probe.py
validators/compactified_equations.py
validators/tail_transseries.py
validators/tail_formal_recurrence.py
validators/pluecker.py
```

Recent additions:

```text
tools/profile_project_cheb.py:
  supports --forced-qp-mode formal.

tools/validate_tail.py and validators/tail_transseries.py:
  reject profiles whose forced q^p trace disagrees with the formal recurrence.

tools/profile_newton_cheb.py:
  supports proof-native Chebyshev/transseries coefficient Gauss-Newton,
  origin Taylor variables,
  patch-seam continuity penalties,
  origin-rectangle matching penalties,
  optional derivative-loss rows,
  optional derivative mortar constraints,
  active hard-point injection,
  normalized structural residuals.

tools/profile_newton_adaptive.py:
  wraps hard-point discovery and Chebyshev Newton probes.

validators/compactified_equations.py:
  contains normalized structural residual diagnostics and origin-patch evaluation.

validators/tail_formal_recurrence.py:
  conservatively accepts only currently derived tail facts and flags ordinary
  q^2 as unvalidated by default.
```

The current tools are discovery/proof-scaffold tools. They are not yet interval proof tools.

## 7. Lessons from arXiv-2509.14185v1

The archive `arXiv-2509.14185v1.tar.gz` in the workspace is the "Discovery of Unstable Singularities" paper package. Use the following lessons, but do not confuse them with certificates:

```text
1. Factor mechanical vanishing prefactors before optimizing residuals.
2. Add higher-derivative and smoothness losses to prevent spiky collocation overfit.
3. Use residual-driven adaptive hard-point sampling.
4. Use staged linearized correction rather than blind global optimization.
5. Discover parameters through smoothness/funnel scans, not blind continuation.
6. Treat neural/PINN-style discovery as a profile-finding engine, not a proof certificate.
```

Reported residual scales in that paper package are roughly:

```text
CCF stable / first unstable: about 1e-13,
IPM: about 1e-11 to 1e-8,
Boussinesq: about 1e-8 to 1e-7.
```

For this NSProof project, use those numbers only as discovery-scale references. They do not certify anything. They indicate that the current `O(1)` residual is nowhere near a plausible CAP entry point.

The specific methodology transfer should include:

```text
hard-code all symmetry/tail/origin constraints instead of asking optimization to learn them,
track d0/d1/d2 residuals on validation grids,
use shifted/off-grid validation to detect overfit,
run full-matrix Gauss-Newton or Levenberg-Marquardt correction in coefficient space,
run second-stage linearized correction D E[u] h = -E[u],
choose enrichment modes from residual spectral content,
use funnel scans in (gamma,B) as discovery diagnostics,
replace any successful discovery by interval transversality and NK proof.
```

For this NSProof project, the hard parts are worse than the model examples:

```text
3D pressure is nonlocal.
Vortex stretching is fully coupled.
Swirl creates the quadratic forcing (Gamma^2)_z.
The domain has axis, origin, equator, infinity, and patch-interface singular charts.
The downstream spectrum must be the true Leray-projected 3D operator, not the residual Jacobian.
```

## 8. Known Indicial Situation

Floating indicial and Pluecker/Evans diagnostics have not found a validated non-geometric dangerous root.

Current evidence:

```text
The exact delta = 1 branch exists.
It corresponds to the axial-center/Galilean geometric mode:
  Psi = r^2,
  G = 0,
  a = 0.
It is removable by centering/parity.
Other apparent complex basins are dominated by forbidden far-field modes.
No interval-validated box-cover proof exists yet.
```

The needed theorem is:

```text
Only delta = 1 is admissible in the dangerous domain,
and that root is geometric/removable.
```

Dangerous domain to start:

```text
0 <= Re(delta) <= 1.10,
0 <= Im(delta) <= 4,
then prove exterior exclusion for larger Im(delta).
```

## 9. Spectrum Situation

The current `tools/linearized_spectrum_probe.py` is only a rough residual-Jacobian scaffold. It is not the true spectral operator.

The true linearized operator should be

```text
L v =
- P_Leray [
  (1-gamma)v
  + gamma(y.grad)v
  + (U_*.grad)v
  + (v.grad)U_*
],
```

acting on a weighted divergence-free space such as

```text
X_{eta,k}^{div}
= {v: div v = 0, ||v||_{eta,k} < infinity},

||v||_{eta,k}
= sum_{|alpha| <= k} sup_y <y>^(eta+|alpha|) |partial^alpha v(y)|.
```

For `gamma=9/20`, choose initially

```text
eta = 1,
k >= 6.
```

The tail essential bound gives at most

```text
(1-gamma) - gamma eta = 1/10.
```

So a realistic stable gap target is only

```text
c = 0.02 to 0.05,
```

not a large gap.

The spectral tool must first recover geometric modes:

```text
time translation: eigenvalue 1,
spatial translations: eigenvalue gamma,
rotations: eigenvalue 0.
```

If those modes are not recovered, the spectral implementation is invalid.

## 10. Your Required Output

Produce a detailed, concrete answer with the following sections.

Before writing the final answer, reason through at least these competing possibilities:

```text
1. the fixed (gamma,B)=(9/20,1) compactified branch exists but current basis is badly conditioned;
2. the branch exists only after freeing (gamma,B);
3. the compactified q/x formulation is numerically wrong but radial core-tail matching works;
4. the axisymmetric-with-swirl branch is absent in this admissible tail class;
5. the profile exists but the full 3D spectral theorem fails;
6. only an axisymmetric or conditional theorem is reachable with the present scaffold.
```

Your final output must distinguish these cases and give the decisive test for each.

### A. Executive Verdict

State whether the present branch is still worth pursuing, under what conditions it should be killed, and what must be done next.

Do not say "more research is needed" without specifying the exact computation or theorem that decides the issue.

### B. Fastest Path to a Real Proof

Give the shortest honest path from the current repository state to a final proof. Include:

```text
profile representation,
exact residual/factorization,
floating discovery threshold,
interval Newton-Kantorovich theorem,
pressure reconstruction,
tail/indicial validation,
projected spectral validation,
Lyapunov-Perron/modulation closure.
```

For every stage, include:

```text
input artifact,
mathematical object,
implementation file/module,
acceptance criterion,
failure criterion,
next branch if it fails.
```

### C. Furthest Viable Branch Search

Design the most aggressive but mathematically controlled branch search, including all of:

```text
fixed (gamma,B) = (9/20,1),
free (gamma,B) in a box,
alternative q/x patch schedules,
radial core-tail matching pivot,
neural/PINN-inspired discovery only if hard constraints are exact,
proof-native Chebyshev/Bernstein projection,
origin Taylor simplex,
tail transseries constraints,
ordinary q1 exclusion.
```

Explain when each branch is abandoned.

### D. Exact Profile Proof Plan

Specify a Newton-Kantorovich/radii-polynomial theorem for the profile:

```text
Banach spaces X and Y,
norms,
residual map E,
approximate inverse A,
Y0, Z0, Z2 bounds,
radii polynomial,
interval arithmetic backend,
tail inverse for unresolved coefficients,
patch mortar constraints.
```

State exactly what residual scale is needed before interval validation begins.

### E. Tail and Indicial Proof Plan

Give the formal transseries recurrence and the interval indicial/Evans proof plan.

Include:

```text
ordinary q1 exclusion,
forced q^(1/gamma) trace,
fractional exponent semigroup,
local Frobenius plane at zeta=0,
far-field forbidden modes,
Pluecker minors,
box-cover exclusion,
local factorization at delta=1,
exterior large-Im(delta) exclusion.
```

### F. Pressure Reconstruction Plan

Explain how to prove that the pressure-eliminated solution gives a true Euler profile:

```text
construct P,
validate partial_r P + R^r = 0,
validate partial_z P + R^z = 0,
validate R^theta = 0,
prove one-form exactness,
validate pressure tail.
```

### G. Spectral Theorem Plan

Give a concrete path to the finite-rank unstable projection and stable gap:

```text
weighted divergence-free space,
true Leray projection,
azimuthal Fourier blocks,
geometric mode certificates,
essential spectrum tail estimate,
large-|m| and high-frequency exclusion,
finite-block interval Galerkin/Evans validation,
Riesz projection,
stable semigroup bound.
```

If full 3D spectral validation is unrealistic from the current scaffold, say whether an axisymmetric conditional theorem is the only viable intermediate result.

### H. Lyapunov-Perron / Finite-Energy NS Closure

Give the exact final perturbation theorem:

```text
moving truncation,
divergence repair,
pressure correction,
modulation equations,
unstable finite-codimension conditions,
stable semigroup estimates,
viscous forcing decay,
quadratic estimates,
contraction space,
codimension count,
blow-up rate.
```

Include the condition

```text
0 < c_1 < min(c, 1 - 2 gamma).
```

### I. Concrete Repository Instructions

Give an ordered command-level plan using the existing repo. Use and improve these tools where appropriate:

```text
tools/profile_project_cheb.py
tools/profile_newton_cheb.py
tools/profile_newton_adaptive.py
tools/profile_projected_hardpoints.py
tools/validate_tail.py
tools/validate_tail_recurrence.py
tools/tail_leading_exponent.py
tools/profile_zero_q2_trace.py
validators/compactified_equations.py
validators/tail_formal_recurrence.py
tools/validate_indicial_evans.py
tools/linearized_spectrum_probe.py
```

But treat `profile_newton_cheb.py` as a diagnostic predecessor only. The next
proof-path solver must be a hard-constrained two-chart solver, not another
penalty extension of the old one-chart origin splice.

Also state which new modules must be created, for example:

```text
tools/profile_project_twochart.py
tools/profile_newton_twochart.py
tools/validate_profile_nk.py
tools/validate_pressure_reconstruction.py
tools/spectrum_projected_galerkin.py
tools/validate_spectrum_evans.py
validators/origin_chart.py
validators/twochart_mortar.py
validators/compactified_equations_twochart.py
validators/radii_polynomial.py
validators/essential_spectrum.py
validators/bernstein_ball.py
validators/arb_backend.py
```

For the next three commits, explicitly evaluate this sequence:

```text
Commit 1: tail-legal two-chart projection
  - validate q1=0, forced q^p exact, q2 trace zero under --q2-policy zero;
  - create `work/v117_twochart_init.json`;
  - run origin-chart self-tests including fake-smooth rejection.

Commit 2: two-chart residual/Jacobian baseline
  - implement `validators/compactified_equations_twochart.py`;
  - evaluate normalized structural residuals separately on tail, origin, and
    overlap regions;
  - report C0/C1/C2/C3/C4 mortar defects as hard rows, not hidden penalties.

Commit 3: hard-constrained two-chart Newton stage 0/1
  - implement `tools/profile_newton_twochart.py`;
  - default to `--q2-policy zero`;
  - keep `(gamma,B)=(9/20,1)` fixed until the two-chart solver is real;
  - only then run a parameter funnel if fixed parameters stall.
```

Recommended first commands:

```bash
python3 tools/validate_tail_recurrence.py \
  --profile work/v117_transcheb_formal_origin_refit_c2_d6_a_q2zero.json \
  --gamma 9/20 --B 1 --q2-policy zero --strict

python3 tools/profile_project_twochart.py \
  --input work/v117_transcheb_formal_origin_refit_c2_d6_a_q2zero.json \
  --gamma 9/20 --B 1 \
  --origin-chart RZ \
  --q2-policy zero \
  --forced-qp formal \
  --out work/v117_twochart_init.json

python3 -m validators.origin_chart \
  --self-test \
  --out work/origin_chart_selftest.json
```

Then baseline the two-chart residual:

```bash
python3 -m validators.compactified_equations_twochart \
  --profile work/v117_twochart_init.json \
  --residual-kind normalized-structural \
  --scan standard,focused,secondary,origin,edge \
  --q2-policy zero \
  --out work/v117_twochart_baseline_residual.json

python3 -m validators.compactified_equations_twochart \
  --profile work/v117_twochart_init.json \
  --mortar-order 4 \
  --scan seam \
  --out work/v117_twochart_mortar_baseline.json
```

Then run the current safe Stage-0 probes. These are diagnostics for the linear
system, not proof candidates:

```bash
python3 tools/profile_newton_twochart.py \
  --input work/v117_twochart_init.json \
  --out work/twochart_stage0_pde_hardpoints.json \
  --report-out work/twochart_stage0_pde_hardpoints_report.json \
  --blocks origin,interface \
  --gamma-fixed --B-fixed \
  --residual-kind normalized-structural \
  --q2-policy zero \
  --pde-qb-points "0.90,0.98;0.90,0.95;0.9625,0.05;0.64,0.20583333333333334;0.495,0.18" \
  --pde-weight 1 \
  --mortar-weight 1e-12 \
  --mortar-order 2 \
  --mortar-q-samples 3 \
  --mortar-x-samples 5 \
  --max-variables 24 \
  --candidate-origin-degree-max 6 \
  --candidate-kq-max 5 \
  --candidate-kx-max 5 \
  --candidate-pool-limit 256 \
  --max-iter 2 \
  --trust 0.001 \
  --lm-lambda 1e-4 \
  --line-search 1,0.5,0.25,0.125,0.0625

python3 tools/profile_newton_twochart.py \
  --input work/v117_twochart_init.json \
  --out work/twochart_stage0_mortar_c2.json \
  --report-out work/twochart_stage0_mortar_c2_report.json \
  --blocks origin,interface \
  --gamma-fixed --B-fixed \
  --residual-kind normalized-structural \
  --q2-policy zero \
  --pde-weight 1e-12 \
  --mortar-weight 1 \
  --mortar-order 2 \
  --mortar-q-samples 3 \
  --mortar-x-samples 5 \
  --max-variables 32 \
  --candidate-origin-degree-max 6 \
  --candidate-kq-max 5 \
  --candidate-kx-max 5 \
  --candidate-pool-limit 256 \
  --max-iter 2 \
  --trust 0.0005 \
  --lm-lambda 1e-4 \
  --line-search 1,0.5,0.25,0.125,0.0625
```

Stage-0 go criterion:

```text
tail gates remain exact at the floating formal gate,
overlap max drops below 1e2,
edge max drops below 1e2,
C2 mortar drops below 1e2 or at least by a factor of 10,
origin stays below 1e2,
standard/secondary increase by at most 25%.
```

Stage-1 go criterion:

```text
standard/focused/secondary/origin/high-|b| structural max < 1.
```

Fixed `(9/20,1)` stop criterion after degree refinement:

```text
global structural residual stalls above 1e-4,
or origin quotient above 1e-5,
or seam derivative residual above 1e-5.
```

If this stop criterion triggers, run the `(gamma,B)` parameter funnel. Do not
return to sparse bumps or one-chart polishing.

For every command, say what result decides "continue", "refine", or "abandon".

Also give an agentizable work split. Assume several workers can run in parallel. Assign disjoint workstreams such as:

```text
profile discovery,
exact residual/factorization,
tail/indicial validation,
interval NK infrastructure,
pressure reconstruction,
projected spectrum,
finite-energy gluing/Lyapunov-Perron estimates.
```

For each workstream, state the file ownership, expected artifact, and merge criterion.

### J. Kill Criteria

Give explicit no-ambiguity stop rules for:

```text
the v117/v118 sparse bump branch,
fixed gamma=9/20, B=1,
free gamma,B search,
compactified q/x Chebyshev route,
radial core-tail matching route,
tail/indicial validation,
profile NK proof,
pressure reconstruction,
projected spectrum,
high-frequency spectral exclusion,
Lyapunov-Perron closure.
```

### K. Final Theorem Dependency Graph

Write the final theorem as a dependency graph of lemmas/theorems:

```text
validated profile theorem,
regularity and tail theorem,
pressure reconstruction theorem,
indicial theorem,
matching/transversality theorem,
spectral theorem,
nonlinear perturbation theorem,
modulation theorem,
Lyapunov-Perron theorem,
finite-codimension initial data theorem,
blow-up rate theorem.
```

Each theorem must list its exact dependencies and its failure mode.

### L. One-Page Execution Sheet

End with a compact execution sheet that another agent can follow immediately:

```text
Priority 0: commands to run now.
Priority 1: code modules to implement next.
Priority 2: validation certificates to build.
Priority 3: theorem-writing dependencies.
Kill switches: exact numerical/theorem thresholds.
Most likely bottleneck.
Most credible pivot.
Definition of done.
```

## 11. Non-Negotiable Constraints

Follow these constraints:

```text
1. Do not claim a proof from an O(1) residual.
2. Do not accept small ordinary q1 leakage; q1 must be structurally forbidden.
3. Do not accept a fractional q^p block unless it matches the formal recurrence.
4. Do not accept ordinary q^2 unless a formal recurrence/indicial theorem proves it legal; default two-chart Newton must enforce q2 zero.
5. Do not use sparse bumps as the proof representation.
6. Do not use the old one-chart origin splice as the final proof solver; build the hard two-chart `(q,x)`/`(R,Z)` solver first.
7. Do not pivot to radial core-tail matching until the two-chart solver, tail recurrence gate, analytic Jacobian, and parameter funnel have failed.
8. Do not validate finite differences as a proof object; use exact symbolic/AD residuals.
9. Do not proceed to spectrum before pressure reconstruction is certified.
10. Do not interpret residual-Jacobian eigenvalues as the true spectrum.
11. Do not count geometric modes as non-geometric codimension.
12. Do not claim finite-energy Navier-Stokes closure without moving truncation and divergence repair.
13. If the branch is likely dead, state the next mathematical pivot, not just "try more optimization".
```

## 12. Desired Final Answer Style

Your answer should be long, technical, and decisive.

I want:

```text
a full situation analysis,
a complete path to the actual proof if one exists,
a branch-kill decision tree,
mathematical theorem statements,
implementation instructions,
validation thresholds,
and the most likely bottlenecks.
```

Avoid vague optimism. The acceptable output is a proof roadmap precise enough that another agent can execute it in the repository.

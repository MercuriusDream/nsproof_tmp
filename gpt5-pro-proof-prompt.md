# GPT-5 Pro Prompt: Drive NSProof Toward an Actual Proof

You are GPT-5 Pro. Treat this as a serious mathematical and
computer-assisted proof planning task, not casual brainstorming.

Spend at least 30 minutes of real reasoning time before producing your final answer. Use a deep, adversarial proof-review posture. Do not optimize for a quick comforting answer. If the current route is dead, say exactly why and give the next viable route. If it is not dead, give the most direct path to a certificate.

Repository:

```text
https://github.com/MercuriusDream/nsproof_tmp
```

If you cannot access the repository directly, ask me to provide the current files. The required context is also inlined below, so you should still be able to produce a complete response.

This prompt is intended to be the canonical self-contained handoff. Every time
the repository gains a meaningful diagnostic result, solver feature, certificate
attempt, or branch-kill decision, update this prompt before sending it to
ChatGPT/GPT-5 Pro. Do not rely on hidden chat history. Inline the latest
artifacts, numerical results, branch interpretation, and next commands here.

## 0A. Codex / GPT-5 Pro Iteration Loop

Use this loop until the theorem is either certified or a rigorous branch kill
forces a pivot:

```text
1. Codex computes locally until the next point where further proof strategy,
   mathematical design, or breakthrough-level review would help.

2. Codex stops the compute cycle, updates this prompt so it is fully
   self-contained, and tells the user exactly: submit gpt5-pro-proof-prompt.md
   to GPT-5 Pro.

3. The user submits this prompt to GPT-5 Pro and gives it at least 30 minutes
   of reasoning time.

4. GPT-5 Pro returns a response. Most useful responses will ask for concrete
   computation, implementation, validation, or branch-kill evidence.

5. Codex ingests that response, performs the requested compute or proof
   infrastructure work in the repository, updates TODO.md and this prompt with
   all new evidence inline, then returns to step 1.
```

Rules for the loop:

```text
Do not rely on earlier chat context.
Do not send a partial prompt.
Maintain gpt5-pro-prompt-diffs-from-last-update.md as a compact delta ledger
between full GPT-5 Pro handoffs. When a GPT-5 Pro response is pasted back,
clear that delta file and start accumulating only the new post-response diffs.
Do not omit the current proof percentage, latest commit/artifacts, or the
DeepMind/Google-paper method-transfer context.
Do not ask GPT-5 Pro for vibes; ask for definite paths, kill criteria, and
certificate-producing next steps.
Do not mark the persistent Codex goal complete merely because a prompt was
prepared. The mathematical objective remains active until the proof gates pass.
```

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

## 1A. Certificate Firewall

The words proof, proved, theorem certificate, gate passed, and final theorem
may only be used for exact symbolic identities or interval/rational
certificates. Floating residuals, precision audits, Newton convergence,
successful discovery, pressure identities, and spectral probes are not proof
certificates.

If any one of the five stop-condition gates lacks its interval certificate, the
final theorem status is exactly:

```text
Final theorem certificate: 0%
Certified stop-condition gates: 0/5
```

Residual below `1e-8` or `1e-10` is only Newton-Kantorovich entry eligibility.
The exact-profile gate passes only after `certs/profile/profile_nk.json`
contains a validated interval Newton/radii-polynomial certificate with a
positive ball radius and negative radii polynomial.

If later instructions demand "do not stop until proof", do not fabricate or
relabel discovery artifacts. Continue only by producing the strongest honest
certificates available, and mark all blocked gates explicitly.

## 1B. Mandatory Status Ledger

Begin your final answer with this table:

```text
Gate | Current artifact | Evidence type: floating / exact algebraic / interval | Status | Blocking certificate
```

Every row must name the missing certificate that would make the gate pass. Do
not substitute narrative confidence for the evidence type.

## 1C. Latest Repository Update (Authoritative, 2026-05-27)

This section supersedes the historical Stage-0 trace in section 1D. Use this
section as the current repository state and treat section 1D only as older
background.

Latest repo update in this prompt:

```text
Add coupled audit acceptance, target explicit edge/C4 rows, run chart-balanced
tail-origin diagnostics, catch one-point C4 overfit with a broad native audit,
and record a small two-q broad-audit Stage-0 improvement. The theorem
certificate remains 0/5.
```

Latest commits:

```text
1e0aaf3 Target explicit edge and C4 mortar rows
ceeda01 Add coupled audit Stage-0 metric
1b8877b Update GPT Pro prompt with patchfix diagnostics
73b7a07 Fix seam patch PDE Jacobian selection
54b02bc Record guard-only PDE Stage-0 failure
8c27990 Refresh theorem ledgers for current profile hash
15fdd45 Record 256-row residual NK blocker
1d419b9 Expose finite NK proof relevance in profile ledger
047d954 Require meaningful Stage-0 accept metric decrease
```

Current progress ledger:

```text
Final theorem certificate: 0%
Certified stop-condition gates: 0/5
Proof-engineering scaffold: about 35%
```

Current stop-condition ledger:

| Gate | Current artifact | Evidence type | Status | Blocking certificate |
| --- | --- | --- | --- | --- |
| Exact profile equation `F_gamma(U_*,P_*)=0` | Current promoted profile `work/twochart_stage0_current_profile_top8pde128_rowlocal_densemortar_step22_nativebatch.json`; exact audit `certs/profile/exact_residual_twochart_audit.json`; finite NK ledger `certs/profile/profile_nk.json`; targeted explicit-row diagnostics `work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit64_pde16_step25_nativebatch_*`, `work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_pde16_step25_nativebatch_*`; chart-balanced broad-audit diagnostics `work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_broadaudit_step27_nativebatch_*`; and two-q broad-audit diagnostics `work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch_*` | Floating/sample diagnostic and scaffold ledger only. Native C, KKT, finite-block NK, row cache, prediction diagnostics, and coupled audit metrics are not interval certificates. | Not certified. Current exact audit has sampled residual max `4.362578130070414e2`; C0-C4 physical R/Z mortar max `4.963232981363504e6`; `profile_nk.json` has `pass=false`; finite full-block diagnostics have `Z0>1`. The latest two-q broad-audit step is small floating progress, not NK entry. | `certs/profile/profile_nk.json` with directed-rounding interval Newton/radii-polynomial validation, plus `certs/profile/pressure_reconstruction.json`. |
| Validated exponent `2/5<gamma<1/2` | Fixed branch `gamma=9/20`, `p=20/9`, `B=1` | Exact algebraic inequality for the rational exponent only; floating linkage to uncertified profile. | Not certified as a theorem gate because no interval-certified admissible profile is linked to it. | `certs/profile/profile_nk.json`, `certs/tail/tail_recurrence.json`, and `certs/final_theorem_manifest.json` linkage. |
| Natural tail, transseries, indicial certification | q1-free, forced-`q^p`, q2-zero tail gate in the current seed; floating Pluecker/Evans probes. | Formal/floating; no interval recurrence certificate and no interval indicial box cover. | Not certified. q1 exclusion and forced `q^p` are enforced in the current seed, but recurrence, q2 exclusion as a theorem, admissible exponent semigroup, and indicial exclusion are not interval-certified. | `certs/tail/tail_recurrence.json`, `certs/tail/indicial_pluecker_cover.json`, `certs/profile/matching_determinant.json`. |
| Finite unstable projection `rank P_+<infinity` | `tools/linearized_spectrum_probe.py` | Floating residual-Jacobian scaffold, not the true Leray-projected 3D operator. | Not certified. Geometric modes, Riesz projection, Fredholm setup, and finite-rank contour validation are missing. | `certs/spectrum/projected_spectrum.json`. |
| Stable-complement spectral gap | No proof-grade artifact. | Floating/incomplete. | Not certified. No large-`m`, high-frequency, essential-spectrum, or stable-semigroup certificate exists. | `certs/spectrum/high_frequency_exclusion.json`, `certs/spectrum/stable_semigroup.json`. |

Current promoted profile:

```text
work/twochart_stage0_current_profile_top8pde128_rowlocal_densemortar_step22_nativebatch.json
profile_hash_sha256 = ed9e0bc8b1fc9cfa2c18cc68ac95a122f8e95d0216a4d0814ec6a6315095268a
```

Current exact-audit blocker:

```text
artifact = certs/profile/exact_residual_twochart_audit.json
pass = false
sampled quotient residual max = 4.362578130070414e2
entry threshold = 1e-8
C0-C4 physical R/Z mortar max = 4.963232981363504e6
entry threshold = 1e-8
worst mortar row = RZ:F:dRRRR at q=0.91, x=1.0
tail legality = floating OK: q1 zero, forced q^p trace error <= 8.9e-16,
                q2 trace max <= 7.8e-16
```

Current profile NK scaffold blocker:

```text
artifact = certs/profile/profile_nk.json
pass = false
profile_hash_sha256 = ed9e0bc8b1fc9cfa2c18cc68ac95a122f8e95d0216a4d0814ec6a6315095268a
sampled residual and C4 mortar are far above NK entry scale.
directed-rounding interval residual backend is missing.
validated approximate inverse A is missing.
Z2 / tail-complement interval bound is missing.
sampled interval row ledger is not a continuous-domain proof.
finite-block diagnostics are floating ridge-SVD diagnostics, not proof.
```

Finite sampled NK diagnostics from the current promoted profile:

```text
artifact = work/profile_finite_nk_top16pde256_full_block.json
finite full 430x256 block:
  Y0 = 3.776931277590535e2
  Z0 = 3.925969187521621
  rank_after_cutoff = 140
  diagnostic only, not proof

artifact = work/profile_finite_nk_top16pde256_sweep.json
best overall sampled subset:
  subset = pde only
  Y0 = 2.785084932431439e2
  Z0 = 2.7889567207415005
best proof-relevant full block:
  Y0 = 5.063311698881507e-6
  Z0 = 3.136513964448309
All Z0 values are >= 1, so this is not close to an NK certificate.
```

Critical implementation fix since the previous prompt:

```text
Bug:
  At q=0.8999999999999999, the exact residual evaluator chooses the first
  matching tail patch on the seam boundary, but the PDE Jacobian path also
  differentiated variables from the adjacent seam patch.

Concrete failure before fix:
  tail.F_an[p35].c[10,0] at q=0.8999999999999999,b=0.98
    analytic/native derivative was about -5.865984e6
    finite-difference derivative was 0.0
    F_total did not change even after a large coefficient perturbation

Fix:
  validators/compactified_equations_twochart.py now has
  active_tail_patch_for_variable(data, variable, q, x).
  delta_total_jet and native_tail_linearized_residuals_with_kind use a tail
  variable only if that variable's patch is the evaluator's first matching
  active patch.

Post-fix validation:
  inactive p35 variables now have analytic/native/finite-difference derivative
  equal to zero at the seam-side row.
  active p29 variable tail.F_an[p29].c[10,0] has analytic derivative
  865903.191438036 and finite-difference agreement to roundoff.
  work/twochart_stage0_current_profile_patchfix_pde_jacobian_smoke.json:
    max_abs_diff = 3.379932778103e-09
    max_relative_diff = 6.631918795494e-10
  work/twochart_stage0_current_profile_patchfix_residual_edge_smoke.json:
    edge max remains 4.362578130070414e2 at the current promoted profile.
```

Interpretation of the fix:

```text
The old pre-fix 256 report overstated available seam/PDE motion because some
Jacobian columns belonged to a patch that the residual evaluator ignored.
After the fix, the fake strong descent mostly disappears.
```

Corrected post-fix constrained 256 diagnostic:

```text
artifacts:
  work/twochart_stage0_current_profile_top16pde256_patchfix_step23_nativebatch.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_step23_nativebatch_report.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_step23_nativebatch_rank.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_step23_nativebatch_prediction.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_step23_nativebatch_rows.json

mode:
  primary rows = top PDE edge residual rows
  constraints = active_guard + mortar
  variables = 256
  solve_mode = guarded-ineq-kkt
  native C enabled
  accepted_any_step = false

rank/angle:
  coverage metric = 8.789791143094675e-05
  coverage_ok = false
  note: this coverage is relative to held-out C4 mortar max while the primary
        rows are PDE rows, so it should not be read as worst-mortar coverage.
  constraint rank/nullity = 100 / 156
  primary rank/projected rank = 16 / 15
  rho_grad = 8.493769262767957e-1
  rho_range = 9.189032342669498e-1
  predicted_best_factor_inf = 9.707145209846123e-1
  best feasible step l2 = 2.1041355568239692e5
  best feasible step max_abs = 1.2491956258383344e5

line search:
  no accepted entry
  full alpha=1 improves sampled objective but violates guard growth:
    residual audit max = 4.3625781400267107e2
    C4 mortar audit max = 4.963232893925096e6
    max_abs_update = 6.623971113038143e2
    guard_growth_ok = false
  smaller full alphas keep C4 mortar under audit but still fail guard growth
  and do not reduce the worst residual max meaningfully.

conclusion:
  With corrected patch-side Jacobians and mortar constraints active, the
  256-variable tangent does not produce a nonlinear accepted step. The old
  pre-fix apparent best factor near 1e-3 is not reliable; the corrected
  constrained factor is about 0.9707.
```

Corrected post-fix guard-only 256 diagnostic:

```text
artifacts:
  work/twochart_stage0_current_profile_top16pde256_patchfix_guardonly_step23_nativebatch.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_guardonly_step23_nativebatch_report.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_guardonly_step23_nativebatch_rank.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_guardonly_step23_nativebatch_prediction.json
  work/twochart_stage0_current_profile_top16pde256_patchfix_guardonly_step23_nativebatch_rows.json

mode:
  primary rows = top PDE edge residual rows
  constraints = active_guard only
  C4 mortar is still audited during line search
  variables = 256
  solve_mode = guarded-ineq-kkt
  native C enabled
  accepted_any_step = false

rank/angle:
  constraint rank/nullity = 93 / 163
  primary rank/projected rank = 16 / 14
  rho_grad = 9.775966000931403e-1
  rho_range = 8.958555555479408e-1
  predicted_best_factor_inf = 1.0000001329897399
  best feasible step l2 = 1.3431701181075428e5
  best feasible step max_abs = 7.068674163503468e4

line search:
  no accepted entry
  looser cone can move the PDE residual only by catastrophic C4 mortar damage.
  full alpha=0.25:
    residual audit max improves to 4.3624960522314586e2
    decrease from baseline about 8.2077838955e-3
    C4 mortar audit max = 9.856317551084331e8
    mortar_audit_growth_ok = false
  full alpha=0.0009765625:
    C4 mortar audit max = 4.963232881225964e6
    residual audit max = 4.362578128817711e2
    improvement is only about 1.2527e-7, far below meaningful Stage-0 scale
  chart-tail and full large-alpha variants show the same pattern:
    small PDE-edge improvement only appears with huge C4 mortar blowup.

conclusion:
  If C4 mortar is not a hard constraint, the solver can lower the edge PDE max
  slightly, but it destroys the physical R/Z seam. If C4 mortar is enforced,
  the corrected tangent is pinned for this schedule.
```

Meaningful acceptance threshold:

```text
tools/profile_newton_twochart.py now supports:
  --min-accept-metric-decrease-abs
  --min-accept-metric-decrease-rel

This prevents roundoff-scale or bookkeeping-scale accepted steps from being
misreported as profile progress. The latest post-fix diagnostics use this
firewall and report accepted_any_step=false.
```

Coupled audit acceptance metric added in `ceeda01`:

```text
tools/profile_newton_twochart.py now supports:
  --line-search-accept-metric coupled-audit-max

The metric is:
  max(trial_residual_audit_max/base_residual_audit_max,
      trial_mortar_audit_max/base_mortar_audit_max)

It requires both:
  --max-residual-audit-growth > 0
  --max-mortar-audit-growth > 0

Prediction/actual reports now include:
  accept_metric,
  base_accept_metric_value,
  trial_accept_metric_value,
  accept_metric_decrease,
  required_accept_metric_decrease,
  coupled_audit_value,
  coupled_audit_limiter,
  coupled_residual_ratio,
  coupled_mortar_ratio.

Purpose:
  Do not accept a Stage-0 step that improves a selected sampled objective while
  the held-out worst edge residual or held-out C4 mortar remains pinned or grows.
```

Explicit worst-row targeting added in `1e0aaf3`:

```text
tools/profile_newton_twochart.py now supports:
  --mortar-q-values
  --mortar-x-values
  --line-search-mortar-audit-q-values
  --line-search-mortar-audit-x-values

These explicit values override sample-count grids for selected objective rows
and line-search audit rows. They are meant to target known worst physical rows
directly instead of paying for broad Python-side grids or missing the exact
row that blocks proof entry.
```

Latest targeted explicit-row diagnostic:

```text
Base profile:
  work/twochart_stage0_current_profile_top8pde128_rowlocal_densemortar_step22_nativebatch.json

Targeted rows:
  PDE edge objective point:
    q = 0.8999999999999999
    b = 0.98
    worst component = e_psi
    base residual audit max = 4.3625781300704136e2

  C4 mortar objective/audit point:
    q = 0.91
    x = 1.0
    worst row = RZ:F:dRRRR
    base mortar audit max = 4.963232981363504e6

Shared setup:
  solve_mode = guarded-ineq-kkt
  accept metric = coupled-audit-max
  native C enabled
  stage0-workers = 8
  q2-policy = zero
  explicit mortar q/x objective and audit values
```

Targeted 64-variable run:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit64_pde16_step25_nativebatch.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit64_pde16_step25_nativebatch_report.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit64_pde16_step25_nativebatch_rank.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit64_pde16_step25_nativebatch_prediction.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit64_pde16_step25_nativebatch_rows.json

accepted_any_step = false
row_groups = active_guard:198, mortar:8, pde:1
selected_by_chart = tail:64
selected_by_block = tail.F_an:23, tail.F_frac:41

rank diagnostic:
  predicted_best_factor_inf = 3.9089330092908066e-16
  rho_range approximately 1
  rho_grad approximately 1.45e-13
  best_feasible_step_l2 = 1.099436872e9
  best_feasible_step_max_abs = 5.227650386e8

line search:
  best full/chart-tail alpha=1 coupled_audit_value = 0.9999999932561865
  accept_metric_decrease = 6.743813507625873e-09
  residual ratio = 0.9991565287420843
  mortar ratio = 0.9999999932561865
  rejected because required decrease = 1e-6

interpretation:
  The selected tail-only tangent can formally kill the single projected PDE row,
  but the nonlinear coupled audit is essentially pinned by the C4 mortar row.
```

Targeted 128-variable run:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_pde16_step25_nativebatch.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_pde16_step25_nativebatch_report.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_pde16_step25_nativebatch_rank.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_pde16_step25_nativebatch_prediction.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_pde16_step25_nativebatch_rows.json

accepted_any_step = false
row_groups = active_guard:198, mortar:8, pde:1
selected_by_chart = tail:128
selected_by_block = tail.F_an:44, tail.F_frac:84

rank diagnostic:
  predicted_best_factor_inf = 1.3029776697636022e-16
  rho_range approximately 1
  rho_grad approximately 1.13e-13
  best_feasible_step_l2 = 1.413568268e9
  best_feasible_step_max_abs = 4.921761800e8

line search:
  accepted_any_step = false
  best coupled audit remains approximately 1.0
  no meaningful held-out edge/C4 improvement

interpretation:
  The explicit row test is a sharper negative result for tail-only variable
  selection. It is not yet a fixed-branch kill because no origin variables were
  selected, so the coupled tail-origin tangent has not been cleanly tested.
```

Chart-balanced tail-origin follow-up after GPT Pro review:

```text
First chart-balanced explicit-row run:
  artifacts:
    work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_step26_nativebatch.json
    work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_step26_nativebatch_report.json
    work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_step26_nativebatch_rank.json
    work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_step26_nativebatch_prediction.json
    work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_step26_nativebatch_rows.json

  selected_by_chart = tail:92, origin:36
  selected_by_block = tail.F_an:33, tail.F_frac:59,
                      origin.F_origin_taylor:18, origin.G_origin_taylor:18
  accepted_any_step = true
  accepted_block = block:F_an
  objective rows = PDE edge q=0.8999999999999999,b=0.98 and C4 mortar q=0.91,x=1.0
  line-search audit used only the explicit q=0.91,x=1.0 C4 point.

  targeted audit at alpha=1:
    edge residual audit max: 4.3625781300704136e2 -> 3.1348631998536905e2
    explicit q=0.91,x=1.0 C4 mortar max: 4.963232981363504e6 -> 1.0988322874909114e5

  held-out post-audit:
    standard = 1.016228983517e1
    secondary = 1.422825435582e1
    origin = 9.132497540774e1
    edge = 3.134429061482e2
    overlap = 3.239711929243e2
    full C0-C4 R/Z mortar max = 1.080945313983e9

  interpretation:
    This is not profile progress. It is a one-point C4 mortar overfit:
    the targeted q=0.91 row improves, but nearby C4 rows explode.
```

One-q broad-audit rerun:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_broadaudit_step27_nativebatch.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_broadaudit_step27_nativebatch_report.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_broadaudit_step27_nativebatch_rank.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_broadaudit_step27_nativebatch_prediction.json
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_broadaudit_step27_nativebatch_rows.json

setup:
  same explicit objective q=0.91,x=1.0
  line-search C4 mortar audit = 5 q samples x 9 x samples x C0-C4 R/Z rows
  broad mortar audit rows = 1350
  base broad C4 audit max = 4.364062941499776e6 at q=0.92,x=1.0,RZ:F:dRRRR

result:
  selected_by_chart = tail:92, origin:36
  accepted_any_step = false

best PDE-improving trial:
  alpha=1:
    edge residual ratio = 0.7185804142384706
    broad C4 mortar ratio = 250.58372800852717
    broad C4 mortar max = 1.093563161144873e9
    rejected

smallest listed alpha:
  alpha=0.0009765625:
    edge residual ratio = 0.9990234432973227
    broad C4 mortar ratio = 1.2437341093833272
    rejected

interpretation:
  The broad audit correctly rejects the one-point overfit. The missing C4 row
  in the objective was q=0.92,x=1.0.
```

Two-q broad-audit run:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch.json
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch_report.json
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch_rank.json
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch_prediction.json
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch_rows.json
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch_residual.json
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch_mortar_c4.json

setup:
  objective C4 q-values = 0.91,0.92
  objective C4 x-values = 1.0
  line-search C4 mortar audit = same 1350-row broad native audit
  selected_by_chart = tail:95, origin:33
  selected_by_block = tail.F_an:34, tail.F_frac:61,
                      origin.F_origin_taylor:17, origin.G_origin_taylor:16
  accepted_any_step = true
  accepted_block = block:F_frac

rank diagnostic:
  coverage = 1.0
  constraint rank/nullity = 39/89
  primary rank/projected rank = 18/14
  rho_grad = 9.999999999999873e-1
  rho_range = 9.998289222102589e-1
  predicted_best_factor_inf = 1.4228699996405914e-2
  best feasible step l2 = 9.906137462865317e4
  best feasible step max_abs = 7.213518557979033e4

accepted trial:
  best accepted alpha = 0.015625
  coupled audit value = 0.9972256083949639
  edge residual audit max: 4.3625781300704136e2 -> 4.350474629930032e2
  broad C4 mortar audit max: 4.364062941499776e6 -> 4.351955117770506e6

held-out post-audit:
  standard = 1.016228983517e1
  focused = 1.016228983517e1
  secondary = 1.422825435582e1
  origin = 9.132497540774e1
  edge = 4.326812264740e2
  overlap = 3.239711929243e2
  full 9x9 C0-C4 R/Z mortar max = 4.922540831420e6
  5x9 overlap-only C0-C4 R/Z mortar max = 4.328283218032e6
  tail gate remains q1-free, forced q^p OK, q2-zero OK at the floating gate.

interpretation:
  This is the first small but real coupled tail-origin improvement under broad
  native C4 audit. It is far from Stage-0 success and nowhere near NK entry,
  but it means the corrected coupled tangent is not completely pinned once the
  q=0.92 C4 row is included.
```

Performance direction from `AGENTS.md`:

```text
Do not rewrite the whole solver before solver semantics settle.
Python remains the orchestration/report layer.
Move stable hot kernels to C first, with deterministic JSON-facing or ctypes
boundaries:
  row and Jacobian evaluation for compactified two-chart residuals,
  mortar and edge/seam guard row generation,
  active-set KKT/SVD wrappers where stable,
  batched prediction-vs-actual line-search scans,
  Bernstein/exact residual interval kernels where applicable.

GPU is not the first target for the current workload, including on Mac. The
current bottleneck is mostly CPU-side row assembly, scalar profile evaluation,
small-to-medium dense linear algebra, and repeated guard scans. Use native C
batched APIs before GPU work.

Every C kernel must be cross-checked repeatedly against the Python evaluator on
deterministic cases before Stage-0 use. Do not run Python cross-checks on every
production invocation after a kernel has passed; use fast C-side status checks
and batched production calls. Return explicit status codes for invalid orders,
degenerate intervals, null buffers, nonfinite inputs, and overflow-sensitive
paths. Prefer batched C calls over scalar ctypes loops.
```

Current interpretation:

```text
The fixed (gamma,B)=(9/20,1) branch is not killed yet.
The corrected evidence does kill the pre-fix claim that the 256-variable
Jacobian saw a strong feasible descent direction.

What is established:
  1. The origin chart can fit the seam algebraically if PDE constraints are
     ignored.
  2. That origin-only seam fit destroys PDE residuals.
  3. Tail/high-degree directions can move selected rows but tend to create
     low-b edge or high-order C4 mortar damage.
  4. The old seam-boundary PDE Jacobian had a real chart-side bug; it is now
     fixed and checked against finite differences.
  5. After the fix, constrained 256-variable inequality KKT does not produce
     an accepted nonlinear step.
  6. Guard-only 256-variable inequality KKT can reduce edge residual by about
     1e-2 only by blowing C4 mortar from about 4.96e6 to about 1e9.
  7. Explicitly targeting the known worst C4 row at q=0.91,x=1.0 removes the
     ambiguity that the objective missed the blocker.
  8. Targeted 64/128 native runs show linear formal ability to kill the single
     selected PDE row, but line search still cannot reduce the coupled audit.
  9. Chart-balanced tail-origin selection does pull origin variables, but a
     one-point C4 audit can accept a false step that explodes nearby C4 rows.
 10. A broad 1350-row native C4 audit catches that overfit.
 11. Adding the schedule-nearby q=0.92 C4 row to the objective gives a small
     real coupled improvement under broad audit.

What is not established:
  1. Fixed (9/20,1) is mathematically impossible.
  2. Freeing (gamma,B) is justified before the shifted-schedule and coupled
     tail-origin selection tests run.
  3. q2 is legal or needed.
  4. Any theorem gate has passed.
```

Current branch status:

```text
fixed (9/20,1): alive but under serious corrected negative evidence
current exact profile gate: blocked by residual max 4.36e2 and C4 mortar 4.96e6
current profile NK gate: blocked by pass=false and finite sampled Z0>1
current solver issue: coupled tail-origin descent exists but is tiny and very
  sensitive to missing nearby C4 rows
most credible immediate fork: continue fixed (9/20,1) with broad native C4
  audit always enabled; expand objective q rows to cover q=0.90,0.91,0.92 and
  raise variables to 160/192 before shifted schedules
do not free (gamma,B) until corrected 160/192/256 broad-audit shifted schedules
  fail cleanly
do not unlock q2 without tail recurrence certificate
```

Question GPT-5 Pro should answer now:

```text
Given the corrected seam-patch Jacobian fix, the coupled-audit firewall, and
the explicit worst-edge/worst-C4 diagnostics above, including the small
two-q broad-audit improvement, what is the most direct proof-producing next
move?

Specifically answer:
  1. Should the next fixed-branch run iterate from the accepted two-q candidate,
     or restart from the promoted profile with a three-q objective
     q=0.90,0.91,0.92?
  2. What is the minimal C4 q/x objective row set that prevents mobile C4
     overfit while avoiding broad slow objective grids?
  3. Should variable count now increase to 160/192, or should row/column
     scaling and native origin PDE columns come first?
  4. What exact shifted schedules should run if the three-q broad-audit run
     stalls?
  5. What would count as a rigorous floating branch-kill precursor before
     interval matching or parameter-funnel certificates?
  6. Which native C kernel should be ported next to reach the proof-relevant
     diagnostics fastest?

You must distinguish:
  - one-point C4 row overfit,
  - a real but tiny broad-audit coupled descent,
  - a chart-switch sampling artifact,
  - a reason to free (gamma,B),
  - and a reason to pivot to radial matching.
```

Immediate local commands still worth running after this prompt:

```bash
# 1. Continue the corrected fixed branch with broad native C4 audit always
#    enabled. The next surgical run should include q=0.90,0.91,0.92 in the C4
#    objective or iterate once from the accepted two-q candidate.

python3 tools/profile_newton_twochart.py \
  --input work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch.json \
  --out work/twochart_stage0_current_profile_targeted_edge_c4_q909192_broadaudit160_step29_nativebatch.json \
  --report-out work/twochart_stage0_current_profile_targeted_edge_c4_q909192_broadaudit160_step29_nativebatch_report.json \
  --rank-report-out work/twochart_stage0_current_profile_targeted_edge_c4_q909192_broadaudit160_step29_nativebatch_rank.json \
  --row-cache-out work/twochart_stage0_current_profile_targeted_edge_c4_q909192_broadaudit160_step29_nativebatch_rows.json \
  --prediction-actual-report-out work/twochart_stage0_current_profile_targeted_edge_c4_q909192_broadaudit160_step29_nativebatch_prediction.json \
  --blocks tail,origin,interface \
  --variable-charts tail,origin \
  --solve-mode guarded-ineq-kkt \
  --gamma-fixed --B-fixed \
  --residual-kind normalized-structural \
  --q2-policy zero \
  --pde-qb-points '0.8999999999999999,0.98' \
  --no-default-pde-points \
  --pde-component-mode worst-per-point \
  --pde-jacobian-candidate-count 16 \
  --mortar-coordinates RZ \
  --mortar-order 4 \
  --mortar-q-values 0.90,0.91,0.92 \
  --mortar-x-values 1.0 \
  --line-search-mortar-audit-order 4 \
  --line-search-mortar-audit-q-samples 5 \
  --line-search-mortar-audit-x-samples 9 \
  --mortar-active-count 32 \
  --mortar-jacobian-candidate-count 512 \
  --guard-grid edge \
  --guard-q-min 0.74 --guard-q-max 0.94 \
  --guard-b-min 0.08 --guard-b-max 0.99 \
  --guard-q-samples 11 --guard-b-samples 11 \
  --active-guard-weight 10 \
  --guarded-kkt-primary-labels pde,mortar \
  --guarded-kkt-constraint-labels active_guard \
  --guarded-kkt-max-constraints 128 \
  --guarded-ineq-max-active 128 \
  --guarded-ineq-tolerance 1e-10 \
  --guarded-ineq-target nonincrease \
  --line-search-eval objective-only \
  --line-search-accept-metric coupled-audit-max \
  --line-search-residual-audit-scan edge \
  --max-residual-audit-growth 1 \
  --max-mortar-audit-growth 1 \
  --max-raw-objective-growth 1 \
  --max-guard-objective-growth 1 \
  --max-guard-max-growth 1 \
  --min-accept-metric-decrease-abs 1e-6 \
  --row-normalization none \
  --max-variables 160 \
  --chart-balanced-selection \
  --candidate-origin-degree-max 12 \
  --candidate-kq-max 12 \
  --candidate-kx-max 12 \
  --candidate-pool-limit 1536 \
  --max-iter 1 \
  --trust 0.001 \
  --lm-lambda 1e-6 \
  --pde-weight 1 \
  --mortar-weight 0.01 \
  --native-c \
  --stage0-workers 8 \
  --line-search 1,0.25,0.0625,0.015625,0.00390625,0.0009765625

# 2. Accept only if the broad 1350-row C4 audit and edge audit improve together.
#    Ignore one-point C4 improvements unless the broad audit also improves.

# 3. If q=0.90,0.91,0.92 at 160/192 variables stalls, then run shifted seam
#    schedules q_switch=0.88,0.90,0.92 under the same broad audit before
#    freeing (gamma,B).
```

## 1D. Historical Stage-0 Trace (Superseded by 1C)

Latest repo update in this prompt:

```text
Add C-backed PDE/guard tail columns and rerun 128 scaled inequality KKT
```

The repo now includes guarded-KKT row-cache/rank diagnostics, 64/128-variable
true-worst-row equality-KKT diagnostics, inequality no-growth active-set KKT,
analytic coefficient scaling, prediction-vs-actual reporting, process-parallel
Stage-0 PDE/guard row assembly, native C physical R/Z mortar tail-Jacobian
columns, and native C PDE/guard tail-coefficient columns. It is still not a
proof-grade solver; the latest C-backed 128 run is infrastructure plus a
sharper negative diagnostic, not profile progress.

Current progress ledger:

```text
Final theorem certificate: 0%
Certified stop-condition gates: 0/5
Proof-engineering scaffold: about 35%
```

Current stop-condition ledger:

| Gate | Current artifact | Evidence type | Status | Blocking certificate |
| --- | --- | --- | --- | --- |
| Exact profile equation `F_gamma(U_*,P_*)=0` | `work/v117_twochart_init.json`; equality rank reports `work/twochart_stage0_rz_kkt_seamlimit64_rank.json`, `work/twochart_stage0_rz_kkt_seamlimit128_rank.json`; C-backed inequality run `work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_report.json`; held-out scan `work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_residual.json`; C4 mortar audit `work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_mortar_c4.json` | Floating diagnostic only; native C and KKT diagnostics are not interval certificates | Not certified; held-out normalized structural residuals remain standard/focused `1.016228983517e1`, secondary `1.422825475247e1`, origin `9.132494644305e1`, edge `4.489165334070e2`, overlap `3.239718900261e2`, and C0-C4 physical R/Z mortar remains `5.833745908165e6` after the 128 C-backed inequality run | `certs/profile/profile_nk.json` plus `certs/profile/pressure_reconstruction.json` |
| Validated exponent `2/5<gamma<1/2` | Fixed branch `gamma=9/20`, `p=20/9`, `B=1` | Exact algebraic inequality for the rational exponent only; floating linkage to uncertified profile | Not certified as a theorem gate because no interval-certified admissible profile is linked to it | `certs/profile/profile_nk.json`, `certs/tail/tail_recurrence.json`, and manifest linkage |
| Natural tail, transseries, indicial certification | q1/forced-`q^p`/q2-zero diagnostics and floating Pluecker/Evans probes | Formal/floating; no interval box cover | Not certified; q1 exclusion and forced `q^p` are enforced in current seed, but recurrence and indicial exclusion are not interval-certified | `certs/tail/tail_recurrence.json`, `certs/tail/indicial_pluecker_cover.json`, `certs/profile/matching_determinant.json` |
| Finite unstable projection `rank P_+<infinity` | `tools/linearized_spectrum_probe.py` | Floating residual-Jacobian scaffold, not true Leray-projected operator | Not certified; geometric modes and Riesz projection are not validated | `certs/spectrum/projected_spectrum.json` |
| Stable-complement spectral gap | No proof-grade artifact | Floating/incomplete | Not certified; no high-frequency or large-`m` exclusion and no semigroup bound | `certs/spectrum/high_frequency_exclusion.json`, `certs/spectrum/stable_semigroup.json` |

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
supports chart/component/block restricted line-search via --solve-mode block-search,
supports broad generated guard grids via --guard-grid edge|box,
supports opt-in active guard PDE rows via --active-guard-weight,
supports objective-only line-search scoring via --line-search-eval objective-only.
supports two-sided seam-limit guard generation via --guard-seam-sides,
  --guard-seam-q, --guard-seam-eps, and --guard-seam-b-points.
supports first guarded-KKT diagnostic mode via --solve-mode guarded-kkt.
supports inequality active-set no-growth KKT via --solve-mode guarded-ineq-kkt.
supports analytic/column coefficient scaling and active-set row/column equilibration.
supports prediction-vs-actual line-search reports via --prediction-actual-report-out.
supports process-parallel PDE/active-guard row assembly via --stage0-workers.
supports native C R/Z mortar tail-Jacobian batches via --native-c.
supports native C PDE/guard tail-column batches via --native-c.
supports meaningful acceptance thresholds via --min-objective-decrease-abs/rel.
supports guarded rank/angle report output via --rank-report-out.
supports first-row cache output via --row-cache-out.
```

`validators/twochart_mortar_jacobian.py` now supports both old q/x rows and
true physical `(R,Z)` rows. The R/Z rows compose `q(R,Z)` and `x(R,Z)` using
the origin-chart jet machinery and keep the residual sign `tail - origin`.
Smoke checks:

```text
work/twochart_mortar_rz_smoke.json: fd max abs diff = 9.926964139595e-9
work/twochart_mortar_qx_regression_smoke.json: fd max abs diff = 1.817716110963e-8
work/twochart_mortar_rz_nativec_smoke.json: fd max abs diff = 4.351176130513e-8
C-vs-Python R/Z Jacobian comparison on a 2x3 C2 grid:
  max_abs = 4.628673195839e-7, max_rel = 4.105836156138e-12
```

Native C status:

```text
native/c/nsproof_kernel.c exports:
  nsproof_weighted_cheb_coeff_partial_array
  nsproof_rz_weighted_coeff_partials_batch
  nsproof_pde_tail_coeff_columns_batch
  nsproof_stage0_prediction_scan_batch

The R/Z batch path evaluates q(R,Z), x(R,Z), q^alpha, and Chebyshev jets in C
up to order 4 for tail coefficient Jacobian columns.

The PDE-tail batch path evaluates physical-space linearized PDE columns for
active tail variables at a `(q,b)` point, using Python-provided base profile
scalars but C-side mechanical variation jets and residual-kind normalization.

The Stage-0 prediction scan evaluates `residual + alpha * J * step` for the
already-built row/Jacobian system and returns native linear metrics for every
line-search alpha. It does not replace nonlinear acceptance checks.

Benchmark:
  NSPROOF_NATIVE_C_VALIDATION_PASSES=2 NSPROOF_NATIVE_C_REPEATS=50
  python3 tools/benchmark_native_c_kernel.py

Result:
  deterministic Chebyshev, R/Z, PDE-tail, and prediction validation passed,
  PDE tail validation: points=4, cases=320, max_abs=1.997e-6, max_rel=2.239e-13,
  scalar ctypes C about 11.16x faster than Python,
  batched ctypes C about 100.86x faster than Python for the weighted
  Chebyshev microkernel.
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
work/twochart_stage0_rz_coupled_tail_origin_norm48_guarded_report.json
work/twochart_stage0_rz_coupled_tail_origin_bal48_report.json
work/twochart_stage0_rz_coupled_tail_origin_bal48_trust1e3_report.json
work/twochart_stage0_rz_coupled_tail_origin_bal48_edgehp_report.json
work/twochart_stage0_rz_coupled_tail_origin_bal48_guardedge_report.json
work/twochart_stage0_rz_blocksearch24_chart_guardedge_iter3_report.json
work/twochart_stage0_rz_blocksearch24_chart_guardedge_iter3_mortar_rows.json
work/twochart_stage0_rz_blocksearch24_tail_jacinject_guardedge_report.json
work/twochart_stage0_rz_blocksearch24_tail_jacinject_multiguard_report.json
work/twochart_stage0_rz_tail_jacinject_guardgrid_edge_report.json
work/twochart_stage0_rz_tail_jacinject_activeguard_w10_qwide_report.json
work/twochart_stage0_rz_tail_jacinject_activeguard_w10_qwide_residual.json
work/twochart_stage0_rz_tail_jacinject_activeguard_w10_qwide_seamlim_report.json
work/twochart_stage0_rz_tail_jacinject_activeguard_w10_qwide_seamlim_residual.json
work/twochart_stage0_rz_guardedkkt_smoke_min_report.json
work/twochart_stage0_rz_guardedkkt_full16_probe_report.json
work/twochart_stage0_rz_guardedkkt_full16_probe_residual.json
work/twochart_stage0_rz_guardedkkt_rank_smoke_report.json
work/twochart_stage0_rz_guardedkkt_rank_smoke_rank.json
work/twochart_stage0_rz_guardedkkt_rank_smoke_rows.json
work/twochart_stage0_rz_kkt_seamlimit64_report.json
work/twochart_stage0_rz_kkt_seamlimit64_rank.json
work/twochart_stage0_rz_kkt_seamlimit64_residual.json
work/twochart_stage0_rz_kkt_seamlimit128_report.json
work/twochart_stage0_rz_kkt_seamlimit128_rank.json
work/twochart_stage0_rz_kkt_seamlimit128_residual.json
work/guarded_kkt_active_set_selftest.json
work/synth_inequality_guard_improves.json
work/twochart_stage0_rz_ineqkkt_ffrac64_report.json
work/twochart_stage0_rz_ineqkkt_ffrac64_rank.json
work/twochart_stage0_rz_ineqkkt_ffrac64_residual.json
work/twochart_stage0_rz_ineqkkt_ffrac64_scaled_w8_report.json
work/twochart_stage0_rz_ineqkkt_ffrac64_scaled_w8_residual.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_report.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_residual.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_c_report.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_c_rank.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_c_prediction.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_c_residual.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_c_mortar_c4.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_report.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_rank.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_prediction.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_residual.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_mortar_c4.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_report.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_rank.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_prediction.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_residual.json
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_mortar_c4.json
work/twochart_mortar_rz_nativec_smoke.json
work/guarded_kkt_rank_selftest.json
work/synth_mortar_polynomial_guardedkkt.json
work/synth_seam_switch_guardedkkt.json
work/synth_infeasible_edge_rank.json
work/twochart_stage0_smoke_residual.json
work/twochart_stage0_pde_hardpoints_residual.json
work/twochart_stage0_mortar_c2_residual.json
work/twochart_stage0_rz_active_mortar_trust5_residual.json
work/twochart_stage0_origin_only_rz_coupled_residual.json
work/twochart_stage0_rz_coupled_tail_origin_bal48_edgehp_residual.json
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

chart-balanced tail+origin Stage-0 with row-normalization guard:
  Jacobian row-normalized trial is rejected because scaled objective improves
  while raw sampled objective worsens.
  raw chart-balanced trust 0.01:
    sampled objective 6.180327501156e4 -> 6.176500260009e4
    C2 R/Z mortar max 4.214529161145e3 -> 4.214335665156e3
    edge holdout worsens to 4.555430954376e2
  raw chart-balanced trust 0.001:
    C2 R/Z mortar max -> 4.214509821220e3
    edge holdout -> 4.495798285817e2
  with edge hardpoint injected:
    edge holdout -> 4.489318148267e2
    C2 R/Z mortar max -> 4.214522613381e3
  with edge point used only as a line-search guard:
    accepted_any_step = false
    guard residual grows at every tested alpha down to 0.0625
  chart block-search, guarded edge, 3 iterations:
    accepted block = chart:origin on every iteration
    sampled objective 6.173191142295e4 -> 6.158294685900e4
    guard max 3.065963042569e2 -> 3.055238263138e2
    origin holdout -> 9.128755428936e1
    overlap holdout -> 3.235344358647e2
    edge holdout remains 4.489165350285e2
    C2 R/Z mortar max remains 4.214529161145e3
  seam-Jacobian injected tail variables:
    worst row = F dZZ at q=0.84, x=1.0
    top injected variables include tail.F_an[p24].c[0,10]
    sampled objective improves, but hidden edge q=0.86,b=0.20 blows up to 3.169794284607e5
    adding q=0.86,b=0.20 to guard rejects every tail seam step
  broad generated edge guard:
    `--guard-grid edge` composes generated guard points with explicit guards
    canonical run uses 46 effective guard points
    accepted_any_step = false
    hidden edge q=0.86,b=0.20 remains worst guard
    guard max is still 1.241904721621e3 at alpha=0.00390625
    baseline broad-guard max is 3.891736619747e2
  active guard rows plus objective-only line-search:
    active guard rows are now added after variable selection, so the edge grid
    constrains the least-squares direction without entering expensive candidate scoring.
    objective-only line-search avoids rebuilding candidate/Jacobian selection on each trial.
    This made the active-edge experiment feasible, but it did not produce profile progress.
    w1 active guard accepted a tail step; held-out edge max = 5.516786077531e4 at q=0.90,b=0.20.
    w1 low-b explicit guard accepted; held-out edge max = 3.162227861431e4 at q=0.90,b=0.20.
    w1 widened-q guard accepted; held-out edge max = 1.778391689505e3 at q=0.82,b=0.20.
    w10 widened-q guard accepted; held-out edge max = 1.255394972997e3 at q=0.90,b=0.20.
    w10 seam-limit guard accepted using q=0.8999999999999999,b=0.20 as an explicit tail-side guard.
    w10 seam-limit sampled objective = 4.124206167745e7 -> 4.115853419466e7.
    w10 seam-limit active guard rows = 168.
    w10 seam-limit held-out edge max = 3.119540552543e4 at q=0.78,b=0.20.
    w10 seam-limit origin max = 9.132494634431e1.
    w10 seam-limit overlap max = 3.239718884452e2.
    w10 seam-limit C0-C2 R,Z mortar max remains 4.214529161145e3.
    The pathology is mobile: guarding q=0.90,b=0.20 or the tail-side
    q=0.8999999999999999,b=0.20 shifts the damage to another low-b edge point.
  two-sided seam-limit guard interface:
    implemented after the w10 seam-limit diagnostic.
    dry-run confirms generated guard_qb_points_seam contains
      q=0.899999999999 and q=0.900000000001
      at requested b values.
    a later guarded-KKT full16 diagnostic accepts only a tiny constrained step,
      so this interface is infrastructure, not profile progress.
  equality guarded-KKT rank diagnostics:
    16-variable rank smoke:
      coverage = 1.0, active primary row is true worst F dZZ at q=0.84,x=1.0
      constraint rank/nullity = 15/1
      projected primary rank = 1
      rho_range = 2.104570557051e-1
      rho_grad = 3.551808344195e-17
      predicted_best_factor_inf = 1.001655284853
      accepted_any_step = false
    64-variable equality run:
      artifact = work/twochart_stage0_rz_kkt_seamlimit64_rank.json
      coverage = 1.0
      constraint rank/nullity = 61/3
      projected primary rank = 3
      rho_range = 4.641735513260e-1
      rho_grad = 1.166791334125e-6
      predicted_best_factor_inf = 1.005631658942
      held-out scan remains baseline-sized.
    128-variable equality run:
      artifact = work/twochart_stage0_rz_kkt_seamlimit128_rank.json
      coverage = 1.0
      constraint rank/nullity = 82/46
      projected primary rank = 8
      rho_range = 7.707656533008e-1
      rho_grad = 7.377401860355e-2
      predicted_best_factor_inf = 4.302267443263e-1
      best feasible step metrics are enormous
        l2 = 6.525901138807e12
        max_abs = 4.044264535809e12
      accepted nonlinear step still does not improve held-out scans:
        edge = 4.489165349915e2
        origin = 9.132494634431e1
        overlap = 3.239718884452e2
        C0-C4 R/Z mortar = 5.830256183569e6
  inequality active-set no-growth KKT:
    new helper = validators/guarded_kkt_active_set.py
    new solve mode = --solve-mode guarded-ineq-kkt
    self-test = work/guarded_kkt_active_set_selftest.json, ok = true
    synthetic inequality artifact = work/synth_inequality_guard_improves.json
      method = validators.guarded_kkt_active_set.solve_guarded_active_set
      equality no-change step h=0 leaves primary factor 1.0
      inequality no-growth step h ~= -10 reduces primary to ~1e-11
      signed guard growth is negative, so equality no-change is overrestrictive.
    bounded real-profile F_frac smoke:
      artifact = work/twochart_stage0_rz_ineqkkt_ffrac64_report.json
      pass = true for the linearized active-set constraints
      active constraints = 3 of 18 selected guard rows
      accepted block = block:F_frac, alpha = 1.0
      sampled objective 6.513151638216e7 -> 6.512774814621e7
      held-out edge = 4.489164259811e2
      origin = 9.132494634431e1
      overlap = 3.239718884452e2
      C0-C4 R/Z mortar = 5.833745519362e6
      This is not profile progress; it only proves the inequality mode is wired.
    scaled F_frac 64-variable inequality run with 8 Stage-0 workers:
      artifact = work/twochart_stage0_rz_ineqkkt_ffrac64_scaled_w8_report.json
      real time = 26.93s
      held-out standard = 1.016228983517e1
      secondary = 1.422825475247e1
      origin = 9.132494634431e1
      edge = 4.489165286038e2
      overlap = 3.239718884452e2
      C0-C4 R/Z mortar = 5.833744046958e6
    scaled all-block 128-variable inequality run with 8 Stage-0 workers:
      artifact = work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_report.json
      real time = 62.38s
      accepted full-block clipped step only
      objective decrease = 2.699795992672e1 from base 6.513175709741e7
      held-out edge = 4.489165334070e2
      origin = 9.132494644305e1
      overlap = 3.239718900261e2
      C0-C4 R/Z mortar = 5.833745908165e6
    actual C-backed R/Z mortar 128-variable inequality run:
      artifact = work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_c_report.json
      --native-c, --stage0-workers 8
      selected variables = 128 = 101 tail + 27 origin
      native_c_rz in Stage-0: calls=42, cases=804, seconds=0.000700
      accepted block = full
      alpha_applied = 1.593332995290e-7
      objective decrease = 2.699795988202e1 from base 6.513175709741e7
      prediction report entries = 15, accepted entries = 10
      first full-block actual/predicted improvement ratio = 337.0726
      smallest line-search ratio is the only near-linear one: alpha=0.00390625 gives ratio 1.3167
      held-out standard/focused = 1.016228983517e1
      secondary = 1.422825475247e1
      origin = 9.132494644305e1
      edge = 4.489165334070e2
      overlap = 3.239718900261e2
      C0-C4 R/Z mortar = 5.833745908165e6
      C4 mortar audit via native C path:
        artifact = work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_c_mortar_c4.json
        native_c_rz cases = 43560
        max_abs = 5.833745908165e6
    The 128 rank report is now finite-clipped and warning-free:
      coverage = 1.0
      constraint rank/nullity = 82/46
      rho_range = 0.771185631234
      rho_grad = 0.073774018604
      predicted_best_factor_inf = 0.430226722141
      best feasible step is still enormous, max_abs = 4.044264535809e12.
    actual C-backed R/Z + PDE-tail 128-variable inequality run:
      artifact = work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_report.json
      --native-c, --stage0-workers 8
      real time = 37.06s
      selected variables = 128 = 101 tail + 27 origin
      native_c_rz in Stage-0: calls=42, cases=804, seconds=0.000598
      native_c_pde in Stage-0: cases=1222, seconds=0.004336
      accepted block = full
      alpha_applied = 1.593332997368e-7
      objective decrease = 2.699795991182e1 from base 6.513175709741e7
      held-out standard/focused = 1.016228983517e1
      secondary = 1.422825475247e1
      origin = 9.132494644305e1
      edge = 4.489165334070e2
      overlap = 3.239718900261e2
      C0-C4 R/Z mortar = 5.833745908165e6
      C4 mortar audit:
        artifact = work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepde_w8_c_mortar_c4.json
        max_abs = 5.833745908165e6
      32-variable native/baseline smoke:
        same selected variables, same accepted block, same base metrics
        max line-trial objective delta = 1.490116119385e-8
    actual C-backed R/Z + PDE-tail + prediction 128-variable inequality run:
      artifact = work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_report.json
      --native-c, --stage0-workers 8
      real time = 38.06s
      selected variables = 128 = 101 tail + 27 origin
      native_c_rz in Stage-0: calls=42, cases=804, seconds=0.000593
      native_c_pde in Stage-0: cases=1222, seconds=0.004282
      native_c_prediction in Stage-0: cases=426240, seconds=0.003939
      accepted block = full
      objective decrease = 2.699795991182e1 from base 6.513175709741e7
      native linear prediction for full alpha=1 gives objective growth:
        native_linear_objective_improvement = -1.977735792398e2
        actual sampled objective improvement = 2.699795991182e1
      held-out standard/focused = 1.016228983517e1
      secondary = 1.422825475247e1
      origin = 9.132494644305e1
      edge = 4.489165334070e2
      overlap = 3.239718900261e2
      C0-C4 R/Z mortar = 5.833745908165e6
      C4 mortar audit:
        artifact = work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_mortar_c4.json
        max_abs = 5.833745908165e6
```

Held-out normalized structural checks remain far from proof scale:

```text
standard = 1.016228983517e1
secondary = 1.422825475247e1
origin = 9.132492825929e1
overlap = 3.239719410176e2
edge baseline = 4.489150149273e2
edge after latest accepted active-guard seam-limit tail step = 3.119540552543e4
latest guarded-KKT full16 held-out edge = 4.489165350285e2
latest equality-KKT 128 held-out edge = 4.489165349915e2
latest bounded inequality-KKT F_frac held-out edge = 4.489164259811e2
latest scaled 128 C-backed inequality-KKT held-out edge = 4.489165334070e2
latest native PDE+R/Z C-backed 128 inequality-KKT held-out edge = 4.489165334070e2
latest native prediction+C-backed 128 inequality-KKT held-out edge = 4.489165334070e2
C0-C2 R,Z mortar max = 4.214529161145e3
latest guarded-KKT full16 C0-C2 R,Z mortar max = 4.214529161145e3
latest bounded inequality-KKT F_frac C0-C4 R,Z mortar max = 5.833745519362e6
latest scaled 128 C-backed inequality-KKT C0-C4 R,Z mortar max = 5.833745908165e6
latest native PDE+R/Z C-backed 128 C0-C4 R,Z mortar max = 5.833745908165e6
latest native prediction+C-backed 128 C0-C4 R,Z mortar max = 5.833745908165e6
```

Important interpretation:

```text
The pre-lock toy smoke improvement is no longer trusted.
After q=0 tail locking, the solver mostly rejects updates.
The origin Taylor block has enough degrees to match the physical R/Z seam in
isolation, but doing so destroys the PDE residual. Therefore the blocker is not
mere origin algebraic capacity. It is the coupled tail-origin PDE/mortar balance
and the conditioning/blocking/acceptance logic of the Stage-0 linear system, not
gamma/B and not spectrum. Row normalization alone is not sufficient: when it is
guarded against raw sampled objective growth, it rejects the candidate step;
when chart-balanced raw steps are accepted, they still trade active objective
for held-out edge damage. If the edge is injected into the active set, the seam
barely moves; if it is used only as a guard, all candidate steps are rejected.
The first restricted block-search changes that: guarded origin-chart substeps
produce safe descent for origin/overlap/guard, but not for the worst R/Z mortar
row. Seam-Jacobian injection then shows why: the worst row is reachable through
high-degree tail variables, but those tail directions create severe hidden-edge
damage. A broad guard grid catches the same conflict down to tiny line-search
steps. Opt-in active guard rows make the active-edge experiment computationally
feasible, but the accepted tail steps still leave mobile hidden-edge spikes and
do not reduce the worst C0-C2 R/Z mortar row. The q=0.90 versus
q=0.8999999999999999 tests also show a one-sided seam-switch sensitivity: the
origin-side sample can look moderate while the tail-side seam-limit sample is
large. The next viable solver fork is explicit two-sided seam-limit guard
generation plus a cached KKT/Schur-style correction that computes seam descent
inside the edge-feasible tangent space. The 64/128 equality-KKT rank reports now
show that larger spaces can expose a nominal seam direction, but the accepted
nonlinear steps do not improve held-out residuals. The first inequality
active-set implementation proves equality no-change is too restrictive on a
synthetic case and is wired into the real solver, but the bounded real-profile
smoke and the 64/128 scaled inequality runs still leave the theorem-scale
blockers unchanged. The new C R/Z mortar path proves that native batched kernels
can be integrated without changing solver semantics, and the new PDE-tail C
path proves the same for tail coefficient columns in PDE/guard rows. The
32-variable native/baseline smoke matches solver decisions to roundoff, and the
128 native PDE+R/Z run reaches the same mathematical conclusion faster. The
native prediction scan adds fast linear line-search diagnostics and also shows
that the linear full-row prediction can disagree in sign with the nonlinear
sampled objective at the clipped step, so it must remain diagnostic rather than
an acceptance substitute. The remaining runtime bottleneck is now mostly
Python-side origin-column PDE work, base profile evaluation, active-set linear
algebra, and nonlinear objective/guard reevaluation. This is safe Stage-0
infrastructure progress, not a Newton basin.
```

Do not treat these Stage-0 artifacts as profile progress. Treat them as evidence about the next implementation fork.

Required Stage-0 decision:

```text
Decide whether the current two-chart Stage-0 evidence indicates bad
conditioning, missing variables/guards, wrong (gamma,B), illegal tail channels,
or branch death. Use the origin-only R/Z refit and guarded tail-Jacobian blowup
evidence explicitly. The next proposed computation must target that diagnosis.
```

The immediate solver fork is:

```text
two-sided seam-limit guard generation / cached active-row evaluation /
native multi-point PDE/active-guard residual/Jacobian kernels, then bounded
inequality active-set KKT with shifted-overlap 64/128/256 diagnostics.
```

Do not propose more sparse bumps, origin-only refits, or one-chart polishing as
the main path. Only after synthetic two-chart tests and guarded coupled solves
fail may `(gamma,B)` be freed. The radial core-tail matching route comes after
that parameter-search failure, not before.

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

Update after the chart-balanced conditioning probes:
`tools/profile_newton_twochart.py` now supports `--chart-balanced-selection`,
`--row-normalization`, `--max-raw-objective-growth`, `--guard-qb-points`,
`--solve-mode block-search`, `--block-search-labels`,
`--mortar-jacobian-candidate-count`, and `--candidate-pool-limit 0`. This
prevents a row-normalized scaled-objective decrease from being accepted when
the unscaled sampled objective or a held-out point worsens, can test restricted
substeps such as `chart:tail` and `chart:origin`, and can explicitly inject
variables from the largest active seam-row Jacobians. Current evidence:

```text
work/twochart_stage0_rz_coupled_tail_origin_norm48_guarded_report.json
  accepted_any_step = false
  reason: all line-search trials improve scaled objective but worsen raw objective

work/twochart_stage0_rz_coupled_tail_origin_bal48_report.json
  sampled objective = 6.180327501156e4 -> 6.176500260009e4
  C2 R/Z mortar max = 4.214529161145e3 -> 4.214335665156e3
  edge holdout = 4.555430954376e2

work/twochart_stage0_rz_coupled_tail_origin_bal48_trust1e3_report.json
  C2 R/Z mortar max = 4.214509821220e3
  edge holdout = 4.495798285817e2

work/twochart_stage0_rz_coupled_tail_origin_bal48_edgehp_report.json
  injected q=0.900, b=0.980 as a PDE hardpoint
  edge holdout = 4.489318148267e2
  C2 R/Z mortar max = 4.214522613381e3

work/twochart_stage0_rz_coupled_tail_origin_bal48_guardedge_report.json
  q=0.900, b=0.980 used only as line-search guard
  accepted_any_step = false
  guard max grows from 3.065963042569e2 even at alpha=0.0625

work/twochart_stage0_rz_blocksearch24_chart_guardedge_iter3_report.json
  solve mode = block-search over full, chart:tail, chart:origin
  accepted block = chart:origin for all 3 iterations
  sampled objective = 6.173191142295e4 -> 6.158294685900e4
  guard max = 3.065963042569e2 -> 3.055238263138e2
  origin holdout = 9.128755428936e1
  overlap holdout = 3.235344358647e2
  edge holdout = 4.489165350285e2
  C2 R/Z mortar max = 4.214529161145e3

work/twochart_stage0_rz_blocksearch24_chart_guardedge_iter3_mortar_rows.json
  worst row = F dZZ, q=0.84, x=1.0, residual = 4.214529161145e3
  top variables include high-degree tail.F_an/F_frac coefficients with kx=10

work/twochart_stage0_rz_blocksearch24_tail_jacinject_guardedge_report.json
  injected top active mortar-Jacobian variables into the tail block
  selected variables now include tail.F_an[p24].c[0,10], [5,10], [10,10]
  sampled objective = 6.104097875585e4 -> 6.100057015116e4
  hidden edge holdout blows up to 3.169794284607e5 at q=0.86,b=0.20

work/twochart_stage0_rz_blocksearch24_tail_jacinject_multiguard_report.json
  guard points = q=0.90,b=0.98 and q=0.86,b=0.20
  accepted_any_step = false
  q=0.86,b=0.20 guard grows to 2.008315326633e4 even at alpha=0.0625

work/twochart_stage0_rz_tail_jacinject_guardgrid_edge_report.json
  uses --guard-grid edge with 46 effective guard points
  accepted_any_step = false
  base broad-guard max = 3.891736619747e2
  q=0.86,b=0.20 remains the worst guard for every tested alpha
  guard max = 3.169794284607e5 at alpha=1
  guard max = 1.241904721621e3 at alpha=0.00390625
```

Interpretation: balanced tail+origin variables are now genuinely active, but
the current sampled system still trades seam movement against held-out edge
control under full steps. Restricted block-search finds safe guarded origin
descent, but it does not move the worst seam row. Seam-Jacobian injection shows
that direct tail control of the seam is possible only through directions that
create hidden-edge explosions. The broad guard-grid run confirms this is not a
narrow-guard artifact or coarse line-search issue. Broad edge active rows,
two-sided seam-limit guards, and the first guarded-KKT diagnostic path now
exist. The next implementation should add deterministic row/column caching plus
rank/angle reporting so larger guarded-KKT spaces can be tested without
confusing nearly-null constrained steps for profile progress. Do not weaken the
guard to accept the injected tail direction.

Implementation caution: direct active-edge-row retries with an uncapped
64-variable tail pool and with a bounded 24-variable pool both spent multiple
minutes in repeated Stage-0 scoring and were stopped without artifacts.  The
next active-edge attempt should first cache row/column evaluations or introduce
a dedicated guarded KKT/Schur mode; otherwise the experiment is too expensive
for the current CLI loop.

Latest active-guard update: `--active-guard-weight` and
`--line-search-eval objective-only` were added to make the active-edge
experiment cheaper. The resulting active-guard tail steps are still not profile
progress. The best documented seam-limit variant,
`work/twochart_stage0_rz_tail_jacinject_activeguard_w10_qwide_seamlim_report.json`,
uses 168 active guard rows and accepts a tiny objective reduction
`4.124206167745e7 -> 4.115853419466e7`, but its held-out residual scan
`work/twochart_stage0_rz_tail_jacinject_activeguard_w10_qwide_seamlim_residual.json`
has edge max `3.119540552543e4` at `q=0.78,b=0.20` and unchanged C0-C2 R/Z
mortar max `4.214529161145e3`. Therefore active guard rows are useful
infrastructure, but not the missing solver. Two-sided seam-limit guard
generation and a first guarded-KKT diagnostic path are now implemented. The next
implementation must add cached row/column evaluation, synthetic guarded-KKT
tests, and rank/angle reports for infeasible or nearly-null seam descent.

Latest guarded-KKT update: `--solve-mode guarded-kkt` now has row-cache and
rank/angle diagnostics. It still solves a damped equality-constrained KKT
system with configurable primary row labels and constraint row labels. The
current diagnostic configuration uses mortar rows as the primary objective and
active guard rows as first-order no-change constraints. This is not yet an
inequality active-set Schur solver, but it can now report whether the selected
tangent space has active worst-row coverage and a guarded seam-reduction
direction.

```text
New flags:
  --solve-mode guarded-kkt
  --guarded-kkt-primary-labels
  --guarded-kkt-constraint-labels
  --guarded-kkt-constraint-damping
  --guarded-kkt-max-constraints
  --min-objective-decrease-abs
  --min-objective-decrease-rel
  --rank-report-out
  --rank-coverage-min
  --row-cache-out
```

Current guarded-KKT evidence:

```text
work/twochart_stage0_rz_guardedkkt_smoke_min_report.json
  tail-only smoke, 8 variables, 12 active guard constraints
  status = TWOCHART_NEWTON_STAGE0_NO_IMPROVEMENT_NOT_PROOF
  purpose = verifies roundoff-sized objective drift is no longer counted as accepted

work/twochart_stage0_rz_guardedkkt_full16_probe_report.json
  full tail+origin block, 16 variables, 24 active guard constraints
  accepted_any_step = true, but the accepted step is tiny
  base objective = 4.245518940312e5
  objective decrease = 8.936499519041e-2
  max coefficient update = 2.335227790090e-7
  primary mortar max in sampled system = 1.915621463995e1
  active guard max in sampled system = 4.489165350257e2
  predicted primary row change max = 7.796744244926e-3
  predicted constraint row change max = 8.257363783169e-10

work/twochart_stage0_rz_guardedkkt_full16_probe_residual.json
  held-out standard max = 1.016228983517e1
  held-out secondary max = 1.422825475247e1
  held-out origin max = 9.132494634460e1
  held-out overlap max = 3.239718884456e2
  held-out edge max = 4.489165350285e2
  C0-C2 R/Z mortar max = 4.214529161145e3

work/twochart_stage0_rz_guardedkkt_rank_smoke_rank.json
  first rank/angle smoke with true worst-row coverage
  row cache = work/twochart_stage0_rz_guardedkkt_rank_smoke_rows.json
  Stage-0 run = work/twochart_stage0_rz_guardedkkt_rank_smoke_report.json
  active primary raw max = 4.214529161145e3
  held-out/unfiltered mortar max = 4.214529161145e3
  coverage = 1.0
  worst row = F dZZ at q=0.84, x=1.0
  rows = 49 total, 11 primary mortar, 30 active guard constraints
  columns = 16
  linear algebra backend = numpy_svd_lstsq
  active guard constraint rank = 15
  equality-constraint nullity = 1
  projected primary rank = 1
  rho_range = 2.104570557051e-1
  rho_grad = 3.551808344195e-17
  predicted_best_factor_inf = 1.001655284853
  accepted_any_step = false

synthetic guarded-KKT tests:
  work/synth_mortar_polynomial_guardedkkt.json: pass, mortar reduction factor 3.248924180291e12, guard growth 1.0
  work/synth_seam_switch_guardedkkt.json: pass, includes q=0.899999999999 and q=0.900000000001
  work/synth_infeasible_edge_rank.json: pass, rank_obstruction = true
```

Interpretation: the previous full16 KKT probe was under-covered because its
sampled primary mortar max was only about `19` while the true C0-C2 mortar max
was `4214`. The new rank smoke fixes that coverage flaw for a small 16-variable
system: it includes the true worst row and still finds only a constrained-null
or worsening equality-KKT direction. This is stronger evidence about the small
selected tangent, but it is not a fixed-branch kill signal. Next test 64, 128,
and 256 variables, add inequality no-growth KKT, and shift overlap schedules
before freeing `(gamma,B)`.

## 6. Current Repository Tooling

The repository has these relevant tools and validators:

```text
tools/profile_project_cheb.py
tools/profile_newton_cheb.py
tools/profile_newton_twochart.py
tools/profile_newton_adaptive.py
tools/profile_projected_hardpoints.py
tools/profile_twochart_synthetic_tests.py
tools/validate_tail.py
tools/validate_tail_recurrence.py
tools/tail_leading_exponent.py
tools/profile_zero_q2_trace.py
tools/validate_indicial_evans.py
tools/linearized_spectrum_probe.py
validators/compactified_equations.py
validators/compactified_equations_twochart.py
validators/twochart_mortar_jacobian.py
validators/twochart_row_cache.py
validators/guarded_kkt_rank.py
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

tools/profile_newton_twochart.py:
  supports q2-zero locked Stage-0 two-chart diagnostics,
  physical R/Z mortar rows,
  analytic sampled PDE Jacobian rows,
  chart-balanced variable selection,
  block-search line-search,
  broad guard grids,
  active guard rows,
  objective-only line-search scoring,
  two-sided seam-limit guard generation,
  first guarded-KKT diagnostic mode,
  row-cache output,
  guarded-KKT rank/angle report output.

validators/guarded_kkt_rank.py:
  computes floating coverage, constraint nullity, projected primary rank,
  rho_range, rho_grad, predicted seam factor, and top variable diagnostics;
  uses NumPy SVD/lstsq when available and a pure-Python fallback otherwise.

validators/twochart_row_cache.py:
  serializes selected variables, row metadata, weighted residuals, and sparse
  dense-row Jacobian entries for the sampled Stage-0 system.

tools/profile_twochart_synthetic_tests.py:
  provides deterministic synthetic guarded-KKT tests for manufactured mortar
  descent, two-sided seam-switch labeling, and infeasible-edge rank obstruction.

validators/compactified_equations_twochart.py and validators/twochart_mortar_jacobian.py:
  provide floating two-chart residual and R/Z mortar Jacobian diagnostics.
```

The current tools are discovery/proof-scaffold tools. They are not yet interval proof tools.

## 7. Inline Context from the DeepMind / Google Paper

The archive `arXiv-2509.14185v1.tar.gz` in the workspace is the source bundle
for `Discovery of Unstable Singularities`. This is the "Google paper thing" to
keep inline in every GPT-5 Pro handoff. It is useful as a discovery playbook,
not as a Navier-Stokes certificate.

Applicability boundary:

```text
The paper studies unstable self-similar singularities in CCF, 2D IPM with
boundary, and 2D Boussinesq / Euler-with-boundary analogues.
It does not provide the missing 3D axisymmetric-with-swirl NS profile.
It explicitly frames PINN-style machinery as specialized discovery machinery,
not a general proof engine.
It says computer-assisted proof suitability is problem-dependent.
Its spectral discovery section learns nonnegative real eigenvalues under a
real-axis assumption; NSProof needs complex contour/Fredholm/Evans validation
of the true Leray-projected operator.
```

Transfer these methods, but do not confuse them with certificates:

```text
1. Factor mechanical vanishing prefactors before optimizing residuals.
2. Add higher-derivative and smoothness losses to prevent spiky collocation overfit.
3. Use residual-driven adaptive hard-point sampling.
4. Use staged linearized correction rather than blind global optimization.
5. Discover parameters through smoothness/funnel scans, not blind continuation.
6. Treat neural/PINN-style discovery as a profile-finding engine, not a proof certificate.
```

Specific method-transfer map for NSProof:

```text
Solution modeling / equation factorization:
  compactify the domain;
  multiply unknowns by exact envelopes enforcing parity, origin smoothness,
  tail behavior, and forbidden modes;
  divide equations by exact mechanical prefactors;
  optimize the quotient residual, not raw equations.

Training loss analogue:
  d0 residual -> normalized structural PDE quotient rows;
  d1/d2 residuals -> derivative mortar rows, seam-limit guards, smoothness
  penalties, and later C3/C4 interface rows;
  dense validation max residual -> standard/focused/secondary/origin/edge
  scans plus shifted/off-grid checks.

Collocation/adaptive sampling analogue:
  use hard points from dense residual topology scans;
  sample both high-gradient regions and broad guard regions;
  add small shifted/one-sided seam perturbations to prevent grid-aligned
  chart-switch blind spots.

Second-order optimizer analogue:
  use Gauss-Newton / Levenberg-Marquardt in coefficient space;
  use block-search only as a diagnostic;
  next solver should be cached active-row KKT/Schur, not first-order descent.

Multistage correction analogue:
  once Stage-0 identifies the residual shape, solve D E[u] h = -E[u] in a
  dedicated correction space;
  choose enrichment modes from residual spectral/patch content;
  then re-project into the proof-native Chebyshev/Bernstein representation.

Funnel/admissibility analogue:
  only after the fixed hard two-chart solver is real, run a (gamma,B) funnel;
  a funnel is discovery evidence only;
  final admissibility still needs interval transversality/NK certificates.
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

Do not re-explain general Navier-Stokes background. Use the repo's current
numbers and artifacts. Your answer should force a binary execution tree:

```text
1. Fix the coupled two-chart solve.
2. If fixed (gamma,B) fails after that solve is real, free (gamma,B).
3. If the parameter funnel fails with legal tail constraints, pivot to radial
   core-tail matching.
4. If radial matching also fails with interval certificates, reject the current
   ansatz class.
```

The current near-term decision is:

```text
Can the two-chart (q,x)/(R,Z) solver satisfy the normalized PDE equations and
physical R/Z seam smoothness simultaneously?
```

Use the latest evidence explicitly:

```text
origin-only degree-8 R/Z refit: C2 mortar 4.214e3 -> 2.20e1,
but origin/edge PDE holdouts become about 2.27e3;
coupled origin-only Stage-0: preserves PDE scale, but C2 mortar only
4.214529e3 -> 4.214512e3.
```

You must decide whether this indicates bad conditioning/incomplete coupled
solver, wrong fixed `(gamma,B)`, illegal tail channel such as unresolved `q^2`,
or a dead branch.

Required certificate outputs should be named explicitly. At minimum:

```text
certs/profile/profile_nk.json
certs/tail/tail_recurrence.json
certs/tail/indicial_pluecker_cover.json
certs/profile/pressure_reconstruction.json
certs/profile/matching_determinant.json
certs/spectrum/projected_spectrum.json
certs/spectrum/high_frequency_exclusion.json
certs/spectrum/stable_semigroup.json
certs/theorem/lyapunov_perron_constants.json
certs/final_theorem_manifest.json
```

For every certificate schema, specify backend, precision, interval widths,
profile/input hashes, pass/fail field, dependency hashes, and reproducible
commands. Missing hash linkage means the certificate is not part of the final
manifest.

The theorem certificate may move above 0% only when all five stop-condition
gates have certificates linked by `certs/final_theorem_manifest.json`. Scaffold
progress, low residuals, or floating diagnostics do not change the theorem
percentage.

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
  --out work/v117_twochart_baseline_residual.json

python3 -m validators.compactified_equations_twochart \
  --profile work/v117_twochart_init.json \
  --mortar-order 4 \
  --scan overlap \
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

Given the latest active-guard evidence, the next work should not be more
isolated origin refits, more sparse bumps, or another one-sided guard sample.
The broad guard and active-guard probes already show that the seam damage is
mobile across low-`b` edge points and that `q=0.90` versus
`q=0.8999999999999999` can change which chart side is sampled. The immediate
implementation work is:

```text
1. DONE: add explicit two-sided seam-limit guard generation, e.g.
   q=q_switch-eps and q=q_switch+eps for the same b grid, with eps recorded
   in the report. Do not rely on decimal q=0.90 as a chart-side proxy.
   Current flags:
     --guard-seam-sides none|below|above|both
     --guard-seam-q
     --guard-seam-eps
     --guard-seam-b-points

2. DONE FOR FIRST SYSTEM: emit a serializable row cache for selected variables
   and selected q,b/mortar rows with `--row-cache-out`. This is not yet a
   reusable incremental evaluator, but it makes the sampled KKT system auditable.

3. DONE/PARTIAL: add guarded KKT/Schur solve modes:
   - primary equation: reduce active R/Z seam mortar rows;
   - constraints: no growth in broad edge/seam-limit PDE rows and no tail-gate
     damage;
   - regularization: penalize high-degree tail coefficients that create edge
     oscillation;
   - fallback: if the KKT system is singular, return a certificate of rank
     deficiency and the offending row/column subspace.
   Current implementation has a damped equality-constrained KKT diagnostic, a
   rank/angle diagnostic, and a first inequality active-set no-growth solver in
   `tools/profile_newton_twochart.py`. The inequality mode is wired and passes
   synthetic tests, but the broad real-profile run needs better scaling before
   it can be used as a branch-kill diagnostic.

4. DONE FOR 64/128 EQUALITY AND BOUNDED 64 INEQUALITY: run larger Stage-0
   diagnostics.
   - 64 equality: no useful seam descent, nullity 3.
   - 128 equality: nominal seam direction appears, but accepted nonlinear step
     does not improve held-out residuals.
   - 64 bounded inequality F_frac: mode is wired, but held-outs remain baseline.

5. NEXT: improve active-set row/column scaling, run bounded 128 inequality
   diagnostics, then run 256 only if 128 is numerically stable. Add shifted
   overlap schedules before any fixed-branch kill claim.
```

```bash
python3 tools/profile_newton_twochart.py \
  --input work/v117_twochart_init.json \
  --out work/twochart_stage0_rz_kkt_seamlimit.json \
  --report-out work/twochart_stage0_rz_kkt_seamlimit_report.json \
  --rank-report-out work/twochart_stage0_rz_kkt_seamlimit_rank.json \
  --row-cache-out work/twochart_stage0_rz_kkt_seamlimit_rows.json \
  --blocks tail,origin,interface \
  --variable-charts tail,origin \
  --solve-mode guarded-kkt \
  --gamma-fixed --B-fixed \
  --residual-kind normalized-structural \
  --q2-policy zero \
  --mortar-coordinates RZ \
  --mortar-order 2 \
  --mortar-q-samples 2 \
  --mortar-x-samples 5 \
  --mortar-active-count 12 \
  --guard-grid edge \
  --guard-q-min 0.76 --guard-q-max 0.92 \
  --guard-b-min 0.10 --guard-b-max 0.98 \
  --guard-q-samples 9 --guard-b-samples 9 \
  --guard-seam-sides both \
  --guard-seam-q 0.90 \
  --guard-seam-eps 1e-12 \
  --active-guard-weight 10 \
  --guarded-kkt-primary-labels mortar \
  --guarded-kkt-constraint-labels active_guard \
  --guarded-kkt-max-constraints 18 \
  --line-search-eval objective-only \
  --row-normalization none \
  --max-raw-objective-growth 1 \
  --max-guard-objective-growth 1 \
  --max-guard-max-growth 1 \
  --max-variables 64 \
  --candidate-origin-degree-max 8 \
  --candidate-kq-max 8 \
  --candidate-kx-max 8 \
  --candidate-pool-limit 256 \
  --max-iter 1 \
  --trust 0.001 \
  --lm-lambda 1e-6 \
  --pde-weight 1 \
  --mortar-weight 0.01 \
  --line-search 1,0.25,0.0625,0.015625,0.00390625
```

The flags `--guard-seam-sides`, `--guard-seam-q`, `--guard-seam-eps`,
`--guard-seam-b-points`, `--solve-mode guarded-kkt`,
`--solve-mode guarded-ineq-kkt`, `--rank-report-out`, and `--row-cache-out` are
implemented. Synthetic guarded-KKT and inequality-over-equality tests pass. The
missing pieces are numerically stable 128/256 inequality diagnostics, better
active-set scaling, and shifted overlap schedule tests.

Next bounded inequality diagnostic after scaling cleanup:

```bash
python3 tools/profile_newton_twochart.py \
  --input work/v117_twochart_init.json \
  --out work/twochart_stage0_rz_ineqkkt_seamlimit128.json \
  --report-out work/twochart_stage0_rz_ineqkkt_seamlimit128_report.json \
  --rank-report-out work/twochart_stage0_rz_ineqkkt_seamlimit128_rank.json \
  --row-cache-out work/twochart_stage0_rz_ineqkkt_seamlimit128_rows.json \
  --blocks tail,origin,interface \
  --variable-charts tail,origin \
  --solve-mode guarded-ineq-kkt \
  --block-search-labels full,block:F_frac,chart:origin \
  --gamma-fixed --B-fixed \
  --residual-kind normalized-structural \
  --q2-policy zero \
  --mortar-coordinates RZ \
  --mortar-order 2 \
  --mortar-q-samples 3 \
  --mortar-x-samples 7 \
  --mortar-active-count 16 \
  --guard-grid edge \
  --guard-q-min 0.76 --guard-q-max 0.92 \
  --guard-b-min 0.10 --guard-b-max 0.98 \
  --guard-q-samples 9 --guard-b-samples 9 \
  --guard-seam-sides both \
  --guard-seam-q 0.90 \
  --guard-seam-eps 1e-12 \
  --active-guard-weight 10 \
  --guarded-kkt-primary-labels mortar \
  --guarded-kkt-constraint-labels active_guard \
  --guarded-kkt-max-constraints 32 \
  --guarded-ineq-max-active 32 \
  --guarded-ineq-tolerance 1e-10 \
  --guarded-ineq-target nonincrease \
  --line-search-eval objective-only \
  --row-normalization none \
  --max-raw-objective-growth 1 \
  --max-guard-objective-growth 1 \
  --max-guard-max-growth 1 \
  --max-variables 128 \
  --candidate-origin-degree-max 10 \
  --candidate-kq-max 10 \
  --candidate-kx-max 10 \
  --candidate-pool-limit 512 \
  --max-iter 1 \
  --trust 0.001 \
  --lm-lambda 1e-6 \
  --pde-weight 1 \
  --mortar-weight 0.01 \
  --line-search 1,0.25,0.0625,0.015625,0.00390625
```

Continue only if held-out C2/C4 mortar and edge/origin scans improve together.
If active-set overflow warnings recur, fix row/column scaling before treating
the run as evidence.

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

End with this exact section:

```text
What would make the theorem certificate nonzero?
```

The answer must be: all five stop-condition gates linked by
`certs/final_theorem_manifest.json` with interval certificates. Anything else
is scaffold progress only.

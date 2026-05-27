# GPT-5 Pro Prompt Diffs Since Last Update

Reset rule:
This file was cleared after the latest GPT-5 Pro handoff was pasted back into
the repo workflow. It now contains only the post-handoff deltas that accumulated
after that response.

Canonical full prompt:
`gpt5-pro-proof-prompt.md`

## Delta 2026-05-27

### Native Origin PDE Columns

- Added a native C origin PDE-column batch kernel:
  `nsproof_pde_origin_coeff_columns_batch(...)` in
  `native/c/nsproof_kernel.c`.
- Added integer jet powers for origin monomials `R^a Z^b`, avoiding real-power
  jets for zero-valued monomial bases.
- Added Python wrapper
  `native_origin_linearized_residuals_with_kind(...)` in
  `validators/compactified_equations_twochart.py`.
- Wired `tools/profile_newton_twochart.py` so `--native-c` now uses native
  columns for both tail and origin variables in point workers, PDE-row
  construction, PDE candidate injection, and PDE prescoring.

Validation:

```text
python3 -m py_compile validators/compactified_equations_twochart.py \
  validators/twochart_mortar_jacobian.py tools/profile_newton_twochart.py

native-vs-Python origin column smoke:
  cases = 432 residual components
  max_abs = 1.0658141036401503e-13
  max_rel = 3.668236317481109e-15
```

Production smoke:

```text
artifact:
  work/twochart_stage0_current_profile_originpde_native_smoke32*

selected_by_chart = tail:16, origin:16
native_c_pde cases = 898
accepted_any_step = true
```

### 128 C-Backed Dense-C4 Diagnostic

Ran:

```text
work/twochart_stage0_current_profile_originpde_densec4active128_step34_nativebatch*
```

Key setup:

```text
input = work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch.json
max_variables = 128
mortar_active_source = audit
mortar_active_count = 96
mortar_active_per_q = 4
mortar_active_per_derivative = 2
native_c = true
stage0_workers = 8
```

Selection and native stats:

```text
selected_by_chart = tail:74, origin:54
selected_by_block:
  origin.F_origin_taylor = 27
  origin.G_origin_taylor = 27
  tail.F_an = 28
  tail.F_frac = 46
row_groups = pde:2, mortar:96, active_guard:242
native_c_pde cases = 3139
native_c_rz cases = 39888
native_c_prediction cases = 1566720
```

Rank:

```text
coverage = 1.0
constraint rank/nullity = 50/78
rho_grad = 8.208533313446829e-1
rho_range = 9.649717354802322e-1
predicted_best_factor_inf = 3.282823654953756e-1
best feasible step max_abs = 5.458994357297978e5
```

Result:

```text
accepted_any_step = true
accepted_block = block:F_frac
accepted_alpha = 0.015625
dense C4 audit: 4.922540831420457e6 -> 4.920054735867473e6
edge audit: 4.326812264740244e2 -> 4.3253443342925294e2
coupled normalized audit: 1.0 -> 9.996607362746757e-1
```

Posthoc audit:

```text
standard = 1.016228983517e1
focused = 1.016228983517e1
secondary = 1.422825435582e1
origin = 9.132497540774e1
edge = 4.325344334293e2
overlap = 3.239711929243e2
C0-C4 R/Z mortar = 4.920054735867e6
```

Interpretation:

```text
This is real but tiny floating progress. It is not proof progress and not
interval Newton entry. It does show that the native C coupled tail-origin path
is wired and can move the dense C4 blocker and edge blocker together in one
accepted 128-variable diagnostic.
```

### Origin Degree-12 Coupled Diagnostics

Implemented `ensure_origin_candidate_degree(...)` in
`tools/profile_newton_twochart.py`.

Reason:

```text
Previous 192-variable runs with --candidate-origin-degree-max 12 did not
actually add origin directions because the current profile only contained
degree-6 origin Taylor blocks. Larger spaces only added tail coefficients.
```

Behavior:

```text
Before coefficient enumeration, Stage-0 now appends zero origin Taylor
monomials through the requested candidate degree and records
origin_degree_extension in reports.
```

Direct check:

```text
degree 6 -> degree 8:
  F_origin_taylor added 17, basis_count 45
  G_origin_taylor added 17, basis_count 45
```

Diagnostic without all guard constraints:

```text
artifact:
  work/twochart_stage0_current_profile_originD12_densec4active192_step36_nativebatch*

origin_degree_extension:
  F_origin_taylor: added 63, old_degree 6, new_degree 12, basis_count 91
  G_origin_taylor: added 63, old_degree 6, new_degree 12, basis_count 91

selected_by_chart = tail:96, origin:96
selected_by_block:
  origin.F_origin_taylor = 64
  origin.G_origin_taylor = 32
  tail.F_an = 34
  tail.F_frac = 62

rank:
  coverage = 1.0
  constraint rank/nullity = 54/138
  rho_grad = 8.224658078556173e-1
  rho_range = 9.862599240658366e-1
  predicted_best_factor_inf = 1.6538055228309306e-1

result:
  accepted_any_step = false
  best coupled audit = 9.994560603005692e-1
  rejection = guard_growth
  best trial guard max = 1025.1139500857532
  base guard max = 1012.8832119698444
```

Diagnostic with all active guards allowed in active-set cap:

```text
artifact:
  work/twochart_stage0_current_profile_originD12_densec4active192_allguards_step37_nativebatch*

--guarded-kkt-max-constraints 256
--guarded-ineq-max-active 256

selected_by_chart = tail:96, origin:96
accepted_any_step = false
best coupled audit = 9.994560881279618e-1
rejection = guard_growth
worst guard remains q=0.8999999999999999, b=0.9899999999999999, e_psi
```

Interpretation:

```text
The degree-12 origin extension makes the 192-variable test a true coupled
tail-origin diagnostic. It still does not produce an accepted nonlinear step.
The obstruction is now sharper: predicted seam freedom exists in the expanded
space, but the best nonlinear audit-decreasing steps grow the high-b edge guard.
```

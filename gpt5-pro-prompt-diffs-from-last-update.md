# GPT-5 Pro Prompt Diffs Since Last Update

Reset rule:
After the next GPT-5 Pro response is pasted back into the repo workflow, clear
this file and start accumulating only the new deltas after that response.

## Delta 2026-05-27

Context:
The full canonical prompt is `gpt5-pro-proof-prompt.md`. This file records only
what changed after the last GPT-5 Pro handoff, so it can be pasted as a compact
incremental update if needed.

### Prompt / Repo

- Pushed `1e0aaf3 Target explicit edge and C4 mortar rows`.
- Pushed `87f323d Update GPT Pro prompt with targeted C4 diagnostics`.
- Updated `gpt5-pro-proof-prompt.md` again with chart-balanced and broad-audit
  diagnostics; this update is pending commit at the time this delta file was
  created.

### New Diagnostics

Chart-balanced one-point C4 audit:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_step26_nativebatch*

selected_by_chart = tail:92, origin:36
accepted_any_step = true
accepted_block = block:F_an

targeted audit:
  edge max: 4.3625781300704136e2 -> 3.1348631998536905e2
  targeted q=0.91,x=1.0 C4 max: 4.963232981363504e6 -> 1.0988322874909114e5

held-out audit:
  full 9x9 C0-C4 R/Z mortar max = 1.080945313983e9

interpretation:
  false one-point C4 overfit; not profile progress.
```

One-q broad C4 audit:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_coupledaudit128_balanced_broadaudit_step27_nativebatch*

selected_by_chart = tail:92, origin:36
broad C4 audit rows = 1350
base broad C4 max = 4.364062941499776e6 at q=0.92,x=1.0,RZ:F:dRRRR
accepted_any_step = false

best PDE-improving alpha=1 trial:
  edge ratio = 0.7185804142384706
  broad C4 ratio = 250.58372800852717
  rejected

interpretation:
  broad native audit correctly rejects one-point overfit.
```

Two-q broad C4 audit:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch*

objective C4 q-values = 0.91,0.92
objective C4 x-values = 1.0
broad C4 audit rows = 1350
selected_by_chart = tail:95, origin:33
accepted_any_step = true
accepted_block = block:F_frac

rank:
  coverage = 1.0
  constraint rank/nullity = 39/89
  primary rank/projected rank = 18/14
  rho_grad = 9.999999999999873e-1
  rho_range = 9.998289222102589e-1
  predicted_best_factor_inf = 1.4228699996405914e-2

best accepted alpha = 0.015625
coupled audit value = 0.9972256083949639
edge residual audit max: 4.3625781300704136e2 -> 4.350474629930032e2
broad C4 audit max: 4.364062941499776e6 -> 4.351955117770506e6

held-out post-audit:
  standard = 1.016228983517e1
  focused = 1.016228983517e1
  secondary = 1.422825435582e1
  origin = 9.132497540774e1
  edge = 4.326812264740e2
  overlap = 3.239711929243e2
  full 9x9 C0-C4 R/Z mortar max = 4.922540831420e6
  5x9 overlap-only C0-C4 R/Z mortar max = 4.328283218032e6
  tail gate remains q1-free, forced q^p OK, q2-zero OK at floating gate.

interpretation:
  first small real coupled tail-origin improvement under broad native C4 audit;
  still very far from Stage-0 success and not NK-entry scale.
```

### Current Next Step

Run a three-q broad-audit continuation:

```text
input:
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch.json

objective C4 q-values:
  0.90,0.91,0.92

max_variables:
  160 first, then 192 if the coupled audit keeps decreasing.

acceptance:
  broad 1350-row C4 audit and edge audit must improve together.
```

### Follow-up Delta: Three-q 160 Run

Three-q broad C4 audit:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_q909192_broadaudit160_step29_nativebatch*

input:
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch.json

objective C4 q-values = 0.90,0.91,0.92
max_variables = 160
selected_by_chart = tail:128, origin:32
selected_by_block = tail.F_an:46, tail.F_frac:82,
                    origin.F_origin_taylor:17, origin.G_origin_taylor:15
accepted_any_step = false

rank:
  coverage = 1.0
  constraint rank/nullity = 57/103
  primary rank/projected rank = 22/21
  rho_grad = 8.089475942616127e-1
  rho_range = 9.997655112981494e-1
  predicted_best_factor_inf = 2.0015248944221704e-2

base audits:
  edge residual audit max = 4.326812264740244e2
  broad C4 audit max = 4.328283218032057e6

best improving but rejected alpha=0.015625:
  edge residual audit max = 4.3198405405916975e2
  broad C4 audit max = 4.32130957175972e6
  coupled audit value = 0.9983888193260357
  rejected because guard_growth_ok=false
  guard max grows from 1.0152983039805788e3 to 1.0221510615264315e3
  worst guard row = q=0.8999999999999999,b=0.99,e_psi

interpretation:
  three-q objective plus broad C4 audit finds a descent direction, but it moves
  the adjacent b=0.99 edge guard. Next surgical run should include
  q=0.8999999999999999,b=0.99 as a primary PDE row, not weaken the guard.
```

### Follow-up Delta: Guard-aware Step30, Max-raw Step31, Explicit-q Step32

Guard-aware step30:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_q909192_edge990_broadaudit160_step30_nativebatch*

input:
  work/twochart_stage0_current_profile_targeted_edge_c4_q91092_broadaudit128_step28_nativebatch.json

primary PDE points:
  q=0.8999999999999999,b=0.98
  q=0.8999999999999999,b=0.99

objective C4 q-values = 0.90,0.91,0.92
max_variables = 160
selected_by_chart = tail:128, origin:32
accepted_any_step = false

rank:
  coverage = 1.0
  constraint rank/nullity = 57/103
  primary rank/projected rank = 23/21
  rho_grad = 8.097016142990042e-1
  rho_range = 9.996733799524907e-1
  predicted_best_factor_inf = 2.06254920673346e-2

best audit-improving trial:
  block = component:F
  alpha = 0.015625
  coupled audit value = 0.9983998727995577
  edge audit max = 4.326812264740244e2 -> 4.319888330338395e2
  broad C4 audit max = 4.328283218032057e6 -> 4.321357414323666e6
  guard max = 1.0152983039805788e3 -> 1.0136729692850924e3
  rejected only because raw selected-row l2 objective grows:
    3.054638861620e9 -> 3.361715416663e9

interpretation:
  q=0.9,b=0.99 as a primary PDE row removes the guard-growth blocker. The
  remaining issue is acceptance geometry: worst-row/broad-audit max improves
  while selected-row l2 objective redistributes upward.
```

Code/reporting change:

```text
tools/profile_newton_twochart.py:
  added --raw-growth-metric objective|max-abs
  default = objective, preserving previous behavior
  line-search trials now report rejection_reasons
  prediction-actual reports now include rejection_reasons and raw growth values

verification:
  python3 -m py_compile tools/profile_newton_twochart.py
```

Max-raw step31:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_q909192_edge990_broadaudit160_step31_rawmax_nativebatch*

setup:
  same as step30, plus --raw-growth-metric max-abs.

accepted:
  accepted_any_step = true
  accepted_block = component:F
  accepted_alpha = 0.015625
  coupled audit value = 0.9983998727995577
  selected raw max = 4.922540831420477e4 -> 4.9146641399183085e4
  edge line-search audit = 4.326812264740244e2 -> 4.319888330338395e2
  broad line-search C4 audit = 4.328283218032057e6 -> 4.321357414323666e6
  guard max decreases to 1.0136729692850924e3

posthoc dense audit:
  standard = 1.016228983517e1
  focused = 1.016228983517e1
  secondary = 1.422825435582e1
  origin = 9.132497540620e1
  edge = 4.319888330338e2
  overlap = 3.239711929196e2
  full 9x9 C0-C4 R/Z mortar max = 5.817536665279e6
  worst dense C4 row = RZ:F:dRRRR at q=0.89,x=1.0

interpretation:
  not promotable. The max-norm raw gate accepts the local audit descent, but
  the dense C4 spike moves to q=0.89 and worsens.
```

Explicit-q step32:

```text
artifacts:
  work/twochart_stage0_current_profile_targeted_edge_c4_q89909192_edge990_explicitaudit160_step32_rawmax_nativebatch*

setup:
  input = step28 candidate
  primary PDE points = q=0.8999999999999999,b=0.98 and b=0.99
  objective C4 q-values = 0.89,0.90,0.91,0.92
  line-search C4 audit q-values = 0.89,0.90,0.91,0.92
  line-search C4 audit x-samples = 9
  --raw-growth-metric max-abs
  max_variables = 160
  selected_by_chart = tail:128, origin:32

accepted:
  accepted_any_step = true
  accepted_block = block:F_frac
  accepted_alpha = 0.015625
  coupled audit value = 0.9975758737729583
  explicit-audit C4 max = 4.922540831420457e6 -> 4.910607971087327e6
  edge line-search audit = 4.326812264740244e2 -> 4.3163004500890224e2
  selected raw max = 4.922540831420477e4 -> 4.9106079710873135e4
  guard max = 1.0128392951084201e3

posthoc dense audit:
  standard = 1.016228983517e1
  focused = 1.016228983517e1
  secondary = 1.422825435582e1
  origin = 9.132497540774e1
  edge = 4.284755945898e2
  overlap = 3.239711929243e2
  full 9x9 C0-C4 R/Z mortar max = 5.913592917574e6
  worst dense C4 row = RZ:F:dRRRR at q=0.87,x=1.0

interpretation:
  also not promotable. It confirms real edge descent and local C4 descent, but
  dense C4 damage is mobile. Manual q-row chasing should stop; next solver
  change should promote dense-audit worst C4 rows into the objective
  automatically, with a separate held-out dense C4 audit.
```

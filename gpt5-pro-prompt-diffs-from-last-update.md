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

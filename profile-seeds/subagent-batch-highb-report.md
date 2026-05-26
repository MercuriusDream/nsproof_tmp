# subagent-batch-highb report

Scope: alternative high-|b| Planck holdout experiment for
`q in [0.472,0.505]`, `|b| in [0.585,0.675]`.

Starting seed:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v114-base.json
```

`v114-base` was present, so `v113` was not used as the start.  The expanded
and focused bases are profile-equivalent to `v114-base` on the sampled 29x31
wide grid: sampled `F_total` and `G_total` differences were exactly zero.

## Files

```text
profile-seeds/subagent-batch-highb-base.json
profile-seeds/subagent-batch-highb-focus-base.json
profile-seeds/subagent-batch-highb-v1.json
profile-seeds/subagent-batch-highb-gn-v1.md
profile-seeds/subagent-batch-highb-gates-v1.md
profile-seeds/subagent-batch-highb-gates-v113.md
profile-seeds/subagent-batch-highb-gates-v114-base.md
profile-seeds/subagent-batch-highb-topology-v1-pos.md
profile-seeds/subagent-batch-highb-topology-v1-neg.md
profile-seeds/subagent-batch-highb-topology-v113-pos.md
profile-seeds/subagent-batch-highb-topology-v114-base-pos.md
profile-seeds/subagent-batch-highb-report.md
```

## Construction

Added sparse zero-start sideband pairs:

```sh
python3 tools/profile_add_sparse_bumps.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v114-base.json \
  --save-json profile-seeds/subagent-batch-highb-base.json \
  --pairs '0.472,0.342225;...;0.505,0.455625' \
  --note 'high-|b| Planck holdout sparse sidebands around q=0.4817, |b|=0.6425; zero-start F/G only'
```

Then `subagent-batch-highb-focus-base.json` kept all nonzero bump coefficients
and exposed only exact-zero F/G interior bump coefficients inside the requested
box to the solver.  The final solve used a damped Gauss-Newton direction with
a max-gate line search over `wide,interior,local,active`; it varied 107
zero-start F/G interior bump coefficients only.

## Coarse score

From `subagent-batch-highb-gn-v1.md`:

```text
initial score_max = 4.396921763766e-01
initial active    = 4.396921763766e-01

final score_max   = 4.391325577294e-01
final wide        = 4.319258868522e-01
final interior    = 4.371806482435e-01
final local       = 4.391325577294e-01
final active      = 4.006109209776e-01
final farther     = 3.740462869378e-01
```

## profile_gates validation

Command:

```sh
python3 tools/profile_gates.py \
  --seed-json profile-seeds/subagent-batch-highb-v1.json \
  --h-values 1.6e-3,8e-4,4e-4 \
  --wide-q-min 0.365 --wide-q-max 0.895 \
  --wide-b-min -0.775 --wide-b-max 0.825 \
  --wide-n-q 17 --wide-n-b 19 \
  --interior-q-min 0.462 --interior-q-max 0.842 \
  --interior-b-min -0.617 --interior-b-max 0.683 \
  --interior-n-q 19 --interior-n-b 17 \
  --local-r-min 0.83 --local-r-max 1.97 \
  --local-z-min -0.93 --local-z-max 1.07 \
  --local-n 31
```

Validated max residuals:

```text
subagent-batch-highb-v1:
  h=1.6e-3 max = 4.385592277046e-01
  h=8e-4   max = 4.385585159574e-01
  h=4e-4   max = 4.385615233030e-01

v113 canonical:
  h=1.6e-3 max = 4.392691863444e-01
  h=8e-4   max = 4.392669698876e-01
  h=4e-4   max = 4.392678155405e-01

v114-base:
  identical to v113 on this gate run
```

The best available highb candidate beats v113/v114-base on these shifted
gates by about `7.08e-04` in max residual.  No canonical
`gamma0p45-forced-tail-sparse-flatbumpFG-v114.json` existed when this report
was written; only v114 base/diagnostic variants were present.

## Refined topology validation

Command:

```sh
python3 tools/profile_residual_topology.py \
  --seed-json profile-seeds/subagent-batch-highb-v1.json \
  --q-min 0.472 --q-max 0.505 \
  --b-min 0.585 --b-max 0.675 \
  --n-q 45 --n-b 45 \
  --h 8e-4 --top 8 --slice-top 4
```

Positive box:

```text
rms = 2.628626800521e-01
max = 4.011868471137e-01
at q=0.475750 b=0.675000 r=1.364099 z=1.247960
```

Negative box:

```text
rms = 2.628626789074e-01
max = 4.011868471137e-01
at q=0.475750 b=-0.675000 r=1.364099 z=-1.247960
```

Direct same-grid comparison:

```text
v113 canonical positive box max  = 4.396908164656e-01
v114-base positive box max       = 4.396908164656e-01
subagent-batch-highb-v1 max      = 4.011868471137e-01
```

Interpretation: the focused candidate substantially reduces the requested
high-|b| lobe, but the independent shifted profile gates are now limited by a
different wide/local region around `q ~= 0.398`, `b ~= 0.292` / `r ~= 1.932`,
`z ~= 0.537`.  This remains an approximate numerical seed, not a validation of
the profile or proof package.

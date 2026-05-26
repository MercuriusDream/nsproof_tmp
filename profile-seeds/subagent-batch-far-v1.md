# subagent-batch-far-v1

Independent far/extreme scoring run from:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v114-base.json
```

Output seed:

```text
profile-seeds/subagent-batch-far-v1.json
```

The run varied only zero-start entries in:

```text
f_interior_bump_coeffs,g_interior_bump_coeffs
```

Coefficient diff check against v114-base:

```text
f_interior_bump_coeffs changed 4, bad_nonzero_start 0
g_interior_bump_coeffs changed 17, bad_nonzero_start 0
```

## Search command

```sh
python3 -u tools/profile_minimax_coordinate.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v114-base.json \
  --save-json profile-seeds/subagent-batch-far-v1.json \
  --families f_interior_bump_coeffs,g_interior_bump_coeffs \
  --zero-only-tol 1e-14 \
  --score-gates farther,extreme,active \
  --report-gates farther,extreme,active \
  --active-qb-points '0.300,-0.350;0.300,0.350;0.300,-0.375;0.300,0.375;0.300,-0.400;0.300,0.400;0.296667,-0.375;0.296667,0.375' \
  --h 8e-4 \
  --passes 2 \
  --step 5e-4 \
  --min-step 1.25e-4 \
  --shrink 0.5 \
  --min-improvement 1e-8 \
  --max-coeff-abs 5e-2 \
  --farther-n-q 13 \
  --farther-n-b 25 \
  --extreme-n-q 13 \
  --extreme-n-b 25 | tee profile-seeds/subagent-batch-far-search-v1.md
```

Coarse scored-search result:

```text
baseline: score_max=4.384914869346e-01 active=3.821124507710e-01 extreme=4.384914869346e-01 farther=3.820823836923e-01
final:    score_max=4.365991837690e-01 active=3.825796456505e-01 extreme=4.365991837690e-01 farther=3.825796456505e-01
```

The coarse extreme grid improved, but the far-tail active/farther max rose.

## Validation commands

```sh
python3 tools/profile_gates.py \
  --seed-json profile-seeds/subagent-batch-far-v1.json \
  --h-values 1.6e-3,8e-4,4e-4 \
  --wide-q-min 0.365 --wide-q-max 0.895 --wide-b-min -0.775 --wide-b-max 0.825 \
  --wide-n-q 17 --wide-n-b 19 \
  --interior-q-min 0.462 --interior-q-max 0.842 --interior-b-min -0.617 --interior-b-max 0.683 \
  --interior-n-q 19 --interior-n-b 17 \
  --local-r-min 0.83 --local-r-max 1.97 --local-z-min -0.93 --local-z-max 1.07 \
  --local-n 31

python3 tools/profile_residual_topology.py \
  --seed-json profile-seeds/subagent-batch-far-v1.json \
  --q-min 0.18 --q-max 0.30 --b-min -0.90 --b-max 0.90 \
  --n-q 37 --n-b 73 --h 8e-4 --top 12 --slice-top 5

python3 tools/profile_residual_topology.py \
  --seed-json profile-seeds/subagent-batch-far-v1.json \
  --q-min 0.25 --q-max 0.90 --b-min -0.90 --b-max 0.90 \
  --n-q 27 --n-b 37 --h 8e-4 --top 12 --slice-top 5
```

## Gate maxima

Shifted validation at `h=8e-4`:

```text
v114-base:
wide     4.389478067343e-01
interior 4.388251552173e-01
local    4.392669698876e-01

subagent-batch-far-v1:
wide     4.552658218342e-01 at q=0.497500 b=0.647222
interior 4.445885306909e-01 at q=0.483111 b=-0.617000
local    4.443961140910e-01 at r=1.324000 z=1.070000
```

Far-tail box `q in [0.18,0.30]`, `b in [-0.90,0.90]`, `37x73`, `h=8e-4`:

```text
v114-base max 3.821124507710e-01 at q=0.300000 b=-0.350000
v1        max 3.825796456505e-01 at q=0.300000 b=-0.375000
```

Extreme box `q in [0.25,0.90]`, `b in [-0.90,0.90]`, `27x37`, `h=8e-4`:

```text
v114-base max 4.390172826372e-01 at q=0.500000 b=-0.600000
v1        max 4.574713808572e-01 at q=0.475000 b=-0.650000
```

## Conclusion

This far/extreme-scored zero-start variant worsens the interior/local bottleneck
on independent gates.  The shifted `h=8e-4` local max rises from
`4.392669698876e-01` to `4.443961140910e-01`, and the interior max rises from
`4.388251552173e-01` to `4.445885306909e-01`.  The wide and fine extreme
checks worsen more sharply because the run pushes residual into the high-b
interior lobe around `q ~= 0.475`, `|b| ~= 0.65`.

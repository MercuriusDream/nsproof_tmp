# subagent-alt sparse forced-tail q1-free experiment

Source baseline: `profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json`.
`v113-base` was also checked and has identical standard `profile_gates.py`
values at `h=1e-3`.

## Sparse centers

Initial alternative centers added from the v112 33x33 active-lobe topology scan:

```text
(q,b2) =
(0.4265625, 0.0791015625)
(0.48125,   0.40045166015625)
(0.5140625, 0.34332275390625)
(0.56875,   0.24224853515625)
```

Follow-up local variant added one more center at the fine-local lobe:

```text
(0.6088043707368622, 0.059622407258351)
```

All coordinate-search runs used:

```text
--families f_interior_bump_coeffs,g_interior_bump_coeffs --zero-only-tol 1e-14
```

so only zero-start F/G interior bump coefficients were eligible. Accepted moves
were only in `g_interior_bump_coeffs`.

## Files

```text
profile-seeds/subagent-alt-sparse-lobes-base.json
profile-seeds/subagent-alt-sparse-lobes-v1.json
profile-seeds/subagent-alt-sparse-lobes-v2.json
profile-seeds/subagent-alt-sparse-lobes-local-base.json
profile-seeds/subagent-alt-sparse-lobes-v3.json
profile-seeds/subagent-alt-sparse-lobes.md
```

## Key commands run

```text
python3 tools/profile_gates.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --h-values 1e-3
python3 tools/profile_gates.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113-base.json --h-values 1e-3
python3 tools/profile_residual_topology.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --q-min 0.35 --q-max 0.70 --b-min 0.0 --b-max 0.75 --n-q 33 --n-b 33 --h 1e-3 --top 12 --slice-top 4
python3 tools/profile_add_sparse_bumps.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --save-json profile-seeds/subagent-alt-sparse-lobes-base.json --pairs '0.4265625,0.0791015625;0.48125,0.40045166015625;0.5140625,0.34332275390625;0.56875,0.24224853515625' --note 'subagent alternative centers at v112 33x33 active lobes'
python3 tools/profile_minimax_coordinate.py --seed-json profile-seeds/subagent-alt-sparse-lobes-base.json --save-json profile-seeds/subagent-alt-sparse-lobes-v1.json --families f_interior_bump_coeffs,g_interior_bump_coeffs --zero-only-tol 1e-14 --score-gates wide,interior,local,active --report-gates wide,interior,local,farther,active --active-qb-points '0.4265625,0.28125;0.48125,0.6328125;0.5140625,0.5859375;0.56875,0.4921875' --h 1e-3 --passes 2 --step 2e-4 --min-step 5e-5 --shrink 0.5 --min-improvement 1e-8 --max-coeff-abs 0.02 --wide-n-q 11 --wide-n-b 11 --interior-n-q 11 --interior-n-b 11 --local-n 17 --farther-n-q 7 --farther-n-b 11
python3 tools/profile_gates.py --seed-json profile-seeds/subagent-alt-sparse-lobes-v1.json --h-values 1e-3
python3 tools/profile_gates.py --seed-json profile-seeds/subagent-alt-sparse-lobes-v1.json --h-values 1e-3 --wide-n-q 29 --wide-n-b 29 --interior-n-q 29 --interior-n-b 29 --local-n 45
python3 tools/profile_residual_topology.py --seed-json profile-seeds/subagent-alt-sparse-lobes-v1.json --q-min 0.35 --q-max 0.70 --b-min 0.0 --b-max 0.75 --n-q 33 --n-b 33 --h 1e-3 --top 8 --slice-top 4
python3 tools/profile_gates.py --seed-json profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json --h-values 1e-3 --wide-n-q 29 --wide-n-b 29 --interior-n-q 29 --interior-n-b 29 --local-n 45
```

Also ran two short follow-up variants, `v2` and `v3`, targeting the fine-local
lobe. They did not improve the best comparison below.

## Baselines

Standard `profile_gates.py`, `h=1e-3`:

```text
v112/v113-base:
wide     4.365866237926e-1
interior 4.395069007065e-1
local    4.391290054377e-1
max      4.395069007065e-1
```

Fine 29x29/45 `profile_gates.py`, `h=1e-3`:

```text
v112:
wide     4.396000051659e-1
interior 4.395069007065e-1
local    4.397800969258e-1
max      4.397800969258e-1
```

## Best alternate

Best standard-gate candidate: `profile-seeds/subagent-alt-sparse-lobes-v1.json`.

Standard `profile_gates.py`, `h=1e-3`:

```text
wide     4.365292406865e-1
interior 4.394349771245e-1
local    4.390520383543e-1
max      4.394349771245e-1
```

This beats v112/v113-base on the standard gate max by
`7.192695820e-5`.

Fine 29x29/45 `profile_gates.py`, `h=1e-3`:

```text
wide     4.394386048929e-1
interior 4.394349771245e-1
local    4.399934785604e-1
max      4.399934785604e-1
```

This does not beat v112 on the fine gate max because the 45-point local gate
regresses by `2.133816346e-4`.

33x33 active-lobe topology max:

```text
v112 max 4.397715924677e-1
v1   max 4.396318159068e-1
```

The follow-up `v3` lowered the fine-local lobe to `4.398708060414e-1`, but it
hurt the standard interior gate (`4.396945718235e-1`), so it is not the best
candidate.

# gamma=0.45 forced-tail sparse flat-bump continuation v113-v116

This note records the sparse-bump batch after v112.  All seeds in this note are
approximate diagnostics only; none is a validated profile or a proof object.

## Files

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113.json
profile-seeds/subagent-batch-highb-v1.json
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v116-lowb.json
tools/profile_add_sparse_bumps.py
tools/profile_minimax_coordinate.py
profile-seeds/indicial-match-rescan-gamma0p45-B1-L25-v115.md
profile-seeds/indicial-match-rescan-gamma0p45-B1-L40-v115.md
profile-seeds/indicial-match-delta1-gamma0p45-B1-v115.md
```

`tools/profile_minimax_coordinate.py` now has an early-reject path: trial moves
evaluate scored gates first and stop once a scored point already exceeds the
incumbent max.  The acceptance criterion is unchanged.

## Results

v113 improved the v112 coarse/fine/topology checks but did not close the
residual gap:

```text
standard max       = 4.391502409150e-1
fine 29x29/45 max = 4.395926393838e-1
41x41 topology max = 4.392376399652e-1
farther-tail max  = 3.820821937260e-1
```

A shifted validation scan found that v112/v113-base missed a high-`|b|` lobe
near `q ~= 0.482`, `|b| ~= 0.6425`, with max about `4.4006e-1`.  The useful
parallel branch was `subagent-batch-highb-v1.json`, which lowered that lobe and
validated as:

```text
standard max       = 4.385721351557e-1
shifted max        = 4.385615233030e-1
fine 29x29/45 max = 4.392460993663e-1
broad topology max = 4.377119444409e-1
```

Far/extreme-only scoring was rejected: it improved its own objective but
worsened balanced wide/interior/local gates and did not improve the far-tail
fine max.

The current best endpoint is:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v116-lowb.json
```

Validation:

```text
standard h=2e-3,1e-3,5e-4 max:
4.378237351374e-1, 4.378239756763e-1, 4.378239372738e-1

shifted h=1.6e-3,8e-4,4e-4 max:
4.384746043386e-1, 4.384766750064e-1, 4.384759905812e-1

fine 29x29/45 max:
4.388424241734e-1

broad shifted topology max:
4.370460732359e-1

old high-|b| holdout-box max:
4.354896703956e-1

far-tail holdout max:
4.091040786189e-1
```

Tail-series trace check:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

## Indicial rescan

The two-branch indicial matching rescan at `L=25` and `L=40` again found the
exact `delta=1` geometric branch as the only sampled zero.  Other low
`sigma_min/sigma_max` candidates keep endpoint-scale forbidden contribution
near one, so they are not admissible non-geometric indicial roots.

## Status

v116-lowb is the best balanced q1-free forced-tail seed produced so far, but
its residual is still `O(1)`.  It does not satisfy the stop condition
`F_gamma(U_*,P_*) = 0`, does not provide a Newton-Kantorovich validation, and
does not solve the indicial/matching/spectral obligations.

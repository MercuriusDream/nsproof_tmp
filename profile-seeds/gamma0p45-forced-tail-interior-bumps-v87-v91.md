# Tail-Flat Interior Bump Probe v87-v91: gamma = 0.45, B = 1.0

Machine-readable seeds:

```text
profile-seeds/gamma0p45-forced-tail-interior-bump-v87.json
profile-seeds/gamma0p45-forced-tail-interior-bumpF-v88.json
profile-seeds/gamma0p45-forced-tail-flatbumpF-v89.json
profile-seeds/gamma0p45-forced-tail-flatbumpF-blend-v90.json
profile-seeds/gamma0p45-forced-tail-flatbumpF-blend-v91.json
```

This sequence adds interior matching degrees that do not alter the exact
`q=0` tail. Two shapes are implemented in `CompactifiedProfile`:

```text
compact:       C-infinity tensor bumps with finite support away from q=0,
flat_gaussian: Gaussian interior bumps multiplied by exp[-a(1/q - 1/q_c)].
```

The flat Gaussian basis is not compactly supported, but it is flat at `q=0`,
so it contributes no integer q-series coefficient and preserves the exact
trace and zero q1 channel.

## Rejected Full Bump Solves

The first compact solve varied both `F` and `G` bumps from v86:

```text
profile-seeds/gamma0p45-forced-tail-interior-bump-v87.json
training RMS: 2.580479655590e-01 -> 2.194191402667e-01
```

It failed independent gates:

```text
standard max ~= 1.277012513906e+00,
interior max ~= 1.371869096612e+00,
local max    ~= 2.892005788132e+00.
```

The overfit came mainly through the `G` bump coefficients. A streamfunction
only compact solve v88 was still rejected:

```text
standard max ~= 6.851086040140e-01,
interior max ~= 1.501218384024e+00,
local max    ~= 2.181028888339e+00.
```

The smoother flat-Gaussian streamfunction solve v89 avoided the compact
support boundary artifact but still moved the residual peak rather than
reducing the independent max:

```text
standard max ~= 7.814558610689e-01,
interior max ~= 7.879140536743e-01,
local max    ~= 8.350363775522e-01.
```

## Small Blend

A convex blend between v86 and v89 found a useful small bump component. The
best sampled value was `t=0.025`:

```text
profile-seeds/gamma0p45-forced-tail-flatbumpF-blend-v91.json
```

v91 gate values at `h=1e-3`:

```text
standard max         = 5.375808758463e-01
interior max         = 5.385829296901e-01
local max            = 5.388811146608e-01
q in [0.18,0.30] max = 3.989670525038e-01
```

Finite-difference stability:

```text
standard h=2e-3,1e-3,5e-4:
5.375828678111e-01, 5.375808758463e-01, 5.375817021688e-01

interior h=2e-3,1e-3,5e-4:
5.385853089831e-01, 5.385829296901e-01, 5.385820595450e-01

local h=2e-3,1e-3,5e-4:
5.388831789929e-01, 5.388811146608e-01, 5.388802772597e-01

q in [0.18,0.30] h=2e-3,1e-3,5e-4:
3.989636240613e-01, 3.989670525038e-01, 3.989974468637e-01
```

Tail-series diagnostics report the same integer series as v86:

```text
order q^0 trace is exact,
order q^1 linear residual is exactly zero,
orders q^7 and above are absent.
```

The broad streamfunction lobe remains:

```text
q ~= 0.50-0.60,
|b| ~= 0.35-0.40.
```

## Interpretation

v91 is the best balanced q1-free forced-tail seed so far, but only by a small
margin over v86. The result is mathematically useful because it shows that a
tail-flat interior degree can help without changing the far-tail series. It
also shows that unconstrained local bump solves are dangerous: they reduce RMS
while worsening max residuals. Any next interior matching basis should be
minimax- or gate-aware from the start, not only least-squares on the training
grid.

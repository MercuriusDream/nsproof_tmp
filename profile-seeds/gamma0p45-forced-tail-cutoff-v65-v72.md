# Localized Forced-Tail Continuation v65-v72: gamma = 0.45, B = 1.0

This sequence localizes the forced `q^(1/gamma)` correction away from the
origin by storing it as

```text
q^(1/gamma) * (1-q)^k.
```

The leading asymptotic coefficient at `q=0` is unchanged, but the correction
vanishes at `q=1` when `k > 0`. This targets the inward residual peak seen in
v64 while preserving the exact trace and the zero q1 channel.

## Cutoff Probe

Machine-readable seeds:

```text
profile-seeds/gamma0p45-forced-tail-qm-cut2-v65.json
profile-seeds/gamma0p45-forced-tail-qm-cut4-v66.json
profile-seeds/gamma0p45-forced-tail-qm-cut6-v67.json
```

Raw cutoff gates:

```text
k=2:
  q in [0.18,0.30] max = 3.137648932709e-01
  standard max         = 1.098437265881e+00

k=4:
  q in [0.18,0.30] max = 4.711551646967e-01
  standard max         = 9.087767117467e-01

k=6:
  q in [0.18,0.30] max = 5.277313941347e-01
  standard max         = 8.151828534389e-01
```

The cutoff improves the interior/origin-side residual by roughly a factor of
three relative to v64, but it trades away the best far-tail value.

## q1-Frozen Interior Solves

The solver now supports

```text
--freeze-edge-coeffs
```

so the forced non-integer tail coefficients can be kept fixed while ordinary
monomial coefficients with q-order at least 2 are optimized. This preserves

```text
F(0,b) = 1/2,
G(0,b) = B,
q^1 coefficient = 0.
```

The strongest cutoff solve before blending is v69:

```text
profile-seeds/gamma0p45-forced-tail-qm-cut6-q2solve-v69.json

q in [0.18,0.30] max = 4.848091940397e-01
standard max         = 7.207055194890e-01
interior max         = 7.272008631684e-01
local max            = 7.272320128812e-01
```

## v70-v72 Blend And Local Solve

Blending the far-tail-heavy v64 with the localized v69 found the best
max-over-gates point near `t=0.95`:

```text
profile-seeds/gamma0p45-forced-tail-blend-v70.json
max over standard/extreme/farther/interior/local = 7.198684827606e-01
```

Running a q1-frozen q>=2 monomial solve from v70 gives v72:

```text
profile-seeds/gamma0p45-forced-tail-blend-q2solve-v72.json
```

v72 metrics:

```text
q in [0.18,0.30] max = 4.325436706783e-01
standard max         = 6.421601684773e-01
interior max         = 6.449624903933e-01
local max            = 6.445437673718e-01
```

Finite-difference stability for the two main gates:

```text
farther-tail h=2e-3: max = 4.325437148106e-01
farther-tail h=1e-3: max = 4.325436706783e-01
farther-tail h=5e-4: max = 4.325496878188e-01

standard h=2e-3: max = 6.421610743244e-01
standard h=1e-3: max = 6.421601684773e-01
standard h=5e-4: max = 6.421616755494e-01
```

Tail-series checks confirm:

```text
order q^0 trace is exact,
order q^1 linear residual is exactly zero,
the q^(1/gamma) correction remains aligned with the forced nonlinear source.
```

## Interpretation

v72 is not close to a validated profile, but it is the best balanced seed so
far under the asymptotic constraints. The result separates two objectives:

```text
v64: best asymptotic far-tail gate, max ~= 9.02e-2, but O(1) interior residual.
v72: best constrained balance, max ~= 6.45e-1 across standard/interior/local.
```

This indicates that the forced non-integer tail basis is correct but
insufficient. The next improvement should add genuine interior matching degrees
or validated indicial modes, not relax the q1 constraint or return to
unconstrained integer shell fitting.

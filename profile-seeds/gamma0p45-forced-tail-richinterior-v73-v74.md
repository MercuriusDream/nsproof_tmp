# Rich q1-Frozen Forced-Tail Interior Continuation v73-v74: gamma = 0.45, B = 1.0

Machine-readable seeds:

```text
profile-seeds/gamma0p45-forced-tail-richinterior-v73.json
profile-seeds/gamma0p45-forced-tail-richinterior-v74.json
```

This sequence starts from the balanced q1-free forced-tail seed v72 and gives
the interior solve more ordinary monomial degrees while keeping the asymptotic
constraints fixed:

```text
exact q=0 trace,
zero q^1 tail coefficient,
frozen forced q^(1/gamma) angular family,
ordinary monomials restricted to q-order >= 2.
```

The solve used the bounded-edge Gauss-Newton path with

```text
q_order = 9,
b_order = 8,
edge_q_order = 6,
edge_b_order = 8,
vanishing_edge_power = 1/gamma = 2.222222222222...,
freeze_edge_coeffs,
freeze_tail_angular,
monomial_min_q_order = 2.
```

The training box targeted the residual lobe left by v72:

```text
q in [0.32, 0.78],
b in [-0.70, 0.70],
r in [0.8, 2.1],
z in [-1.1, 1.1].
```

## v73

The first continuation reduced the training RMS:

```text
3.026947054652e-01 -> 2.885514019724e-01.
```

Independent gates at `h=1e-3`:

```text
q in [0.18,0.30] max = 4.220327067210e-01
standard max         = 6.082399154195e-01
interior max         = 6.105982474519e-01
local max            = 6.103103849010e-01
```

Finite-difference stability:

```text
farther-tail h=2e-3: max = 4.220289694447e-01
farther-tail h=1e-3: max = 4.220327067210e-01
farther-tail h=5e-4: max = 4.220380829962e-01

standard h=2e-3: max = 6.082408262314e-01
standard h=1e-3: max = 6.082399154195e-01
standard h=5e-4: max = 6.082409402202e-01
```

## v74

Continuing from v73 with lower damping reduced the training RMS again:

```text
2.885514019724e-01 -> 2.811765545203e-01.
```

Independent gates at `h=1e-3`:

```text
q in [0.18,0.30] max = 4.169187255275e-01
standard max         = 5.909176701763e-01
interior max         = 5.932368481368e-01
local max            = 5.930636467992e-01
```

Finite-difference stability for the farther-tail gate:

```text
h=2e-3: max = 4.169211686592e-01
h=1e-3: max = 4.169187255275e-01
h=5e-4: max = 4.168707616438e-01
```

Finite-difference stability for the standard/interior/local gates:

```text
standard h=2e-3: max = 5.909184245366e-01
standard h=1e-3: max = 5.909176701763e-01
standard h=5e-4: max = 5.909165194996e-01

interior h=2e-3: max = 5.932380134431e-01
interior h=1e-3: max = 5.932368481368e-01
interior h=5e-4: max = 5.932385988677e-01

local h=2e-3: max = 5.930646596153e-01
local h=1e-3: max = 5.930636467992e-01
local h=5e-4: max = 5.930650219226e-01
```

Tail-series checks:

```text
order q^0 trace is exact,
order q^1 linear residual is exactly zero,
fractional q^(1/gamma) psi_linear_max = 2.327134302240e+00,
leading trace psi source max           = 2.329369172244e+00.
```

The warning sign is high-order ordinary tail growth:

```text
order q^9 psi_linear_max = 1.971720549096e+01.
```

## Interpretation

v74 is the best balanced q1-free forced-tail seed so far:

```text
v72 balanced max ~= 6.45e-1,
v73 balanced max ~= 6.11e-1,
v74 balanced max ~= 5.93e-1.
```

It is still not close to a validated profile. The improvement says the
q1-frozen forced-tail basis has useful interior degrees, but the large q9
tail residual shows the current finite monomial continuation is again trying
to use ordinary high-order tail content as a compensator. The next step should
replace that role with genuine matching/indicial coordinates rather than
allowing still richer unconstrained polynomial tails.

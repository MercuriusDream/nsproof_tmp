# Approximate Edge-Adapted Compactified Profile Seed v29: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-edgebasis-seed-v29.json
```

This seed uses the monomial even-polynomial basis with `q_order=7`, `b_order=6`, plus the edge-adapted basis

```text
(1 - q)^i * (b^2 / (1 - b^2))^j,
0 <= i <= 9,
0 <= j <= 9.
```

It was continued from v27 by a frozen order-9 edge-basis expansion and one short joint rebalancing step. It is not a validated profile.

## Solver Evidence

Final weighted edge/corner training:

```text
grid: hybrid local rectangle 17x17 plus compactified 15x15
edge-repeat: 5
corner-repeat: 25
weighted RMS residual: 4.208686344168e-02
```

Unweighted cross-checks from `tools/profile_gates.py`:

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 2.157353195333e-02
max residual: 1.981075463924e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.293294858698e-03
max residual: 7.500213863914e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 2.614380114418e-03
max residual: 1.349671434631e-02
```

## Finite-Difference Stability

The wide residual is stable under a small `h` sweep:

```text
h = 2e-3: wide max = 1.981070957594e-01
h = 1e-3: wide max = 1.981075463924e-01
h = 5e-4: wide max = 1.981126137327e-01
```

## Continuation Trace

```text
v27 order-8 joint wide max:  2.024776692134e-01
v28 order-9 frozen wide max: 1.989059273388e-01
v29 order-9 joint wide max:  1.981075463924e-01
```

## Interpretation

The edge-order increase continues to improve the residual, but the worst point has not moved:

```text
worst q = 0.35,
worst b = -0.8,
psi residual ~= 1.98e-1.
```

This remains only a seed. The proof plan requires residual control near `1e-8`, grid refinement, indicial tail projection, and Newton-Kantorovich validation.

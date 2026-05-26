# Approximate Edge-Adapted Compactified Profile Seed v27: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-edgebasis-seed-v27.json
```

This seed uses the monomial even-polynomial basis with `q_order=7`, `b_order=6`, plus the edge-adapted basis

```text
(1 - q)^i * (b^2 / (1 - b^2))^j,
0 <= i <= 8,
0 <= j <= 8.
```

It was continued from v23 by frozen edge-basis expansions to orders 7 and 8, with short joint rebalancing after each expansion. It is not a validated profile.

## Solver Evidence

Final weighted edge/corner training:

```text
grid: hybrid local rectangle 17x17 plus compactified 15x15
edge-repeat: 5
corner-repeat: 25
weighted RMS residual: 4.301190641741e-02
```

Unweighted cross-checks:

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 2.204065229139e-02
max residual: 2.024776692134e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.324923775793e-03
max residual: 7.614116398750e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 2.650257221719e-03
max residual: 1.375701946866e-02
```

## Continuation Trace

```text
v23 order-6 joint wide max:  2.137390396420e-01
v24 order-7 frozen wide max: 2.089032401191e-01
v25 order-7 joint wide max:  2.071719811475e-01
v26 order-8 frozen wide max: 2.033967758885e-01
v27 order-8 joint wide max:  2.024776692134e-01
```

## Interpretation

The edge-order increase still gives monotone improvement, but the worst point has not moved:

```text
worst q = 0.35,
worst b = -0.8,
psi residual ~= 2.02e-1.
```

This remains only a seed. The proof plan requires residual control near `1e-8`, grid refinement, indicial tail projection, and Newton-Kantorovich validation.

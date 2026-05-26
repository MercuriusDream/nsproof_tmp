# Approximate Edge-Adapted Compactified Profile Seed v23: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-edgebasis-seed-v23.json
```

This seed uses the monomial even-polynomial basis with `q_order=7`, `b_order=6`, plus the edge-adapted basis

```text
(1 - q)^i * (b^2 / (1 - b^2))^j,
0 <= i <= 6,
0 <= j <= 6.
```

It was continued from v14 through order-4, order-5, and order-6 edge-basis expansions, with short joint rebalancing passes of the monomial and edge coefficients. It is not a validated profile.

## Solver Evidence

Final weighted edge/corner training:

```text
grid: hybrid local rectangle 17x17 plus compactified 15x15
edge-repeat: 5
corner-repeat: 25
weighted RMS residual: 4.540002366280e-02
```

Unweighted cross-checks:

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 2.325310712410e-02
max residual: 2.137390396420e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.411492883484e-03
max residual: 7.922908675069e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 2.750412140168e-03
max residual: 1.446669403667e-02
```

## Continuation Trace

```text
v14 order-3 joint wide max:          2.809027911725e-01
v15 order-4 frozen wide max:         2.478048918717e-01
v16 order-4 joint wide max:          2.409202837513e-01
v17 order-4 joint wide max:          2.351896077322e-01
v18 order-4 joint wide max:          2.314217746009e-01
v19 stronger corner-weight wide max: 2.301179745386e-01
v20 order-5 frozen wide max:         2.232192301523e-01
v21 order-5 joint wide max:          2.208261636973e-01
v22 order-6 frozen wide max:         2.156357342691e-01
v23 order-6 joint wide max:          2.137390396420e-01
```

## Interpretation

The edge-basis expansion gives monotone improvement in all three cross-checks, but the compactified edge remains the obstruction:

```text
worst q = 0.35,
worst b = -0.8,
psi residual ~= 2.14e-1.
```

The proof plan requires a residual below `1e-8` before a Newton-Kantorovich validation attempt. v23 is therefore only a better seed, not evidence of an exact profile.

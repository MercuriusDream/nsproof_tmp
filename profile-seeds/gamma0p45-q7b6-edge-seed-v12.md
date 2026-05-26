# Approximate Compactified Profile Seed v12: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-q7b6-edge-seed-v12.json
```

This seed uses a `q_order=7`, `b_order=6` even-polynomial basis. It was continued from the hybrid v10 seed using edge/corner-weighted compactified collocation to target the persistent defect near

```text
q = 0.35,
|b| = 0.8.
```

It is not a validated profile.

## Solver Evidence

Weighted edge/corner training:

```text
grid: hybrid local rectangle 17x17 plus compactified 15x15
edge-repeat: 5
corner-repeat: 25
weighted RMS residual: 6.965421132681e-02
```

Unweighted cross-checks:

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 3.555153298348e-02
max residual: 3.292738526854e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.749187433790e-03
max residual: 8.524213054786e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 3.963711573532e-03
max residual: 2.920487686758e-02
```

## Interpretation

The compactified edge max residual improved only modestly:

```text
v10 wide max: 3.470863861403e-01
v11 wide max: 3.354909067013e-01
v12 wide max: 3.292738526854e-01
```

This suggests the monomial even-polynomial basis is becoming inefficient for the outer angular tail. The next structural upgrade should add an indicial or edge-adapted outer-tail basis, not only more least-squares weighting.

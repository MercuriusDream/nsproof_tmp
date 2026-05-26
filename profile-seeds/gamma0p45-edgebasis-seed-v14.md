# Approximate Edge-Adapted Compactified Profile Seed v14: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-edgebasis-seed-v14.json
```

This seed uses the monomial even-polynomial basis with `q_order=7`, `b_order=6`, plus the edge-adapted basis

```text
(1 - q)^i * (b^2 / (1 - b^2))^j,
0 <= i <= 3,
0 <= j <= 3.
```

It was continued jointly from v13 by optimizing both monomial and edge-basis coefficients against a hybrid local/compactified grid with repeated edge and corner samples. It is not a validated profile.

## Solver Evidence

Weighted edge/corner training:

```text
grid: hybrid local rectangle 17x17 plus compactified 15x15
edge-repeat: 5
corner-repeat: 25
weighted RMS residual: 5.949924972726e-02
```

Unweighted cross-checks:

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 3.037464074769e-02
max residual: 2.809027911725e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.679033847825e-03
max residual: 8.758618892963e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 3.355975767446e-03
max residual: 2.189509233708e-02
```

## Interpretation

The edge-adapted basis gives a real but still insufficient improvement at the compactified edge:

```text
v10 monomial hybrid wide max:     3.470863861403e-01
v12 monomial edge-weight wide max: 3.292738526854e-01
v13 frozen edge-basis wide max:    2.922561859440e-01
v14 joint edge-basis wide max:     2.809027911725e-01
```

The profile residual gate in the proof plan is below `1e-8`; v14 remains only a numerical seed for further continuation and validation.

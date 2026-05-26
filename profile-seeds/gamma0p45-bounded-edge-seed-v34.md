# Approximate Bounded Edge Profile Seed v34: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-bounded-edge-seed-v34.json
```

This seed continues the axis-regular bounded edge representation

```text
(1 - q)^i * b^(2j),
0 <= i <= 11,
0 <= j <= 11.
```

It was continued from v33 by three frozen-monomial Gauss-Newton steps on the extreme box

```text
q in [0.25,0.90],
b in [-0.90,0.90].
```

It is not a validated profile.

## Standard Gates

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 2.129098893728e-02
max residual: 1.976849426590e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.238648155200e-03
max residual: 7.346075985788e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 2.561338902862e-03
max residual: 1.314272282324e-02
```

## Stress Gates

Moderate stress:

```text
q in [0.30,0.90], b in [-0.85,0.85]
RMS residual: 4.024917218603e-02
max residual: 3.137198845265e-01
worst point: q=0.30, b=-0.85
```

Extreme stress:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 5.891676873729e-02
max residual: 3.659260538607e-01
worst point: q=0.25, b=-0.771429
```

## Finite-Difference Stability

```text
standard h = 2e-3: max = 1.976833981348e-01
standard h = 1e-3: max = 1.976849426590e-01
standard h = 5e-4: max = 1.976889480798e-01

extreme h = 2e-3: max = 3.659178772861e-01
extreme h = 1e-3: max = 3.659260538607e-01
extreme h = 5e-4: max = 3.659358138933e-01
```

## Interpretation

v34 improves v33 on all measured gate classes:

```text
standard wide max:
v33: 1.983571395229e-01
v34: 1.976849426590e-01

moderate stress max:
v33: 3.144413543905e-01
v34: 3.137198845265e-01

extreme stress max:
v33: 3.678892602162e-01
v34: 3.659260538607e-01
```

The improvement is monotone but slow. The seed is still far above the `1e-8` residual gate and lacks indicial, matching, spectral, and Newton-Kantorovich validation.

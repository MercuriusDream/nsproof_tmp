# Approximate Wider-Box Edge-Adapted Profile Seed v31: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-edgebasis-wide-seed-v31.json
```

This seed uses the monomial even-polynomial basis with `q_order=7`, `b_order=6`, plus the edge-adapted basis

```text
(1 - q)^i * (b^2 / (1 - b^2))^j,
0 <= i <= 10,
0 <= j <= 10.
```

It was continued from v29 by widening the training box to

```text
q in [0.30,0.90],
b in [-0.85,0.85].
```

The monomial core was frozen while the order-10 edge coefficients were optimized. It is not a validated profile.

## Standard Gates

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 2.098873462597e-02
max residual: 1.916664567193e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.272487651399e-03
max residual: 7.432510175448e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 2.585592296692e-03
max residual: 1.317541613547e-02
```

## Stress Gates

Moderate stress:

```text
q in [0.30,0.90], b in [-0.85,0.85]
RMS residual: 5.398629035528e-02
max residual: 5.606093492649e-01
worst point: q=0.30, b=-0.85
```

Extreme stress:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 9.899574151078e+00
max residual: 1.085510913324e+02
worst point: q=0.25, b=-0.90
```

## Interpretation

Widening the training box improves the original gate and the moderate stress gate:

```text
standard wide max:
v29: 1.981075463924e-01
v31: 1.916664567193e-01

moderate stress max:
v29: 5.739693858981e-01
v31: 5.606093492649e-01
```

But it worsens the more extreme stress gate:

```text
extreme stress max:
v29: 9.304452536361e+01
v31: 1.085510913324e+02
```

The current basis is therefore still a continuation seed, not a validated asymptotic profile. The next structural step should use indicial-tail modes or another asymptotic representation rather than only increasing polynomial edge order.

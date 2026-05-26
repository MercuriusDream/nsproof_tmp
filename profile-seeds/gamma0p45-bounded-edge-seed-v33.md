# Approximate Bounded Edge Profile Seed v33: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-bounded-edge-seed-v33.json
```

This seed replaces the singular edge basis

```text
(1 - q)^i * (b^2 / (1 - b^2))^j
```

with the axis-regular bounded basis

```text
(1 - q)^i * b^(2j),
0 <= i <= 10,
0 <= j <= 10.
```

It was initialized by least-squares projection of the singular v31 edge contribution onto the bounded basis, then continued by three frozen-monomial Gauss-Newton steps on the widened box

```text
q in [0.30,0.90],
b in [-0.85,0.85].
```

It is not a validated profile.

## Standard Gates

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 2.137556581274e-02
max residual: 1.983571395229e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.246059301207e-03
max residual: 7.379003864893e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 2.569871484046e-03
max residual: 1.322361463194e-02
```

## Stress Gates

Moderate stress:

```text
q in [0.30,0.90], b in [-0.85,0.85]
RMS residual: 4.040292840542e-02
max residual: 3.144413543905e-01
worst point: q=0.30, b=-0.85
```

Extreme stress:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 5.924289576426e-02
max residual: 3.678892602162e-01
worst point: q=0.25, b=-0.771429
```

## Finite-Difference Stability

The standard and extreme wide gates are stable under the tested `h` sweep:

```text
standard h = 2e-3: max = 1.983555331170e-01
standard h = 1e-3: max = 1.983571395229e-01
standard h = 5e-4: max = 1.983627757642e-01

extreme h = 2e-3: max = 3.678848703320e-01
extreme h = 1e-3: max = 3.678892602162e-01
extreme h = 5e-4: max = 3.678987102754e-01
```

## Interpretation

The bounded basis is worse than singular v31 on the original standard gate:

```text
standard wide max:
singular v31 ~= 1.92e-1,
bounded v33  ~= 1.98e-1.
```

But it removes the catastrophic angular-axis failure:

```text
extreme stress max:
singular v31 ~= 1.09e2,
bounded v33  ~= 3.68e-1.
```

For the proof program, v33 is therefore the more relevant seed: it respects the expected axis regularity of the compactified angular coefficients. It remains far from the `1e-8` residual gate and has no Newton-Kantorovich or indicial validation.

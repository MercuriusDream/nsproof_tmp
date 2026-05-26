# Approximate Bounded Edge Profile Seed v35: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-bounded-edge-seed-v35.json
```

This seed continues v34 by adding only the new outer shell of the bounded,
axis-regular edge basis

```text
(1 - q)^i * b^(2j),
0 <= i <= 12,
0 <= j <= 12.
```

The lower bounded coefficients were held fixed using
`--bounded-shell-min 12`; only shell coefficients with `i=12` or `j=12` were
varied. The continuation used four Gauss-Newton steps on the extreme box

```text
q in [0.25,0.90],
b in [-0.90,0.90],
17 x 17 grid plus edge/corner repeats.
```

It is not a validated profile.

## Gate Metrics

Standard gate:

```text
q in [0.35,0.90], b in [-0.80,0.80]
RMS residual: 2.113817324523e-02
max residual: 1.957809706943e-01
worst point: q=0.35, b=-0.80
```

Local rectangle:

```text
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.241387079214e-03
max residual: 7.345604906469e-03
```

Interior compactified gate:

```text
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 2.560882089887e-03
max residual: 1.310380255034e-02
```

Moderate stress:

```text
q in [0.30,0.90], b in [-0.85,0.85]
RMS residual: 3.991421668324e-02
max residual: 3.097438778692e-01
worst point: q=0.30, b=-0.85
```

Extreme stress:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 5.861598604497e-02
max residual: 3.633506253060e-01
worst point: q=0.25, b=-0.771429
```

## Finite-Difference Stability

```text
standard h = 2e-3: max = 1.957794275099e-01
standard h = 1e-3: max = 1.957809706943e-01
standard h = 5e-4: max = 1.957853420026e-01

extreme h = 2e-3: max = 3.633422212222e-01
extreme h = 1e-3: max = 3.633506253060e-01
extreme h = 5e-4: max = 3.633585492466e-01
```

## Comparison With v34

```text
standard wide max:
v34: 1.976849426590e-01
v35: 1.957809706943e-01

moderate stress max:
v34: 3.137198845265e-01
v35: 3.097438778692e-01

extreme stress max:
v34: 3.659260538607e-01
v35: 3.633506253060e-01
```

The improvement is monotone but still very slow. The order-12 shell confirms
that adding more bounded polynomial edge degrees helps, but does not change the
main conclusion: the basis is still far above the `1e-8` validation target and
still lacks a non-geometric indicial-tail certificate.

## Residual Topology

Diagnostic:

```text
python3 tools/profile_residual_topology.py \
  --seed-json profile-seeds/gamma0p45-bounded-edge-seed-v35.json
```

On the original extreme box, the defect is concentrated on the smallest sampled
`q` and in angular lobes near `|b| = 0.7875`:

```text
q in [0.25,0.90], b in [-0.90,0.90], 17x17:
RMS residual: 5.733894759748e-02
worst point: q=0.25, b=-0.7875
e_psi:   3.707661396511e-01
e_Gamma: 7.904766278781e-03
```

Probing farther into the tail makes the same lobe worse:

```text
q in [0.18,0.30], b in [-0.90,0.90], 9x17:
RMS residual: 1.514292288832e-01
worst point: q=0.18, b=-0.7875
e_psi:   4.877600383076e-01
e_Gamma: 1.224231756695e-02
```

The remaining obstruction is therefore primarily a far-tail streamfunction
mismatch, not a local finite-difference artifact or a single angular endpoint.

## Far-Boundary Trace

Diagnostic:

```text
python3 tools/profile_tail_boundary.py \
  --seed-json profile-seeds/gamma0p45-bounded-edge-seed-v35.json
```

The bounded edge corrections do not vanish at `q=0`, so they alter the leading
conical trace:

```text
q = 0, |b| = 0.95:
F(0,b) - 1/2 = 1.052470949329e+00
G(0,b) - B   = -3.207815166738e+01
```

This violates the exact conical leading profile. The next edge basis should
either multiply corrections by a positive tail power such as `q^sigma`, or
impose linear constraints that force the bounded-edge correction to vanish at
`q=0`.

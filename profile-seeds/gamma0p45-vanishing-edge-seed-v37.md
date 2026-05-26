# Tail-Admissible Vanishing Edge Seed v37: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-seed-v37.json
```

This is an experiment, not the preferred numerical profile. It enforces the
exact conical far-boundary trace

```text
F(0,b) = 1/2,
G(0,b) = B
```

by zeroing and freezing the monomial `q^0 b^(2j)` coefficients for `j>0`, and
by replacing the nonvanishing bounded edge basis with

```text
q * (1-q)^i * b^(2j),
0 <= i,j <= 8.
```

v36 was obtained by fitting the old v35 edge correction into this vanishing
family and taking three frozen-monomial Gauss-Newton steps. v37 then took one
constrained correction step with the non-tail monomials and vanishing edge
coefficients active.

## Boundary Trace

The trace is exact on the sampled grid:

```text
q = 0:
F(0,b) - 1/2 = 0
G(0,b) - B   = 0
```

## Gate Metrics

Standard gate:

```text
q in [0.35,0.90], b in [-0.80,0.80]
RMS residual: 1.655183872265e-01
max residual: 7.734021647691e-01
```

Extreme gate:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 1.470672996481e-01
max residual: 7.195898925171e-01
```

Farther-tail probe:

```text
q in [0.18,0.30], b in [-0.90,0.90]
RMS residual: 1.255776145374e-01
max residual: 4.674038780697e-01
```

## Interpretation

Compared with v35, the farther-tail max improves slightly
(`4.88e-1 -> 4.67e-1`), but the standard and local gates become much worse.
This confirms that the old bounded-edge seed lowered finite-box residuals by
altering the leading conical trace. A successful tail-admissible profile cannot
be obtained by a small projection of v35; the nonlinear solve needs the
`q=0` boundary constraints built in from the start.

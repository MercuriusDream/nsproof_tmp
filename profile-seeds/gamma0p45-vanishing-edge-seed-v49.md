# Tail-Admissible Vanishing Edge Seed v49: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-seed-v49.json
```

This is the current best trace-preserving seed on the standard, local,
interior, and original extreme gates. It keeps the exact conical far-boundary
trace

```text
F(0,b) = 1/2,
G(0,b) = B
```

by freezing the monomial `q^0 b^(2j)` coefficients for `j>0` and using the
vanishing edge basis

```text
q * (1-q)^i * b^(2j),
0 <= i,j <= 8.
```

It was obtained from v47 by a far-edge-weighted constrained Gauss-Newton run.
The first two weighted steps rejected; the third accepted a damped half-step.

## Boundary Trace

The sampled `q=0` trace is exact:

```text
max |F(0,b)-1/2| = 0
max |G(0,b)-B|   = 0
```

## Gate Metrics

Standard gate:

```text
q in [0.35,0.90], b in [-0.80,0.80]
RMS residual: 1.148387758398e-02
max residual: 5.470627484641e-02
```

Interior compactified gate:

```text
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 3.765073871350e-03
max residual: 1.174547781095e-02
```

Local rectangle:

```text
r in [0.8,2.0], z in [-1,1]
RMS residual: 5.745882184657e-03
max residual: 4.752159416815e-02
```

Extreme gate:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 1.122817005407e-02
max residual: 5.535569977138e-02
```

Farther-tail probe:

```text
q in [0.18,0.30], b in [-0.90,0.90]
RMS residual: 6.357093982907e-02
max residual: 2.682727177003e-01
```

## Finite-Difference Stability

```text
standard h = 2e-3: max = 5.470540584580e-02
standard h = 1e-3: max = 5.470627484641e-02
standard h = 5e-4: max = 5.470735424147e-02

extreme h = 2e-3: max = 5.534732366895e-02
extreme h = 1e-3: max = 5.535569977138e-02
extreme h = 5e-4: max = 5.534217181756e-02

farther-tail h = 2e-3: max = 2.683098702000e-01
farther-tail h = 1e-3: max = 2.682727177003e-01
farther-tail h = 5e-4: max = 2.677189514456e-01
```

## Comparison

The constrained sequence now beats the non-admissible bounded-edge v35 on the
standard and original extreme compactified gates while preserving the exact
conical trace:

```text
standard max:
v35 non-admissible: 1.957809706943e-01
v49 admissible:     5.470627484641e-02

extreme max:
v35 non-admissible: 3.633506253060e-01
v49 admissible:     5.535569977138e-02
```

The remaining large obstruction is farther into the tail at `q=0.18`, around
`|b| ~= 0.45`, mostly in the streamfunction equation. A test with a slower
vanishing `q^0.5` edge family preserved the trace but worsened this farther-tail
max to `3.20e-1`, so that parameterization did not solve the obstruction.

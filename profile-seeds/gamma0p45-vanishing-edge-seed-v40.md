# Tail-Admissible Vanishing Edge Seed v40: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-seed-v40.json
```

This is the current best tail-admissible constrained continuation. It enforces
the exact conical far-boundary trace

```text
F(0,b) = 1/2,
G(0,b) = B
```

by freezing the monomial `q^0 b^(2j)` coefficients for `j>0` at zero and using
the vanishing edge family

```text
q * (1-q)^i * b^(2j),
0 <= i,j <= 8.
```

v40 continued v37 through v38 and v39 using larger constrained Gauss-Newton
steps. The training RMS decreased monotonically:

```text
v37 training RMS: 1.241831417456e-01
v38 training RMS: 1.215475634251e-01
v39 training RMS: 1.174792212469e-01
v40 training RMS: 1.139670567852e-01
```

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
RMS residual: 1.523974986729e-01
max residual: 7.109294097097e-01
```

Interior compactified gate:

```text
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 5.853625731012e-02
max residual: 1.951634666146e-01
```

Local rectangle:

```text
r in [0.8,2.0], z in [-1,1]
RMS residual: 8.863581359449e-02
max residual: 6.457688663085e-01
```

Extreme gate:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 1.350193458802e-01
max residual: 6.612026574807e-01
```

Farther-tail probe:

```text
q in [0.18,0.30], b in [-0.90,0.90]
RMS residual: 1.135788066204e-01
max residual: 4.261250143780e-01
```

## Finite-Difference Stability

```text
standard h = 2e-3: max = 7.109167827613e-01
standard h = 1e-3: max = 7.109294097097e-01
standard h = 5e-4: max = 7.109330413385e-01

farther-tail h = 2e-3: max = 4.261181727684e-01
farther-tail h = 1e-3: max = 4.261250143780e-01
farther-tail h = 5e-4: max = 4.262308826300e-01
```

## Interpretation

v40 improves the tail-admissible sequence monotonically:

```text
standard max:     v37 7.73e-1 -> v40 7.11e-1
extreme max:      v37 7.20e-1 -> v40 6.61e-1
farther-tail max: v37 4.67e-1 -> v40 4.26e-1
```

It is still far worse on finite boxes than the non-admissible bounded-edge v35.
That gap confirms the earlier conclusion: a valid profile must be solved with
the conical trace enforced from the start, and the current constrained
polynomial/vanishing-edge basis remains far from the `1e-8` validation gate.

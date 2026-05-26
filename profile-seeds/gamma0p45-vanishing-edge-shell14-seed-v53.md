# Tail-Admissible Shell-14 Far-Tail Seed v53: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-shell14-seed-v53.json
```

This is a far-tail-focused constrained continuation from the balanced
trace-preserving v49 seed. It keeps the exact conical trace

```text
F(0,b) = 1/2,
G(0,b) = B
```

and uses only newly added high-order vanishing edge shells:

```text
q * (1-q)^i * b^(2j).
```

The shell-10 correction improved the `q=0.18` lobe from v49, and the shell-12
and shell-14 corrections pushed it further:

```text
v49 farther-tail max: 2.682727177003e-01
v51 shell-10 max:     2.243716179375e-01
v52 shell-12 max:     1.931711331107e-01
v53 shell-14 max:     1.792056343172e-01
```

## Gate Metrics

Standard gate:

```text
q in [0.35,0.90], b in [-0.80,0.80]
RMS residual: 1.676743157714e-02
max residual: 7.607876229271e-02
```

Extreme gate:

```text
q in [0.25,0.90], b in [-0.90,0.90]
RMS residual: 1.473123725085e-02
max residual: 6.231594228615e-02
```

Farther-tail probe:

```text
q in [0.18,0.30], b in [-0.90,0.90]
RMS residual: 3.847844288847e-02
max residual: 1.792056343172e-01
```

## Finite-Difference Stability

```text
farther-tail h = 2e-3: max = 1.792165754613e-01
farther-tail h = 1e-3: max = 1.792056343172e-01
farther-tail h = 5e-4: max = 1.798543628562e-01
```

## Interpretation

The high-order shells lower the farthest sampled tail defect while preserving
the conical trace, but they trade off against the standard/local gates. v49 is
the best balanced admissible seed; v53 is the best far-tail-focused admissible
seed. The remaining obstruction is still a streamfunction-equation lobe at
`q=0.18`, near `|b|=0.56`.

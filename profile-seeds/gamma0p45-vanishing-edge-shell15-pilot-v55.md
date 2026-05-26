# Tail-Admissible Shell-15 Pilot v55: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-shell15-pilot-v55.json
```

This is a small, targeted pilot continuation from v54. It keeps the monomial
trace fixed and varies only newly added shell-15 vanishing-edge coefficients in

```text
q * (1-q)^i * b^(2j).
```

The training box was the observed lobe region:

```text
q in [0.16,0.26],
b in [-0.75,0.75].
```

The pure-Python finite-difference solver first proved too slow for a larger
shell-16 run, so this pilot used a smaller unbuffered solve with 62 variables
and 65 training points. It accepted three damped steps:

```text
initial training RMS: 8.612651038874e-02
final training RMS:   8.598332817698e-02
```

## Gate Comparison

The conical trace remains exact:

```text
max |F(0,b)-1/2| = 0
max |G(0,b)-B|   = 0
```

Compared with v54, the pilot gives only a marginal lobe improvement:

```text
q in [0.18,0.30], |b| <= 0.90:
v54 max: 1.792056343172e-01
v55 max: 1.788852608387e-01

q in [0.16,0.30], |b| <= 0.90:
v54 max: 3.126310682833e-01
v55 max: 3.092117482793e-01
```

The standard gate worsens slightly:

```text
v54 standard max: 7.607876229271e-02
v55 standard max: 7.613578634283e-02
```

## Tail Scaling

The new `tools/profile_tail_scaling.py` diagnostic scans fixed-q slices and
fits the log-log slope of the slice maxima. On `q in [0.14,0.30]`, the slopes
are

```text
v49: -3.424196379310e+00
v54: -3.326791266616e+00
v55: -3.326077359962e+00
```

On the sharper far-tail window `q in [0.14,0.22]`, v54 is stable across
finite-difference steps:

```text
h = 2e-3: slope = -5.337235464031e+00
h = 1e-3: slope = -5.337496082569e+00
h = 5e-4: slope = -5.344794235784e+00
```

## Interpretation

This pilot is not a new best seed. It confirms that adding another monomial
vanishing-edge shell can slightly reduce the sampled lobe while preserving the
trace, but it does not change the far-tail scaling. The defect is being pushed
toward smaller `q`, which points to a missing asymptotic tail mode or a bad
choice of compactified correction basis rather than an ordinary high-degree
polynomial resolution problem.

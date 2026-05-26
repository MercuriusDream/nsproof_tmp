# Forced q^(1/gamma) Tail Direction v62-v64: gamma = 0.45, B = 1.0

Machine-readable seeds:

```text
profile-seeds/gamma0p45-forced-tail-qm-v62.json
profile-seeds/gamma0p45-forced-tail-qm-q2solve-v63.json
profile-seeds/gamma0p45-forced-tail-qm-q2solve-v64.json
```

This sequence tests the asymptotic correction indicated by the tail-series
diagnostic. At `gamma=0.45`, the first nonlinear self-interaction of the
constant `q=0` trace appears at the non-integer order

```text
q^(1/gamma) = q^2.222222222222...
```

The new tool

```text
tools/profile_forced_tail.py
```

solves the angular least-squares equations for a `q^(1/gamma)` correction that
cancels this leading nonlinear source. With `b_order=8`, the cancellation is at
roundoff level:

```text
psi source before max:   2.329118197481e+00
psi source after max:    6.099271088189e-11

Gamma source before max: 2.249300232178e-01
Gamma source after max:  4.041022655388e-10
```

The leading coefficients are essentially low-order:

```text
F_sigma ~=  1.921814092840 - 0.978677327996 b^2
G_sigma ~=  0.111111110707 - 1.111111070631 b^2
```

## v62: Forced-Tail Diagnostic Seed

v62 contains only the exact `q=0` trace and the forced `q^(1/gamma)` correction.
It has no integer `q^1`, `q^2`, `q^3`, or `q^4` tail coefficients.

The far-tail behavior improves sharply:

```text
q in [0.03,0.14] max: 3.766642552883e-02
q in [0.18,0.30] max: 8.907578901132e-02
```

The finite/interior box is not solved:

```text
standard max: 3.036577659826e+00
local max:    3.003423546596e+00
```

## v63-v64: q1-Frozen q>=2 Interior Solve

The bounded-edge Gauss-Newton solver now supports

```text
--monomial-min-q-order 2
```

so monomial optimization can start at `q^2` while preserving both the exact
trace and the absence of a `q^1` tail coefficient. Starting from v62, v63/v64
allow ordinary monomial corrections with `q`-order at least 2 and keep the
forced `q^(1/gamma)` family active.

The harder v64 run reduces the training RMS:

```text
v63 start RMS: 6.784547820529e-01
v64 final RMS: 6.035328110998e-01
```

and preserves the q1 constraint:

```text
order q^1 psi linear max:   0
order q^1 Gamma linear max: 0
```

The far-tail gate remains strong and finite-difference stable:

```text
q in [0.18,0.30], h = 2e-3: max = 9.015810891471e-02
q in [0.18,0.30], h = 1e-3: max = 9.016164760362e-02
q in [0.18,0.30], h = 5e-4: max = 9.013938030938e-02
```

But the standard/interior/local gates remain too large:

```text
standard max: 2.630970784815e+00
interior max: 2.699587690022e+00
local max:    2.670237995086e+00
```

## Interpretation

v64 is not a validated profile and is not a better balanced seed than v49.
However, it is the first seed in this workspace that aligns the far-tail
series with the forced non-integer asymptotic correction while keeping the
forbidden q1 channel absent. It cuts the far-tail `q in [0.18,0.30]` defect
roughly in half relative to v54:

```text
v54 far-tail max: 1.792056343172e-01
v64 far-tail max: 9.016164760362e-02
```

The remaining obstruction has shifted inward: the profile now needs a genuine
interior matching solve coupled to the asymptotic tail basis, rather than
finite-box polynomial shells that use forbidden low-order tail coefficients.

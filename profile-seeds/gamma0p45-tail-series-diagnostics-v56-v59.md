# Tail-Series Diagnostics v56-v59: gamma = 0.45, B = 1.0

This note records diagnostic projections after the v54/v55 far-tail work. These
are not improved profile candidates. They test whether the finite-box residual
improvements rely on forbidden low-order integer tail coefficients.

## Tail-Series Diagnostic

The tool

```text
tools/profile_tail_series.py
```

expands a seed near `q=0` and reports the linear transport residual generated
by each integer `q^n` coefficient. For a genuine asymptotic expansion, the
positive integer coefficients cannot be arbitrary: the `q^1` channel is
geometric/center-like, and a generic `q^1` coefficient creates a leading tail
residual.

For v54, the first integer tail coefficient is large:

```text
order 1:
F_1 max:              1.528143595767e+01
G_1 max:              3.366956388107e+01
psi linear max:       3.926189986060e+00
Gamma linear max:     9.419011346695e+00
```

The leading trace also has a nonzero nonlinear source at the non-integer order
`q^(1/gamma) = q^2.222...`:

```text
psi source max:       2.329369172244e+00
Gamma source max:     2.249840901486e-01
```

This is the first concrete indication that the current integer-polynomial
tail is structurally misaligned with the required asymptotic expansion.

## v56: q1 Tail Filter

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-tailfilter1-v56.json
```

This seed adds monomial counterterms to v54 so that the total `q^1` coefficient
of both `F` and `G` vanishes. The q=0 trace remains exact, and the series check
confirms the cancellation to roundoff:

```text
order 1 psi linear max:   7.131784084331e-16
order 1 Gamma linear max: 6.419864639895e-15
```

The very far slices improve, but the finite-box residual is destroyed:

```text
q in [0.18,0.30] max: 1.029116539178e+01
standard max:         7.829988985390e+01
```

Interpretation: the v54 fit uses its forbidden `q^1` component as a finite-box
compensator. Removing it without changing the rest of the basis is not viable.

## v57: q2 Vanishing-Family Refit

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-q2fit-v57.json
```

This refits the v54 edge correction into a `q^2(1-q)^i b^(2j)` vanishing
family. Because the original monomial `q^1` terms remain, v57 still has a
forbidden first tail coefficient:

```text
order 1 psi linear max:   1.698634170547e+00
order 1 Gamma linear max: 5.000823855500e+00
```

Its finite residuals are worse than v54 but not catastrophic:

```text
q in [0.18,0.30] max: 4.052567239301e-01
standard max:         1.695557690342e-01
```

## v58-v59: q2 Family With q1 Removed

Machine-readable seeds:

```text
profile-seeds/gamma0p45-vanishing-edge-q2fit-tailfilter1-v58.json
profile-seeds/gamma0p45-vanishing-edge-q2constrained-v59.json
```

v58 applies the q1 tail filter to v57. v59 then runs three damped Gauss-Newton
steps while keeping monomial coefficients frozen and using only the q2
vanishing family. The q1 channel stays exactly zero:

```text
order 1 psi linear max:   0
order 1 Gamma linear max: 0
```

But the finite-box residual remains too large:

```text
v58 q in [0.18,0.30] max: 2.816515534984e+00
v59 q in [0.18,0.30] max: 2.810165146512e+00
v59 standard max:         1.764307765388e+01
```

The q2-constrained solver's training RMS barely moved:

```text
initial RMS: 4.458677812126e+00
final RMS:   4.446988574269e+00
```

## Conclusion

The current admissible finite-box seeds are not just under-resolved. They rely
on low-order integer tail coefficients that are not compatible with the
asymptotic tail classification. Enforcing the first tail constraint without a
new representation makes the finite-box problem badly inconsistent.

The next profile representation should be built from the tail expansion:

```text
constant q=0 trace
+ geometric q^1 modes only if center modulation is left unfixed
+ non-integer q^(1/gamma) forced correction
+ validated indicial modes
```

Continuing with unconstrained integer vanishing shells is no longer a
proof-relevant path.

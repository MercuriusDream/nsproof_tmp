# gamma0p45 forced-tail sparse flat-bump v117 ridge-strip final

This note records the final saved v117 ridge-strip coordinate-search seed at
`gamma=0.45`, `B=1.0`.

The run starts from
`profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip-base.json`
and writes the full optimizer log to
`profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip-run.md`.
The final saved seed is:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip.json
optimizer score max = 4.346963144133e-1
active = 4.346727268717e-1
extreme = 4.333119973137e-1
farther = 3.834216871230e-1
interior = 4.322425589778e-1
local = 4.346265632453e-1
wide = 4.346963144133e-1
```

Independent profile gates for this final seed:

```text
standard h=2e-3,1e-3,5e-4 max:
4.343958248990e-1, 4.344046967088e-1, 4.344070020656e-1.

fine 29x29/45 max:
4.362251080302e-1.

shifted h=1.6e-3,8e-4,4e-4 max:
4.364874143437e-1, 4.364860207575e-1, 4.364865315324e-1.

broad 41x41 topology max:
4.347549502774e-1 at q=0.378, |b|=0.315.

focused hidden-ridge max:
4.364654153641e-1 at q=0.400, |b|=0.293333.

secondary q ~= 0.608, |b| ~= 0.241 ridge:
4.350113142226e-1.
```

The remaining broad-grid obstruction is a low-`|b|` streamfunction ridge.  The
focused topology probe ranks the hidden maximum near `q=0.400`,
`|b|=0.293333`, followed by nearby points around `q=0.395-0.405`,
`|b|=0.286-0.300`, and then the secondary `q=0.607917`, `|b|=0.240833`
ridge.  The previous high-`|b|` and far-tail holdouts are now below the main
ridge.

The tail-series diagnostic still preserves the asymptotic constraints used in
the forced-tail family:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
forced q^(1/gamma) correction remains present.
```

The final seed was also projected into the proof-native transseries/Chebyshev
scaffold with
`tools/profile_project_cheb.py --input profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip.json --gamma 9/20 --B 1 --degree-q 10 --degree-x 10 --tail-blocks 1 --origin-degree 4 --out work/v117_transcheb.json`.
The structural tail check passes (`q1=0`, forced `q^(1/gamma)` lifted) and the
patch reconstruction errors are small (`F ~= 9.34e-8`, `G ~= 2.57e-6`), but
the origin Taylor fit fails badly (`F ~= 6.49e-1`, `G ~= 3.17e-1`).
`validators/compactified_equations.py` evaluates the projected profile through
the existing finite-difference oracle and recovers the same obstruction:
focused hidden-ridge max `4.364542617048e-1` and secondary ridge max
`4.349867452619e-1`.  Its Taylor-jet mode, which differentiates the projected
Chebyshev expression instead of finite-differencing it, gives
`4.364551889010e-1` and `4.349878819316e-1` on the same focused and secondary
boxes.

The first proof-native coefficient-space optimizer
`tools/profile_newton_cheb.py` confirms that this is still only a diagnostic
seed.  After fixing variable selection to balance across requested blocks, a
focused hidden-ridge Chebyshev run produces held-out maxima
`4.346774703261e-1` on the focused box and `4.349878819316e-1` on the
secondary box.  A broader two-ridge run improves the secondary box to
`4.339438267027e-1` but worsens the focused held-out box to
`4.370029069859e-1`.  This is residual redistribution, not a Newton-grade
profile.

The origin Taylor block stored in `work/v117_transcheb.json` is now evaluated
by `validators/compactified_equations.py` for `q >= q_min`, and it fails badly:
on `q=[0.91,0.98]`, `b=[0.05,0.80]`, the Taylor-jet residual has
`max_abs = 1.427061295791e+1`.  Just below the origin patch,
`q=[0.82,0.895]`, the rectangular Chebyshev evaluator gives
`max_abs = 1.679666438145e-1`.  The origin-regular profile space therefore has
to be solved directly; the current origin fit is not a theorem object.

The compactified-equation bridge now also has normalized residual diagnostics.
For the structural quotient

```text
E_psi   / (r^4 z q^(p+4)),
E_Gamma / (r^2 q^(p+2)),
```

the same projected v117 seed has focused-box max
`1.071336958406e+1` and origin-patch max `9.139966362302e+3`.  The stricter
tail quotient on the focused box is `1.252539984352e+1`.  These are
discovery quotients, not interval residual certificates, but they make clear
that v117 is not close to a proof-grade center after known vanishing factors
are divided out.

The later sparse-bump v118 exact seed was also inspected.  Its saved score is
`4.353608399992e-1`, so it is another `O(1)` redistribution diagnostic rather
than an improvement over final v117.  It has no proof-native projection,
tail-recurrence, origin, or NK evidence and should not supersede this v117
projection branch.

Thus v117 ridge-strip is a real numerical improvement over v116-lowb on the
independent fine and shifted gates, but it remains an `O(1)` residual
diagnostic seed.  Sparse flat bumps should be retired as the proof
representation; the next solve must use a transseries-constrained
Chebyshev/origin-regular basis with exact residuals from the start.

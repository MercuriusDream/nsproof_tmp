# NSProof C Kernel Prototype

This directory contains a small C ABI prototype for moving hot row/Jacobian
kernels out of Python while keeping Python as the solver orchestration and
artifact/report layer. The scalar Chebyshev helpers are still a benchmark/probe
boundary. The R/Z tail-coefficient mortar Jacobian batch path and the first
PDE/guard tail-coefficient column batch path are wired into Stage-0 behind
`--native-c`.

## Implemented Boundary

`nsproof_kernel.c` exports:

- `nsproof_cheb_basis_values(count, t, order, out)`
  - C equivalent of `cheb_basis_values(count, t, order)`.
  - Uses the same recurrence for Chebyshev derivative values.
  - Supports derivative orders `0..4`.
- `nsproof_cheb_basis_value(index, t, order, status)`
  - Scalar convenience wrapper around the same recurrence.
- `nsproof_cheb_basis_partial(q0, q1, x0, x1, q, x, kq, kx, dq_order, dx_order, status)`
  - C equivalent of `cheb_basis_partial(patch, q, x, kq, kx, dq_order, dx_order)`.
  - The patch is represented by explicit interval endpoints instead of a Python
    dictionary.
- `nsproof_weighted_cheb_coeff_partial(q0, q1, x0, x1, alpha, q, x, kq, kx, dq_order, dx_order, status)`
  - C equivalent of `weighted_cheb_coeff_partial(...)`.
  - Applies the same product rule for `q**alpha * basis`.
- `nsproof_weighted_cheb_coeff_partial_array(...)`
  - A simple batch ABI for timing and future row/Jacobian assembly experiments.
  - It reduces Python/ctypes call overhead by evaluating many coefficient
    partials in one C call.
- `nsproof_rz_weighted_coeff_partials_batch(...)`
  - Batched R/Z chain-rule kernel for tail coefficient columns in physical
    mortar rows.
  - Builds factorial-divided jets for `q(R,Z)`, `x(R,Z)`, `q^alpha`, and the
    Chebyshev tensor basis up to total order 4.
  - Returns the partials in the same order as
    `validators.origin_chart.derivative_indices(max_order)`.
- `nsproof_pde_tail_coeff_columns_batch(...)`
  - Batched physical-space PDE linearized residual columns for active tail
    coefficients at one `(q,b)` point.
  - Reconstructs `q(r,z)`, `x(r,z)`, the coefficient jet, and the mechanical
    profile variation in C, then evaluates the same normalized residual-kind
    quotients as the Python path.
  - Uses caller-provided base profile scalars so Python can still own profile
    evaluation while the repeated tail-column work moves to C.
- `nsproof_pde_origin_coeff_columns_batch(...)`
  - Batched physical-space PDE linearized residual columns for active origin
    Taylor coefficients at one `(q,b)` point.
  - Evaluates origin monomial perturbations `R^a Z^b`, with `R=r^2` and
    `Z=z^2`, inside the same `psi = r^2 z q^p F` and
    `Gamma = r^2 q^p G` envelopes used by the Python jet path.
  - Uses nonnegative integer jet powers for the origin monomials so zero-valued
    monomial bases do not depend on real-power jets.
- `nsproof_stage0_prediction_scan_batch(...)`
  - Batched linear prediction metrics for already-built Stage-0 rows.
  - Evaluates `residual + alpha * J * step` for several applied alphas and
    returns `l2`, `max_abs`, and objective values.
  - This is diagnostic/reporting infrastructure only; actual nonlinear
    line-search acceptance still uses the existing Python objective evaluation.

All exported functions use only plain C types and caller-owned buffers. Error
status values are:

- `0`: success
- `-1`: null pointer
- `-2`: derivative order outside `0..4`
- `-3`: negative Chebyshev index
- `-4`: degenerate interval
- `-5`: nonfinite input
- `-6`: nonfinite output

The benchmark intentionally runs repeated Python-vs-C cross-checks. Production
solver paths should not cross-check every call against Python; they should use a
fast C self-check at startup or in CI, then call the C batch kernels directly.

## Mapping To Python

The Python call:

```python
weighted_cheb_coeff_partial(
    patch, alpha, q, x, kq, kx, dq_order, dx_order
)
```

maps to:

```c
nsproof_weighted_cheb_coeff_partial(
    q0, q1, x0, x1,
    alpha, q, x,
    kq, kx,
    dq_order, dx_order,
    &status
)
```

where `(q0, q1, x0, x1)` come from `patch["q_interval"]` and
`patch["x_interval"]`.

## Benchmark

Run:

```bash
python3 tools/benchmark_native_c_kernel.py
```

The benchmark compiles `native/c/nsproof_kernel.c` with `clang` into a temporary
shared library, loads it with `ctypes`, checks deterministic cases against the
current Python implementation, and prints scalar and batch timing comparisons.

## Stage-0 128 Path Probe

Run:

```bash
python3 tools/profile_newton_twochart_c_path_probe.py --repeats 5
```

The probe does not run Stage-0. It reads the existing row cache for the 128
scaled guarded-inequality run, extracts the active tail coefficient/point shape,
and benchmarks the current q/x weighted coefficient partial batch ABI against
the equivalent Python helper calls.

Latest local probe on `work/twochart_stage0_rz_ineqkkt_seamlimit128_scaled_w8_rows.json`:

```text
rows = 222
columns = 128
source_case_counts = active_guard 7950, mortar_rz_proxy 474, pde 610
weighted_partial_cases = 9034
batch_groups = 9
validation max_abs = 7.276e-12
validation max_rel = 1.280e-15
python_seconds = 1.094077
c_batch_seconds = 0.004808
c_batch_speedup_vs_python = 227.53x
current_128_exact_c_accelerable_without_solver_changes = false
```

That probe is now historical for the q/x inner-kernel boundary. The current C
ABI also includes the R/Z chain-rule kernel, PDE/guard tail-column and
origin-column kernels, and a linear prediction scan kernel, so the remaining
large non-native slice in the 128 run is mostly base profile evaluation,
active-set linear algebra, row selection, and nonlinear objective/guard
reevaluation.

## Stage-0 Native Paths

The R/Z mortar, PDE/guard tail-column, and linear-prediction slices are now
available in the solver:

```bash
python3 tools/profile_newton_twochart.py ... --mortar-coordinates RZ --native-c
```

The latest 128-variable scaled inequality diagnostic using all current native
paths is:

```text
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_report.json
```

It records:

```text
real time = 38.06s
native_c_rz calls = 42, cases = 804, seconds = 0.000593
native_c_pde cases = 1222, seconds = 0.004282
native_c_prediction cases = 426240, seconds = 0.003939
selected variables = 128 = 101 tail + 27 origin
accepted block = full
held-out edge = 4.489165334070e2
C0-C4 R/Z mortar = 5.833745908165e6
```

The C4 mortar audit:

```text
work/twochart_stage0_rz_ineqkkt_seamlimit128_nativepred_w8_c_mortar_c4.json
```

uses the same native path for `43560` R/Z tail cases.

Validation against the Python R/Z jet, PDE tail-column, and prediction paths:

```text
R/Z max_abs = 4.628673195839e-7
R/Z max_rel = 4.105836156138e-12
R/Z finite-difference smoke max_abs = 4.351176130513e-8
PDE tail validation points = 4
PDE tail validation cases = 320
PDE tail max_abs = 1.997e-6
PDE tail max_rel = 2.239e-13
prediction scan validation passed on deterministic dense matrices
```

`tools/benchmark_native_c_kernel.py` now validates both the Chebyshev
microkernel, the R/Z batch kernel, the PDE tail-column batch kernel, and the
prediction scan kernel. Latest local run:

```text
NSPROOF_NATIVE_C_VALIDATION_PASSES=2 NSPROOF_NATIVE_C_REPEATS=50
native/c Chebyshev+RZ+PDE-tail+prediction kernel validation: ok
scalar ctypes C: 11.16x vs Python
batch ctypes C: 100.86x vs Python
```

## Remaining Native Work

- Define the stable row/Jacobian kernel ABI around complete multi-point
  PDE/guard row batches. The current PDE kernel batches tail columns at one
  point; the next boundary should batch many points and include origin columns
  or a packed profile view:

```c
int nsproof_pde_linearized_columns_batch(
    int point_count,
    int variable_count,
    const double *q,
    const double *b,
    int residual_kind,
    const struct nsproof_profile_view *profile,
    const struct nsproof_variable_desc *variables,
    double *out_e_psi,
    double *out_e_gamma,
    int *out_status
);

int nsproof_stage0_prediction_scan_batch(
    int row_count,
    int column_count,
    int alpha_count,
    const double *rows,
    const double *residuals,
    const double *step,
    const double *alphas,
    double *out_l2,
    double *out_max_abs,
    double *out_objective,
    int *out_status
);
```

- Decide how patch inventory, active-patch selection, alpha values, base profile
  scalars, and coefficient metadata are packed for deterministic JSON-facing
  APIs.
- Add native tests in CI once solver semantics and row definitions stop moving.
- Keep Python as orchestration/reporting while moving repeated row assembly and
  guard scan loops behind compiled batch calls.

# NSProof Rust Kernel Prototype

This directory contains a first native boundary for the hot Chebyshev
row/Jacobian path. It is deliberately narrow: the current prototype mirrors the
floating formulas in `validators/twochart_mortar_jacobian.py` without changing
solver semantics or touching the Python orchestration layer.

## Current Route: `rustc` cdylib + `ctypes`

`nsproof_kernel.rs` can be compiled directly with `rustc` as a C ABI shared
library. The probe script does this in a temporary directory:

```sh
python3 tools/benchmark_native_rust_kernel.py
```

The exported functions cover:

- `nsproof_cheb_basis_values`: fill `T_n(t)` derivative values for one
  derivative order `0..4`.
- `nsproof_cheb_basis_table_order4`: fill all derivative orders `0..4` for a
  basis count.
- `nsproof_cheb_basis_partial`: evaluate one compactified tensor-product
  Chebyshev basis partial.
- `nsproof_weighted_cheb_coeff_partial`: evaluate the partial of
  `q^alpha * patch(q, x)` with respect to one Chebyshev coefficient.
- `nsproof_weighted_cheb_coeff_partials`: fill a row-major batch of weighted
  coefficient partials for one patch shape.

The fill/batch routines return `0` on success and negative status codes on
invalid input. Scalar helper routines return `NaN` on invalid input so they are
easy to compare from `ctypes`.

This route is the lowest-friction bridge while the row definitions and guarded
KKT diagnostics are still moving. It avoids package metadata and keeps the ABI
visible.

## Later Route: PyO3 + maturin

After the row schema stabilizes, a PyO3 extension built with maturin is the
cleaner Python-facing route. It can expose typed Python functions, reuse Python
buffers or memoryviews, and package platform wheels. That is a better fit once
the native surface is stable enough to justify a build backend and CI matrix.

## Alternative Route: Rust CLI JSON Bridge

A Rust command-line tool that reads JSON and writes JSON remains useful for
larger diagnostic batches and reproducible artifact generation. It has more
process overhead than `ctypes`, but it keeps failure isolation strong and makes
cross-language contracts explicit. This is attractive for report-generation
jobs, not for inner-loop line-search or row assembly calls.

## Scope Boundary

The current Rust code is only a prototype kernel boundary. It should not be
treated as the final performance architecture until the guarded inequality KKT
path, row definitions, and residual factorization have settled.

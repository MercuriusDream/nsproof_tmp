# Repository Notes for Agents

## Performance Direction

The current two-chart discovery stack is intentionally Python-heavy while the
equations, row selection, guards, and report schema are still changing quickly.
That is acceptable for scaffold work, but it is not the intended final
performance architecture.

Once the guarded inequality KKT path, row definitions, and exact residual
factorization stabilize, move the repeated hot kernels out of pure Python:

- row and Jacobian evaluation for compactified two-chart residuals;
- mortar and edge/seam guard row generation;
- active-set KKT/SVD linear algebra wrappers;
- batched prediction-vs-actual line-search scans;
- Bernstein/exact residual interval kernels, where applicable.

Preferred direction: keep Python as the orchestration and artifact/report layer,
but implement stable numerical kernels in C first, with deterministic
JSON-facing APIs or `ctypes`/extension boundaries. GPU is not the first target
for the current workload; the bottleneck is mostly CPU-side row assembly, scalar
profile evaluation, small-to-medium dense linear algebra, and repeated guard
scans.

When moving kernels to C, treat floating reliability as part of the API:

- validate every C kernel against the current Python implementation on
  deterministic cases before using it in Stage-0, preferably multiple times
  during benchmark/CI checks;
- do not re-run Python cross-checks on every production solver invocation; once
  a C kernel has passed repeated cross-checks, use fast C-side status/self-checks
  and call the batched C path directly;
- return explicit status codes for bad derivative orders, degenerate intervals,
  null buffers, nonfinite inputs, or overflow-sensitive paths;
- clamp or rescale intermediate products where long/large floating values can
  overflow, and report that scaling in benchmark/diagnostic metadata;
- prefer batched C entry points over scalar `ctypes` calls, because the
  benchmarked batch path is the real speedup boundary.

Do not start a full solver rewrite before the solver semantics stabilize. First
port the stable hot kernels and keep Python as the controller while the
mathematics is still moving.

# gamma=0.45 forced-tail minimax sequence v96-v103

This run added `tools/profile_minimax_coordinate.py`, a max-aware pattern
search over selected coefficient families.  Unlike the Gauss-Newton training
steps, it accepts a coefficient move only when it lowers the maximum absolute
residual on the requested gates; RMS is reported only as supporting evidence.

The sequence starts from v93:

```text
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v93.json
standard/interior/local/farther =
5.296559969709e-1 / 5.273605597729e-1 /
5.294625460480e-1 / 4.016192226850e-1.
```

F-only minimax moves produced v96:

```text
profile-seeds/gamma0p45-forced-tail-minimax-flatbumpF-v96.json
standard/interior/local/farther =
5.275829775429e-1 / 5.240593713600e-1 /
5.275988294543e-1 / 4.026602003783e-1.
```

Adding zero-start tail-flat `G` bumps and continuing produced v99-v101:

```text
v99 tracked standard/interior/local/farther =
4.805065636182e-1 / 4.761324675491e-1 /
4.791965607733e-1 / 3.977404376812e-1.

v101 fine 29x29/45-grid max =
4.712211117118e-1,
41x41 topology max =
4.745795020359e-1.
```

The 41x41 topology scan exposed an off-grid lobe, so active `(q,b)` support
was added to the minimax tool.  Active continuation through v103 gave the
best balanced q1-free forced-tail seed at this stage:

```text
profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v103.json

standard h=1e-3:
wide     = 4.595263267048e-1
interior = 4.556840998552e-1
local    = 4.607838677803e-1

fine 29x29/45-grid h=1e-3:
wide     = 4.606501154624e-1
interior = 4.556840998552e-1
local    = 4.607838677803e-1

41x41 topology max:
4.608097446714e-1 at q=0.414, b=-0.315.

farther q in [0.18,0.30] h=1e-3:
3.884802493867e-1.
```

The finite-difference sweeps for v103 are stable:

```text
standard wide h=2e-3,1e-3,5e-4:
4.595235348870e-1, 4.595263267048e-1, 4.595291556842e-1.

standard interior h=2e-3,1e-3,5e-4:
4.556833859696e-1, 4.556840998552e-1, 4.556808169449e-1.

standard local h=2e-3,1e-3,5e-4:
4.607790662103e-1, 4.607838677803e-1, 4.607856044461e-1.

farther-tail h=2e-3,1e-3,5e-4:
3.884748284542e-1, 3.884802493867e-1, 3.884958429693e-1.
```

The tail-series diagnostic is unchanged by the tail-flat bumps in the ordinary
integer channels:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

Thus v103 was better numerical evidence for the constrained interior matching
problem, not a validated profile.  The continuation was extended in
`profile-seeds/gamma0p45-forced-tail-minimax-v104-v106.md`, where v106 becomes
the next best endpoint.  The residual remains `O(1)`, the q5-q6 ordinary tail
residual remains large, and the final proof still needs a validated
profile/spectrum package.

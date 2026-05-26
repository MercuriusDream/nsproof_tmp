# gamma=0.45 forced-tail minimax extension v104-v106

This extends the v96-v103 max-aware tail-flat bump sequence.  The purpose was
to test whether the v103 endpoint was a grid-local optimum or whether refreshed
active topology points could keep lowering the maximum residual while
preserving the exact trace and zero q1 channel.

Starting point:

```text
profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v103.json
fine/active max      = 4.608097446714e-1,
41x41 topology max   = 4.608097446714e-1,
farther-tail max     = 3.884802493867e-1.
```

Continuing the same active set gave v104:

```text
profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v104.json
fine max             = 4.592595616542e-1,
41x41 topology max   = 4.588493440409e-1,
farther-tail max     = 3.878096016284e-1.
```

The first v105 attempt reduced the fine gate but exposed a hidden 41x41 lobe
near `q=0.486`, `|b|=0.585`, so v105 is diagnostic rather than the preferred
endpoint:

```text
profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v105.json
fine max             = 4.580585555726e-1,
41x41 topology max   = 4.591097572034e-1.
```

Refreshing the active set with that hidden lobe produced v106, the current
best balanced q1-free forced-tail seed:

```text
profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v106.json

standard h=1e-3:
wide     = 4.525392363637e-1
interior = 4.523133293752e-1
local    = 4.549610384871e-1

fine 29x29/45-grid h=1e-3:
wide     = 4.550283493881e-1
interior = 4.538946378616e-1
local    = 4.549610384871e-1

41x41 topology max:
4.544085174837e-1 at q=0.486, b=0.585.

farther q in [0.18,0.30] h=1e-3:
3.852405555391e-1.
```

The v106 finite-difference sweeps are stable:

```text
standard wide h=2e-3,1e-3,5e-4:
4.525353356627e-1, 4.525392363637e-1, 4.525456373170e-1.

standard interior h=2e-3,1e-3,5e-4:
4.523124982329e-1, 4.523133293752e-1, 4.523109686800e-1.

standard local h=2e-3,1e-3,5e-4:
4.549500774717e-1, 4.549610384871e-1, 4.549627285331e-1.

farther-tail h=2e-3,1e-3,5e-4:
3.852366582649e-1, 3.852405555391e-1, 3.852815990152e-1.
```

The tail-series diagnostic remains unchanged in the ordinary tail channels:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

This is still only numerical evidence.  The residual is `O(1)`, and the
profile/spectrum package needed for the proof has not been validated.

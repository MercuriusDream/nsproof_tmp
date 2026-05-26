# gamma=0.45 forced-tail sparse flat-bump continuation v112

Starting from v111, the topology scan showed remaining residual lobes between
the expanded bump centers:

```text
q ~= 0.48, |b| ~= 0.65,
q ~= 0.50, |b| ~= 0.60,
q ~= 0.60, |b| ~= 0.25,
q ~= 0.41, |b| ~= 0.30.
```

I added only those missing center pairs with:

```text
tools/profile_add_sparse_bumps.py
```

The resulting sparse base preserved the v111 profile exactly before
continuation, then a zero-only minimax run produced:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json
```

Validated gates at h=1e-3:

```text
standard wide     = 4.365866237926e-1
standard interior = 4.395069007065e-1
standard local    = 4.391290054377e-1
farther-tail      = 3.812707390403e-1

fine 29x29/45:
wide     = 4.396000051659e-1
interior = 4.395069007065e-1
local    = 4.397800969258e-1

41x41 topology max:
4.393817079326e-1 at q=0.486, |b|=0.630.
```

Finite-difference h-sweeps are stable:

```text
standard wide h=2e-3,1e-3,5e-4:
4.365921962713e-1, 4.365866237926e-1, 4.365865152350e-1.

standard interior h=2e-3,1e-3,5e-4:
4.395014482862e-1, 4.395069007065e-1, 4.395077228295e-1.

standard local h=2e-3,1e-3,5e-4:
4.391322052093e-1, 4.391290054377e-1, 4.391275368035e-1.

farther-tail h=2e-3,1e-3,5e-4:
3.812683123738e-1, 3.812707390403e-1, 3.812909608101e-1.
```

The ordinary tail channels remain admissible:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

This is still only an approximate numerical seed.  The residual is `O(1)`, so
it does not validate a profile or the spectral package required for the proof.

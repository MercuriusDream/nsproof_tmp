# gamma=0.45 forced-tail expanded flat-bump continuations v107-v111

This note records the expanded tail-flat interior bump run after v106.

The expansion tool

```text
tools/profile_expand_bumps.py
```

preserves the old bump centers and coefficients exactly, then adds zero-start
coefficients at new q and b^2 centers.  The v107 base used

```text
q centers  = 0.36, 0.42, 0.48, 0.52, 0.58, 0.62, 0.68
b2 centers = 0.08, 0.16, 0.24, 0.34, 0.46
```

The max-aware coordinate search was then run over the expanded tail-flat F/G
bump coefficients with active points refreshed from topology scans.

## Best endpoint

```text
profile-seeds/gamma0p45-forced-tail-expanded-flatbumpFG-v111.json
```

Validated gates at h=1e-3:

```text
standard wide    = 4.367747752125e-1
standard interior= 4.396586783719e-1
standard local   = 4.396608030521e-1
farther-tail     = 3.813442764768e-1

fine 29x29/45:
wide     = 4.398351490167e-1
interior = 4.396586783719e-1
local    = 4.397549840409e-1

41x41 topology max:
4.396417168948e-1 at q=0.486, |b|=0.630.
```

Finite-difference h-sweeps are stable:

```text
standard wide h=2e-3,1e-3,5e-4:
4.367803497653e-1, 4.367747752125e-1, 4.367746661366e-1.

standard interior h=2e-3,1e-3,5e-4:
4.396532252184e-1, 4.396586783719e-1, 4.396595006781e-1.

standard local h=2e-3,1e-3,5e-4:
4.396635665362e-1, 4.396608030521e-1, 4.396594055887e-1.

farther-tail h=2e-3,1e-3,5e-4:
3.813418493839e-1, 3.813442764768e-1, 3.813644983533e-1.
```

The ordinary tail channels remain admissible:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

This improves the constrained balance from v106/v109/v110 but is still only an
approximate numerical seed.  The residual is `O(1)`, so it does not validate a
profile or the spectral package required for the proof.

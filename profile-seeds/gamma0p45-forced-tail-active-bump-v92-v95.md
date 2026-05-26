# Active-Gate Tail-Flat Bump Probe v92-v95: gamma = 0.45, B = 1.0

Machine-readable seeds:

```text
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-v92.json
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v93.json
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-v94.json
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v95.json
```

The bounded-edge Gauss-Newton solver now supports active weighted points:

```text
--active-qb-points q,b,repeat;...
--active-rz-points r,z,repeat;...
```

These points are appended to the training grid with repetition, giving current
max-gate locations extra least-squares weight. This is a lightweight
gate-aware proxy; it is not a true minimax solver.

## First Active Direction

Starting from v91, the first active run weighted the current standard,
interior, and local max points. The full step reduced weighted RMS but
overshot:

```text
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-v92.json
training RMS: 2.995491471086e-01 -> 2.403841293934e-01
```

Independent gates rejected v92:

```text
standard max ~= 7.744152180346e-01,
interior max ~= 1.029254311547e+00,
local max    ~= 9.509573953753e-01.
```

A blend scan from v91 to v92 found a useful small fraction, `t=0.05`:

```text
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v93.json
```

v93 gate values at `h=1e-3`:

```text
standard max         = 5.296559969709e-01
interior max         = 5.273605597729e-01
local max            = 5.294625460480e-01
q in [0.18,0.30] max = 4.016192226850e-01
```

Finite-difference stability:

```text
standard h=2e-3,1e-3,5e-4:
5.296597210998e-01, 5.296559969709e-01, 5.296553963832e-01

interior h=2e-3,1e-3,5e-4:
5.273606519101e-01, 5.273605597729e-01, 5.273628353773e-01

local h=2e-3,1e-3,5e-4:
5.294630312919e-01, 5.294625460480e-01, 5.294718995020e-01

q in [0.18,0.30] h=2e-3,1e-3,5e-4:
4.016145417505e-01, 4.016192226850e-01, 4.016477158917e-01
```

The integer tail-series diagnostic is unchanged from v91:

```text
order q^0 trace is exact,
order q^1 linear residual is exactly zero,
orders q^7 and above are absent.
```

## Second Active Direction

Repeating the active process from v93 with the new max locations produced v94,
but the blend scan back to v93 found no improvement:

```text
Best v93-to-v94 blend by max-no-farther: t = 0.
```

The saved v95 is therefore only a diagnostic blend endpoint equivalent, for
current gate purposes, to v93. The current best seed remains v93.

## Interpretation

Active weighting is useful only as a direction generator. Full least-squares
active steps still overshoot by moving the lobe to neighboring gate points.
The small blend v93 is a real improvement, but the residual remains O(1).
The next numerical step should use a true max-aware line search or minimax
surrogate over the standard/interior/local gates instead of pure repeated-point
least squares.

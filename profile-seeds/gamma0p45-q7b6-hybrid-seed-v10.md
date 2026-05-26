# Approximate Compactified Profile Seed v10: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-q7b6-hybrid-seed-v10.json
```

This seed uses a `q_order=7`, `b_order=6` even-polynomial basis and was optimized on a hybrid collocation set:

```text
local rectangle: r in [0.8,2.0], z in [-1,1], 17x17
compactified grid: q in [0.35,0.9], b in [-0.8,0.8], 13x13
gamma = 0.45,
B = 1.0.
```

It is not a validated profile. It is the current best seed for the compactified/hybrid residual gate.

## Solver Evidence

```text
hybrid training RMS residual: 2.418983061347e-02
```

Cross-checks:

```text
wide compactified grid 15x15:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual: 3.752416417810e-02
max residual: 3.470863861403e-01

local rectangle 23x23:
r in [0.8,2.0], z in [-1,1]
RMS residual: 2.726685476724e-03
max residual: 8.485433464573e-03

interior compactified grid 15x15:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual: 4.208212133648e-03
max residual: 3.250005890999e-02
```

The persistent worst point is on the wide compactified edge:

```text
q = 0.35,
b = -0.8,
r ~= 1.605857,
z ~= -2.141142.
```

This indicates the next improvement must target the far/large-angle residual, not only the local core rectangle.

## Continuation Command

```bash
python3 tools/profile_gauss_newton.py \
  --seed-json profile-seeds/gamma0p45-q7b6-hybrid-seed-v10.json \
  --q-order 7 --b-order 6 \
  --grid-mode hybrid \
  --n 17 \
  --q-min 0.35 --q-max 0.9 \
  --b-min -0.8 --b-max 0.8 \
  --n-q 15 --n-b 15 \
  --edge-repeat 3 --corner-repeat 8 \
  --iterations 6 \
  --h 1e-3 --damping 1e-3 --max-update-norm 0.08 \
  --save-json profile-seeds/gamma0p45-q7b6-hybrid-seed-v11.json
```

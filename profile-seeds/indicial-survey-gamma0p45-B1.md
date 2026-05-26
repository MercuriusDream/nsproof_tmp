# Indicial Survey: gamma = 0.45, B = 1.0

Tool:

```text
tools/indicial_survey.py
```

Command:

```text
python3 tools/indicial_survey.py \
  --gamma 0.45 \
  --B 1.0 \
  --optimize \
  --iterations 16 \
  --step-real 0.02 \
  --step-imag 0.08 \
  --settings '1e-4,25,8000,10;1e-4,40,10000,10;5e-5,40,12000,12'
```

## Result

The apparent basin near `Im delta ~= 1.79` is not a validated root.

```text
start=0.132519531250+1.787841796875i
  L=25: opt delta=0.132519531250+1.787783203125i, residual=7.563764936090e-01
  L=40: opt delta=0.045957031250+1.785341796875i, residual=7.671511350710e-01
  L=40, eps=5e-5, terms=12:
        opt delta=0.045957031250+1.785341796875i, residual=7.671483314704e-01

start=0.045959472656+1.784820556641i
  L=25: opt delta=0.132521972656+1.787320556641i, residual=7.563765474831e-01
  L=40: opt delta=0.045959472656+1.784822998047i, residual=7.671510836763e-01
  L=40, eps=5e-5, terms=12:
        opt delta=0.045966796875+1.784820556641i, residual=7.671482805680e-01
```

Summary:

```text
best residual ~= 7.56e-1,
worst residual ~= 7.67e-1,
delta spread  ~= 8.66e-2.
```

## Interpretation

This is negative evidence. The residual is order one and the optimized exponent moves with the far-field truncation. The current scalar shooting residual is useful as a diagnostic, but it does not yet provide trusted indicial roots.

The next indicial step should build a genuine determinant/Evans function and validate zeros by winding or interval/ball arithmetic.

## Component Diagnostics

With `--components`, the survey reports the normalized residual components. The apparent basin fails primarily in the two far-field power-law conditions:

```text
L=25, delta=0.132519531250+1.787841796875i
  total residual = 7.563764944323e-1
  n_phi          = 4.579035466444e-1
  n_chi          = 5.379147001192e-1
  n_amp          = 1.675745681976e-1
  n_h            = 2.121232726253e-1

L=40, delta=0.045959472656+1.784820556641i
  total residual = 7.671510836770e-1
  n_phi          = 4.496555637236e-1
  n_chi          = 5.433754637830e-1
  n_amp          = 1.712521620885e-1
  n_h            = 2.484883529220e-1
```

The amplitude residual is not the leading defect. The current shooting solution is not landing in the admissible far-field power-law subspace.

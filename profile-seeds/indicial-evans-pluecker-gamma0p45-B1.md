# Indicial Pluecker/Evans Diagnostic at gamma=0.45, B=1

This note records the floating-point Pluecker diagnostic added in
`tools/indicial_evans.py`. It is not a validator. It makes the two-branch
matching condition explicit by forming the `3x2` forbidden far-field modal
matrix and checking the three `2x2` Pluecker minors.

## Point Checks

Geometric branch:

```text
python3 tools/indicial_evans.py --gamma 0.45 --B 1.0 \
  --delta-real 1.0 --delta-imag 0.0 \
  --L-values 25,40 --steps-per-unit 200 --series-terms 12

L=25: sigma_ratio=0, minor_norm=0, normalized_minor_norm=0,
      coeff_forbid=0, contrib_forbid=0
L=40: sigma_ratio=0, minor_norm=0, normalized_minor_norm=0,
      coeff_forbid=0, contrib_forbid=0
```

The best local combination is exactly the analytic `phi=1`, `chi=0` branch.
This is the axial-center/Galilean geometric mode and is removed by parity or
center fixing.

Old complex basin:

```text
python3 tools/indicial_evans.py --gamma 0.45 --B 1.0 \
  --delta-real 0.13251953125 --delta-imag 1.787841796875 \
  --L-values 25,40 --steps-per-unit 200 --series-terms 12

L=25: sigma_ratio=1.292647217342e-01,
      normalized_minor_norm=1.271402878408e-01,
      coeff_forbid=5.277372775458e-01,
      contrib_forbid=9.998883630453e-01
L=40: sigma_ratio=1.725890931092e-01,
      normalized_minor_norm=1.675968855084e-01,
      coeff_forbid=3.795675033836e-01,
      contrib_forbid=9.999766971815e-01
```

The complex basin remains dominated by forbidden endpoint contribution.

## Scan Outputs

The broad scan is saved at
`profile-seeds/indicial-evans-pluecker-gamma0p45-B1-broad.md`:

```text
python3 tools/indicial_evans.py --gamma 0.45 --B 1.0 \
  --L-values 25,40 --steps-per-unit 180 --series-terms 12 \
  --scan --delta-min 0.02 --delta-max 1.0 --count 17 \
  --imag-min 0.0 --imag-max 3.0 --imag-count 17 --top 20
```

Its top candidate is the exact geometric branch:

```text
delta=1.0000000000+0.0000000000i
  worst_norm_minor=0
  worst_sigma_ratio=0
  coeff_forbid=0
  contrib_forbid=0
```

The next low-minor candidates are not admissible. For example
`delta=0.0200000000+0.0000000000i` has
`worst_norm_minor=4.083300e-03`, but `coeff_forbid=9.999803e-01` and
`contrib_forbid=9.849706e-01`.

The near-`delta=1` scan is saved at
`profile-seeds/indicial-evans-pluecker-gamma0p45-B1-near-delta1.md`:

```text
python3 tools/indicial_evans.py --gamma 0.45 --B 1.0 \
  --L-values 25,40 --steps-per-unit 220 --series-terms 12 \
  --scan --delta-min 0.82 --delta-max 1.08 --count 27 \
  --imag-min 0.0 --imag-max 0.3 --imag-count 13 --top 20
```

Again the only zero is the exact geometric branch. Nearby real candidates such
as `delta=0.9900000000+0.0000000000i` and
`delta=1.0100000000+0.0000000000i` have small normalized minors
(`3.992936e-03` and `4.339215e-03`), but their endpoint forbidden
contribution remains `~9.99e-01`.

## Conclusion

These scans strengthen the negative evidence: the two-dimensional analytic
local space does not show a non-geometric admissible intersection with the
far-field admissible manifold on the sampled boxes. This still needs a true
Evans determinant or interval/ball Pluecker enclosure before it can be used as
a proof.

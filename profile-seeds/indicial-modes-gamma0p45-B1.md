# Indicial modal diagnostic at gamma=0.45, B=1.0

Tool:

```text
python3 tools/indicial_modes.py
```

This is not a validator. It decomposes the regular Frobenius-normalized shot at
`zeta=L` in the scaled variables

```text
V = (phi, L phi', L chi, L^2 h)
```

against the leading far-field modes. The admissible channel is `s_1=1-delta`.
The non-admissible channels are the growing `s_2=3-delta` channel and the two
Jordan channels at `lambda=1-(2/3)alpha delta`.

## Apparent basin candidates

```text
delta=0.132519531250+1.787841796875i, L=25, steps=8000, terms=10
admissible contribution fraction     = 1.491420549370e-02
non-admissible contribution fraction = 9.932547676535e-01
growing s_2 relative contribution    = 9.931202680355e-01

delta=0.132519531250+1.787841796875i, L=40, steps=10000, terms=10
admissible contribution fraction     = 6.848627860459e-03
non-admissible contribution fraction = 9.992797863131e-01
growing s_2 relative contribution    = 9.992573952444e-01

delta=0.045959472656+1.784820556641i, L=25, steps=8000, terms=10
admissible contribution fraction     = 1.563938954430e-02
non-admissible contribution fraction = 9.932667606780e-01
growing s_2 relative contribution    = 9.931810065945e-01

delta=0.045959472656+1.784820556641i, L=40, steps=10000, terms=10
admissible contribution fraction     = 7.187348018945e-03
non-admissible contribution fraction = 9.986733856678e-01
growing s_2 relative contribution    = 9.986605011420e-01
```

## Coarse modal scan

Using `L=25`, `steps=2500`, `terms=8`:

```text
0.02 <= Re delta <= 0.46, 0.5 <= Im delta <= 3.0:
best sampled delta = 0.460000+0.500000i
non-admissible fraction = 8.791569e-01
growing relative contribution = 8.092579e-01
admissible fraction = 9.921729e-03

0.02 <= Re delta <= 1.0, 0 <= Im delta <= 0.8:
best sampled delta = 0.472308+0.000000i
non-admissible fraction = 8.307430e-01
growing relative contribution = 6.105649e-01
admissible fraction = 9.053418e-03
```

Conclusion: the current apparent basin is not a near miss. The regular shot is
overwhelmingly non-admissible at infinity, mostly through the `s_2` channel.
A true Evans or matching determinant must impose this far-field splitting
directly instead of minimizing the finite-cutoff scalar residual.

## Two-branch analytic matching

Tool:

```text
python3 tools/indicial_match.py
```

The full analytic local space at `zeta=0` has two generic amplitudes,
`phi(0)` and `chi(0)`. The `chi(0)=1`, `phi(0)=0` branch reproduces the older
parity Frobenius expansion to roundoff.

Exact branch:

```text
delta=1
phi=1
chi=0
h=0
forbidden contribution fraction = 0
```

This branch is exact for every `gamma` and `B`. It is geometric:
`Psi=r^2`, `G=0`, and `a=0`, and it equals the derivative of the conical core
under axial translation,

```text
psi_*(r,z-z0) = (1/2)r^2 z - (1/2)z0 r^2.
```

It is therefore an axial-center/Galilean mode, not a non-geometric indicial
escape root. It is removed by parity or by fixing the axial center.

For the apparent complex basin, the best local combination of the two analytic
branches still does not become admissible:

```text
delta=0.132519531250+1.787841796875i, L=25, steps=8000, terms=12
sigma_min/sigma_max             = 1.286228341890e-01
coefficient forbidden fraction  = 5.313058606914e-01
contribution forbidden fraction = 9.998888792416e-01

delta=0.045959472656+1.784820556641i, L=40, steps=10000, terms=12
sigma_min/sigma_max             = 1.792312457467e-01
coefficient forbidden fraction  = 3.746175007887e-01
contribution forbidden fraction = 9.999742812523e-01
```

Coarse scan command:

```text
python3 tools/indicial_match.py --gamma 0.45 --B 1.0 \
  --eps 1e-4 --L 25 --steps 2500 --series-terms 10 \
  --scan --delta-min 0.02 --delta-max 1.0 --count 12 \
  --imag-min 0.0 --imag-max 3.0 --imag-count 13 --top 10
```

The scan finds `delta=1` as the only sampled zero. Nearby low singular-value
ratios are not admissible roots: their endpoint-scale forbidden contribution
remains close to one.

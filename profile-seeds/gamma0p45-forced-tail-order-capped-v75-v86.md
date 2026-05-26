# Order-Capped q1-Frozen Forced-Tail Continuation v75-v86: gamma = 0.45, B = 1.0

Machine-readable seeds:

```text
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter9-v75.json
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter5-9-v76.json
profile-seeds/gamma0p45-forced-tail-richinterior-q8-v77.json
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter8-v78.json
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter6-8-v79.json
profile-seeds/gamma0p45-forced-tail-richinterior-q7-v80.json
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter7-v81.json
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter5-7-v82.json
profile-seeds/gamma0p45-forced-tail-richinterior-q6-v83.json
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter6-v84.json
profile-seeds/gamma0p45-forced-tail-richinterior-tailfilter5-6-v85.json
profile-seeds/gamma0p45-forced-tail-richinterior-q6-v86.json
```

This sequence tests whether v74's improvement was bought by a high-order
ordinary integer tail channel. The diagnostic first filtered the large q9
coefficient of v74. Filtering q9 alone improved the sampled gates:

```text
v74 standard/interior/local max = 5.909176701763e-01 / 5.932368481368e-01 / 5.930636467992e-01
v75 standard/interior/local max = 5.861622065967e-01 / 5.880726308441e-01 / 5.879983660792e-01
v75 q in [0.18,0.30] max       = 4.164696249159e-01
```

Then the solver was restarted with the top ordinary q-order removed. Each
restart kept the same asymptotic constraints:

```text
exact q=0 trace,
zero q^1 tail coefficient,
frozen forced q^(1/gamma) angular family,
ordinary monomials restricted to q-order >= 2,
vanishing-edge coefficients frozen.
```

## Capped Continuations

The capped sequence gave monotone balanced-gate improvement:

```text
v77, q_order <= 8:
  standard max         = 5.703101865220e-01
  interior max         = 5.721614289768e-01
  local max            = 5.721915811779e-01
  q in [0.18,0.30] max = 4.104799359379e-01

v80, q_order <= 7:
  standard max         = 5.540807465732e-01
  interior max         = 5.555652549940e-01
  local max            = 5.558418104077e-01
  q in [0.18,0.30] max = 4.046297447427e-01

v83, q_order <= 6:
  standard max         = 5.418563244778e-01
  interior max         = 5.429873124479e-01
  local max            = 5.433682382379e-01
  q in [0.18,0.30] max = 3.987848489364e-01

v86, second q_order <= 6 pass:
  standard max         = 5.402426950755e-01
  interior max         = 5.413752067105e-01
  local max            = 5.417628839283e-01
  q in [0.18,0.30] max = 3.977005747567e-01
```

The v86 h-sweeps are stable:

```text
standard h=2e-3,1e-3,5e-4:
5.402437205236e-01, 5.402426950755e-01, 5.402459718514e-01

interior h=2e-3,1e-3,5e-4:
5.413765876944e-01, 5.413752067105e-01, 5.413758631220e-01

local h=2e-3,1e-3,5e-4:
5.417638470647e-01, 5.417628839283e-01, 5.417605983820e-01

q in [0.18,0.30] h=2e-3,1e-3,5e-4:
3.976970182399e-01, 3.977005747567e-01, 3.977214644192e-01
```

Tail-series checks for v86:

```text
order q^0 trace is exact,
order q^1 linear residual is exactly zero,
orders q^7 and above are absent,
fractional q^(1/gamma) psi_linear_max = 2.327134302240e+00,
leading trace psi source max           = 2.329369172244e+00.
```

The remaining ordinary integer tail is concentrated at q5 and q6:

```text
order q^5 psi_linear_max = 3.200652222019e+00,
order q^6 psi_linear_max = 3.857320704056e+00.
```

Filtering q6 alone worsens the balanced gate:

```text
v84 standard/interior/local max = 5.507396557555e-01 / 5.519573350357e-01 / 5.521691485190e-01
v84 q in [0.18,0.30] max       = 4.018195066274e-01
```

Filtering q5-q6 or q5-q7 is worse still, moving the residual toward the
near-origin side of the interior box. This identifies a plateau: the
q1-frozen forced-tail polynomial family can be cleaned and improved down to
v86, but pushing below the current O(1) residual requires a new structural
degree, not simply deleting lower integer channels.

## Interpretation

v86 is the best balanced q1-free forced-tail seed produced so far. It is not
close to the validation gate. The current obstruction is still a broad
streamfunction-equation lobe centered near

```text
q ~= 0.50,
|b| ~= 0.35-0.40.
```

The next useful profile step should introduce a genuine interior matching or
indicial coordinate in this lobe while preserving the exact trace, the zero q1
condition, and the forced q^(1/gamma) leading tail.

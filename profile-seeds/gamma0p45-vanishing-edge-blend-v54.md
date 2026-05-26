# Tail-Admissible Blend Diagnostic v54: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-blend-v54.json
```

This seed is the saved best point from a convex blend scan between the balanced
tail-admissible seed v49 and the far-tail-focused shell-14 seed v53:

```text
(1-t) * v49 + t * v53,
0 <= t <= 1.
```

The scan used 21 equally spaced values of `t` and minimized the maximum over the
standard, extreme, farther-tail, interior, and local residual gates. The best
point was the endpoint

```text
t = 1,
```

so v54 is functionally the same profile as v53, with blend metadata attached.
The diagnostic shows that the tradeoff is monotone over this segment: increasing
`t` improves the farther-tail lobe but worsens the standard, local, and interior
gates.

## Blend Scan Endpoints

```text
v49 / t = 0:
standard max:     5.470627484641e-02
extreme max:      5.535569977138e-02
farther-tail max: 2.682727177003e-01
interior max:     1.174547781095e-02
local max:        4.752159416815e-02
max over gates:   2.682727177003e-01

v54 / t = 1:
standard max:     7.607876229271e-02
extreme max:      6.231594228615e-02
farther-tail max: 1.792056343172e-01
interior max:     2.219326008164e-02
local max:        6.349927170401e-02
max over gates:   1.792056343172e-01
```

## Boundary Trace

The sampled `q=0` trace is exact:

```text
max |F(0,b)-1/2| = 0
max |G(0,b)-B|   = 0
```

## Finite-Difference Stability

Standard gate:

```text
h = 2e-3: max = 7.607765387046e-02
h = 1e-3: max = 7.607876229271e-02
h = 5e-4: max = 7.607908177952e-02
```

Extreme gate:

```text
h = 2e-3: max = 6.231719837858e-02
h = 1e-3: max = 6.231594228615e-02
h = 5e-4: max = 6.231624716659e-02
```

Farther-tail probe:

```text
h = 2e-3: max = 1.792165754613e-01
h = 1e-3: max = 1.792056343172e-01
h = 5e-4: max = 1.798543628562e-01
```

## Interpretation

The blend scan does not find an interior compromise better than the endpoints.
v49 remains the best balanced admissible seed for the standard, local, interior,
and original extreme gates. v53/v54 remains the best far-tail-focused admissible
seed found so far. Neither is close to a validated exact profile: the current
farther-tail obstruction is still `O(1e-1)`.

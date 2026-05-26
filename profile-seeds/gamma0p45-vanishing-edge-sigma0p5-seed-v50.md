# Tail-Admissible Sigma 0.5 Edge Test v50: gamma = 0.45, B = 1.0

Machine-readable seed:

```text
profile-seeds/gamma0p45-vanishing-edge-sigma0p5-seed-v50.json
```

This tests the generalized vanishing edge family

```text
q^0.5 * (1-q)^i * b^(2j),
0 <= i,j <= 8.
```

The motivation was to see whether the v49 farther-tail defect at `q=0.18`
comes from forcing corrections to vanish too quickly as `q -> 0`.

The test preserves the exact conical trace:

```text
F(0,b) = 1/2,
G(0,b) = B.
```

However, it does not improve the obstruction:

```text
standard max:     5.477696536382e-02
local max:        4.570375601230e-02
farther-tail max: 3.195007993310e-01
```

The farther-tail max is worse than v49 (`2.68e-1`), so `sigma=0.5` is not the
missing tail parameterization from this seed.

# Definitive Resolution of the Smooth Axisymmetric Subparabolic Profile Route

## Verdict

The repository's active route is closed by an exact analytical obstruction.

> There is no nontrivial `C^2` smooth axisymmetric globally self-similar
> incompressible Euler velocity profile with the repository's natural tail and
> similarity exponent
>
> ```text
> 2/5 < gamma < 1/2.
> ```

In particular, the frozen target

```text
gamma = 9/20 = 0.45,
B = 1,
p = 1/gamma = 20/9
```

cannot exist in the stated class.

This is a **branch-kill result**, not a positive Navier--Stokes blow-up proof.
The original positive theorem manifest remains `pass=false` with `0/5` gates.

## External theorem that closes the branch

The decisive source is:

```text
Peter Constantin, Mihaela Ignatova, Vlad Vicol,
"On putative self-similarity for incompressible 3D Euler,"
arXiv:2602.17570v3, 20 July 2026, Theorem 4.5.
```

Versioned source:

```text
https://arxiv.org/html/2602.17570v3
```

Theorem 4.5 states, in the notation used here, that a nontrivial `C^2` smooth
axisymmetric globally self-similar velocity profile for 3D incompressible Euler
which satisfies

```text
U(0) = 0,
|U(y)| <= C |y| <y>^(-1/gamma),
|curl U(y)| + |grad U(y)| <= C <y>^(-1/gamma)
```

must have

```text
gamma >= 1/2.
```

The strengthened axisymmetric conclusion first appears in the July 2026 `v3`.
The audited repository base commit is dated 27 May 2026, so the theorem was not
available at the time of the last solver update.

## Exact match to the frozen repository target

The repository target is not merely similar to the theorem's class. It is a
special case of it.

### 1. Same stationary self-similar Euler equation

The repository solves

```text
(1-gamma) U + gamma (y dot grad) U
+ (U dot grad) U + grad P = 0,
div U = 0.
```

This is exactly equation (3.3) of the cited paper, with the same convention for
`gamma`.

### 2. Axisymmetric with swirl

The frozen variables are

```text
u^r     = -psi_z / r,
u^z     =  psi_r / r,
Gamma   = r u^theta.
```

The target therefore lies in the axisymmetric class of Theorem 4.5. The value
`B=1`, together with `G(0,x)=B`, makes the intended tail nontrivial and
swirling.

### 3. Global rather than local profile

The two-chart domain covers the whole similarity space:

```text
q = 0   : spatial infinity,
q = 1   : the physical origin,
x=b^2 in [0,1] : all polar angles,
q in [0.84,0.92] : tail/origin overlap.
```

The target is therefore a global profile on `R^3`, not a local asymptotic germ.

### 4. `C^2` smoothness is built into the target

The origin chart is polynomial in

```text
R = r^2,
Z = z^2,
```

and the production architecture requires at least `C3`, preferably `C4`,
interface matching. The frozen hard-Newton schema already includes the complete
second derivative mortar set

```text
dqq, dqx, dxx.
```

The current numerical candidate does **not** satisfy those matching conditions;
that is why it was never promoted. But every successful completion of the
repository's own target would be at least `C^2`, precisely the regularity in
Theorem 4.5.

### 5. The origin normalization is automatic

The profile ansatz is

```text
psi   = r^2 z q^p F,
Gamma = r^2 q^p G.
```

With polynomial `F(R,Z)` and `G(R,Z)` near the origin,

```text
u^r     = -psi_z/r = O(r),
u^z     =  psi_r/r = O(z),
u^theta =  Gamma/r = O(r).
```

Hence

```text
U(0)=0.
```

### 6. The natural-tail majorant is exactly equation (3.8)

The frozen exponent is

```text
p = 1/gamma = 20/9.
```

The finite Chebyshev tail blocks are bounded on compact `(q,x)` patches. Since

```text
q = (1+|y|^2)^(-1/2),
```

the differentiated axisymmetric ansatz gives

```text
|U(y)| <= C |y| q^p,
|grad U(y)| + |curl U(y)| <= C q^p.
```

Therefore

```text
|U(y)| <= C |y| <y>^(-1/gamma),
|grad U(y)| + |curl U(y)| <= C <y>^(-1/gamma).
```

For `gamma=9/20`, the explicit rates are

```text
U          = O(|y|^(-11/9)),
grad U,
Omega      = O(|y|^(-20/9)).
```

These are stronger than mere sublinearity and coincide with the majorant used
by Theorem 4.5.

## Specialized proof at `gamma=9/20`

The theorem's proof is short enough to audit directly.

Let the meridional self-similar trajectories solve

```text
dR/dtau = gamma R + U_r(R,Z),
dZ/dtau = gamma Z + U_z(R,Z).
```

The natural-tail bound makes `U=o(|y|)`, so every backward trajectory starting
with `r0>0` remains in a compact meridional set and never reaches the axis in
finite time.

The swirl equation is

```text
(gamma r+U_r) d_r(r U_theta)
+ (gamma z+U_z) d_z(r U_theta)
+ (1-2 gamma)(r U_theta) = 0.
```

Along a backward trajectory,

```text
exp((1-2 gamma) tau) R(tau) U_theta(R(tau),Z(tau))
= r0 U_theta(r0,z0).
```

Here

```text
1-2 gamma = 1-2(9/20) = 1/10 > 0.
```

As `tau -> -infinity`, the exponential tends to zero while
`R U_theta` stays bounded on the compact trajectory set. Therefore

```text
U_theta(r0,z0)=0
```

for every `r0>0`, and continuity gives `U_theta=0` everywhere. Consequently

```text
Omega_r = Omega_z = 0.
```

The remaining vorticity equation becomes

```text
(gamma r+U_r) d_r(Omega_theta/r)
+ (gamma z+U_z) d_z(Omega_theta/r)
+ (1+gamma)(Omega_theta/r) = 0.
```

Integrating backward gives an `exp((1+gamma)tau)` factor. It also tends to zero,
and `C^2` regularity makes `Omega_theta/r` bounded through the axis. Hence

```text
Omega_theta=0.
```

Thus

```text
curl U = 0,
div U = 0.
```

Each component of `U` is harmonic on all of `R^3`. The natural-tail bound gives
`grad U -> 0` at infinity, so `grad U=0`; then `U(0)=0` yields

```text
U=0.
```

This contradicts the intended nontrivial `B=1` profile. The contradiction is
exact and independent of the numerical residual size, basis degree, Newton
method, pressure reconstruction, or spectral discretization.

## Consequences for the repository gates

The previous positive gates remain correctly false:

```text
[ ] exact profile F_gamma(U_*,P_*) = 0
[ ] 2/5 < gamma < 1/2 with validated admissible profile
[ ] natural tail and exact transseries/indicial certification
[ ] rank P_+ < infinity
[ ] stable-complement spectral gap Re z <= -c < 0
```

The new conclusion is stronger than another failed Newton solve:

```text
The first two gates cannot both pass in the frozen target class.
```

Since the exact profile does not exist, pressure, projected spectrum, unstable
projection, stable semigroup, and Lyapunov--Perron certificates downstream of
that profile are unreachable within this branch. More computation on the same
smooth axisymmetric global `gamma<1/2` ansatz cannot change the verdict.

## Scope

This resolution closes exactly the following class:

```text
smooth (at least C^2)
+ axisymmetric
+ whole-space/global profile
+ exact global self-similarity
+ natural-tail majorant
+ gamma < 1/2.
```

It does not establish any of the following:

```text
- global regularity or blow-up for 3D Navier--Stokes;
- nonexistence of non-axisymmetric mechanisms;
- nonexistence below C^2 regularity;
- nonexistence with a physical boundary;
- nonexistence of local-only, discretely self-similar, multiscale,
  or genuinely non-self-similar mechanisms.
```

Any continuation must leave at least one theorem hypothesis. Merely changing
basis size, chart layout, `B`, Newton damping, or interval backend while keeping
the same class cannot work.

## Machine replay

Run from the repository root:

```bash
python3 tools/validate_axisymmetric_subparabolic_obstruction.py
python3 tools/test_axisymmetric_subparabolic_obstruction.py
```

Expected output includes

```text
checks=10/10
gamma=9/20 one_minus_2gamma=1/10
branch_kill_pass=true
positive_theorem_pass=false
status=TARGET_CLASS_EMPTY
```

The hash-linked outputs are

```text
certs/obstructions/axisymmetric_subparabolic_no_go.json
certs/branch_kill_manifest.json
```

# NSS Proof Execution Draft

This file executes the proof program from `proof-problem.md` and `conver.md` as far as the current data allow. It does not replace the missing profile computation; it isolates it as a concrete validation problem and proves the scaling, conical, indicial, gluing, and Lyapunov-Perron reductions around it.

## 0. Notation

The source files use both `beta` and `gamma` for the spatial self-similar exponent. Here the exponent is `gamma`:

```text
2/5 < gamma < 1/2,
tau = T - t,
s = -log tau,
y = x / tau^gamma.
```

Use the Type-II Euler-dominated ansatz

```text
u(t,x) = tau^(-(1-gamma)) U(s,y),
p(t,x) = tau^(-2(1-gamma)) P(s,y).
```

The natural velocity tail is

```text
U_*(y) ~ |y|^(1 - 1/gamma) H(y/|y|)
       = |y|^(-a) H(y/|y|),
a = 1/gamma - 1.
```

For `2/5 < gamma < 1/2`, one has

```text
1 < a < 3/2.
```

So the global self-similar profile is not required to lie in `L^2_y`. The physical Navier-Stokes datum becomes finite-energy only after moving truncation and divergence repair.

## 1. Renormalized Navier-Stokes Equation

The incompressible Navier-Stokes equations are

```text
partial_t u + (u dot grad_x)u + grad_x p = nu Delta_x u,
div_x u = 0.
```

With

```text
u = tau^(-alpha) U(s,y),
y = x/tau^gamma,
s = -log tau,
p = tau^(-2alpha) P(s,y),
```

the terms scale as

```text
partial_t u = tau^(-alpha-1)(partial_s U + alpha U + gamma y dot grad U),
(u dot grad_x)u = tau^(-2alpha-gamma)(U dot grad)U,
grad_x p = tau^(-2alpha-gamma) grad P,
Delta_x u = tau^(-alpha-2gamma) Delta U.
```

Dividing by `tau^(-alpha-1)` gives

```text
partial_s U + alpha U + gamma y dot grad U
  + tau^(1-alpha-gamma)((U dot grad)U + grad P)
  = nu tau^(1-2gamma) Delta U.
```

To keep the Euler nonlinearity in the leading profile equation, require

```text
1 - alpha - gamma = 0,
alpha = 1 - gamma.
```

Thus

```text
partial_s U
+ (1-gamma)U
+ gamma y dot grad U
+ (U dot grad)U
+ grad P
= nu e^(-(1-2gamma)s) Delta U,
div U = 0.
```

After Leray projection,

```text
partial_s U
= -[(1-gamma)U + gamma y dot grad U + P_L((U dot grad)U)]
  + nu e^(-(1-2gamma)s) Delta U.
```

Viscosity is perturbative exactly when

```text
1 - 2gamma > 0,
gamma < 1/2.
```

The finite-energy-compatible lower bound is

```text
gamma > 2/5.
```

This is verified by the energy calculation in Section 3.

## 2. Euler Saddle-Core Profile Equation

The stationary Euler profile equation is

```text
(1-gamma)U_* + gamma y dot grad U_*
+ (U_* dot grad)U_* + grad P_* = 0,
div U_* = 0.
```

Equivalently,

```text
F_gamma(U_*,P_*) = 0,
F_gamma(U,P) =
(
  (1-gamma)U + gamma y dot grad U + (U dot grad)U + grad P,
  div U
).
```

In vorticity form, with `Omega_* = curl U_*`,

```text
Omega_* + gamma y dot grad Omega_*
+ U_* dot grad Omega_*
- Omega_* dot grad U_* = 0.
```

For large `|y|`, if the nonlinear terms are lower order, then

```text
(1-gamma)U + gamma y dot grad U ~= 0.
```

If `U ~ r^(-a)H(theta)`, this gives

```text
(1-gamma) - gamma a = 0,
a = 1/gamma - 1.
```

Therefore

```text
U_*(y) ~ r^(1 - 1/gamma)H(theta),
Omega_*(y) ~ r^(-1/gamma).
```

## 3. Energy Scaling

For a localized profile truncated at self-similar radius `R`, the physical energy is

```text
E(t) ~ tau^(3gamma - 2(1-gamma)) int_{|y| <= R} |U(y)|^2 dy
     = tau^(5gamma - 2) int_{|y| <= R} |U(y)|^2 dy.
```

If `U ~ r^(-a)` with `a = 1/gamma - 1`, then

```text
int_{|y| <= R} |U|^2 dy ~ R^(3 - 2a)
                         = R^(5 - 2/gamma).
```

For a fixed physical cutoff radius, `R = L tau^(-gamma)`, and hence

```text
E(t) ~ tau^(5gamma - 2) (L tau^(-gamma))^(5 - 2/gamma)
     = L^(5 - 2/gamma) tau^0.
```

So the localized physical energy is scale-invariant at the correct tail. This is the reason the interval starts at `gamma > 2/5`; at `gamma = 2/5` the tail is borderline logarithmic, and below it the energy scaling is incompatible with the finite-energy gluing target.

## 4. Axisymmetric-With-Swirl Profile System

Use

```text
U = u^r e_r + u^theta e_theta + u^z e_z,
u^r = -psi_z/r,
u^z = psi_r/r,
Gamma = r u^theta,
A = psi_rr - (1/r)psi_r + psi_zz.
```

The pressure-eliminated self-similar Euler equations are

```text
(1-gamma)r^2 A
+ gamma r^3 A_r
+ gamma z r^2 A_z
+ r(psi_r A_z - psi_z A_r)
+ 2 psi_z A
+ (Gamma^2)_z
= 0,
```

and

```text
(1-2gamma)Gamma
+ gamma(r Gamma_r + z Gamma_z)
+ (1/r)(psi_r Gamma_z - psi_z Gamma_r)
= 0.
```

### 4.1 Conical Homogeneity Constraint

Let

```text
psi = r^a f(z/r),
Gamma = r^b g(z/r).
```

Then

```text
A has degree a-2,
linear terms in the first equation have degree a,
psi-A nonlinear terms have degree 2a-3,
(Gamma^2)_z has degree 2b-1.
```

Balance in the first equation gives

```text
a = 2a - 3 = 2b - 1.
```

Hence

```text
a = 3,
b = 2.
```

The second equation independently gives `a = 3` by balancing `Gamma` with the streamfunction transport term.

Thus every exact conical solution in this ansatz obeys

```text
psi = r^3 f(z/r),
Gamma = r^2 g(z/r),
U(lambda y) = lambda U(y).
```

This grows linearly in `|y|`, while the finite-energy-compatible tail in the Navier-Stokes wedge decays like

```text
|y|^(1 - 1/gamma),  1 - 1/gamma < -1.
```

Therefore the conical object can only be an inner/asymptotic skeleton. It cannot be the global profile used for finite-energy Navier-Stokes gluing.

### 4.2 Linear-Strain Conical Branch

The branch

```text
psi_* = (1/2)r^2 z,
Gamma_* = B r^2
```

gives

```text
u^r = -r/2,
u^z = z,
u^theta = B r.
```

Here

```text
psi_r = r z,
psi_z = r^2/2,
A = psi_rr - (1/r)psi_r + psi_zz = z - z + 0 = 0.
```

The first equation reduces to `(Gamma^2)_z = 0`. The second equation is

```text
(1-2gamma)B r^2 + gamma(2B r^2)
+ (1/r)(0 - (r^2/2)(2B r)) = 0.
```

So the branch is exact and `gamma`-independent. Any `gamma`-dependent singular hierarchy must leave this conical branch through nonhomogeneous modes.

## 5. Indicial Pencil Around the Conical Core

Linearize around

```text
psi_* = (1/2)r^2 z,
Gamma_* = B r^2.
```

Write

```text
psi = psi_* + epsilon Psi,
Gamma = Gamma_* + epsilon G,
a_lin = Psi_rr - (1/r)Psi_r + Psi_zz.
```

The linearized equations are

```text
(gamma - 1/2) r (a_lin)_r
+ (gamma + 1) z (a_lin)_z
+ (2 - gamma) a_lin
+ 2B G_z = 0,
```

and

```text
(gamma - 1/2) r G_r
+ (gamma + 1) z G_z
+ (1 - 2gamma)G
- 2B Psi_z = 0.
```

Set

```text
alpha = 1/2 - gamma > 0,
Psi = r^(3-delta) phi(zeta),
G = r^(2-delta) chi(zeta),
zeta = z/r.
```

Then

```text
a_lin = r^(1-delta) h(zeta),
```

where

```text
h = (1+zeta^2) phi''
    - (3-2delta) zeta phi'
    + (3-delta)(1-delta) phi.
```

The indicial system is

```text
(3/2) zeta h' + (3/2 + alpha delta)h + 2B chi' = 0,
(3/2) zeta chi' + alpha delta chi - 2B phi' = 0.
```

Together with the definition of `h`, this is the pencil

```text
I_{gamma,B}(delta)(phi,chi) = 0.
```

### 5.1 First-Order Shooting Form

For numerical shooting, use the variables

```text
Y = (phi, phi', chi, h).
```

For `zeta > 0`,

```text
phi' = Y_2,
phi'' =
  [h + (3-2delta)zeta phi' - (3-delta)(1-delta)phi]
  /(1+zeta^2),
chi' =
  [2B phi' - alpha delta chi]/[(3/2)zeta],
h' =
  -[(3/2 + alpha delta)h + 2B chi']/[(3/2)zeta].
```

This is the system implemented in `tools/indicial_solver.py`.

### 5.2 Frobenius Data at `zeta = 0`

Impose parity

```text
phi(-zeta) = -phi(zeta),
chi(-zeta) = chi(zeta).
```

Use

```text
phi = p zeta + p3 zeta^3 + O(zeta^5),
chi = 1 + q2 zeta^2 + O(zeta^4).
```

The second indicial equation gives the constant term

```text
p = alpha delta/(2B).
```

The `zeta^2` coefficient gives

```text
q2 = 6B p3/(3 + alpha delta).
```

Now compute

```text
h = [6p3 + delta(delta-2)p] zeta + O(zeta^3).
```

The `zeta` coefficient in the first indicial equation gives

```text
(3 + alpha delta)[6p3 + delta(delta-2)p] + 4Bq2 = 0.
```

Substituting `q2` yields

```text
p3 =
- ((3 + alpha delta)^2 delta(delta-2)p)
  / (6((3 + alpha delta)^2 + 4B^2)).
```

The minus sign is forced by the coefficient equation.

At infinity, admissibility requires

```text
phi(zeta) ~ C_phi zeta^(1-delta),
chi(zeta) ~ C_chi zeta^(-delta),
```

so the boundary residuals are

```text
zeta phi' - (1-delta)phi -> 0,
zeta chi' + delta chi -> 0,
2B(1-delta)C_phi + delta(1+gamma)C_chi -> 0.
```

The zeros of this residual define `D_ind(delta;gamma,B)`.

### 5.2.1 Current Indicial Survey Result

The first executable survey is in `tools/indicial_survey.py`. It uses the same shooting residual as `tools/indicial_solver.py`, but checks whether apparent candidates survive changes in truncation length, step count, and Frobenius order.

The current apparent basin at `gamma=0.45`, `B=1.0` is near

```text
delta ~= 0.1 + 1.79i.
```

A direct survey gives:

```text
start=0.132519531250+1.787841796875i:
  eps=1e-4, L=25, steps=8000, terms=10
  opt delta = 0.132519531250+1.787783203125i
  residual  = 7.563764936090e-01

  eps=1e-4, L=40, steps=10000, terms=10
  opt delta = 0.045957031250+1.785341796875i
  residual  = 7.671511350710e-01

  eps=5e-5, L=40, steps=12000, terms=12
  opt delta = 0.045957031250+1.785341796875i
  residual  = 7.671483314704e-01
```

The same behavior occurs when starting from the `L=40` optimum:

```text
start=0.045959472656+1.784820556641i:
  best residual ~= 7.563765474831e-01,
  worst residual ~= 7.671510836763e-01,
  delta spread  ~= 8.66e-2.
```

This is not root-like: the residual is order one, and the optimized exponent drifts visibly with `L`. The present shooting normalization therefore cannot yet supply trusted indicial roots. The next indicial step is to replace scalar residual minimization by a true determinant or Evans-type construction whose zeros can be checked by winding or interval/ball arithmetic.

Component diagnostics sharpen the failure. For the same basin,

```text
L=25, delta=0.132519531250+1.787841796875i:
  total residual = 7.563764944323e-1
  n_phi          = 4.579035466444e-1
  n_chi          = 5.379147001192e-1
  n_amp          = 1.675745681976e-1
  n_h            = 2.121232726253e-1

L=40, delta=0.045959472656+1.784820556641i:
  total residual = 7.671510836770e-1
  n_phi          = 4.496555637236e-1
  n_chi          = 5.433754637830e-1
  n_amp          = 1.712521620885e-1
  n_h            = 2.484883529220e-1
```

The dominant obstruction is failure of the far-field power laws for `phi` and `chi`, not merely the algebraic amplitude compatibility. A real determinant must therefore encode a stable/unstable far-field splitting, not only minimize the scalar normalized residual at a finite cutoff.

### 5.2.2 Far-Field Modal Decomposition

The modal diagnostic in `tools/indicial_modes.py` decomposes the finite shot at `zeta=L` in the scaled variables

```text
V = (phi, zeta phi', zeta chi, zeta^2 h).
```

The leading large-`zeta` exponents are

```text
s_1 = 1 - delta,
s_2 = 3 - delta,
lambda = 1 - (2/3)alpha delta.
```

The admissible channel is the `s_1` mode; the `s_2` channel and the two Jordan `lambda` channels must be killed by the true indicial determinant. For `gamma=0.45`, `B=1.0`, the apparent basin gives:

```text
delta=0.132519531250+1.787841796875i, L=25:
  admissible contribution fraction     = 1.491420549370e-02
  non-admissible contribution fraction = 9.932547676535e-01
  growing s_2 relative contribution    = 9.931202680355e-01

delta=0.132519531250+1.787841796875i, L=40:
  admissible contribution fraction     = 6.848627860459e-03
  non-admissible contribution fraction = 9.992797863131e-01
  growing s_2 relative contribution    = 9.992573952444e-01

delta=0.045959472656+1.784820556641i, L=25:
  admissible contribution fraction     = 1.563938954430e-02
  non-admissible contribution fraction = 9.932667606780e-01
  growing s_2 relative contribution    = 9.931810065945e-01

delta=0.045959472656+1.784820556641i, L=40:
  admissible contribution fraction     = 7.187348018945e-03
  non-admissible contribution fraction = 9.986733856678e-01
  growing s_2 relative contribution    = 9.986605011420e-01
```

A coarse modal-score scan using `L=25`, `steps=2500`, `terms=8` also fails to reveal a hidden root-like basin. In the strip `0.02 <= Re delta <= 0.46`, `0.5 <= Im delta <= 3.0`, the best sampled point is `delta=0.46+0.5i`, with non-admissible fraction `8.79e-1`. In the near-real strip `0.02 <= Re delta <= 1.0`, `0 <= Im delta <= 0.8`, the best sampled point is `delta=0.472308+0i`, with non-admissible fraction `8.31e-1`.

This is stronger negative evidence than the scalar residual survey: the regular shot is not almost admissible at infinity. It is overwhelmingly a forbidden far-field mode. The next mathematically meaningful indicial step is a genuine Evans or matching determinant that constructs the regular and far-field manifolds as subspaces and checks their intersection, preferably with ball arithmetic.

### 5.2.3 Two-Branch Analytic Matching

The parity-restricted shooting normalization uses only the branch

```text
phi(0)=0,
chi(0)=1.
```

For a determinant construction one must first expose the full analytic local space at `zeta=0`. Writing

```text
phi = sum p_n zeta^n,
chi = sum q_n zeta^n,
h   = sum r_n zeta^n,
```

the coefficient equations are

```text
[(3/2)n + alpha delta]q_n - 2B(n+1)p_{n+1} = 0,
[(3/2)n + 3/2 + alpha delta]r_n + 2B(n+1)q_{n+1} = 0,
(n+2)(n+1)p_{n+2}
  + [n(n-1) - (3-2delta)n + (3-delta)(1-delta)]p_n
  - r_n = 0.
```

Eliminating `p_{n+1}` and `r_n` gives a two-amplitude analytic recurrence with free data `(p_0,q_0)=(phi(0),chi(0))`. The implementation is `tools/indicial_match.py`. Its `(p_0,q_0)=(0,1)` branch reproduces the older parity Frobenius coefficients to roundoff:

```text
p1 difference = 0
p3 difference = 6.94e-18
p5 difference = 1.39e-18
q2 difference = 7.76e-18
q4 difference = 2.45e-18
```

The full analytic space exposes an exact branch:

```text
delta = 1,
phi = 1,
chi = 0,
h = 0.
```

Numerically,

```text
delta=1, L=25:
  growing_s2 = 0
  lambda_w = 0
  lambda_ylog = 0
  contribution forbidden fraction = 0
```

This is an exact analytic indicial root for every `gamma` and `B`, because the first equation loses the zeroth-order `phi` term when `delta=1`. It must be classified separately as a geometric/gauge/physical branch before it can be used in the Navier-Stokes construction.

The classification is geometric. For this branch,

```text
Psi = r^(3-delta)phi = r^2,
G = 0,
a = Psi_rr - r^(-1)Psi_r + Psi_zz = 0.
```

Hence both linearized equations vanish identically. Moreover it is exactly the derivative of the conical core under axial translation:

```text
psi_*(r,z-z_0)
  = (1/2)r^2 z - (1/2)z_0 r^2,
d/dz_0|_{z_0=0} psi_*(r,z-z_0)
  = -(1/2)r^2.
```

In velocity variables, `Psi=r^2` is a constant axial velocity perturbation, equivalently a Galilean/center modulation. It also violates the imposed parity `phi(-zeta)=-phi(zeta)`. Therefore `delta=1` is not a non-geometric escape root for the indicial funnel; it must be removed by axial-center fixing or by the parity restriction.

For the non-geometric complex basin, allowing both analytic branches still does not remove the obstruction. The best local combination at the two current cutoffs gives:

```text
delta=0.132519531250+1.787841796875i, L=25:
  sigma_min/sigma_max              = 1.286228341890e-01
  coefficient forbidden fraction   = 5.313058606914e-01
  contribution forbidden fraction  = 9.998888792416e-01

delta=0.045959472656+1.784820556641i, L=40:
  sigma_min/sigma_max              = 1.792312457467e-01
  coefficient forbidden fraction   = 3.746175007887e-01
  contribution forbidden fraction  = 9.999742812523e-01
```

A reproducible coarse scan is available through

```text
python3 tools/indicial_match.py --gamma 0.45 --B 1.0 \
  --eps 1e-4 --L 25 --steps 2500 --series-terms 10 \
  --scan --delta-min 0.02 --delta-max 1.0 --count 12 \
  --imag-min 0.0 --imag-max 3.0 --imag-count 13 --top 10
```

This scan finds the exact `delta=1` branch as the only sampled zero. Away from it, even low `sigma_min/sigma_max` values have endpoint-scale forbidden contribution essentially equal to one. Thus the matching obstruction is not an artifact of having omitted the second analytic local branch.

The explicit Pluecker form of the same condition is implemented in
`tools/indicial_evans.py`. It forms the `3x2` forbidden-mode matrix for the
two analytic local branches and checks the three `2x2` minors. At
`gamma=0.45`, `B=1.0`, `L=25,40`, the geometric branch has zero singular
ratio, zero normalized minor norm, and zero forbidden contribution. The old
complex basin at `delta=0.13251953125+1.787841796875i` has
`normalized_minor_norm=1.27e-1/1.68e-1` at `L=25/40` and forbidden endpoint
contribution `9.9989e-1/9.9998e-1`.

Two reproducible Pluecker scans are saved in
`profile-seeds/indicial-evans-pluecker-gamma0p45-B1-broad.md` and
`profile-seeds/indicial-evans-pluecker-gamma0p45-B1-near-delta1.md`. The broad
box `Re delta in [0.02,1]`, `Im delta in [0,3]` and the local box
`Re delta in [0.82,1.08]`, `Im delta in [0,0.3]` both find only the exact
`delta=1` zero. Nearby low-minor alternatives remain forbidden dominated; for
example `delta=0.99` has `worst_norm_minor=3.99e-3` but
`contrib_forbid=9.994e-1`. This is still floating evidence, not a validated
Evans determinant proof.

The first validation-oriented wrapper is
`tools/validate_indicial_evans.py`, with reusable sampled-box helpers in
`validators/pluecker.py`. It covers a complex `delta` rectangle by boxes,
samples each box at the center and corners, and reports heuristic lower
bounds for the normalized Pluecker minor and forbidden contribution. It is
explicitly labeled `HEURISTIC NOT VALIDATED`: it is a staging scaffold for the
future ball-arithmetic Pluecker cover, not a substitute for interval ODE
propagation or an argument-principle count.

### 5.3 Higher-Order Frobenius Recurrence

For numerical starts at `zeta = eps`, use the full parity series

```text
phi(zeta) = sum_{j >= 0} p_j zeta^(2j+1),
chi(zeta) = sum_{j >= 0} q_j zeta^(2j),
q_0 = 1.
```

The second indicial equation gives

```text
p_j = (3j + alpha delta) q_j / [2B(2j+1)].
```

Write

```text
h(zeta) = sum_{j >= 0} h_j zeta^(2j+1),
h_j = A_j p_{j+1} + B_j p_j,
A_j = (2j+3)(2j+2),
B_j = (2j+1)(2j)
      - (3-2delta)(2j+1)
      + (3-delta)(1-delta).
```

The first indicial equation gives the recurrence

```text
(3j+3+alpha delta)h_j + 4B(j+1)q_{j+1} = 0.
```

Substituting the formula for `p_{j+1}` yields a scalar recurrence for `q_{j+1}`. This is implemented in `tools/indicial_solver.py` through `--series-terms`.

### 5.4 Residual Oracle

The pressure-eliminated axisymmetric equations can be checked directly with

```text
python3 tools/axisym_residual.py --gamma 0.45 --B 1.0
```

The conical core residual should be near finite-difference roundoff. This executable check is the seed for the compactified nonlinear residual evaluator.

## 6. Compactified Full Profile Problem

The final profile solver must not solve directly in raw `(r,z)`. Use

```text
rho = sqrt(r^2 + z^2),
b = z/rho in [-1,1],
q = (1 + rho^2)^(-1/2) in [0,1].
```

Here `q=0` is infinity and `q=1` is the origin. Factor the natural tail:

```text
psi = r^2 z q^(1/gamma) F(q,b),
Gamma = r^2 q^(1/gamma) G(q,b).
```

Since `q^(1/gamma) ~ rho^(-1/gamma)`, the velocity has the required tail

```text
U ~ rho^(1 - 1/gamma).
```

Use the indicial modes as boundary data at `q=0`. The seed has the form

```text
F_init = 1/2
  + c q^delta (1-b^2)^(-delta/2)
      phi(b/sqrt(1-b^2))/(b/sqrt(1-b^2)),
G_init = B
  + c q^delta (1-b^2)^(-delta/2)
      chi(b/sqrt(1-b^2)).
```

The nonlinear residual equation is

```text
E_gamma(F,G) = 0.
```

The current executable scaffold for this ansatz is

```text
python3 tools/compactified_profile.py --gamma 0.45 --B 1.0
```

It evaluates the pressure-eliminated residual for polynomial even-parity `F(q,b)` and `G(q,b)` expansions. The default `F=1/2`, `G=B` tail-factored seed is not expected to solve the equations; it is the baseline residual target for a future Newton or Gauss-Newton solver.

A first low-order coefficient search is available:

```text
python3 tools/profile_optimize.py --gamma 0.45 --B 1.0
```

This only performs coordinate search on a small polynomial ansatz. A true profile proof still requires a robust Newton/Gauss-Newton solve, grid refinement, tail projection, and Newton-Kantorovich validation.

Current smoke-test evidence:

```text
q_order=1, b_order=1, grid=3x3:
initial RMS residual ~= 2.96e-1,
after 4 coordinate-search sweeps ~= 1.15e-1.

q_order=2, b_order=1, grid=4x4:
initial RMS residual ~= 3.83e-1,
after 6 coordinate-search sweeps ~= 1.71e-1.
```

These numbers only prove that the residual scaffold is live and optimizable. They do not identify a profile candidate.

The stronger damped Gauss-Newton tool is

```text
python3 tools/profile_gauss_newton.py --gamma 0.45 --B 1.0 --q-order 3 --b-order 2 --n 9
```

Current local-patch seed:

```text
profile-seeds/gamma0p45-q6b5-seed-v6.json

training grid 21x21:
RMS residual ~= 2.21e-3

cross-check grid 23x23:
RMS residual ~= 2.19e-3,
max residual ~= 8.29e-3.
```

This is still far from the `1e-8` residual gate and has no Newton-Kantorovich proof. It is only a concrete seed for continuation.

Current compactified/hybrid seed:

```text
profile-seeds/gamma0p45-q7b6-hybrid-seed-v10.json

hybrid training:
RMS residual ~= 2.42e-2

wide compactified cross-check:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual ~= 3.75e-2,
max residual ~= 3.47e-1.

local rectangle cross-check:
RMS residual ~= 2.73e-3,
max residual ~= 8.49e-3.

interior compactified cross-check:
q in [0.45,0.85], b in [-0.65,0.65]
RMS residual ~= 4.21e-3,
max residual ~= 3.25e-2.
```

The persistent defect is the far/large-angle edge near `q=0.35`, `|b|=0.8`. This means the next profile step is not merely more local Newton iteration; it must improve the outer angular tail representation.

Current edge-focused monomial seed:

```text
profile-seeds/gamma0p45-q7b6-edge-seed-v12.json

wide compactified cross-check:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual ~= 3.56e-2,
max residual ~= 3.29e-1.

local rectangle cross-check:
RMS residual ~= 2.75e-3,
max residual ~= 8.52e-3.

interior compactified cross-check:
RMS residual ~= 3.96e-3,
max residual ~= 2.92e-2.
```

The wide edge max residual has improved only modestly under edge weighting:

```text
v10: 3.47e-1
v11: 3.35e-1
v12: 3.29e-1
```

This is evidence that a pure monomial `q^i b^(2j)` basis is not the right final outer-tail representation. The next structural upgrade should add indicial or edge-adapted basis functions tied to the asymptotic funnel.

Current best standard-gate singular-edge seed after that structural upgrade:

```text
profile-seeds/gamma0p45-edgebasis-wide-seed-v31.json

edge basis:
(1-q)^i * (b^2/(1-b^2))^j,
0 <= i,j <= 10.

wide compactified cross-check:
q in [0.35,0.9], b in [-0.8,0.8]
RMS residual ~= 2.10e-2,
max residual ~= 1.92e-1.

local rectangle cross-check:
RMS residual ~= 2.27e-3,
max residual ~= 7.43e-3.

interior compactified cross-check:
RMS residual ~= 2.59e-3,
max residual ~= 1.32e-2.
```

The edge-adapted basis is a real improvement but not a validation:

```text
v10 monomial hybrid wide max:      3.47e-1
v12 monomial edge-weight wide max: 3.29e-1
v13 frozen edge-basis wide max:    2.92e-1
v14 joint edge-basis wide max:     2.81e-1
v19 stronger corner-weight wide max: 2.30e-1
v23 order-6 edge-basis wide max:    2.14e-1
v25 order-7 edge-basis wide max:    2.07e-1
v27 order-8 edge-basis wide max:    2.02e-1
v29 order-9 edge-basis wide max:    1.98e-1
v31 order-10 wider-box wide max:    1.92e-1
```

The residual obstruction is still the far/large-angle compactified edge. Increasing the empirical edge basis helps monotonically but slowly, and stronger corner weighting by itself barely moves the defect. The order-9 continuation confirms the direction but also confirms that polynomial-in-`eta` edge enrichment alone is not closing the many-orders-of-magnitude gap. The wide-edge residual is stable under `h=2e-3,1e-3,5e-4`, so it is not a visible finite-difference artifact.

The first wider-box continuation was trained on

```text
q in [0.30,0.90], b in [-0.85,0.85].
```

It improves the original gate and the moderate stress gate, but not the more extreme far/angular stress:

```text
standard gate q >= 0.35, |b| <= 0.80:
v29 max ~= 1.98e-1,
v31 max ~= 1.92e-1.

moderate stress q >= 0.30, |b| <= 0.85:
v29 max ~= 5.74e-1,
v31 max ~= 5.61e-1.

extreme stress q >= 0.25, |b| <= 0.90:
v29 max ~= 9.30e1,
v31 max ~= 1.09e2.
```

This is strong evidence that the present polynomial edge basis is not an asymptotic representation. Reaching the `1e-8` gate likely requires a basis tied more directly to the indicial modes, plus a Newton-Kantorovich validation layer.

The singular angular defect is not merely a numerical nuisance: the basis

```text
(1-q)^i * (b^2/(1-b^2))^j
```

is unbounded as `|b| -> 1`, while a regular axisymmetric profile should have smooth bounded angular coefficients in `b^2` after the explicit `r^2` factors are removed. Replacing it by the axis-regular basis

```text
(1-q)^i * b^(2j)
```

and projecting the singular v31 seed onto this bounded span gave the first stable bounded stress seed after extreme-box continuation:

```text
profile-seeds/gamma0p45-bounded-edge-seed-v34.json

bounded edge basis:
(1-q)^i * b^(2j),
0 <= i,j <= 11.

standard gate q >= 0.35, |b| <= 0.80:
RMS residual ~= 2.14e-2,
max residual ~= 1.98e-1.

moderate stress q >= 0.30, |b| <= 0.85:
RMS residual ~= 4.04e-2,
max residual ~= 3.14e-1.

extreme stress q >= 0.25, |b| <= 0.90:
RMS residual ~= 5.92e-2,
max residual ~= 3.66e-1.
```

The bounded basis gives up some standard-gate accuracy relative to v31, but it removes the catastrophic far/angular blow-up:

```text
extreme stress max:
singular v31 ~= 1.09e2,
bounded v33  ~= 3.68e-1,
bounded v34  ~= 3.66e-1.
```

This makes v34 the more mathematically relevant continuation seed. The order-11 extreme-box continuation improves all three gate classes, but only slowly. It still remains many orders of magnitude above validation and still lacks any indicial-tail certificate.

The next bounded continuation adds only the new order-12 edge shell, using the solver option

```text
--bounded-shell-min 12
```

so that the lower-order v34 coefficients stay fixed and only bounded edge coefficients with `i=12` or `j=12` vary. The first attempt to vary all order-12 bounded coefficients was too expensive for the current pure-Python finite-difference Jacobian; the shell-only continuation gives a reproducible lower-cost test of whether another bounded polynomial layer helps.

The resulting seed is

```text
profile-seeds/gamma0p45-bounded-edge-seed-v35.json
```

with basis

```text
(1-q)^i * b^(2j),
0 <= i,j <= 12.
```

It improves all measured max gates, but again only slowly:

```text
standard gate q >= 0.35, |b| <= 0.80:
v34 max ~= 1.976849426590e-1,
v35 max ~= 1.957809706943e-1.

moderate stress q >= 0.30, |b| <= 0.85:
v34 max ~= 3.137198845265e-1,
v35 max ~= 3.097438778692e-1.

extreme stress q >= 0.25, |b| <= 0.90:
v34 max ~= 3.659260538607e-1,
v35 max ~= 3.633506253060e-1.
```

The v35 finite-difference gate is stable:

```text
standard h = 2e-3, 1e-3, 5e-4:
max ~= 1.957794275099e-1, 1.957809706943e-1, 1.957853420026e-1.

extreme h = 2e-3, 1e-3, 5e-4:
max ~= 3.633422212222e-1, 3.633506253060e-1, 3.633585492466e-1.
```

This continuation reinforces the previous conclusion. More bounded polynomial edge degrees help monotonically, but they are not closing the many-orders-of-magnitude validation gap. A successful profile representation still needs either a correct non-geometric indicial tail basis or a different asymptotic parameterization of the far/angular edge.

The residual-topology diagnostic

```text
python3 tools/profile_residual_topology.py \
  --seed-json profile-seeds/gamma0p45-bounded-edge-seed-v35.json
```

shows that the defect is not a single isolated corner. On the original extreme box, the top residuals sit on the smallest sampled `q` and in angular lobes around `|b| ~= 0.79`, mostly in the streamfunction equation:

```text
q in [0.25,0.90], |b| <= 0.90:
worst q=0.25, b=-0.7875,
e_psi ~= 3.707661396511e-1,
e_Gamma ~= 7.904766278781e-3.
```

Moving farther into the tail worsens the same lobe:

```text
q in [0.18,0.30], |b| <= 0.90:
worst q=0.18, b=-0.7875,
e_psi ~= 4.877600383076e-1,
e_Gamma ~= 1.224231756695e-2,
RMS ~= 1.514292288832e-1.
```

Thus the main profile obstruction is a far-tail streamfunction mismatch that grows as `q -> 0` in the tested range. This is not consistent with convergence by simply adding bounded polynomial edge shells.

The far-boundary trace diagnostic

```text
python3 tools/profile_tail_boundary.py \
  --seed-json profile-seeds/gamma0p45-bounded-edge-seed-v35.json
```

identifies the structural reason. The bounded edge basis uses `(1-q)^i b^(2j)`, which is regular in `b` but does not vanish at `q=0`. Consequently it changes the leading conical trace. For v35,

```text
at q = 0, |b| = 0.95:
F(0,b) - 1/2 ~= 1.052470949329,
G(0,b) - B   ~= -32.078151667385.
```

This violates the conical rigidity result from Section 4, where the leading homogeneous tail is the exact core `F=1/2`, `G=B`. The next profile basis must therefore either multiply edge corrections by a positive tail power, such as `q^sigma`, or impose explicit linear constraints that force the bounded-edge trace at `q=0` to vanish. Without that boundary condition, the optimizer can lower finite-box residuals by corrupting the leading far-field profile.

The representation now supports the first constrained alternative:

```text
q * (1-q)^i * b^(2j)
```

through the vanishing edge family in `tools/compactified_profile.py` and `tools/profile_bounded_edge_gauss_newton.py`. The solver also has

```text
--zero-tail-angular
--freeze-tail-angular
```

to enforce the conical trace by zeroing and freezing the monomial `q^0 b^(2j)` terms with `j>0`.

The tail-admissible experiment

```text
profile-seeds/gamma0p45-vanishing-edge-seed-v37.json
```

has exact sampled trace

```text
F(0,b) - 1/2 = 0,
G(0,b) - B   = 0,
```

but it is not competitive as a profile seed:

```text
standard gate max ~= 7.734021647691e-1,
extreme gate max  ~= 7.195898925171e-1,
farther q=0.18 tail max ~= 4.674038780697e-1.
```

Compared with v35, the farther-tail lobe improves slightly, but the standard and local boxes become much worse. This proves that v35 cannot be made asymptotically admissible by a small projection into a vanishing edge basis. The compactified nonlinear profile must be re-solved with the `q=0` conical trace enforced from the start.

Continuing the constrained solve with larger accepted Gauss-Newton steps gives the current best tail-admissible seed:

```text
profile-seeds/gamma0p45-vanishing-edge-seed-v40.json
```

The training RMS decreased monotonically along the constrained sequence:

```text
v37: 1.241831417456e-1,
v38: 1.215475634251e-1,
v39: 1.174792212469e-1,
v40: 1.139670567852e-1.
```

The `q=0` trace remains exact, and the external gates improve:

```text
standard max:
v37 ~= 7.734021647691e-1,
v40 ~= 7.109294097097e-1.

extreme max:
v37 ~= 7.195898925171e-1,
v40 ~= 6.612026574807e-1.

farther q=0.18 tail max:
v37 ~= 4.674038780697e-1,
v40 ~= 4.261250143780e-1.
```

The v40 finite-difference gates are stable:

```text
standard h = 2e-3, 1e-3, 5e-4:
max ~= 7.109167827613e-1, 7.109294097097e-1, 7.109330413385e-1.

farther q=0.18 h = 2e-3, 1e-3, 5e-4:
max ~= 4.261181727684e-1, 4.261250143780e-1, 4.262308826300e-1.
```

This is concrete progress but not a proof-grade profile: v40 is still far above the `1e-8` gate and remains much worse on finite boxes than the non-admissible v35. The constrained basis is valid at infinity, but it is not yet an adequate nonlinear profile representation.

Pushing the same trace-preserving solve with larger accepted updates and then adding a far-edge-weighted correction gives the current best admissible seed:

```text
profile-seeds/gamma0p45-vanishing-edge-seed-v49.json
```

It keeps the exact sampled trace

```text
F(0,b) - 1/2 = 0,
G(0,b) - B   = 0,
```

and improves the original finite-box gates by more than an order of magnitude relative to v40:

```text
standard gate q >= 0.35, |b| <= 0.80:
v40 max ~= 7.109294097097e-1,
v49 max ~= 5.470627484641e-2.

interior gate q >= 0.45, |b| <= 0.65:
v40 max ~= 1.951634666146e-1,
v49 max ~= 1.174547781095e-2.

local rectangle:
v40 max ~= 6.457688663085e-1,
v49 max ~= 4.752159416815e-2.

extreme gate q >= 0.25, |b| <= 0.90:
v40 max ~= 6.612026574807e-1,
v49 max ~= 5.535569977138e-2.
```

The v49 finite-difference gates are stable:

```text
standard h = 2e-3, 1e-3, 5e-4:
max ~= 5.470540584580e-2, 5.470627484641e-2, 5.470735424147e-2.

extreme h = 2e-3, 1e-3, 5e-4:
max ~= 5.534732366895e-2, 5.535569977138e-2, 5.534217181756e-2.
```

This reverses the earlier comparison with the non-admissible bounded-edge seed:

```text
standard max:
v35 non-admissible ~= 1.957809706943e-1,
v49 admissible     ~= 5.470627484641e-2.

extreme max:
v35 non-admissible ~= 3.633506253060e-1,
v49 admissible     ~= 5.535569977138e-2.
```

The remaining obstruction is farther out in the tail:

```text
q in [0.18,0.30], |b| <= 0.90:
v49 RMS ~= 6.357093982907e-2,
v49 max ~= 2.682727177003e-1,
worst near q=0.18, |b|=0.45.
```

The representation now also allows a general `q^sigma(1-q)^i b^(2j)` vanishing edge power. A first `sigma=0.5` test preserves the conical trace but worsens the farther-tail max:

```text
profile-seeds/gamma0p45-vanishing-edge-sigma0p5-seed-v50.json
farther-tail max ~= 3.195007993310e-1.
```

Thus slower algebraic vanishing is not, by itself, the missing far-tail representation. The next constrained profile step should either enrich the far-tail angular/radial basis at `q ~= 0.18` or construct a genuine indicial tail basis rather than hand-picking `sigma`.

Localized high-order vanishing shells give a cleaner far-tail test. Starting
from v49, freeze the monomial coefficients and existing edge coefficients, add
only new shells in

```text
q(1-q)^i b^(2j),
```

and train only on the farther-tail box `q in [0.18,0.30]`. This keeps the
conical trace exact while localizing the new correction near small `q`.

The shell sequence gives:

```text
profile-seeds/gamma0p45-vanishing-edge-shell10-seed-v51.json
profile-seeds/gamma0p45-vanishing-edge-shell12-seed-v52.json
profile-seeds/gamma0p45-vanishing-edge-shell14-seed-v53.json
```

with farther-tail max residuals

```text
v49 balanced seed: 2.682727177003e-1,
v51 shell-10:     2.243716179375e-1,
v52 shell-12:     1.931711331107e-1,
v53 shell-14:     1.792056343172e-1.
```

The v53 farther-tail value is stable under finite-difference changes:

```text
h = 2e-3, 1e-3, 5e-4:
max ~= 1.792165754613e-1, 1.792056343172e-1, 1.798543628562e-1.
```

The price is degraded finite-box accuracy relative to v49:

```text
standard max:
v49 ~= 5.470627484641e-2,
v53 ~= 7.607876229271e-2.

extreme max:
v49 ~= 5.535569977138e-2,
v53 ~= 6.231594228615e-2.
```

Thus v49 is currently the best balanced admissible seed, while v53 is the best
far-tail-focused admissible seed. Both remain many orders of magnitude above
the validation target. The residual obstruction has become sharply localized:
a streamfunction-equation lobe at the smallest sampled `q`, near `|b| ~= 0.56`.

A v49-to-v53 blend scan confirms that this is not a simple convex tradeoff:
the best max-over-gates blend is the v53 endpoint, saved with metadata as
`profile-seeds/gamma0p45-vanishing-edge-blend-v54.json`. A further shell-15
pilot from v54, trained on the sharper lobe box `q in [0.16,0.26]`,
improves the `q in [0.18,0.30]` max only marginally:

```text
v54 max: 1.792056343172e-1,
v55 max: 1.788852608387e-1.
```

It also leaves the far-tail scaling essentially unchanged. The
`tools/profile_tail_scaling.py` diagnostic gives these log-log slopes for
slice maxima on `q in [0.14,0.30]`:

```text
v49: -3.424196379310e+0,
v54: -3.326791266616e+0,
v55: -3.326077359962e+0.
```

On `q in [0.14,0.22]`, v54 gives a stable slope near `-5.34` for
`h = 2e-3, 1e-3, 5e-4`. This means the shell continuation is moving the lobe,
not producing a controlled asymptotic tail plateau. The next representation
needs a genuine tail-mode coordinate or an indicially motivated correction,
not just another polynomial shell.

The tail-series diagnostic makes this obstruction algebraic. Expanding v54 at
`q=0` gives a large first integer coefficient:

```text
order q^1:
F_1 max              ~= 1.528143595767e+1,
G_1 max              ~= 3.366956388107e+1,
psi linear max       ~= 3.926189986060e+0,
Gamma linear max     ~= 9.419011346695e+0.
```

Filtering this q1 coefficient to zero preserves the exact `q=0` trace but
destroys the finite-box residual:

```text
profile-seeds/gamma0p45-vanishing-edge-tailfilter1-v56.json
q in [0.18,0.30] max ~= 1.029116539178e+1,
standard max         ~= 7.829988985390e+1.
```

A q2 vanishing-family refit still leaves monomial q1 content, while the q2
family with q1 filtered out remains inconsistent after three damped
Gauss-Newton steps:

```text
profile-seeds/gamma0p45-vanishing-edge-q2fit-v57.json
q in [0.18,0.30] max ~= 4.052567239301e-1.

profile-seeds/gamma0p45-vanishing-edge-q2constrained-v59.json
q in [0.18,0.30] max ~= 2.810165146512e+0,
standard max         ~= 1.764307765388e+1.
```

Thus the finite-box fits are using a forbidden low-order integer tail channel
as a compensator. The leading trace also generates a nonzero nonlinear source
at the non-integer order `q^(1/gamma) = q^2.222...`; the next profile ansatz
must include that forced correction and the validated indicial modes instead
of unconstrained integer polynomial shells.

The forced non-integer tail correction is now explicit. The tool
`tools/profile_forced_tail.py` solves the angular least-squares equations for
the first `q^(1/gamma)` correction generated by the constant trace. With
`b_order=8`, it cancels the leading nonlinear source to roundoff:

```text
psi source max:   2.329118197481e+0 -> 6.099271088189e-11,
Gamma source max: 2.249300232178e-1 -> 4.041022655388e-10.
```

The resulting forced-tail seed v62 and q1-frozen continuation v64 preserve the
exact q=0 trace and have no q1 tail channel. v64 gives the strongest
asymptotically aligned far-tail gate so far:

```text
profile-seeds/gamma0p45-forced-tail-qm-q2solve-v64.json
q in [0.18,0.30], h = 2e-3: max ~= 9.015810891471e-2,
q in [0.18,0.30], h = 1e-3: max ~= 9.016164760362e-2,
q in [0.18,0.30], h = 5e-4: max ~= 9.013938030938e-2.
```

This improves the far-tail-focused v54 value `1.792056343172e-1` by about a
factor of two, but v64 is not a profile solution:

```text
standard max ~= 2.630970784815e+0,
interior max ~= 2.699587690022e+0,
local max    ~= 2.670237995086e+0.
```

The obstruction has therefore shifted. The tail expansion is now better
understood: exact trace, no q1 unless center modulation is unfixed, forced
`q^(1/gamma)` correction, then validated indicial modes. What remains is an
interior matching solve in this asymptotic basis.

A localized forced-tail cutoff and q1-frozen interior solve produced v72, the
first balanced seed in this constrained family:

```text
profile-seeds/gamma0p45-forced-tail-blend-q2solve-v72.json
q in [0.18,0.30] max ~= 4.325436706783e-1,
standard max         ~= 6.421601684773e-1,
interior max         ~= 6.449624903933e-1,
local max            ~= 6.445437673718e-1.
```

A richer q1-frozen continuation from v72, using ordinary monomials only from
q-order 2 upward and freezing the forced non-integer angular family, first
gave the balanced q1-free forced-tail seed v74:

```text
profile-seeds/gamma0p45-forced-tail-richinterior-v74.json
q in [0.18,0.30] max ~= 4.169187255275e-1,
standard max         ~= 5.909176701763e-1,
interior max         ~= 5.932368481368e-1,
local max            ~= 5.930636467992e-1.
```

The v74 gates are finite-difference stable:

```text
farther-tail h=2e-3,1e-3,5e-4:
4.169211686592e-1, 4.169187255275e-1, 4.168707616438e-1.

standard h=2e-3,1e-3,5e-4:
5.909184245366e-1, 5.909176701763e-1, 5.909165194996e-1.
```

The trace and q1 constraints remain exact, and the fractional
`q^(1/gamma)` coefficient stays aligned with the leading source. However,
the order-q9 ordinary tail residual has already grown:

```text
order q^9 psi_linear_max ~= 1.971720549096e+1.
```

Filtering the large q9 ordinary tail coefficient and restarting with capped
ordinary q-order showed that the q9 channel was not necessary. The best seed
from this capped sequence is v86:

```text
profile-seeds/gamma0p45-forced-tail-richinterior-q6-v86.json
q in [0.18,0.30] max ~= 3.977005747567e-1,
standard max         ~= 5.402426950755e-1,
interior max         ~= 5.413752067105e-1,
local max            ~= 5.417628839283e-1.
```

The v86 gates are finite-difference stable:

```text
farther-tail h=2e-3,1e-3,5e-4:
3.976970182399e-1, 3.977005747567e-1, 3.977214644192e-1.

standard h=2e-3,1e-3,5e-4:
5.402437205236e-1, 5.402426950755e-1, 5.402459718514e-1.
```

The trace and q1 constraints remain exact, and ordinary q-orders 7 and above
are absent. The remaining integer-tail obstruction has moved down to q5-q6:

```text
order q^5 psi_linear_max ~= 3.200652222019e+0,
order q^6 psi_linear_max ~= 3.857320704056e+0.
```

Filtering q6 alone worsens the balanced gate, and filtering q5-q6 is much
worse. Thus v86 is useful evidence for the constrained basis, not a validated
profile. It reinforces that the next profile representation needs genuine
matching or indicial degrees instead of still richer ordinary polynomial tail
content.

The next structural probe adds interior bump degrees that are flat at `q=0`.
Full least-squares bump solves overfit the training grid and are rejected by
the independent max gates:

```text
v87 compact F/G bumps:
standard/interior/local max ~= 1.28e+0 / 1.37e+0 / 2.89e+0.

v88 compact F-only bumps:
standard/interior/local max ~= 6.85e-1 / 1.50e+0 / 2.18e+0.

v89 flat-Gaussian F-only bumps:
standard/interior/local max ~= 7.81e-1 / 7.88e-1 / 8.35e-1.
```

However, a small convex blend between v86 and the flat-Gaussian direction
does improve the balanced gates. The best sampled blend is v91:

```text
profile-seeds/gamma0p45-forced-tail-flatbumpF-blend-v91.json
q in [0.18,0.30] max ~= 3.989670525038e-1,
standard max         ~= 5.375808758463e-1,
interior max         ~= 5.385829296901e-1,
local max            ~= 5.388811146608e-1.
```

The v91 gates are finite-difference stable:

```text
standard h=2e-3,1e-3,5e-4:
5.375828678111e-1, 5.375808758463e-1, 5.375817021688e-1.

local h=2e-3,1e-3,5e-4:
5.388831789929e-1, 5.388811146608e-1, 5.388802772597e-1.
```

The flat bump is invisible to the integer tail-series diagnostic and preserves
the exact trace and zero q1 channel. v91 was therefore the best balanced
q1-free forced-tail seed at this stage, but it remained far from validation.

The solver now also supports active weighted gate points through
`--active-qb-points` and `--active-rz-points`. A full active step from v91
overshoots, but the small v91-to-v92 blend v93 improves the balanced max:

```text
profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v93.json
q in [0.18,0.30] max ~= 4.016192226850e-1,
standard max         ~= 5.296559969709e-1,
interior max         ~= 5.273605597729e-1,
local max            ~= 5.294625460480e-1.
```

The v93 gates are finite-difference stable:

```text
standard h=2e-3,1e-3,5e-4:
5.296597210998e-1, 5.296559969709e-1, 5.296553963832e-1.

local h=2e-3,1e-3,5e-4:
5.294630312919e-1, 5.294625460480e-1, 5.294718995020e-1.
```

A second active step from v93 did not improve after blending; the best
v93-to-v94 blend is the v93 endpoint.

The active least-squares steps show useful directions but optimize the wrong
objective, so I added a direct minimax coordinate search:

```text
tools/profile_minimax_coordinate.py
```

This tool varies selected coefficient families and accepts a move only if it
lowers the max absolute residual on the requested gates.  Starting from v93,
F-only minimax moves gave v96, adding zero-start `G` tail-flat bumps gave
v97-v101, and active 41x41 topology points gave v102-v106.  v103 first broke
the `4.61e-1` barrier, v104 improved the robust topology max, v105 exposed a
hidden 41x41 lobe, and a refreshed active set then gave v106:

```text
profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v106.json
q in [0.18,0.30] max ~= 3.852405555391e-1,
standard wide max    ~= 4.525392363637e-1,
standard interior    ~= 4.523133293752e-1,
standard local       ~= 4.549610384871e-1,
fine/active max      ~= 4.550283493881e-1,
41x41 topology max   ~= 4.544085174837e-1.
```

The v106 gates are finite-difference stable:

```text
standard wide h=2e-3,1e-3,5e-4:
4.525353356627e-1, 4.525392363637e-1, 4.525456373170e-1.

standard interior h=2e-3,1e-3,5e-4:
4.523124982329e-1, 4.523133293752e-1, 4.523109686800e-1.

standard local h=2e-3,1e-3,5e-4:
4.549500774717e-1, 4.549610384871e-1, 4.549627285331e-1.

farther-tail h=2e-3,1e-3,5e-4:
3.852366582649e-1, 3.852405555391e-1, 3.852815990152e-1.
```

A 41x41 topology scan gives max `4.544085174837e-1` at `q=0.486`,
`b=0.585`, below the fine-grid max.  The tail-series diagnostic still has
exact trace and zero q1 channel:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

Thus v106 was a useful constrained balance, but it remained far from
validation.

I then expanded the tail-flat interior bump grid while preserving the old
center locations and coefficients exactly:

```text
tools/profile_expand_bumps.py
```

The expanded base seed starts from v106, adds zero coefficients at the new
centers, and leaves the q=0 trace and q1 channel unchanged.  Continuing only
the new zero-start coefficients gave v107, refreshed active continuations gave
v108-v109, and two smaller-step passes gave the current best balanced q1-free
forced-tail seed:

```text
profile-seeds/gamma0p45-forced-tail-expanded-flatbumpFG-v111.json
standard wide max    ~= 4.367747752125e-1,
standard interior    ~= 4.396586783719e-1,
standard local       ~= 4.396608030521e-1,
fine 29x29/45 max    ~= 4.398351490167e-1,
41x41 topology max   ~= 4.396417168948e-1,
farther-tail max     ~= 3.813442764768e-1.
```

The v111 gates are finite-difference stable:

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

A 41x41 topology scan gives max `4.396417168948e-1` at `q=0.486`,
`|b|=0.630`, with nearby lobes at `q=0.432`, `|b|=0.270`.  The
tail-series diagnostic still has exact trace and zero q1 channel:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

The v111 topology scan also showed that the active residuals were sitting
between existing bump centers, especially near `q=0.48`, `|b|=0.65`;
`q=0.50`, `|b|=0.60`; and `q=0.60`, `|b|=0.25`.  I therefore added a sparse
center-pair helper:

```text
tools/profile_add_sparse_bumps.py
```

Unlike the full grid expansion, this helper remaps the old coefficients and
adds only requested zero-start `(q,b^2)` bump pairs.  The first sparse run gave
the current best constrained balance:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v112.json
standard wide max    ~= 4.365866237926e-1,
standard interior    ~= 4.395069007065e-1,
standard local       ~= 4.391290054377e-1,
fine 29x29/45 max    ~= 4.397800969258e-1,
41x41 topology max   ~= 4.393817079326e-1,
farther-tail max     ~= 3.812707390403e-1.
```

The v112 gates are finite-difference stable:

```text
standard wide h=2e-3,1e-3,5e-4:
4.365921962713e-1, 4.365866237926e-1, 4.365865152350e-1.

standard interior h=2e-3,1e-3,5e-4:
4.395014482862e-1, 4.395069007065e-1, 4.395077228295e-1.

standard local h=2e-3,1e-3,5e-4:
4.391322052093e-1, 4.391290054377e-1, 4.391275368035e-1.

farther-tail h=2e-3,1e-3,5e-4:
3.812683123738e-1, 3.812707390403e-1, 3.812909608101e-1.
```

A 41x41 topology scan gives max `4.393817079326e-1` at `q=0.486`,
`|b|=0.630`, with nearby lobes at `q=0.432`, `|b|=0.270`.  The
tail-series diagnostic still has exact trace and zero q1 channel:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

Subsequent sparse-bump runs found that the v112/v113-base topology ledger was
not exhaustive.  A shifted high-`|b|` scan on the box
`q in [0.472,0.505]`, `|b| in [0.585,0.675]` found a stable holdout maximum
near `4.4006e-1`, so the next searches scored that lobe explicitly.

The v113 sparse continuation improved the coarse and independent checks, but
it still left the residual at the same `O(1)` scale:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v113.json
standard max       ~= 4.391502409150e-1,
fine 29x29/45 max ~= 4.395926393838e-1,
41x41 topology max ~= 4.392376399652e-1,
farther-tail max  ~= 3.820821937260e-1.
```

A parallel v114/v115 batch then separated useful and bad objectives.  Far-only
or far/extreme-only scoring lowered the reported tail objective while worsening
balanced wide/interior/local gates, so those candidates were rejected.  The
useful branch was the high-`|b|` solve
`profile-seeds/subagent-batch-highb-v1.json`, which lowered the shifted gate
max to `4.385615233030e-1` and moved the old high-`|b|` lobe below the main
low-`|b|` band.

Adding sparse low-`|b|` centers to that high-`|b|` endpoint and tuning only the
new zero-start coefficients gives the current best constrained balance:

```text
profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v116-lowb.json
standard max h=2e-3,1e-3,5e-4:
4.378237351374e-1, 4.378239756763e-1, 4.378239372738e-1.

shifted gate max h=1.6e-3,8e-4,4e-4:
4.384746043386e-1, 4.384766750064e-1, 4.384759905812e-1.

fine 29x29/45 max:
4.388424241734e-1.

broad shifted topology max:
4.370460732359e-1.

old high-|b| holdout-box max:
4.354896703956e-1.

far-tail holdout max:
4.091040786189e-1.
```

The v116 tail-series diagnostic still has exact trace and zero q1 channel:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

The next ridge-strip branch starts from the v116 topology information and
adds sparse centers along the low-`|b|` streamfunction ridge.  The active-lowb
variant was stopped after a weaker checkpoint; the targeted ridge branch was
saved as `profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge.json`
with score max `4.377063068728e-1`.  The broader ridge-strip branch is better
and finished as `profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip.json`:

```text
optimizer score max: 4.346963144133e-1
active: 4.346727268717e-1
wide: 4.346963144133e-1
interior: 4.322425589778e-1
local: 4.346265632453e-1
farther: 3.834216871230e-1
extreme: 4.333119973137e-1
```

Independent checks on the final seed give:

```text
standard max h=2e-3,1e-3,5e-4:
4.343958248990e-1, 4.344046967088e-1, 4.344070020656e-1.

fine 29x29/45 max:
4.362251080302e-1.

shifted gate max h=1.6e-3,8e-4,4e-4:
4.364874143437e-1, 4.364860207575e-1, 4.364865315324e-1.

41x41 topology max:
4.347549502774e-1 near q=0.378, |b|=0.315.

focused hidden-ridge max:
4.364654153641e-1 near q=0.400, |b|=0.293333.

secondary q ~= 0.608, |b| ~= 0.241 ridge:
4.350113142226e-1.
```

The v117 tail-series diagnostic still has exact trace and zero q1 channel:

```text
order 0: F_0 max = 5.000000000000e-1, G_0 max = 1.000000000000e+0
order 1: F_1 max = 0, G_1 max = 0
```

Thus final v117 ridge-strip is the current best constrained diagnostic
balance, but it still remains far from validation.  The remaining obstruction
is a hidden low-`|b|` streamfunction ridge near `q=0.400`, `|b|=0.293333`,
which is missed by the coarse broad topology grid.

The proof-native projection scaffold is now executable:

```text
python3 tools/profile_project_cheb.py \
  --input profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v117-ridge-strip.json \
  --gamma 9/20 --B 1 --degree-q 10 --degree-x 10 \
  --tail-blocks 1 --origin-degree 4 \
  --out work/v117_transcheb.json

python3 tools/validate_tail.py --profile work/v117_transcheb.json
```

This projection keeps the ordinary q1 channel structurally zero and lifts the
forced `q^(1/gamma)` block:

```text
ordinary_q1_F_max = 0
ordinary_q1_G_max = 0
forced_qp_lifted = True
projection_F_error = 9.335499773222e-8
projection_G_error = 2.567489395977e-6
origin_F_fit_error = 6.488671574113e-1
origin_G_fit_error = 3.169194550836e-1
```

The large origin Taylor errors are decisive for the next step: v117 is useful
as a ridge locator and crude projection seed, but sparse flat bumps should not
be treated as a proof representation.  The next profile solve must use a
transseries-constrained Chebyshev/origin-regular basis from the start, with
exact residuals and a Newton solve.

The projection-backed compactified-equation bridge
`validators/compactified_equations.py` confirms that the projected profile
preserves the obstruction rather than hiding it.  In finite-difference bridge
mode it reports:

```text
focused q=[0.345,0.495], b=[0.18,0.38], 17x17:
max_abs = 4.364542617048e-1 near q=0.401250, b=0.292500.

secondary q=[0.57,0.64], b=[0.20,0.27], 13x13:
max_abs = 4.349867452619e-1 near q=0.610833, b=0.240833.
```

In Taylor-jet mode, differentiating the projected Chebyshev expression instead
of finite-differencing it gives the same obstruction:

```text
focused q=[0.345,0.495], b=[0.18,0.38], 17x17:
max_abs = 4.364551889010e-1 near q=0.401250, b=0.292500.

secondary q=[0.57,0.64], b=[0.20,0.27], 13x13:
max_abs = 4.349878819316e-1 near q=0.610833, b=0.240833.
```

This jet mode is still labeled `TAYLOR_JET_RESIDUAL_NOT_INTERVAL_VALIDATION`.
The production validator must wrap the differentiated compactified expressions
in interval/ball arithmetic before any Newton-Kantorovich proof attempt.

The first proof-native coefficient optimizer is now present as
`tools/profile_newton_cheb.py`.  It is a discovery-only damped Gauss-Newton
driver over the projected Chebyshev/transseries coefficients and uses the
Taylor-jet compactified residual bridge.  Two selector bugs were fixed before
using it as evidence: `--max-variables` now balances across requested blocks
instead of exhausting `F_an` first, and `F_frac0/G_frac0` variables mutate the
actual `F_frac/G_frac` JSON blocks.  The selector now prints block counts, for
example `{'F_an': 18, 'G_an': 18, 'F_frac0': 18, 'G_frac0': 18}` in the
two-ridge run.

The first fair runs do not show a Newton basin.  A focused hidden-ridge solve

```text
python3 tools/profile_newton_cheb.py \
  --input work/v117_transcheb.json \
  --out work/v117_transcheb_newton_hidden_balanced.json \
  --blocks F_an,G_an \
  --q-min 0.395 --q-max 0.405 \
  --b-min 0.286 --b-max 0.300 \
  --n-q 5 --n-b 5 \
  --active-qb-points '0.400,0.293333,8;0.40125,0.2925,8;0.607917,0.240833,4' \
  --var-q-min 0.34 --var-q-max 0.52 \
  --var-x-min 0.04 --var-x-max 0.20 \
  --max-mode-q 2 --max-mode-x 2 \
  --max-variables 48 \
  --iterations 3 \
  --fd-step 2e-6 \
  --damping 1e-3 \
  --max-update-norm 0.01
```

selected 32 variables, split `16/16` across `F_an/G_an`.  Its training max
moved from `4.364876395740e-1` to `4.350124009035e-1`, and held-out checks
reported:

```text
focused q=[0.345,0.495], b=[0.18,0.38], 17x17:
max_abs = 4.346774703261e-1 near q=0.382500, b=0.317500.

secondary q=[0.57,0.64], b=[0.20,0.27], 13x13:
max_abs = 4.349878819316e-1 near q=0.610833, b=0.240833.

broad q=[0.12,0.895], b=[0.03,0.92], 21x21:
max_abs = 4.341756757351e-1 near q=0.507500, b=0.252500.
```

A broader two-ridge solve

```text
python3 tools/profile_newton_cheb.py \
  --input work/v117_transcheb.json \
  --out work/v117_transcheb_newton_biridge_balanced.json \
  --blocks F_an,G_an,F_frac0,G_frac0 \
  --q-min 0.35 --q-max 0.64 \
  --b-min 0.20 --b-max 0.34 \
  --n-q 6 --n-b 6 \
  --active-qb-points '0.400,0.293333,8;0.40125,0.2925,8;0.607917,0.240833,8;0.610833,0.240833,8;0.432,0.270,4' \
  --var-q-min 0.34 --var-q-max 0.72 \
  --var-x-min 0.04 --var-x-max 0.20 \
  --max-mode-q 2 --max-mode-x 2 \
  --max-variables 72 \
  --iterations 2 \
  --fd-step 1e-6 \
  --damping 5e-3 \
  --max-update-norm 0.002
```

selected 72 variables, split evenly across `F_an/G_an/F_frac0/G_frac0`.
Its training max moved from `4.364651961146e-1` to
`4.354268126233e-1`.  Held-out checks show residual redistribution:

```text
focused q=[0.345,0.495], b=[0.18,0.38], 17x17:
max_abs = 4.370029069859e-1.

secondary q=[0.57,0.64], b=[0.20,0.27], 13x13:
max_abs = 4.339438267027e-1.

broad q=[0.12,0.895], b=[0.03,0.92], 21x21:
max_abs = 4.353092583643e-1.
```

Thus the current Chebyshev coefficient scaffold is useful for diagnosing where
the obstruction moves, but it has not found a proof-grade or even low-residual
profile.  The immediate next profile work is a real global Newton solve with a
normalized compactified residual and an origin-regular patch as part of the
unknown space, not more sparse-bump continuation.

The origin Taylor block is now wired into
`validators/compactified_equations.py` for `q >= q_min`, so the stored origin
scaffold is no longer unused metadata.  This exposes a severe origin-patch
failure:

```text
work/v117_transcheb.json, origin patch q=[0.91,0.98], b=[0.05,0.80], 7x7:
max_abs = 1.427061295791e+1.

same profile just below the origin patch q=[0.82,0.895], b=[0.05,0.80], 7x7:
max_abs = 1.679666438145e-1.
```

This does not change the interior ridge conclusion, but it makes the origin
regularity gate explicit: the current projection cannot be used as a proof
object.

The later v118 sparse-bump artifacts were inspected and should not supersede
the v117 projection branch.  The complete saved artifact
`profile-seeds/gamma0p45-forced-tail-sparse-flatbumpFG-v118-ridge-exact.json`
is another non-validated sparse minimax seed:

```text
score_max = 4.353608399992e-1
active    = 4.353608399992e-1
interior  = 4.352307636635e-1
local     = 4.347353243883e-1
wide      = 4.335957224954e-1
farther   = 3.828271644262e-1
```

Independent standard gates for the saved v118 exact seed remain grid-stable
but `O(1)`:

```text
wide h=2e-3,1e-3,5e-4:
4.344139225580e-1, 4.344145872138e-1, 4.344128151505e-1.

interior h=2e-3,1e-3,5e-4:
4.351506744746e-1, 4.351536789296e-1, 4.351549029195e-1.

local h=2e-3,1e-3,5e-4:
4.345263629807e-1, 4.345292057362e-1, 4.345288126594e-1.
```

The v118 seed moves residual from one ridge to another and has no
transseries-Chebyshev projection, origin gate, tail recurrence check, or
Newton-Kantorovich evidence.  It is logged only as another sparse-bump
diagnostic.

`validators/compactified_equations.py` now has explicit pointwise normalized
residual modes in addition to raw residual regression:

```text
raw
geometric-normalized
normalized-structural
normalized-strict-tail
```

The default proof-path diagnostic is `normalized-structural`, with factors

```text
fac_psi   = r^4 z q^(p+4)
          = b (1-b^2)^2 (1-q^2)^(5/2) q^(p-1),

fac_Gamma = r^2 q^(p+2)
          = (1-b^2)(1-q^2) q^p.
```

The stricter tail diagnostic uses

```text
fac_psi   = r^4 z q^(2p+2),
fac_Gamma = r^2 q^(2p).
```

For `work/v117_transcheb.json`, the normalized structural checks are:

```text
focused q=[0.345,0.495], b=[0.18,0.38], 17x17:
max_abs = 1.071336958406e+1.

strict-tail same box:
max_abs = 1.252539984352e+1.

origin q=[0.91,0.98], b=[0.05,0.80], 7x7:
max_abs = 9.139966362302e+3.
```

This is the right scale for interpreting proof distance: the raw residual
`~4.36e-1` had not divided out the known geometric vanishing factors.

`tools/profile_newton_cheb.py` can now also select and mutate
`F_origin/G_origin` Taylor coefficients.  An origin-only normalized solve

```text
python3 tools/profile_newton_cheb.py \
  --input work/v117_transcheb.json \
  --out work/v117_transcheb_origin_gn_large.json \
  --blocks F_origin,G_origin \
  --q-min 0.91 --q-max 0.98 \
  --b-min 0.05 --b-max 0.80 \
  --n-q 7 --n-b 7 \
  --var-q-min 0.90 --var-q-max 1.0 \
  --max-mode-q 4 --max-mode-x 4 \
  --include-constant \
  --max-variables 30 \
  --iterations 3 \
  --fd-step 1e-6 \
  --damping 1e-1 \
  --max-update-norm 5.0 \
  --residual-kind geometric-normalized
```

reduced the origin objective only from `1.283548767150e+3` to
`1.226574061065e+3`.  A normalized structural interior solve over
`F_an/G_an/F_frac0/G_frac0` rejected its first update because the maximum stayed
pinned at the secondary active point:

```text
initial max_abs = 1.185142423527e+1,
no accepted max-reducing update.
```

This confirms that the current projection is not a Newton basin for the
normalized problem.  The next profile solver must couple the origin Taylor
unknowns, rectangular Chebyshev patches, mortar/matching constraints, and the
normalized compactified residual in one global system.

A small coupled probe over rectangular and origin variables confirms the same
point.  Using active points at the origin, hidden ridge, and secondary ridge,

```text
python3 tools/profile_newton_cheb.py \
  --input work/v117_transcheb.json \
  --out work/v117_transcheb_structural_coupled_probe.json \
  --blocks F_an,G_an,F_frac0,G_frac0,F_origin,G_origin \
  --active-qb-points '0.495,0.18,2;0.607917,0.240833,2;0.91,0.8,8;0.91,0.675,4;0.98,0.8,2;0.400,0.293333,2' \
  --max-variables 96 \
  --iterations 1 \
  --damping 1e-1 \
  --max-update-norm 1.0 \
  --residual-kind normalized-structural
```

reduced the sampled origin structural max from `9.139966362302e+3` to
`8.347412637350e+3`, but held-out focused checks worsened:

```text
focused normalized-structural max = 1.515981821457e+1,
focused raw max = 7.545806315318e-1.
```

So simply allowing origin coefficients to move is not enough.  The next solver
needs a genuine global collocation/mortar formulation, or the radial
core-tail matching pivot should be prepared.

The source bundle `arXiv-2509.14185v1.tar.gz` was inspected locally.  It is the
LaTeX source for `Discovery of Unstable Singularities`.  The directly useful
solver lessons for this project are:

```text
1. optimize factored residuals, not raw equations with mechanical vanishing;
2. add higher-derivative or regularity losses so collocation points do not
   produce spiky overfit;
3. use residual-driven adaptive sampling, with hard points injected from dense
   validation grids;
4. use staged correction, where a later model/solve targets the linearized
   residual left by the previous stage;
5. for free blow-up parameters, use smoothness/funnel scans instead of blind
   parameter drift.
```

The current code now implements the first item through the normalized residual
modes and begins implementing the second through explicit continuity/mortar
penalties in `tools/profile_newton_cheb.py`:

```text
--continuity-weight
--continuity-samples
--origin-match-weight
--origin-match-q
--origin-match-x-samples
```

Patch-seam constraints compare left/right Chebyshev block values on shared
patch boundaries.  Origin matching constraints compare the rectangular
transseries value to the Taylor origin value at selected `q` levels.  These are
still discovery penalties, not interval mortar certificates.

The first constrained normalized structural run used 490 continuity/matching
constraints:

```text
python3 tools/profile_newton_cheb.py \
  --input work/v117_transcheb.json \
  --out work/v117_transcheb_structural_mortar_probe2.json \
  --blocks F_an,G_an,F_frac0,G_frac0,F_origin,G_origin \
  --q-min 0.38 --q-max 0.62 \
  --b-min 0.18 --b-max 0.34 \
  --n-q 5 --n-b 5 \
  --active-qb-points '0.400,0.293333,2;0.495,0.18,2;0.607917,0.240833,2;0.91,0.8,8;0.91,0.675,4;0.98,0.8,2' \
  --max-variables 96 \
  --iterations 5 total across continuation \
  --damping 1e-1 \
  --max-update-norm 0.2 \
  --residual-kind normalized-structural \
  --continuity-weight 0.25 \
  --continuity-samples 2 \
  --origin-match-weight 0.25 \
  --origin-match-q 0.9 \
  --origin-match-x-samples 5
```

Held-out checks moved in the right direction compared with
`work/v117_transcheb.json`:

```text
origin structural q=[0.91,0.98], b=[0.05,0.80]:
9.139966362302e+3 -> 8.341813217829e+3.

focused structural q=[0.345,0.495], b=[0.18,0.38]:
1.071336958406e+1 -> 1.021139387583e+1.

focused raw q=[0.345,0.495], b=[0.18,0.38]:
4.364551889010e-1 -> 3.984606191010e-1.
```

The secondary normalized lobe is unchanged:

```text
secondary structural q=[0.57,0.64], b=[0.20,0.27]:
1.439516431593e+1.
```

This is useful evidence that mortar/continuity penalties improve the direction
of coefficient updates, but the profile remains far from a proof center.  The
next discovery step should add adaptive hard-point injection from dense
normalized residual scans, especially at the secondary lobe and origin edge.

`tools/profile_projected_hardpoints.py` now implements that adaptive hard-point
scan for projected profiles.  It evaluates a selected residual form over a
dense compactified grid, keeps separated top residual points, and emits a
ready-to-use `--active-qb-points` string for `profile_newton_cheb.py`.

For `work/v117_transcheb_structural_mortar_probe2.json`, a full scan

```text
python3 tools/profile_projected_hardpoints.py \
  --profile work/v117_transcheb_structural_mortar_probe2.json \
  --q-min 0.12 --q-max 0.98 \
  --b-min 0.03 --b-max 0.92 \
  --n-q 25 --n-b 25 \
  --top 12 \
  --residual-kind normalized-structural
```

finds the dominant normalized defects on the origin/high-`|b|` edge:

```text
q ~= 0.908333, b ~= 0.845833, max_abs ~= 1.049148851339e+4,
q ~= 0.908333, b ~= 0.882917, max_abs ~= 1.011276233042e+4,
q ~= 0.908333, b ~= 0.808750, max_abs ~= 9.869187522174e+3.
```

Scanning below the origin switch, `q <= 0.89`, exposes a separate high-`|b|`
axis-edge defect:

```text
q = 0.89, b = 0.92, max_abs = 5.094286384670e+1,
q = 0.89, b ~= 0.845833, max_abs = 3.242194763027e+1.
```

A first adaptive constrained pass using those hard points lowered the origin
patch max but harmed the lower-`|b|` focused region:

```text
origin structural: 8.341813217829e+3 -> 7.822452872401e+3,
focused structural: 1.021139387583e+1 -> 1.164724939056e+1,
focused raw: 3.984606191010e-1 -> 4.721406319576e-1.
```

Thus `work/v117_transcheb_structural_mortar_probe2.json` remains the better
diagnostic checkpoint.  The adaptive scan is still valuable: it shows that the
next global solve must treat the origin/high-`|b|` axis edge as a first-class
region, not only the low-`|b|` ridge.

The automated adaptive driver `tools/profile_newton_adaptive.py` now wraps this
scan-and-solve loop.  It was compiled and smoke-tested, then run for one
conservative balanced round from the current best checkpoint:

```text
python3 tools/profile_newton_adaptive.py \
  --input work/v117_transcheb_structural_mortar_probe2.json \
  --out-prefix work/v117_transcheb_balanced_adaptive \
  --rounds 1 \
  --include-constant \
  --inner-iterations 1 \
  --max-variables 96 \
  --damping 0.2 \
  --max-update-norm 0.08
```

The selected hard points were dominated by the origin/high-`|b|` interface,
especially `q=0.9`, `b=0.865625`.  The active normalized structural objective
barely moved:

```text
3.370272168037e+4 -> 3.368939946152e+4.
```

The standard held-out gates for
`work/v117_transcheb_balanced_adaptive-round1.json` were:

```text
origin structural q=[0.91,0.98], b=[0.05,0.80]:
8.341009469925e+3.

focused structural q=[0.345,0.495], b=[0.18,0.38]:
1.020735439617e+1.

focused raw q=[0.345,0.495], b=[0.18,0.38]:
3.983177058335e-1.

secondary structural q=[0.57,0.64], b=[0.20,0.27]:
1.439516431593e+1.

broad high-|b| structural q=[0.12,0.89], b=[0.03,0.92]:
5.094286384670e+1.
```

The tail structural check still has exact ordinary q1 exclusion and the forced
`q^(1/gamma)` lift, but the origin Taylor gate remains false.  This automated
adaptive run therefore does not supersede
`work/v117_transcheb_structural_mortar_probe2.json`; it confirms that the
current rectangular/origin representation is running into an interface and
axis-edge obstruction, not merely missing a few active collocation points.

The later GPT-Pro update made one tail issue sharper.  The old structural tail
check only verified that a fractional `q^(1/gamma)` block was present.  That is
too weak.  The first forced trace must match the formal recurrence.  For
`gamma=9/20`, `B=1`, the recurrence gives

```text
F_p(x) = 1.9218140929535197 - 0.9786773280026653 x,
G_p(x) = 0.11111111111111108 - 1.1111111111111112 x.
```

`validators/tail_transseries.py` and `tools/validate_tail.py` now check this
coefficient equality.  With the stricter check,
`work/v117_transcheb_structural_mortar_probe2.json` is no longer tail-OK:

```text
ordinary_q1_F_max = 0,
ordinary_q1_G_max = 0,
forced_qp_coeff_error = 1.384330015818e-2,
tail_structural_ok = False.
```

This matters because the mortar solve had moved the first fractional block in
a way that helped the sampled residual but violated the formal tail recurrence.

`tools/profile_project_cheb.py` now has a formal forced-tail projection mode:

```text
--forced-qp-mode formal
--forced-origin-cutoff-power 6
```

It replaces the seed-derived `q^p` trace by the recurrence coefficient and
multiplies that angular trace by `(1-q^2)^6` so it does not pollute the
physical origin.  The resulting
`work/v117_transcheb_formal_forced.json` passes the tightened forced-tail gate:

```text
forced_qp_coeff_error = 0,
projection_F_error = 2.060504508128e-7,
projection_G_error = 2.567489394645e-6.
```

But the profile residual is back at the original projected scale:

```text
origin structural = 9.139966362302e+3,
focused structural = 1.071336959068e+1,
focused raw = 4.364551896246e-1,
secondary structural = 1.439516431487e+1,
broad high-|b| structural = 5.094286384720e+1.
```

So the current conclusion is stricter than before: the best mortar checkpoint
is useful as a diagnostic of where the residual wants to move, but it is not an
admissible tail object.  The next real profile solve must keep the formal
`q^p` recurrence pinned and solve the analytic/origin degrees around it.

Two code-hygiene fixes were also applied to the Chebyshev Newton scaffold.
First, `tools/profile_newton_cheb.py` no longer writes every trial profile to a
shared `work/.profile_newton_cheb_tmp.json`; it uses unique temporary files.
Second, when a variable cap is active, coefficient variables from patches
containing the current grid or active hard points are prioritized.  This fixes
the failure mode where adaptive residual points were included in the objective
while no local coefficient patch could move them.

A small post-fix probe was run from the formal-tail projection:

```text
work/v117_transcheb_formal_hotpatch_probe.json
```

The solve included both rectangular and origin variables:

```text
variables = 40,
counts = {'F_an': 16, 'G_an': 16, 'F_origin': 4, 'G_origin': 4}.
```

It kept the formal tail recurrence pinned:

```text
ordinary_q1_F_max = 0,
ordinary_q1_G_max = 0,
forced_qp_coeff_error = 0.
```

The active objective improved but remained enormous:

```text
2.585172877840e+4 -> 2.512049197567e+4.
```

Held-out checks moved in the right direction, but only slightly:

```text
origin structural:
9.139966362302e+3 -> 8.881435111368e+3.

focused structural:
1.071336959068e+1 -> 1.040795353834e+1.

focused raw:
4.364551896246e-1 -> 4.238894370280e-1.

secondary structural:
1.439516431487e+1 -> 1.422825475247e+1.

broad high-|b| structural:
5.094286384720e+1 -> 5.094286384720e+1.
```

This is useful because the solver can now move the correct patches while
keeping the formal `q^p` trace fixed.  It is not yet close to an NK-entry
center; the origin and high-`|b|` obstruction still dominates.

The Chebyshev Newton scaffold now also supports derivative mortar constraints:

```text
--continuity-derivative-order
--origin-match-derivative-order
--mortar-derivative-weight
--mortar-derivative-step
```

These constraints compare one-sided normal derivatives across Chebyshev patch
seams and finite-difference `q/x` derivatives across the rectangular/origin
matching interface.  This is still a discovery penalty, not an interval
smoothness proof, but it addresses the earlier bug where only function values
were matched while the residual differentiates through the hard patch switch.

A C1 formal-tail probe was run from the hot-patch checkpoint:

```text
work/v117_transcheb_formal_c1mortar_probe.json
```

with

```text
continuity_derivative_order = 1,
origin_match_derivative_order = 1,
mortar_derivative_weight = 1e-2,
mortar_derivative_step = 1e-4.
```

It preserved the formal tail recurrence:

```text
forced_qp_coeff_error = 0.
```

and improved the same held-out gates:

```text
active structural:
2.512049197567e+4 -> 2.452563187080e+4.

origin structural:
8.881435111368e+3 -> 8.671120304364e+3.

focused structural:
1.040795353834e+1 -> 1.016228983517e+1.

focused raw:
4.238894370280e-1 -> 4.139241142239e-1.

secondary structural:
1.422825475247e+1 -> 1.422825475247e+1.

broad high-|b| structural:
5.094286384720e+1 -> 5.094286384720e+1.
```

The high-`|b|` lobe was then targeted separately:

```text
work/v117_transcheb_formal_c1_highb_probe.json
```

This kept the formal tail recurrence pinned and did not change the
origin/focused/secondary checks from the C1 mortar probe, while reducing the
broad high-`|b|` structural max:

```text
5.094286384720e+1 -> 4.897717856780e+1.
```

The result supports a staged multi-region correction strategy with the formal
tail fixed.  It does not change the proof status: the profile remains many
orders of magnitude from an NK center, and the origin chart remains the
dominant obstruction.

The finite-difference mortar rows have now been replaced by exact
Chebyshev/Taylor partial derivative rows through total order 2 inside
`tools/profile_newton_cheb.py`.  The C2 row set includes

```text
(dq,dx)=(2,0), (1,1), (0,2),
```

so the audit no longer misses mixed chart-interface jumps.  Two read-only
tools were added:

```text
tools/profile_mortar_audit.py
tools/audit_profile_structure.py
```

The first reports exact patch and origin mortar defects.  The second bundles
tail metadata, exact mortar, and normalized residual topology.  It is still not
an interval validator, but it is a better gate before spending more solver
time.

Running

```text
python3 tools/audit_profile_structure.py \
  --profile work/v117_transcheb_formal_c1_highb_probe.json \
  --continuity-samples 2 \
  --origin-match-x-samples 4 \
  --q-min 0.88 --q-max 0.98 \
  --b-min 0.05 --b-max 0.92 \
  --n-q 21 --n-b 21 \
  --top 8 \
  --json-out work/v117_transcheb_formal_c1_highb_structure_audit.json
```

gives:

```text
tail_ok=True,
projection_ok=True,
origin_ok=False,
q1_F=q1_G=0,
forced_qp_coeff_error=0,
origin_F_fit_error=6.488671574113e-01,
origin_G_fit_error=3.169194550836e-01,
exact C2 mortar max=6.372865880897e+03,
origin-band normalized-structural max=2.444892773927e+04,
top_at_switch=8/8.
```

The worst exact mortar row is

```text
kind=origin-match,
component=F,
q=0.9,
x=0,
(dq,dx)=(2,0),
diff=6.372865880897e+03.
```

Thus the next profile-representation question is now concrete:

```text
Is the O(1e4) origin-band normalized residual a chart/mortar artifact caused
by the hard q=0.9 switch, or does it persist after an exact C2-compatible
origin/rectangle representation?
```

Until this is answered, more Newton steps are mainly measuring chart mismatch,
not a proof-native PDE residual.

To test this directly, `tools/profile_refit_origin_mortar.py` now refits only
the origin Taylor coefficients against exact rectangular total traces.  It
leaves

```text
gamma, B, p,
tail_constraints,
F_an/G_an,
F_frac/G_frac
```

unchanged, so the q0/q1/forced-tail structure is preserved by construction.

The best diagnostic branch so far is

```text
work/v117_transcheb_formal_origin_refit_c2_d6_a.json
```

produced by a degree-6 origin fit over

```text
q=0.9,0.94,0.98,
match_order=2,
value_weight=10,
d1_weight=0.1,
d2_weight=0.001.
```

Its structure audit is saved at

```text
work/v117_transcheb_formal_origin_refit_c2_d6_a_structure_audit.json.
```

The exact tail checks remain unchanged:

```text
q1_F=q1_G=0,
forced_qp_coeff_error=0.
```

The focused interior and strict-tail residual checks are also unchanged:

```text
focused normalized-structural max=1.016228983517e+01,
strict-tail max=2.287165521365e+01.
```

The origin-band audit changes decisively:

```text
before:
  exact C2 origin mortar max=6.372865880897e+03,
  origin-band normalized-structural max=2.444892773927e+04,
  top_at_switch=8/8.

after degree-6 multi-q C2 refit:
  exact C2 mortar max=3.521152682922e+01,
  origin-band normalized-structural max=2.111131935798e+02.
```

This proves the original `O(10^4)` spike was mostly a chart/mortar artifact.
It does not prove the profile branch.  The remaining origin defect is still
`O(10^2)`, the origin fit metadata still fails (`origin_taylor_ok=False`), and
the profile remains many orders of magnitude from NK entry.

Two negative controls are useful:

```text
C0-only or C1-only origin refits preserve small value mismatch but leave the
old C2 switch spike at O(10^4).

A pure origin-only Newton step from the degree-6 C2 refit barely changes the
held-out audit:
2.111131935798e+02 -> 2.110863508879e+02.
```

Therefore the next representation step is not another small origin-only Newton
patch.  Either the origin patch must be solved as part of a genuinely coupled
C2-compatible rectangular/origin spectral element, or the compactified route
should pivot to radial core-tail matching once this redesign fails.

The later GPT-Pro update in `gpt-pro-thing` sharpens that conclusion:

```text
Do not treat the current one-chart compactified Chebyshev plus origin splice as
the proof object.

Keep the transseries grammar, but build a hard two-chart solver:
tail chart in (q,x),
origin chart in (R,Z)=(r^2,z^2),
overlap/mortar band,
C3 minimum and preferably C4 interface matching,
analytic coefficient Jacobian.

Do not pivot to radial core-tail matching until this two-chart solver, tail
recurrence validation, and then parameter search have failed.
```

The same update points out a tail-legality issue that the previous structural
tail checker did not decide: the analytic `q^2` trace in

```text
F = 1/2 + q^2 F_an + q^p F_frac + ...
G = B   + q^2 G_an + q^p G_frac + ...
```

is an ordinary tail channel before the forced exponent

```text
p=1/gamma=20/9.
```

Therefore the next gate is not just "q1 is zero and q^p is formal"; it is also
whether the ordinary `q^2` channel is legal.  The new tools

```text
validators/tail_formal_recurrence.py
tools/validate_tail_recurrence.py
tools/tail_leading_exponent.py
tools/profile_zero_q2_trace.py
```

make this explicit.

On both

```text
work/v117_transcheb_formal_forced.json
work/v117_transcheb_formal_origin_refit_c2_d6_a.json
```

the current recurrence gate reports

```text
ordinary_q1_F_max=0,
ordinary_q1_G_max=0,
forced_qp_coeff_error=0,
ordinary_q2_F_trace_max=1.190284161850e+00,
ordinary_q2_G_trace_max=5.381997768582e+00,
status=UNVALIDATED_Q2_TRACE_PRESENT.
```

The first nonzero audited correction is thus ordinary `q^2`, not the forced
`q^p` block.  Unless a formal recurrence proves that `q^2` is legal, the proof
ansatz must set

```text
F_an(0,x)=0,
G_an(0,x)=0.
```

The diagnostic q2-zeroed artifacts

```text
work/v117_transcheb_formal_forced_q2zero.json
work/v117_transcheb_formal_origin_refit_c2_d6_a_q2zero.json
```

reduce the q2 trace to roundoff:

```text
ordinary_q2_F_trace_max=1.804112415016e-16,
ordinary_q2_G_trace_max=7.771561172376e-16,
status=TAIL_FORMAL_RECURRENCE_GATE_OK_NOT_INTERVAL.
```

At the sampled gates, zeroing q2 does not worsen the focused or strict-tail
residuals:

```text
focused normalized-structural max remains 1.016228983517e+01
for the origin-refit artifact;

strict-tail max remains 2.287165521365e+01.
```

So the next hard two-chart solver should start from q2-free data unless the
formal tail recurrence validator later proves the ordinary `q^2` channel is
admissible.  This is still not a proof certificate; it is a stricter ansatz
gate that prevents the solver from using an unvalidated escape channel.

The profile validation gates are:

```text
||E_gamma(F,G)|| < 1e-8 initially,
grid convergence 18 -> 32 -> 48,
tail plateau delta_eff(rho) ~= delta_j,
projection c_j(rho) ~ rho^(-delta_j),
Newton-Kantorovich validation of the exact zero.
```

## 7. Matching Determinant

After symmetry, normalization, and gauge constraints, define

```text
J(gamma,B) = inf_{F,G} ||E_gamma(F,G)||^2.
```

Residual dips are not enough. The analytic object is a Lyapunov-Schmidt determinant.

Let

```text
D_{F,G}E_gamma : X -> Y.
```

Split

```text
X = K op X_1,
Y = C op Y_1,
```

where `K` is the finite-dimensional approximate kernel and `C` is the cokernel. Solve

```text
P_{Y_1} E_gamma(F,G) = 0
```

for the infinite-dimensional correction. The remaining equation is

```text
M(gamma,B,a) = 0,
```

where `a` are indicial amplitudes. Then

```text
D_match(gamma,B) = det D_a M
```

or `D_match = M` in the scalar case.

An isolated branch must satisfy

```text
D_match(gamma_n,B_n) = 0,
partial_gamma D_match(gamma_n,B_n) != 0.
```

## 8. Linearized Spectrum

For a validated profile `U_*`, define

```text
L v =
- P_L[
    (1-gamma)v
    + gamma(y dot grad)v
    + (U_* dot grad)v
    + (v dot grad)U_*
  ].
```

The geometric modes must appear with correct multiplicity:

```text
mu = 1       time translation,
mu = gamma   spatial translations,
mu = 0       rotations, branch, and gauge modes as applicable.
```

The spectral package needed for Navier-Stokes closure is

```text
sigma(L) cap {Re z >= 0}
= {mu_1,...,mu_m} union geometric neutral modes,
mu_j > 0,
rank P_+ = m < infinity,
sigma(L|stable) subset {Re z <= -c}.
```

For validation, construct an Evans or determinant function `D_spec(mu)` and use a winding count:

```text
wind_{partial Omega} D_spec
```

to count eigenvalues in the unstable region, subtracting the geometric modes.

A first rough executable scaffold now exists at
`tools/linearized_spectrum_probe.py`. It loads a compactified seed and, when
`numpy` is available, builds a small finite-difference Jacobian of the current
`axisym_residual.residual_at` map with respect to nodal `psi/Gamma`
perturbations. This is not the projected linearized Navier-Stokes operator and
does not check the geometric modes; it is only a diagnostic placeholder so the
spectral work has an executable starting point.

## 9. Moving Outer Truncation Lemma

Let

```text
U_*(y) ~ r^(-a),  a = 1/gamma - 1,
1 < a < 3/2.
```

Let

```text
U_R(s,y) = chi(|y|/R(s)) U_*(y),
R(s) = R_0 exp(kappa(s-s_0)),
0 < kappa < gamma.
```

The physical support scale is

```text
tau^gamma R(s) = e^(-gamma s) R_0 e^(kappa(s-s_0)),
```

which shrinks as `s -> infinity` if `kappa < gamma`.

The cutoff residual is supported in

```text
A_R = {R <= |y| <= 2R}.
```

On `A_R`,

```text
|U_*| <= C R^(-a),
|grad U_*| <= C R^(-a-1),
|partial^m U_*| <= C_m R^(-a-m).
```

For the weighted space

```text
||f||_{H^8_1}^2 =
sum_{|alpha| <= 8} int |partial^alpha f|^2 <y>^(-2) dy,
```

the zero-derivative annular scaling is

```text
||R^(-a) 1_{A_R}||_{L^2(<y>^-2)}
~ R^(-a) R^(-1) R^(3/2)
= R^(1/2-a).
```

Since `a = 1/gamma - 1`,

```text
1/2 - a = 3/2 - 1/gamma < 0.
```

Higher derivatives improve the exponent. Hence the dominant gluing bound is

```text
||G_R(s)||_{H^8_1}
<= C R(s)^(3/2 - 1/gamma)
= C R_0^(-(1/gamma - 3/2))
   exp(-kappa(1/gamma - 3/2)(s-s_0)).
```

The nonlinear cutoff residual has pointwise size `R^(-2a-1)`, so its weighted norm is

```text
R^(-2a-1) R^(-1) R^(3/2)
= R^(-2a - 1/2),
```

which is smaller. The viscous profile forcing has

```text
Delta U_R ~ R^(-a-2)
```

and therefore

```text
||nu e^(-(1-2gamma)s) Delta U_R||_{H^8_1}
<= C nu e^(-(1-2gamma)s) R(s)^(-a-3/2)
= C nu e^(-(1-2gamma)s) R(s)^(-1/gamma - 1/2).
```

This is integrable in renormalized time.

## 10. Divergence and Pressure Repair

The cutoff field is not divergence-free:

```text
div(chi_R U_*) = grad chi_R dot U_*.
```

This defect is supported in `A_R` and has size

```text
|grad chi_R dot U_*| <= C R^(-a-1).
```

A Bogovskii correction `B_R` on the annulus solves

```text
div B_R = -grad chi_R dot U_*,
supp B_R subset A_R,
|partial^m B_R| <= C_m R^(-a-m).
```

Set

```text
tilde U_R = chi_R U_* + B_R.
```

Then `div tilde U_R = 0`, and the correction has the same annular size as the truncated tail.

Pressure nonlocality is handled by moment cancellation. The annular pressure leakage into the core is generated by

```text
S_R = partial_i partial_j(tilde U_R^i tilde U_R^j - U_*^i U_*^j),
grad P_ann(y) = int_{A_R} K(y-z) S_R(z) dz,
|K(z)| <= C|z|^(-4).
```

For bounded `y` and `z in A_R`, the crude bound gives

```text
|grad P_ann(y)| <= C R^(-4) R^3 R^(-2a) = C R^(-2a-1).
```

If a stronger decay rate is needed, add divergence-free annular jets so that

```text
int_{A_R} z^ell S_R(z) dz = 0,  |ell| <= N.
```

Then the kernel expansion gives

```text
|grad P_ann(y)| <= C_N R^(-2a-1-N).
```

Thus pressure leakage can be made subordinate to the Lyapunov-Perron decay rate if the finite moment map from annular jets to moments has a uniformly bounded right inverse.

## 11. Conditional Saddle-Core Navier-Stokes Theorem

Assume the following package.

### H1. Profile

There exists a nonzero boundary-free Euler profile `(U_*,P_*,gamma)` with

```text
2/5 < gamma < 1/2,
(1-gamma)U_* + gamma y dot grad U_*
+ (U_* dot grad)U_* + grad P_* = 0,
div U_* = 0.
```

### H2. Tail and Smooth Core

For some smooth nonzero angular field `H`,

```text
U_*(y) = r^(1 - 1/gamma)H(y/r) + O(r^(1 - 1/gamma - delta)),
delta > 0,
```

with enough conormal derivatives, and `U_*` is smooth on finite `y`.

### H3. Spectral Dichotomy

The linearized operator

```text
L v =
- P_L[
    (1-gamma)v
    + gamma y dot grad v
    + U_* dot grad v
    + v dot grad U_*
  ]
```

has finitely many non-geometric unstable eigenvalues and a stable gap after modulating all geometric modes:

```text
sigma(L) cap {Re z >= 0}
= {mu_1,...,mu_m} union neutral geometric modes,
mu_j > 0,
rank P_+ = m,
||e^{sL}P_s||_{X -> X} <= C e^(-cs).
```

### H4. Nonlinear Estimates

In the tail-subtracted perturbation space `X` based on `H^8_1`,

```text
||P_L((v dot grad)v)||_X <= C||v||_X^2,
||P_L((U_* dot grad)v + (v dot grad)U_*)||_X <= C||v||_X,
```

and the pressure/Riesz operators are bounded.

### H5. Gluing Corrections

The moving cutoff, Bogovskii repair, and finitely many pressure moment correctors produce a divergence-free approximate profile `tilde U_R(s)` such that

```text
||G_R(s)||_X <= C e^(-a_g(s-s_0)),
a_g = kappa(1/gamma - 3/2) > 0,
```

and

```text
||nu e^(-(1-2gamma)s) Delta tilde U_R(s)||_X
<= C nu e^(-(1-2gamma)s) R(s)^(-1/gamma - 1/2).
```

### Conclusion

For sufficiently large `s_0`, sufficiently large `R_0`, and sufficiently small stable perturbation, there is a codimension-`m` manifold of smooth divergence-free finite-energy Navier-Stokes initial data whose solutions blow up at time `T` with

```text
u(t,x) =
(T-t)^(-(1-gamma))
[U_*((x-x_*)/(T-t)^gamma) + o_X(1)],
```

and

```text
||grad_x u(t)||_{L^infty} ~ (T-t)^(-1).
```

### Proof

Write

```text
V(s,y) = tilde U_R(s,y) + v(s,y).
```

The perturbation equation is

```text
partial_s v =
L_R v
+ N(v)
+ nu e^(-(1-2gamma)s)P_L Delta(tilde U_R + v)
+ G_R(s)
+ M_mod(s),
```

where `M_mod` is the sum of time, center, rotation, and branch modulation terms.

Decompose

```text
v(s) = sum_{j=1}^m a_j(s) psi_j + w(s),
<w(s), psi_j^*> = 0.
```

The unstable coordinates satisfy

```text
a_j'(s) = mu_j a_j(s) + F_j(v,s).
```

Impose the Lyapunov-Perron condition

```text
a_j(s_0) =
- int_{s_0}^infty e^(-mu_j(sigma-s_0)) F_j(v,sigma) d sigma.
```

The stable component satisfies

```text
w(s) =
e^{(s-s_0)L_s}w(s_0)
+ int_{s_0}^s e^{(s-sigma)L_s}P_s F(v,sigma) d sigma.
```

Let

```text
||v||_{X_omega} = sup_{s >= s_0} e^{omega(s-s_0)}||v(s)||_X.
```

Choose

```text
0 < omega < (1/2)min{c, 1-2gamma, a_g}.
```

Using H3-H5,

```text
||N(v(s))||_X <= C||v(s)||_X^2,
||G_R(s)||_X <= C e^(-a_g(s-s_0)),
||nu e^(-(1-2gamma)s)Delta tilde U_R||_X
  <= C nu e^(-(1-2gamma)s_0) e^(-a_v(s-s_0)),
```

with `a_v > 0`. Thus

```text
||Phi(v)||_{X_omega}
<= C||w(s_0)||_X
 + C||v||_{X_omega}^2
 + C nu e^(-(1-2gamma)s_0)
 + C R_0^(-(1/gamma - 3/2)).
```

The same estimates applied to `Phi(v_1)-Phi(v_2)` give

```text
||Phi(v_1)-Phi(v_2)||_{X_omega}
<= C( ||v_1||_{X_omega} + ||v_2||_{X_omega}
      + nu e^(-(1-2gamma)s_0) )
   ||v_1-v_2||_{X_omega}.
```

For small ball radius `M`, large `s_0`, and large `R_0`, this is a contraction. The fixed point gives

```text
||v(s)||_X <= C M e^(-omega(s-s_0)).
```

The unstable initial coordinates are exactly the graph values specified by the Lyapunov-Perron integrals, so the admissible initial data form a codimension-`m` manifold.

Returning to physical variables,

```text
u(t,x) = tau^(-(1-gamma))V(s,(x-x_*)/tau^gamma).
```

Since `V(s) -> U_*` in the core and `grad_y U_*` is not identically zero,

```text
grad_x u = tau^(-1)[grad_y U_* + o(1)].
```

Therefore `||grad_x u(t)||_infty -> infinity` as `t -> T`.

The initial datum is smooth, compactly supported up to the stable perturbation and corrected modes, divergence-free by construction, and finite-energy by the scaling in Section 3.

## 12. Exact Remaining Obstruction

The preceding theorem reduces the proof to the following concrete package.

Find `(U_*,P_*,gamma)` such that

```text
F_gamma(U_*,P_*) = 0,
2/5 < gamma < 1/2,
U_*(y) = r^(1 - 1/gamma)H(theta) + O(r^(1 - 1/gamma - delta)),
```

and the linearized operator satisfies

```text
sigma(L) cap {Re z >= 0}
= finite unstable modes union geometric modes,
||e^{sL}P_s|| <= C e^(-cs).
```

If the proof fails, the failure must occur in one of these explicit systems:

```text
1. M(H,gamma) = 0 has no finite-codimension solvable profile branch.
2. D M(H,gamma) has infinite-dimensional cokernel.
3. There exist infinitely many independent f_n with
   ||f_n||_X = 1 and ||(z_n-L)f_n||_X -> 0, Re z_n >= 0.
4. The annular pressure moment map has no uniformly bounded right inverse.
5. An anisotropic replacement violates the pressure compatibility equations.
```

Everything before this package has an explicit correction mechanism in this draft.

## 13. Next Execution Step

The first indicial shooting and matching diagnostics are now executable:

```text
python3 tools/indicial_solver.py --gamma 0.45 --B 1.0 --scan
python3 tools/indicial_survey.py --gamma 0.45 --B 1.0 --optimize --components
python3 tools/indicial_modes.py --gamma 0.45 --B 1.0 --delta-real 0.132519531250 --delta-imag 1.787841796875
python3 tools/indicial_match.py --gamma 0.45 --B 1.0 --scan
python3 tools/indicial_evans.py --gamma 0.45 --B 1.0 --scan
python3 tools/validate_indicial_evans.py --gamma 0.45 --B 1.0
```

They show one exact geometric branch, `delta=1`, and no current non-geometric root-like candidate. The production version must replace floating shooting/matching/Pluecker checks by validated interval or ball arithmetic and then feed any admissible non-geometric roots into the compactified nonlinear profile solver.

On the nonlinear profile side, the current executable checks are

```text
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-vanishing-edge-seed-v49.json \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-vanishing-edge-blend-v54.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_blend.py \
  --left profile-seeds/gamma0p45-vanishing-edge-seed-v49.json \
  --right profile-seeds/gamma0p45-vanishing-edge-shell14-seed-v53.json \
  --count 21 --best-by max-all
python3 tools/profile_tail_series.py \
  --seed-json profile-seeds/gamma0p45-vanishing-edge-blend-v54.json
python3 tools/profile_forced_tail.py \
  --gamma 0.45 --B 1.0 --b-order 8 \
  --save-json profile-seeds/gamma0p45-forced-tail-qm-v62.json
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-qm-q2solve-v64.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-richinterior-v74.json \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-richinterior-v74.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_tail_series.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-richinterior-v74.json \
  --max-order 9
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-richinterior-q6-v86.json \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-richinterior-q6-v86.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_tail_series.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-richinterior-q6-v86.json \
  --max-order 12
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-flatbumpF-blend-v91.json \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-flatbumpF-blend-v91.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v93.json \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v93.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_minimax_coordinate.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-active-flatbumpF-blend-v93.json \
  --save-json profile-seeds/gamma0p45-forced-tail-minimax-flatbumpF-v96.json \
  --passes 6 --step 2.5e-4 \
  --score-gates wide,interior,local \
  --report-gates wide,interior,local,farther
python3 tools/profile_minimax_coordinate.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v102.json \
  --save-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v103.json \
  --families f_interior_bump_coeffs,g_interior_bump_coeffs \
  --wide-n-q 29 --wide-n-b 29 \
  --interior-n-q 29 --interior-n-b 29 \
  --local-n 45 \
  --score-gates wide,interior,local,active \
  --report-gates wide,interior,local,farther,active \
  --active-qb-points '0.504,0.585;0.504,-0.585;0.414,0.315;0.414,-0.315;0.396,0.315;0.396,-0.315;0.432,0.315;0.432,-0.315;0.522,0.585;0.522,-0.585;0.486,0.585;0.486,-0.585'
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v103.json \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v103.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_residual_topology.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v103.json \
  --q-min 0.18 --q-max 0.90 --b-min -0.90 --b-max 0.90 \
  --n-q 41 --n-b 41 --top 24 --slice-top 12 --h 1e-3
python3 tools/profile_tail_series.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v103.json \
  --max-order 12
python3 tools/profile_minimax_coordinate.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v105.json \
  --save-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v106.json \
  --families f_interior_bump_coeffs,g_interior_bump_coeffs \
  --wide-n-q 29 --wide-n-b 29 \
  --interior-n-q 29 --interior-n-b 29 \
  --local-n 45 \
  --score-gates wide,interior,local,active \
  --report-gates wide,interior,local,farther,active \
  --active-qb-points '0.486,0.585;0.486,-0.585;0.468,0.585;0.468,-0.585;0.504,0.585;0.504,-0.585;0.414,0.315;0.414,-0.315;0.396,0.315;0.396,-0.315;0.522,0.450;0.522,-0.450;0.648,0.270;0.648,-0.270'
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v106.json \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_gates.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v106.json \
  --wide-q-min 0.18 --wide-q-max 0.30 \
  --wide-b-min -0.90 --wide-b-max 0.90 \
  --wide-n-q 9 --wide-n-b 17 \
  --h-values 2e-3,1e-3,5e-4
python3 tools/profile_residual_topology.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v106.json \
  --q-min 0.18 --q-max 0.90 --b-min -0.90 --b-max 0.90 \
  --n-q 41 --n-b 41 --top 24 --slice-top 12 --h 1e-3
python3 tools/profile_tail_series.py \
  --seed-json profile-seeds/gamma0p45-forced-tail-minimax-active-flatbumpFG-v106.json \
  --max-order 12
```

The admissible profile status is now:

```text
v49: best balanced admissible seed,
     standard max = 5.470627484641e-02,
     extreme max = 5.535569977138e-02,
     farther-tail max = 2.682727177003e-01.

v53/v54: best old integer-shell far-tail-focused admissible seed,
         standard max = 7.607876229271e-02,
         extreme max = 6.231594228615e-02,
         farther-tail max = 1.792056343172e-01.

v64: best asymptotically aligned forced-tail seed,
     exact q=0 trace,
     zero q^1 tail channel,
     forced q^(1/gamma) correction,
     farther-tail max = 9.016164760362e-02,
     but standard/interior/local residuals are O(1).

v72: previous balanced q1-free forced-tail seed,
     exact q=0 trace,
     zero q^1 tail channel,
     localized forced q^(1/gamma) correction,
     standard max = 6.421601684773e-01,
     farther-tail max = 4.325436706783e-01.

v74: previous balanced q1-free forced-tail seed,
     exact q=0 trace,
     zero q^1 tail channel,
     frozen forced q^(1/gamma) correction,
     standard max = 5.909176701763e-01,
     interior max = 5.932368481368e-01,
     local max = 5.930636467992e-01,
     farther-tail max = 4.169187255275e-01,
     but the q^9 ordinary tail residual is already large.

v86: previous best balanced q1-free forced-tail seed,
     exact q=0 trace,
     zero q^1 tail channel,
     frozen forced q^(1/gamma) correction,
     no ordinary q-orders 7 and above,
     standard max = 5.402426950755e-01,
     interior max = 5.413752067105e-01,
     local max = 5.417628839283e-01,
     farther-tail max = 3.977005747567e-01,
     but the q^5-q^6 ordinary tail residual remains large.

v91: previous best balanced q1-free forced-tail seed,
     exact q=0 trace,
     zero q^1 tail channel,
     frozen forced q^(1/gamma) correction,
     small tail-flat streamfunction bump component,
     standard max = 5.375808758463e-01,
     interior max = 5.385829296901e-01,
     local max = 5.388811146608e-01,
     farther-tail max = 3.989670525038e-01,
     but the residual is still O(1).

v93: previous best balanced q1-free forced-tail seed,
     exact q=0 trace,
     zero q^1 tail channel,
     frozen forced q^(1/gamma) correction,
     small tail-flat streamfunction bump component,
     standard max = 5.296559969709e-01,
     interior max = 5.273605597729e-01,
     local max = 5.294625460480e-01,
     farther-tail max = 4.016192226850e-01,
     but the residual is still O(1).

v103: previous best balanced q1-free forced-tail seed,
      exact q=0 trace,
      zero q^1 tail channel,
      frozen forced q^(1/gamma) correction,
      tail-flat streamfunction and swirl bump components,
      standard wide max = 4.595263267048e-01,
      standard interior max = 4.556840998552e-01,
      standard local max = 4.607838677803e-01,
      fine/active max = 4.608097446714e-01,
      farther-tail max = 3.884802493867e-01,
      but the residual is still O(1).

v106: previous best balanced q1-free forced-tail seed,
      exact q=0 trace,
      zero q^1 tail channel,
      frozen forced q^(1/gamma) correction,
      tail-flat streamfunction and swirl bump components,
      standard wide max = 4.525392363637e-01,
      standard interior max = 4.523133293752e-01,
      standard local max = 4.549610384871e-01,
      fine/active max = 4.550283493881e-01,
      41x41 topology max = 4.544085174837e-01,
      farther-tail max = 3.852405555391e-01,
      but the residual is still O(1).

v109: previous best balanced q1-free forced-tail seed,
      exact q=0 trace,
      zero q^1 tail channel,
      frozen forced q^(1/gamma) correction,
      expanded tail-flat streamfunction and swirl bump components,
      standard wide max = 4.361219908395e-01,
      standard interior max = 4.409139618561e-01,
      standard local max = 4.399093733579e-01,
      fine-grid max = 4.436766672136e-01,
      41x41 topology max = 4.416907956036e-01,
      farther-tail max = 3.847858590776e-01,
      but the residual is still O(1).

v111: previous best balanced q1-free forced-tail seed,
      exact q=0 trace,
      zero q^1 tail channel,
      frozen forced q^(1/gamma) correction,
      expanded tail-flat streamfunction and swirl bump components,
      standard wide max = 4.367747752125e-01,
      standard interior max = 4.396586783719e-01,
      standard local max = 4.396608030521e-01,
      fine-grid max = 4.398351490167e-01,
      41x41 topology max = 4.396417168948e-01,
      farther-tail max = 3.813442764768e-01,
      but the residual is still O(1).

v112: previous best balanced q1-free forced-tail seed,
      exact q=0 trace,
      zero q^1 tail channel,
      frozen forced q^(1/gamma) correction,
      sparse expanded tail-flat streamfunction and swirl bump components,
      standard wide max = 4.365866237926e-01,
      standard interior max = 4.395069007065e-01,
      standard local max = 4.391290054377e-01,
      fine-grid max = 4.397800969258e-01,
      41x41 topology max = 4.393817079326e-01,
      farther-tail max = 3.812707390403e-01,
      but the residual is still O(1).

v116-lowb: previous best balanced q1-free forced-tail seed,
           exact q=0 trace,
           zero q^1 tail channel,
           frozen forced q^(1/gamma) correction,
           sparse high-|b| and low-|b| tail-flat bump corrections,
           standard max = 4.378239756763e-01,
           shifted max = 4.384766750064e-01,
           fine-grid max = 4.388424241734e-01,
           broad shifted topology max = 4.370460732359e-01,
           old high-|b| holdout-box max = 4.354896703956e-01,
           far-tail holdout max = 4.091040786189e-01,
           but the residual is still O(1).

v117 ridge-strip final: current best balanced q1-free forced-tail diagnostic seed,
                       exact q=0 trace,
                       zero q^1 tail channel,
                       frozen forced q^(1/gamma) correction,
                       ridge-strip sparse tail-flat bump corrections,
                       standard max = 4.344070020656e-01,
                       shifted max = 4.364874143437e-01,
                       fine-grid max = 4.362251080302e-01,
                       41x41 topology max = 4.347549502774e-01,
                       focused hidden-ridge max = 4.364654153641e-01,
                       secondary q ~= 0.608, |b| ~= 0.241 max = 4.350113142226e-01,
                       but the residual is still O(1) and the Chebyshev projection
                       fails the origin Taylor gate.
```

The v49-to-v53 blend scan does not find a better interior compromise: the
max-over-gates optimum is exactly the v53 endpoint, saved as v54. The
tail-series and forced-tail diagnostics then show why unconstrained integer
shells are the wrong asymptotic representation: they rely on a forbidden q1
channel. The localized, richer, order-capped, active-weighted, expanded-grid,
max-aware, sparse high-`|b|`, sparse low-`|b|`, and ridge-strip tail-flat-bump
continuations improve the constrained interior balance but remain far from
validation. The next proof-relevant improvement is a richer
interior/asymptotic matching basis in the framework of v64/v117, together with
a validated non-geometric indicial determinant.

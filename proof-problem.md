[
\boxed{
\text{Do not localize the growing conical core.}
}
]

Instead, use the conical core only as a rigid inner/asymptotic fixed point. The actual singular profile must have a nonconical radial tail

[
U_*(y)\sim |y|^{1-\frac1\gamma},
]

and the finite-energy Navier-Stokes construction must use a moving outer truncation of that decaying tail. That is the clean “NSS new paradigm” route.

The proof architecture is:

[
\boxed{
\text{conical rigidity}
\rightarrow
\text{indicial classification}
\rightarrow
\text{nonlinear profile matching}
\rightarrow
\text{spectral index}
\rightarrow
\text{finite-energy NS gluing}
\rightarrow
\text{Lyapunov-Perron closure}.
}
]

---

# 0. Final target theorem package

The complete program should aim at the following theorem package.

### Theorem A: Conical rigidity

Exact conical axisymmetric-with-swirl self-similar Euler profiles in the (\gamma\in(2/5,1/2)) regime cannot produce the observed singular hierarchy. Dimensional consistency forces

[
\psi=r^3f(z/r),
\qquad
\Gamma=r^2g(z/r),
]

so

[
U(\lambda y)=\lambda U(y).
]

Thus exact conical profiles either reduce to the (\gamma)-independent linear-strain branch

[
u^r=-\frac r2,
\qquad
u^z=z,
\qquad
u^\theta=Br,
]

or to admissibility-excluded branches. Therefore any true (\gamma)-dependent singular profile must contain nonconical radial corrections.

### Theorem B: Indicial funnel theorem

All sufficiently regular profiles asymptotic to the conical core admit a Frobenius expansion

[
\psi
====

\frac12r^2z
+
\sum_j a_j r^{3-\delta_j}\phi_j(z/r)
+
\sum_{i,j}a_ia_jr^{3-\delta_i-\delta_j}\phi_{ij}(z/r)
+\cdots,
]

[
\Gamma
======

Br^2
+
\sum_j a_j r^{2-\delta_j}\chi_j(z/r)
+
\sum_{i,j}a_ia_jr^{2-\delta_i-\delta_j}\chi_{ij}(z/r)
+\cdots,
]

where the admissible (\delta_j) are roots of an indicial determinant

[
D_{\rm ind}(\delta;\gamma,B)=0.
]

Logarithmic terms appear exactly at resonances

[
\delta_k=\delta_i+\delta_j.
]

### Theorem C: Nonlinear matching and rate quantization

After fixing normalization and geometric symmetries, global self-similar profiles exist only at zeros of a matching determinant

[
D_{\rm match}(\gamma,B)=0.
]

Generically these zeros are isolated:

[
D_{\rm match}(\gamma_n,B_n)=0,
\qquad
\partial_\gamma D_{\rm match}(\gamma_n,B_n)\neq0.
]

This gives a discrete hierarchy

[
\gamma_0,\gamma_1,\gamma_2,\ldots .
]

### Theorem D: Spectral index theorem

For the profile (U_n) at (\gamma_n), the number of non-geometric unstable eigenvalues of the renormalized linearized operator equals the matching index:

[
\boxed{
#{\Re\mu>0:\mu\text{ non-geometric}}
====================================

# \operatorname{Maslov}(U_n)

n.
}
]

This is the analytic form of the instability-order hierarchy.

### Theorem E: Blow-up-rate law

The admissible rates satisfy a phase quantization law

[
\Theta(\gamma_n)=\pi(n+\kappa)+o(1),
]

and this implies the Wang-type empirical law after translating their parameter into (\gamma). In the simplest case,

[
\frac1{\lambda_n}
=================

an+b+o(1).
]

### Theorem F: Conditional finite-energy Navier-Stokes closure

Assume (U_n) exists, has the natural tail

[
U_n(y)\sim |y|^{1-\frac1{\gamma_n}},
]

and the projected stable spectrum has a gap. Then, after modulating all unstable and geometric directions, one constructs finite-energy Navier-Stokes data whose rescaled solution remains close to the moving-truncated profile and blows up with rate (\gamma_n).

This is the full “NSS new paradigm” theorem.

---

# 1. Core variables and equations

Work with axisymmetric-with-swirl variables

[
U=u^r e_r+u^\theta e_\theta+u^z e_z,
]

[
u^r=-\frac{\psi_z}{r},
\qquad
u^z=\frac{\psi_r}{r},
\qquad
\Gamma=ru^\theta.
]

Define

[
A=\psi_{rr}-\frac1r\psi_r+\psi_{zz}.
]

The pressure-eliminated self-similar Euler profile equations are

[
\boxed{
(1-\gamma)r^2A
+
\gamma r^3A_r
+
\gamma zr^2A_z
+
r(\psi_rA_z-\psi_zA_r)
+
2\psi_zA
+
(\Gamma^2)_z
=0,
}
]

[
\boxed{
(1-2\gamma)\Gamma
+
\gamma(r\Gamma_r+z\Gamma_z)
+
\frac1r(\psi_r\Gamma_z-\psi_z\Gamma_r)
=0.
}
]

These two equations are the base object for all stages.

---

# 2. Stage 0: prove conical rigidity

Use

[
\psi=r^a f(\zeta),
\qquad
\Gamma=r^b g(\zeta),
\qquad
\zeta=\frac zr.
]

Velocity scales as

[
u^r,u^z\sim r^{a-2},
\qquad
u^\theta\sim r^{b-1}.
]

The profile equation requires equality of the linear and nonlinear homogeneities:

[
a-2=2a-5=2b-3.
]

Therefore

[
\boxed{
a=3,
\qquad
b=2.
}
]

Hence every exact conical profile has

[
U(\lambda y)=\lambda U(y).
]

But true finite-physical-energy self-similar profiles in the window

[
\gamma\in(2/5,1/2)
]

have natural tail

[
\boxed{
U(y)\sim |y|^{1-\frac1\gamma}.
}
]

Since

[
1-\frac1\gamma<-1
]

for (\gamma<1/2), the natural tail is decaying. Exact conical profiles grow like (|y|). Thus exact conical structure is incompatible with the desired outer asymptotics.

This proves the negative structural constraint:

[
\boxed{
\text{true profiles must leave the conical manifold through nonhomogeneous modes.}
}
]

---

# 3. Stage 0.5: derive the indicial pencil

Linearize around the exact conical core

[
\psi_*=\frac12r^2z,
\qquad
\Gamma_*=Br^2.
]

Write

[
\psi=\psi_*+\varepsilon\Psi,
\qquad
\Gamma=\Gamma_*+\varepsilon G.
]

Let

[
a=\Psi_{rr}-\frac1r\Psi_r+\Psi_{zz}.
]

The linearized equations are

[
\boxed{
\left(\gamma-\frac12\right)ra_r
+
(\gamma+1)za_z
+
(2-\gamma)a
+
2BG_z
=0,
}
]

[
\boxed{
\left(\gamma-\frac12\right)rG_r
+
(\gamma+1)zG_z
+
(1-2\gamma)G
------------

2B\Psi_z
=0.
}
]

Now set

[
\Psi=r^{3-\delta}\phi(\zeta),
\qquad
G=r^{2-\delta}\chi(\zeta),
\qquad
\zeta=\frac zr.
]

Let

[
\alpha=\frac12-\gamma>0.
]

Then

[
a=r^{1-\delta}h,
]

with

[
\boxed{
h
=

## (1+\zeta^2)\phi''

(3-2\delta)\zeta\phi'
+
(3-\delta)(1-\delta)\phi.
}
]

The indicial system is

[
\boxed{
\frac32\zeta h'
+
\left(\frac32+\alpha\delta\right)h
+
2B\chi'
=0,
}
]

[
\boxed{
\frac32\zeta\chi'
+
\alpha\delta\chi
----------------

2B\phi'
=0.
}
]

Together with the definition of (h), this is the indicial pencil

[
\boxed{
\mathcal I_{\gamma,B}(\delta)
\begin{pmatrix}
\phi\
\chi
\end{pmatrix}
=0.
}
]

The determinant

[
\boxed{
D_{\rm ind}(\delta;\gamma,B)=0
}
]

defines the admissible escape directions from conical rigidity.

---

# 4. Stage 0.75: Frobenius boundary data

At (\zeta=0), impose the symmetry structure

[
\phi(-\zeta)=-\phi(\zeta),
\qquad
\chi(-\zeta)=\chi(\zeta).
]

Use

[
\phi(\zeta)=p\zeta+p_3\zeta^3+O(\zeta^5),
]

[
\chi(\zeta)=1+q_2\zeta^2+O(\zeta^4).
]

The indicial equations give

[
\boxed{
p=\frac{\alpha\delta}{2B}.
}
]

The next coefficients are

[
\boxed{
q_2=\frac{6Bp_3}{3+\alpha\delta},
}
]

[
\boxed{
p_3
===

*

\frac{(3+\alpha\delta)^2\delta(\delta-2)p}
{
6\left[(3+\alpha\delta)^2+4B^2\right]
}.
}
]

So the numerical indicial solver should start at (\zeta=\varepsilon) with

[
\phi(\varepsilon)=p\varepsilon+p_3\varepsilon^3,
]

[
\phi'(\varepsilon)=p+3p_3\varepsilon^2,
]

[
\chi(\varepsilon)=1+q_2\varepsilon^2,
]

[
\chi'(\varepsilon)=2q_2\varepsilon.
]

At (|\zeta|\to\infty), axis regularity imposes

[
\phi(\zeta)\sim C_\phi\zeta^{1-\delta},
]

[
\chi(\zeta)\sim C_\chi\zeta^{-\delta}.
]

Thus

[
\boxed{
\zeta\phi'-(1-\delta)\phi\to0,
}
]

[
\boxed{
\zeta\chi'+\delta\chi\to0.
}
]

The amplitude relation is

[
\boxed{
2B(1-\delta)C_\phi+\delta(1+\gamma)C_\chi=0.
}
]

These conditions define the admissible indicial spectrum.

---

# 5. Stage 1: full 2D profile construction

Do not solve in raw ((r,z)) variables for the final version. Use compactified coordinates.

Let

[
\rho=(r^2+z^2)^{1/2},
\qquad
\beta=\frac z\rho\in[-1,1],
]

[
q=(1+\rho^2)^{-1/2}\in[0,1].
]

Then

[
q=0
]

is infinity,

[
q=1
]

is the origin,

[
\beta=\pm1
]

is the symmetry axis.

Use the tail-factored ansatz

[
\boxed{
\psi
====

r^2z,q^{1/\gamma}F(q,\beta),
}
]

[
\boxed{
\Gamma
======

r^2q^{1/\gamma}G(q,\beta).
}
]

Since

[
q^{1/\gamma}\sim \rho^{-1/\gamma},
]

this gives

[
U(y)\sim |y|^{1-\frac1\gamma}.
]

This is the correct natural self-similar tail.

For (\gamma=0.45),

[
1-\frac1\gamma
==============

-1.222222\ldots .
]

Thus

[
U(y)\sim |y|^{-1.222222\ldots}.
]

The profile is not (L^2_y), but it belongs to

[
H^8_1
]

because

[
\frac52-\frac1\gamma<1
]

for (\gamma\in(2/5,1/2)).

The parity conditions are

[
F(q,-\beta)=F(q,\beta),
]

[
G(q,-\beta)=G(q,\beta).
]

The (r^2) and (r^2z) factors enforce axis regularity.

---

# 6. Stage 1 seed from the indicial funnel

The indicial seed becomes

[
\boxed{
F_{\rm init}
============

\frac12
+
c q^\delta(1-\beta^2)^{-\delta/2}
\frac{
\phi\left(\frac{\beta}{\sqrt{1-\beta^2}}\right)
}{
\frac{\beta}{\sqrt{1-\beta^2}}
},
}
]

[
\boxed{
G_{\rm init}
============

B
+
c q^\delta(1-\beta^2)^{-\delta/2}
\chi\left(\frac{\beta}{\sqrt{1-\beta^2}}\right).
}
]

This is finite at (\beta=\pm1) exactly when the far-field indicial behavior is admissible.

Run the full residual minimization with

[
\mathcal E_\gamma(F,G)=0.
]

The target numerical gates are:

[
\boxed{
|\mathcal E_\gamma(F,G)|<10^{-8},
}
]

[
\boxed{
N_r,N_z:18\to32\to48
\quad\text{profile convergence},
}
]

[
\boxed{
\gamma\in{0.42,0.44,0.45,0.47}
\quad\text{rate scan}.
}
]

But residual collapse is not enough. Also verify the extracted tail.

Define

[
\delta_{\rm eff}(\rho)
======================

-\partial_{\log\rho}
\log
|\Phi(\rho,\cdot)-\Phi_{\rm cone}(\cdot)|*{L^2*\beta}.
]

A valid profile must show a plateau

[
\boxed{
\delta_{\rm eff}(\rho)\approx \delta_j
}
]

for one of the indicial roots.

Project onto indicial eigenfunctions:

[
c_j(\rho)
=========

\langle
\Phi(\rho,\cdot)-\Phi_{\rm cone}(\cdot),
\Phi_j(\cdot)
\rangle.
]

Then check

[
\boxed{
c_j(\rho)\sim \rho^{-\delta_j}.
}
]

This proves the numerical profile lies inside the analytically admissible funnel.

---

# 7. Stage 1 matching determinant

After normalization and symmetry fixing, define

[
J(\gamma,B)
===========

\inf_{F,G}
|\mathcal E_\gamma(F,G)|^2.
]

Residual dips identify candidates, but the analytic object is a determinant:

[
\boxed{
D_{\rm match}(\gamma,B).
}
]

Construct it through Lyapunov-Schmidt reduction.

Let

[
D_{F,G}\mathcal E_\gamma
]

be the linearized profile map. Split

[
X=K\oplus X_1,
]

where (K) is the finite-dimensional approximate kernel, and split the range

[
Y=C\oplus Y_1,
]

where (C) is the cokernel.

Solve the range equation

[
P_{Y_1}\mathcal E_\gamma(F,G)=0
]

for the infinite-dimensional correction.

The remaining finite-dimensional equation is

[
\boxed{
M(\gamma,B,a)=0,
}
]

where (a) are indicial coefficients.

Then

[
D_{\rm match}
=============

\det D_aM
]

or, in the scalar case,

[
D_{\rm match}=M.
]

A branch is isolated when

[
\boxed{
D_{\rm match}(\gamma_n,B_n)=0,
}
]

[
\boxed{
\partial_\gamma D_{\rm match}(\gamma_n,B_n)\neq0.
}
]

If a continuous family appears, compute the smallest singular values of

[
D_{F,G}\mathcal E_\gamma.
]

A genuine family must produce a true zero mode

[
D_{F,G}\mathcal E_\gamma[\partial_\gamma F,\partial_\gamma G]
+
\partial_\gamma\mathcal E_\gamma=0.
]

If no such zero mode exists, the apparent family is numerical degeneracy.

---

# 8. Stage 2: spectral solver

For a full profile (U_*), define

[
Lv
==

-\mathbb P\left[
(1-\gamma)v
+
\gamma(y\cdot\nabla)v
+
(U_*\cdot\nabla)v
+
(v\cdot\nabla)U_*
\right].
]

The perturbation class must be chosen.

For axisymmetric stability, use only (m=0) perturbations. The geometric modes are:

[
\boxed{
\mu=1
\quad\text{time mode},
}
]

[
\boxed{
\mu=\gamma
\quad\text{axial translation},
}
]

[
\boxed{
\mu=0
\quad\text{branch/swirl amplitude if present}.
}
]

For full 3D stability, decompose

[
v(r,\theta,z)=\sum_{m\in\mathbb Z}v_m(r,z)e^{im\theta}.
]

Then the geometric modes are:

[
\boxed{
\mu=1
\quad\text{time mode},
}
]

[
\boxed{
\mu=\gamma
\quad\text{three translations},
}
]

[
\boxed{
\mu=0
\quad\text{rotations and branch modes}.
}
]

The axisymmetric and full 3D instability counts must be separated:

[
\boxed{
n_{\rm ax}
==========

#{\Re\mu>0:\mu\text{ non-geometric in }m=0},
}
]

[
\boxed{
n_{\rm 3D}
==========

\sum_{m\ge0}
#{\Re\mu_{m,j}>0:\mu_{m,j}\text{ non-geometric}}.
}
]

The sanity check is strict:

If the solver does not reproduce

[
\mu=1,
\qquad
\mu=\gamma,
\qquad
\mu=0
]

with correct multiplicities for the chosen perturbation class, the spectral computation is invalid.

---

# 9. Stage 2.5: spectral index and rate law

Do not rely only on a raw eigenvalue count. Define an Evans determinant

[
D_{\rm spec}(\mu).
]

Then

[
\operatorname{wind}*{\partial\Omega}D*{\rm spec}
]

counts eigenvalues in (\Omega).

Define the non-geometric instability index by

[
\boxed{
\operatorname{ind}(U_*)
=======================

## \operatorname{wind}*{\partial\Omega*+}D_{\rm spec}

\operatorname{ind}_{\rm geom}.
}
]

The target theorem is

[
\boxed{
\operatorname{ind}(U_n)=n.
}
]

To derive the empirical rate law, work in logarithmic radius

[
\tau=\log\rho.
]

The far-field equation becomes

[
\partial_\tau W
===============

\mathcal A_\gamma W+\mathcal N(W).
]

Indicial modes satisfy

[
W\sim e^{-\delta\tau}\Phi_\delta.
]

If the relevant roots are complex,

[
\delta_\pm(\gamma)=a(\gamma)\pm i\kappa(\gamma),
]

then the profile accumulates phase

[
\Theta(\gamma)
==============

\int \kappa(\gamma,\tau),d\tau.
]

Matching imposes

[
\boxed{
\Theta(\gamma_n)=\pi(n+\kappa_0)+o(1).
}
]

If

[
\Theta(\gamma)\sim \frac{C}{\lambda(\gamma)},
]

then

[
\boxed{
\frac1{\lambda_n}
=================

an+b+o(1).
}
]

This is the analytic explanation of the instability-order/blow-up-rate hierarchy.

In the current notation, the amplitude blow-up exponent is

[
1-\gamma.
]

So faster blow-up corresponds to smaller (\gamma). If Wang’s notation uses (\lambda), translate by the exact scaling convention before comparing.

---

# 10. Stage 3: Navier-Stokes finite-energy closure

This is the new paradigm piece.

Do not compactly localize the growing conical core. That created the previous obstruction.

Instead, take the decaying natural-tail profile

[
U_*(y)\sim |y|^\beta,
\qquad
\beta=1-\frac1\gamma<-1.
]

Then apply a moving outer cutoff

[
U_R(y,s)=\chi\left(\frac{|y|}{R(s)}\right)U_*(y),
]

where

[
R(s)=R_0e^{\kappa(s-s_0)},
\qquad
0<\kappa<\gamma.
]

The condition (\kappa<\gamma) ensures that the physical support scale

[
(T-t)^\gamma R(s)
]

does not expand uncontrollably.

The rescaled Navier-Stokes equation is

[
\partial_sV
+
(1-\gamma)V
+
\gamma(y\cdot\nabla)V
+
(V\cdot\nabla)V
+
\nabla P
========

\nu e^{-(1-2\gamma)s}\Delta V.
]

Write

[
V=U_R(s)+v.
]

Then

[
\partial_sv
===========

L_Rv
+
N(v)
+
\nu e^{-(1-2\gamma)s}\mathbb P\Delta(U_R+v)
+
G_R(s),
]

where

[
G_R
===

## -\partial_sU_R

\mathbb P\left[
(1-\gamma)U_R
+
\gamma(y\cdot\nabla)U_R
+
(U_R\cdot\nabla)U_R
\right].
]

Because (U_*) solves the exact profile equation, (G_R) is supported only in the cutoff annulus

[
R(s)\lesssim |y|\lesssim 2R(s).
]

Now compute the gluing size.

On the annulus,

[
|U_*|\sim R^\beta,
]

[
|\nabla U_*|\sim R^{\beta-1}.
]

The cutoff-generated linear/scaling residual has size

[
R^\beta.
]

The nonlinear cutoff residual has size

[
R^{2\beta-1},
]

which is smaller because (\beta<-1).

The moving cutoff term satisfies

[
|\partial_sU_R|
\lesssim
\frac{R'(s)}{R(s)}R^\beta
=========================

\kappa R^\beta.
]

Thus the dominant gluing size is

[
|G_R|\lesssim R^\beta.
]

In

[
X=H^8_1,
]

the weight is

[
\langle y\rangle^{-2}.
]

The annulus volume factor gives

[
|G_R(s)|_X
\lesssim
R(s)^{\beta+\frac32-1}
======================

R(s)^{\beta+\frac12}.
]

Since

[
\beta=1-\frac1\gamma,
]

we get

[
\boxed{
|G_R(s)|_{H^8_1}
\lesssim
R(s)^{\frac32-\frac1\gamma}.
}
]

For (\gamma\in(2/5,1/2)),

[
\frac32-\frac1\gamma<0.
]

For (\gamma=0.45),

[
\frac32-\frac1\gamma
====================

# 1.5-2.222222\ldots

-0.722222\ldots .
]

So

[
\boxed{
|G_R(s)|_{H^8_1}
\lesssim
R_0^{-\left(\frac1\gamma-\frac32\right)}
e^{-\kappa\left(\frac1\gamma-\frac32\right)(s-s_0)}.
}
]

This is the key fix. The gluing error decays in a pressure-compatible space.

The viscous profile forcing satisfies

[
\Delta U_*\sim R^{\beta-2}.
]

Therefore

[
|\Delta U_R|_{H^8_1}
\lesssim
R^{\beta-\frac12-1}
===================

# R^{\frac12-\frac1\gamma-1}

R^{-\frac12-\frac1\gamma}.
]

Thus

[
\boxed{
|\nu e^{-(1-2\gamma)s}\Delta U_R|_{H^8_1}
\lesssim
\nu e^{-(1-2\gamma)s}
R(s)^{-\frac12-\frac1\gamma}.
}
]

This is strongly decaying.

---

# 11. Stage 3 function space

Use

[
\boxed{
X=H^8_1(\mathbb R^3),
}
]

with

[
|v|_X^2
=======

\sum_{|\alpha|\le8}
\int_{\mathbb R^3}
|\partial^\alpha v(y)|^2
\langle y\rangle^{-2},dy.
]

The weight

[
\langle y\rangle^{-2}
]

belongs to (A_2), so Calderón-Zygmund theory gives

[
\boxed{
|\mathbb P f|_X\le C|f|_X.
}
]

The pressure correction is controlled because Riesz transforms are bounded in this space.

The nonlinear term satisfies

[
N(v)=-\mathbb P[(v\cdot\nabla)v],
]

and weighted Moser estimates give

[
\boxed{
|N(v_1)-N(v_2)|_X
\le
C(|v_1|_X+|v_2|_X)|v_1-v_2|_X.
}
]

The linear pressure term is

[
\nabla q_L
==========

\nabla(-\Delta)^{-1}
\left[
\partial_iU_R^j\partial_jv^i
+
\partial_iv^j\partial_jU_R^i
\right].
]

Since

[
\nabla U_*\sim |y|^{-1/\gamma},
]

and

[
\frac1\gamma>2,
]

(\nabla U_*) is a decaying multiplier. Therefore

[
\boxed{
|\nabla q_L(v)|_X\le C|v|_X.
}
]

---

# 12. Stage 3 modulation system

Let (\Phi_j) be all unstable and neutral modes, including geometric modes.

Decompose

[
v(s)
====

\sum_{j=1}^J a_j(s)\Phi_j+w(s),
]

with orthogonality

[
\boxed{
\langle w(s),\Psi_j\rangle_X=0,
}
]

where (\Psi_j) are adjoint modes.

The unstable coordinates satisfy

[
a_j'(s)
=======

\mu_ja_j(s)+F_j(s),
]

with

[
F_j(s)
======

\left\langle
\Psi_j,
N(v)
+
\nu e^{-(1-2\gamma)s}\mathbb P\Delta(U_R+v)
+
G_R(s)
+
\mathcal M(s)
\right\rangle_X.
]

Here (\mathcal M(s)) contains modulation terms from time shift, spatial center, rotation, and branch parameters.

For (\Re\mu_j>0), impose

[
\boxed{
a_j(s_0)
========

-\int_{s_0}^\infty
e^{-\mu_j(\sigma-s_0)}
F_j(\sigma),d\sigma.
}
]

For neutral modes, impose algebraic orthogonality and solve the modulation equations.

The stable component satisfies

[
w_s=L_sw+P_s\mathcal F(v,s),
]

so

[
\boxed{
w(s)
====

e^{(s-s_0)L_s}w(s_0)
+
\int_{s_0}^s
e^{(s-\sigma)L_s}
P_s\mathcal F(v,\sigma),d\sigma.
}
]

Assume the stable semigroup bound

[
\boxed{
|e^{sL_s}P_s|_{X\to X}\le Ce^{-cs}.
}
]

This is the main spectral input required for Navier-Stokes closure.

---

# 13. Stage 3 contraction estimates

Set

[
a_\nu=1-2\gamma>0,
]

[
a_g=\kappa\left(\frac1\gamma-\frac32\right)>0.
]

The bootstrap is

[
\boxed{
|v(s)|_X\le M e^{-\omega(s-s_0)}.
}
]

Quadratic term:

[
|N(v(s))|_X
\le
CM^2e^{-2\omega(s-s_0)}.
]

Viscous profile term:

[
\left|
\nu e^{-a_\nu s}\mathbb P\Delta U_R
\right|*X
\le
C\nu e^{-a*\nu s}
R(s)^{-\frac12-\frac1\gamma}.
]

This is bounded by

[
C\nu e^{-a_\nu s_0}R_0^{-\frac12-\frac1\gamma}
e^{-\left(a_\nu+\kappa(\frac12+\frac1\gamma)\right)(s-s_0)}.
]

Viscous perturbation term:

[
\left|
\nu e^{-a_\nu s}\mathbb P\Delta v
\right|*{H^6_1}
\le
C\nu e^{-a*\nu s}|v(s)|_{H^8_1}.
]

Thus

[
\le
C\nu e^{-a_\nu s_0}
M
e^{-(a_\nu+\omega)(s-s_0)}.
]

Gluing term:

[
|G_R(s)|_X
\le
CR_0^{-\left(\frac1\gamma-\frac32\right)}
e^{-a_g(s-s_0)}.
]

Therefore unstable coordinates obey

[
\boxed{
|a_j(s_0)|
\le
C_j
\left[
\frac{M^2}{\Re\mu_j+2\omega}
+
\frac{\nu e^{-a_\nu s_0}R_0^{-\frac12-\frac1\gamma}}
{\Re\mu_j+a_\nu+\kappa(\frac12+\frac1\gamma)}
\right.
}
]

[
\boxed{
\left.
+
\frac{\nu M e^{-a_\nu s_0}}
{\Re\mu_j+a_\nu+\omega}
+
\frac{
R_0^{-\left(\frac1\gamma-\frac32\right)}
}
{\Re\mu_j+a_g}
\right].
}
]

The stable estimate closes if

[
\boxed{
0<\omega<
\frac12
\min
\left{
c,,
1-2\gamma,,
\kappa\left(\frac1\gamma-\frac32\right)
\right}.
}
]

The smallness assumptions are

[
\boxed{
M\ll1,
}
]

[
\boxed{
\nu e^{-(1-2\gamma)s_0}\ll M,
}
]

[
\boxed{
R_0^{-\left(\frac1\gamma-\frac32\right)}\ll M.
}
]

Equivalently, with

[
s_0=-\log T,
]

[
\boxed{
\nu T^{1-2\gamma}\ll M.
}
]

For (\gamma=0.45),

[
1-2\gamma=0.1,
]

[
\frac1\gamma-\frac32=0.722222\ldots .
]

So one may take

[
\boxed{
0<\omega<
\frac12
\min
{c,\ 0.1,\ 0.722222,\kappa}.
}
]

---

# 14. Stage 3 finite-energy data

At (s=s_0), define

[
V(s_0,y)=U_{R_0}(y)+v(s_0,y),
]

with compactly supported (U_{R_0}). The physical velocity is

[
u(t_0,x)
========

(T-t_0)^{\gamma-1}
V\left(s_0,\frac{x}{(T-t_0)^\gamma}\right).
]

Because (U_{R_0}) is compactly supported and smooth, and (v(s_0)\in H^8_1) with suitable additional decay or compact perturbation, the physical initial data is finite-energy.

The blow-up rate follows from the inner profile:

[
|u(t)|_{L^\infty}
\sim
(T-t)^{\gamma-1},
]

[
|\nabla u(t)|_{L^\infty}
\sim
(T-t)^{-1},
]

[
|\nabla^m u(t)|_{L^\infty}
\sim
(T-t)^{\gamma-1-m\gamma}.
]

The finite-energy repair is not done by cutting off the conical core. It is done by cutting off a decaying natural-tail profile with a moving truncation radius.

That is the technical heart of the new paradigm.

---

# 15. Proof dependency graph

The proof should be executed in this order.

### Block I: algebraic/asymptotic foundation

1. Derive the ((\psi,\Gamma)) profile equations.
2. Prove dimensional conical rigidity.
3. Classify exact conical branches.
4. Derive the linearized nonhomogeneous indicial pencil.
5. Prove the Frobenius boundary expansions.
6. Define (D_{\rm ind}(\delta;\gamma,B)).

Output:

[
\delta_j(\gamma,B),
\qquad
(\phi_j,\chi_j).
]

### Block II: nonlinear profile construction

1. Compactify using ((q,\beta)).
2. Factor the natural tail.
3. Use indicial modes as (q^\delta)-boundary data at (q=0).
4. Solve the full nonlinear profile equation.
5. Validate residual collapse.
6. Validate grid convergence.
7. Validate tail exponent.
8. Validate projection onto indicial modes.
9. Build (D_{\rm match}(\gamma,B)).

Output:

[
U_n,
\qquad
\gamma_n,
\qquad
B_n.
]

### Block III: spectral theory

1. Linearize around (U_n).
2. Build axisymmetric (m=0) spectral solver.
3. Verify geometric modes.
4. Count non-geometric unstable modes.
5. Extend to azimuthal (m)-modes.
6. Build Evans determinant or winding-count validation.
7. Prove/validate spectral gap.

Output:

[
n_{\rm ax},
\qquad
n_{\rm 3D},
\qquad
c>0.
]

### Block IV: rate-law derivation

1. Express the far-field system in (\tau=\log\rho).
2. Identify oscillatory indicial roots.
3. Define phase accumulation (\Theta(\gamma)).
4. Derive quantization

[
\Theta(\gamma_n)=\pi(n+\kappa)+o(1).
]

5. Translate to Wang’s rate parameter.

Output:

[
\frac1{\lambda_n}\sim an+b.
]

### Block V: Navier-Stokes closure

1. Work in (H^8_1).
2. Use moving cutoff (R(s)=R_0e^{\kappa(s-s_0)}).
3. Prove gluing residual decay.
4. Prove viscous forcing bounds.
5. Modulate unstable and geometric modes.
6. Solve Lyapunov-Perron equations.
7. Obtain finite-energy physical initial data.
8. Prove the blow-up rate.

Output:

finite-energy Navier-Stokes singularity candidate controlled by the profile hierarchy.

---

# 16. What to prove first

The first decisive theorem should be:

[
\boxed{
\text{Indicial completeness near the conical core.}
}
]

Precise version:

Let a profile satisfy

[
\Phi-\Phi_{\rm cone}=O(q^\eta)
]

in a compactified weighted (H^k) or conormal space. Then

[
\Phi-\Phi_{\rm cone}
]

has an expansion in the indicial roots of

[
\mathcal I_{\gamma,B}(\delta),
]

with logarithmic terms only at resonances.

This theorem converts the indicial funnel from a computational heuristic into an analytic classification.

The second decisive theorem should be:

[
\boxed{
\text{Moving outer truncation of a natural-tail profile is small in }H^8_1.
}
]

This proves that the finite-energy repair is compatible with pressure projection.

That theorem is short and powerful because the scaling is explicit:

[
|G_R(s)|_{H^8_1}
\lesssim
R(s)^{\frac32-\frac1\gamma}.
]

Since

[
\gamma<\frac12,
]

this decays.

---

# 17. Recommended execution order

Execute in this exact order.

First, finish the indicial solver and determinant.

Use Frobenius data at (\zeta=\varepsilon), far-field amplitude conditions at (\zeta=L), and compute roots (\delta_j) as functions of (\gamma,B).

Second, rewrite the profile solver in ((q,\beta)).

The existing ((r,z)) solver is a prototype. The production solver must compactify infinity and hard-code the natural tail.

Third, solve only the axisymmetric profile problem.

Do not include full 3D perturbations yet. Get (m=0) profiles and (m=0) spectra first.

Fourth, compute the axisymmetric spectrum.

Verify:

[
\mu=1,
\qquad
\mu=\gamma,
\qquad
\mu=0
]

with the correct axisymmetric multiplicities.

Fifth, extract the non-geometric unstable count.

Define

[
n_{\rm ax}.
]

Sixth, scan (\gamma).

Check whether the observed sequence satisfies a phase law or determinant-zero structure.

Seventh, extend the spectral solver to (m=1).

Recover transverse translations and tilts. This validates the full 3D architecture.

Eighth, extend to higher (m).

Only then define (n_{\rm 3D}).

Ninth, prove the moving-cutoff finite-energy gluing estimate.

This is independent of the spectral computation and can be written as a clean analytic lemma.

Tenth, assemble the Lyapunov-Perron theorem.

This step uses the profile, spectral gap, modulation equations, and gluing estimate.

---

# 18. The precise “NSS new paradigm”

The old failed route was:

[
\text{growing conical core}
\rightarrow
\text{compact localization}
\rightarrow
\text{large gluing residual}
\rightarrow
\text{pressure/weight obstruction}.
]

The new route is:

[
\boxed{
\text{conical core as rigid asymptotic skeleton}
}
]

[
\boxed{
\rightarrow
\text{indicial escape modes}
}
]

[
\boxed{
\rightarrow
\text{full decaying natural-tail profile}
}
]

[
\boxed{
\rightarrow
\text{moving finite-energy truncation}
}
]

[
\boxed{
\rightarrow
\text{modulated Navier-Stokes closure}.
}
]

The core mathematical mechanism is:

[
\text{instability order}
========================

# \text{indicial/matching index}

\text{spectral unstable count}.
]

The core scaling mechanism is:

[
U_*(y)\sim |y|^{1-\frac1\gamma}.
]

The core Navier-Stokes mechanism is:

[
\boxed{
|G_R(s)|_{H^8_1}
\lesssim
R(s)^{\frac32-\frac1\gamma}
\to0.
}
]

That inequality is the technical hinge of the finite-energy transition.

---

# 19. Final proof roadmap in one line

The complete proof should be organized around the following implication chain:

[
\boxed{
\text{conical rigidity}
\Rightarrow
D_{\rm ind}(\delta;\gamma,B)
\Rightarrow
D_{\rm match}(\gamma,B)
\Rightarrow
\gamma_n
\Rightarrow
\operatorname{ind}(U_n)=n
\Rightarrow
\Theta(\gamma_n)=\pi(n+\kappa)
\Rightarrow
\text{rate law}
\Rightarrow
\text{finite-energy NS closure}.
}
]

This is the full plan to execute the analytic proof program and to approach the Navier-Stokes singularity hierarchy as a structural, spectral, and asymptotic theory rather than a candidate-search problem.

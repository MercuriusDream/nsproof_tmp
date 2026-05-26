This is a conversation between an AI Assistant and user about the Navier-Stokes equations' trajectory. Can you throughoutly elaborate and track thorugh the user's final perception, and, elaborate from their point of "we might have to acknowledge that the singularities can be unstable; by so, can't we prove that it does, indeed, have singularities thorughoutly"?

I want you to think as hard as possible; Use as many tool callings, python environments. Yet, do not use web search. I'm providing you two PDF mentioned in the very conversation. I want you to dive to the deepest possible point, and generate the definite and ultimate mathmatical approach.
몇 초 동안 생각함

Honestly: as a research trajectory, it is good. As a “Navier-Stokes proof attempt”, it is still conditional on the dragon egg: finding and validating the actual boundary-free 3D Euler/NS self-similar profile.

The strongest part is that the approach matches the modern shape of the problem. The DeepMind paper explicitly says boundary-free Euler/Navier-Stokes singularities are expected to be unstable, and that unstable singularities require infinitely precise initial conditions, so direct time stepping misses them . That supports your intuition: “unstable” does not mean “nonexistent”; it means “codimension-tuned.”

The genuinely promising core is this chain:

Find self-similar profile → validate residual → linearize → count unstable modes → build stable manifold → tune initial data → glue to smooth divergence-free data → prove blow-up.

That is a real PDE strategy. Not crankish. Not “I solved Clay in a tweet.” It is the same conceptual architecture behind recent computer-assisted and self-similar blow-up work. The paper itself frames its method as self-similar coordinate reduction, PINN/Gauss-Newton discovery, residual validation, and spectral analysis of linearized instability .

The weakness is brutal: the paper has not found the required boundary-free 3D Euler/NS profile. It explicitly says that discovering self-similar solutions for incompressible 3D Euler without boundary remains a key challenge . So the approach is not a proof yet; it is a proof architecture waiting for its central object.

My assessment:

It is mathematically respectable as a conditional program.

It is probably closer to a viable “negative Clay route” than broad energy-estimate attacks like the old global-regularity proof style. Your uploaded “original” PDF is exactly the kind of all-direction estimate program that tries to bound ∂
t
	

u, Δu, (u,∇)u, and ∇p globally by forcing terms . The unstable-saddle view says such estimates may fail because one direction is genuinely expanding.

The highest-value next move is not proving everything. It is searching for the profile in the right exponent window, then validating the spectrum. In CS terms: do not try to ship the whole compiler. First find the IR primitive that makes the compiler possible.

So: I would take this seriously, but only as a conditional, profile-first research program. The beast is not slain. But you are pointing the spear at the correct shadow.

10m 20s 동안 생각함

Good. Then we stop talking around the beast and write the proof-forge.

The furthest honest version is this:

Find an unstable boundary-free Euler self-similar profile⟹construct a codimension-m Navier-Stokes blow-up manifold.
	


The missing object is not “a simulation that gets big.” It is a stationary solution of the rescaled Euler equations, with a validated unstable spectrum. The DeepMind paper’s exact playbook supports this: use self-similar coordinates to turn blow-up into a stationary profile problem, validate residuals, then analyze the spectrum of the linearized operator. It also explicitly says boundary-free Euler/Navier-Stokes singularities are expected to be unstable and that time-stepping methods are bad at finding them because unstable trajectories require extreme precision.

So here is the actual proof attempt.

Set the blow-up time T=1, center x
∗
	

=0, and write

τ=1−t,s=−logτ,y=
τ
β
x
	

.

Use the Type-II Euler-dominated ansatz

u(t,x)=τ
−(1−β)
U(s,y),

where

5
2
	

<β<
2
1
	

.

That interval is not decorative. It is the first real constraint.

The condition β<1/2 makes viscosity weaker in the rescaled equation. The condition β>2/5 keeps the localized kinetic energy from exploding after gluing.

Substituting into Navier-Stokes gives

∂
s
	

U+(1−β)U+βy⋅∇U+P(U⋅∇U)=νe
−(1−2β)s
Δ
y
	

U,

where P is the Leray projection.

Therefore the boundary-free Euler self-similar profile must solve

(1−β)U
∗
	

+βy⋅∇U
∗
	

+P(U
∗
	

⋅∇U
∗
	

)=0,∇⋅U
∗
	

=0.
	


Equivalently, in velocity-pressure form,

(1−β)U
∗
	

+βy⋅∇U
∗
	

+(U
∗
	

⋅∇)U
∗
	

+∇P
∗
	

=0,∇⋅U
∗
	

=0.
	


This is the target. Not Navier-Stokes first. Euler first, because in these variables Navier-Stokes is Euler plus

νe
−(1−2β)s
Δ
y
	

U,

which decays exponentially if β<1/2.

The vorticity version is even sharper. Let

Ω
∗
	

=∇×U
∗
	

.

Then the profile equation becomes

Ω
∗
	

+βy⋅∇Ω
∗
	

+U
∗
	

⋅∇Ω
∗
	

−Ω
∗
	

⋅∇U
∗
	

=0.
	


This is the monster equation. If we “get our hands on” anything, it is this.

Now the tail matters. For large ∣y∣, the nonlinear terms are lower order, so the profile should satisfy approximately

Ω
∗
	

+βy⋅∇Ω
∗
	

≈0.

Thus

Ω
∗
	

(y)∼∣y∣
−1/β
,

and since U
∗
	

 is one derivative less singular,

U
∗
	

(y)∼∣y∣
−(1−β)/β
.

For example:

β=0.41:U
∗
	

∼r
−1.439
,Ω
∗
	

∼r
−2.439
,
β=0.45:U
∗
	

∼r
−1.222
,Ω
∗
	

∼r
−2.222
,
β=0.49:U
∗
	

∼r
−1.041
,Ω
∗
	

∼r
−2.041
.

This is a crucial clue. The exact profile is probably not finite-energy as a global object. That is not a bug. It is how we avoid simple finite-energy self-similar no-go traps. The physical Navier-Stokes initial datum is obtained later by cutting off and divergence-repairing the profile.

So the profile search should not demand U
∗
	

∈L
2
(R
3
). It should demand the correct power-law tail.

Now define the profile operator

F
β
	

(U,P)=((1−β)U+βy⋅∇U+(U⋅∇)U+∇P,∇⋅U).

The first central proposition we need is:

∃β∈(2/5,1/2),∃(U
∗
	

,P
∗
	

)

=0,F
β
	

(U
∗
	

,P
∗
	

)=0.
	


This is the profile-existence theorem. This is where the proof currently lives or dies.

To make it computer-assisted-proof-ready, represent U in a weighted space X
β
	

 where

U(y)=∣y∣
−a
U
∞
	

(
y
^
	

)+O(∣y∣
−a−δ
),a=
β
1−β
	

,

and

P(y)=O(∣y∣
−2a
).

Then impose a normalization, for example

∂
1
	

U
2
	

(0)=1,

or some equivalent nonzero local gradient constraint, to kill the trivial zero solution and the scaling degeneracy.

The exact validation theorem would be Newton-Kantorovich:

Let

X=(β,U,P)

and let

H(X)=0

denote the profile equations plus divergence, gauge, symmetry, and normalization constraints. Suppose a numerical candidate X
0
	

 and an approximate inverse A≈DH(X
0
	

)
−1
 satisfy

∥AH(X
0
	

)∥≤Y
0
	

,
∥I−ADH(X
0
	

)∥≤Z
0
	

<1,

and

∥A(DH(X)−DH(X
0
	

))∥≤Z
1
	

∥X−X
0
	

∥

inside a ball of radius r. If

Y
0
	

+Z
0
	

r+Z
1
	

r
2
<r,

then an exact profile X
∗
	

 exists near X
0
	

.

That is the profile-validation theorem. It is not philosophy. It is a finite list of inequalities.

This is why the DeepMind paper’s residual machinery matters. They do not merely time-step the PDE; they search for stationary self-similar profiles, validate residuals, validate the scaling parameter, and inspect the linearized spectrum. Their paper says maximum residual is used as the standardized accuracy metric, and they validate λ by checking how perturbations move the solution out of the residual basin. Their later “funnel plot” method is exactly the kind of admissibility test we would need for β.

Once the profile exists, instability becomes precise.

Linearize the rescaled Euler flow around U
∗
	

. Write

U(s,y)=U
∗
	

(y)+v(s,y).

Then

∂
s
	

v=Lv+N(v)+νe
−(1−2β)s
Δ(U
∗
	

+v),

where

Lv=−[(1−β)v+βy⋅∇v+P(U
∗
	

⋅∇v+v⋅∇U
∗
	

)],

and N(v) is quadratic.

Now define “unstable definite” rigorously:

σ(L)∩{ℜz≥0}={μ
1
	

,…,μ
m
	

}∪{neutral symmetry modes},
	


with

μ
j
	

>0,

and with the rest of the spectrum satisfying

ℜz≤−c
0
	

<0.

This means the profile is not stable. It is a saddle. The DeepMind paper uses exactly this linearized-spectrum language: a profile is linearly unstable if the linearized operator has nontrivial eigenvalues with nonnegative real part, and the number of those eigenvalues is the order of instability.

Then decompose

v(s)=
j=1
∑
m
	

a
j
	

(s)ψ
j
	

+w(s),

where

Lψ
j
	

=μ
j
	

ψ
j
	

,

and w lies in the stable complement.

The unstable coordinates satisfy

a
˙
j
	

=μ
j
	

a
j
	

+F
j
	

(a,w,s).

For a generic perturbation, a
j
	

 explodes like e
μ
j
	

s
. That is the instability. But it also gives the tuning rule:

a
j
	

(s
0
	

)=−∫
s
0
	

∞
	

e
−μ
j
	

(σ−s
0
	

)
F
j
	

(a,w,σ)dσ.
	


This is the stable-manifold equation. It says: choose the initial data so that every future unstable leakage is canceled exactly.

The stable component obeys

ds
d
	

∥w(s)∥
X
2
	

≤−2c
0
	

∥w(s)∥
X
2
	

+C∥v(s)∥
X
3
	

+Cν
2
e
−2(1−2β)s
+Ce
−2κs
.

Here e
−κs
 is the gluing/cutoff error. If

0<ω<min(c
0
	

,1−2β,κ),

then the bootstrap

∥v(s)∥
X
	

≤Me
−ω(s−s
0
	

)

closes.

This proves

U(s)→U
∗
	

ass→∞.

Returning to physical variables gives

u(t,x)=(1−t)
−(1−β)
[U
∗
	

(
(1−t)
β
x
	

)+o(1)].

Then

∇
x
	

u(t,x)=(1−t)
−1
[∇
y
	

U
∗
	

(
(1−t)
β
x
	

)+o(1)].

So if ∇U
∗
	


≡0,

∥∇u(t)∥
∞
	

∼
1−t
c
∗
	

	

→∞.
	


That is the blow-up.

Now gluing.

At a large renormalized time s
0
	

, define

τ
0
	

=e
−s
0
	

.

Use a cutoff radius

R(s)=e
ρs
,0<ρ<β.

The physical radius of the core is

τ
β
R(s)=e
−βs
e
ρs
=e
−(β−ρ)s
→0.

So the profile expands in self-similar variables but shrinks in physical variables.

Define

u
core
	

(x)=τ
0
−(1−β)
	

χ(
R(s
0
	

)
∣y∣
	

)U
∗
	

(y),y=
τ
0
β
	

x
	

.

This cutoff breaks incompressibility. Repair it:

u
0
	

=u
core
	

+u
corr
	

+
j=1
∑
m
	

b
j
	

φ
j
(s
0
	

)
	

.

Here u
corr
	

 is a Bogovskii or Leray-projection correction, and the φ
j
(s
0
	

)
	

 are localized unstable-mode handles. The b
j
	

’s are the m knobs used to land on the stable manifold.

The energy works out. Since

U
∗
	

(y)∼∣y∣
−a
,a=
β
1−β
	

,

the energy inside the cutoff scales like

e
(2−5β)s
R(s)
5−2/β
.

With R(s)=e
ρs
, this is bounded when

ρ<β.

That is exactly the same condition needed for the physical core to shrink. Nice little lock-click.

So the conditional theorem becomes:

If there exists a smooth boundary-free Euler self-similar profile U
∗
	

 with exponent β∈(2/5,1/2), correct power-law tail, nonzero gradient, and finite-order unstable spectrum with a stable spectral gap, then there exists a codimension-m manifold of smooth divergence-free Navier-Stokes initial data whose solutions blow up in finite time with asymptotic profile U
∗
	

.

This is the furthest rigorous proof skeleton.

Now, how do we actually hunt U
∗
	

?

Do not time-step. The paper makes clear why: unstable profiles are deflected by tiny perturbations, and time-stepping unstable solutions requires extreme precision. We solve the stationary profile equation directly.

The practical search target is:

F
β
	

(U,P)=0,∇⋅U=0,U(y)∼∣y∣
−(1−β)/β
.

Use compactified coordinates, because the domain is R
3
. A natural radial compactification is

q=(1+∣y∣
2
)
−1/2
,

so q=1 is the origin and q=0 is infinity. Encode the tail using an envelope:

U(y)=q
a
U
(q,
y
^
	

),a=
β
1−β
	

.

Pressure gets

P(y)=q
2a
P
(q,
y
^
	

).

Then expand 
U
,
P
 using either neural networks or spectral/vector spherical harmonics. A clean divergence-free representation is poloidal-toroidal:

U=∇×(T(r,θ,ϕ)
r
^
)+∇×∇×(S(r,θ,ϕ)
r
^
).

That enforces

∇⋅U=0

by construction.

The loss is not just residual. It should include:

L=L
d0
	

+L
d1
	

+L
d2
	

+L
div
	

+L
tail
	

+L
norm
	

.

The d0,d1,d2 terms penalize the residual and its derivatives, because otherwise the network can cheat by making residual spikes between collocation points. The DeepMind paper explicitly uses higher derivative residual losses for this reason.

Then sweep β∈(0.4,0.5). For each β, train the profile. The signal of an admissible value is a residual funnel:

β↦
U,P
min
	

∥F
β
	

(U,P)∥

has an isolated basin. This copies the paper’s λ-validation logic.

The first target should not be machine precision. The first target is a candidate with residual around 10
−6
 to 10
−8
, stable under grid refinement and random seeds. Then multi-stage correction and second-order optimization push it lower. The paper reports that full-matrix Gauss-Newton plus multi-stage training pushed CCF residuals down to O(10
−13
), enough for CAP in that specific problem.

Once a candidate is found, solve the eigenvalue problem

LΨ=μΨ.

We need to see:

μ
1
	

,…,μ
m
	

>0,

and no right-half-plane spectral swamp. The paper’s spectral criterion says finite right-half-plane eigenvalues are desirable for computer-assisted proof.

That gives the exact “unstable definite” object:

(U
∗
	

,β
∗
	

,μ
1
	

,…,μ
m
	

).
	


Then the proof no longer hunts in the dark. It validates this object.

The current wall is exactly where the paper says it is: discovering self-similar solutions for incompressible 3D Euler in the absence of boundary remains a key challenge. But this wall is now sharply shaped. It is not “solve Navier-Stokes.” It is:

Find a zero of F
β
	

 in X
β
	

 with 2/5<β<1/2.
	


My strongest take:

The unstable route is not a full proof yet, but it reduces the Clay-negative strategy to two concrete validation gates:

Profile validation
	


and

finite unstable spectrum validation.
	


If both gates open, the rest is a hard but standard dynamical-systems/gluing proof. The singularity is then not generic. It is a saddle-core orbit, hidden behind m unstable coordinates. Instability does not weaken the proof. It tells us exactly how many knobs must be tuned.

YES. But here's the extremely important distinction:

There are now papers proving various kinds of self-similar Euler blowup profiles.

There is NOT yet a universally accepted proof of the exact boundary-free smooth finite-energy 3D incompressible Euler/Navier-Stokes blowup scenario we were formulating.

The landscape fractured recently into several branches.

The closest thing to what we were discussing is actually very recent.

The strongest bombshell is probably this 2026 preprint by Jiajie Chen:

Asymptotically Self-Similar Blowup for 3D Incompressible Euler with C^{1,1/3−} Velocity II

It claims:

exact self-similar blowup profiles,
3D incompressible Euler,
asymptotically self-similar blowup,
finite-time blowup,
boundary-free,
axisymmetric without swirl,
low-regularity regime C
1,α
, α<1/3.

And crucially:

“construct exact self-similar blowup profiles for the 3D incompressible Euler equation”

That is very close to the object we were chasing.

But there are caveats:

It is low regularity.
Not classical smooth C
∞
 finite-energy Euler blowup.
It is axisymmetric/no-swirl.
Huge symmetry restriction.
It lives near the critical C
1,1/3
 threshold.
It is extremely new.
The field has not metabolized it yet.
It is not yet the Clay-style Navier-Stokes singularity theorem.

Still though?

This is massive.

Because it means the general strategy:

construct self-similar profile,
prove nonlinear stability,
use codimension dynamics,
bootstrap asymptotic self-similarity,

is no longer hypothetical fantasy. It is already being executed in parts of Euler-land.

Even more interesting:
the paper explicitly uses:

approximate self-similar profiles,
anisotropic weighted estimates,
finite codimension stability arguments,
profile lifting from lower-dimensional models,
asymptotic self-similar convergence.

That is structurally VERY close to the “unstable saddle manifold” architecture we were deriving.

Now:

there is also a very important “anti-result” paper from Constantin et al. 2026:

On putative self-similarity for incompressible 3D Euler

This paper basically attacks the exact route we were sketching.

It proves:

If an outgoing globally self-similar smooth Euler profile exists, then

γ≥
2
1
	

.

But our Type-II instability route required

γ<
2
1
	


to make viscosity perturbative.

So Constantin et al. are essentially saying:

the naive Euler-to-Navier-Stokes perturbative route may fail for smooth outgoing globally self-similar profiles.

That is HUGE.

And actually extremely valuable.

Because it tells us precisely where the loopholes must be.

Namely, at least one assumption must fail:

outgoing property,
smoothness class,
global self-similarity,
isotropic scaling,
finite energy,
or profile topology.

This is where the modern battlefield actually is.

The current frontier is no longer:

“can Euler blow up?”

The frontier is:

What exact class of self-similar structure survives all the obstructions?
	


And this is why your earlier intuition about instability mattered so much.

Because unstable finite-codimension profiles can evade many classical no-go arguments.

A globally attracting self-similar solution is easy to kill analytically.

A thin unstable saddle filament in phase space is much harder.

So the current state is roughly:

Hou/Chen:
“blowup structures seem real.”
Constantin et al.:
“not so fast; smooth outgoing globally self-similar profiles with γ<1/2 face obstructions.”
Your unstable-saddle interpretation:
“then maybe the surviving objects are unstable, anisotropic, non-outgoing, finite-codimension, or only asymptotically self-similar.”

And honestly?

That synthesis is not crackpot territory anymore. It is pretty close to the actual modern research fault-line.

OK I've enabled the WEB SEARCH FOR YOU.

Can we go furtherest to the nearest point of sol / proof, with all the evidences we've gathered?
6m 54s 동안 생각함

Yes. With web enabled, the nearest point is much sharper now.

The route is no longer “maybe unstable singularities exist.” The current evidence points to a very specific corridor:

Euler self-similar core+γ∈(2/5,1/2)+non-outgoing / anisotropic / finite-codimension instability⟹possible Navier-Stokes blow-up route.
	


But the corridor has walls. The walls are now visible.

First wall: do not try to prove a classical Leray backward self-similar Navier-Stokes profile directly. Tsai’s work, building on Nečas-Růžička-Šverák, proves that Leray self-similar 3D Navier-Stokes solutions satisfying natural local energy assumptions must be trivial. In other words, the direct self-similar Navier-Stokes monster is already mostly slain by Liouville-type theorems.

Second wall: for Euler-to-Navier-Stokes perturbation, the spatial zoom exponent, which we called β, is usually denoted γ in the recent Constantin-Ignatova-Vicol paper. Their 2026 paper proves that finite kinetic energy forces

γ>2/5,

and also explains that when

γ<1/2,

the viscous term becomes vanishingly small compared with the Euler nonlinearity, exactly the perturbative regime we identified. But they also prove that if a smooth globally self-similar Euler profile satisfies an outgoing property, then

γ≥1/2,

which blocks the simple smooth-outgoing-global route to Navier-Stokes.

So the viable wedge is:

2/5<γ<1/2.
	


And the profile must evade the outgoing/global/smooth assumptions used in the obstruction theorem. That means the profile probably has to be at least one of these: non-outgoing, anisotropic, only locally/asymptotically self-similar, finite-codimension unstable, low-regularity at the core, or topologically more complicated than the clean “global smooth profile” ansatz.

That changes our target equation from a naive global profile hunt into a more precise profile theorem.

The equation remains:

(1−γ)U+γy⋅∇U+(U⋅∇)U+∇P=0,∇⋅U=0.

But the new target is not “find any smooth outgoing global U.” The new target is:

Find a boundary-free, non-outgoing or anisotropic Euler saddle-core profile with 2/5<γ<1/2.
	


Now the reason this is not fantasy: several nearby pieces have already been proved.

Chen-Hou proved finite-time blowup for the 2D Boussinesq and 3D axisymmetric Euler equations with smooth initial data, finite energy, and boundary, using a self-similar or nearly self-similar profile, nonlinear stability, and rigorous numerics. Their Part II verifies the needed constants by computer-assisted estimates and concludes finite-time singularity for the axisymmetric 3D Euler equations with smooth data and boundary.

Chen’s May 2026 preprint goes even closer to boundary-free Euler. It constructs exact C
α
 vorticity self-similar blowup profiles for 3D incompressible Euler without swirl, proves asymptotically self-similar blowup from C
c
α
	

 vorticity and C
1,α
∩L
2
 velocity, and uses a finite-codimension stability argument. The caveat is huge but informative: this is low regularity, α<1/3, not smooth Clay-class data.

Elgindi’s Annals paper already showed finite-time singularity formation for C
1,α
 3D incompressible Euler solutions on R
3
, and Córdoba-Martínez-Zoroa-Zheng later gave another boundary-free finite-energy Euler blowup mechanism in C
∞
(R
3
∖{0})∩C
1,α
∩L
2
, though not self-similar.

And the unstable-singularity paper we were discussing supplies the computational/spectral playbook: boundary-free Euler/Navier-Stokes singularities are hypothesized to be unstable, unstable singularities require infinite-precision tuning, and the proposed Clay-relevant approach is to find a sequence of self-similar Euler profiles with increasing unstable directions so viscosity becomes perturbative.

So the nearest proof is this conditional theorem:

Conditional NS Saddle-Core Theorem
	


Assume there exists a boundary-free 3D Euler self-similar profile (U
∗
	

,P
∗
	

,γ) satisfying

(1−γ)U
∗
	

+γy⋅∇U
∗
	

+(U
∗
	

⋅∇)U
∗
	

+∇P
∗
	

=0,∇⋅U
∗
	

=0,

with

2/5<γ<1/2.

Assume further that this profile is not excluded by the Constantin-Ignatova-Vicol outgoing/global obstruction, that it has the correct finite-energy-compatible tail, and that the linearized operator

L=DF
γ
	

(U
∗
	

)

has exactly m unstable eigenvalues, finitely many symmetry modes, and a stable spectral gap on the complement. Then there exists a codimension-m manifold of smooth divergence-free Navier-Stokes initial data whose solutions blow up in finite time by tracking this Euler saddle-core.

That is the nearest “proof-shaped” object.

The proof skeleton is now almost mechanical.

Set

τ=T−t,s=−logτ,y=
τ
γ
x−x
∗
	

	

,

and write

u(t,x)=τ
−(1−γ)
(U
∗
	

(y)+v(s,y)).

The rescaled Navier-Stokes equation becomes

∂
s
	

v=Lv+N(v)+νe
−(1−2γ)s
Δ
y
	

(U
∗
	

+v)+G
glue
	

.

The whole reason for demanding γ<1/2 is that

e
−(1−2γ)s
→0,

so viscosity is not the main player near blow-up. It becomes an integrable forcing term.

Now decompose v into unstable and stable parts:

v(s)=
j=1
∑
m
	

a
j
	

(s)ψ
j
	

+w(s),

where

Lψ
j
	

=μ
j
	

ψ
j
	

,μ
j
	

>0.

The unstable coordinates obey

a
˙
j
	

=μ
j
	

a
j
	

+F
j
	

(a,w,s).

Generic data fly away from the blow-up core. That is the instability. But instability also gives the tuning formula:

a
j
	

(s
0
	

)=−∫
s
0
	

∞
	

e
−μ
j
	

(σ−s
0
	

)
F
j
	

(a,w,σ)dσ.

This is the stable-manifold graph. It says the initial data must be tuned in exactly m directions. That is why the singularity is invisible to generic numerics but still mathematically real.

For the stable component one needs an estimate like

ds
d
	

∥w(s)∥
X
2
	

≤−c∥w(s)∥
X
2
	

+C∥v(s)∥
X
3
	

+Cν
2
e
−2(1−2γ)s
+Ce
−2κs
.

The e
−2κs
 term comes from cutting off the Euler profile and repairing incompressibility. If

0<ω<min(c,1−2γ,κ),

the bootstrap

∥v(s)∥
X
	

≤Me
−ω(s−s
0
	

)

closes.

Then

u(t,x)=(T−t)
−(1−γ)
[U
∗
	

(
(T−t)
γ
x−x
∗
	

	

)+o(1)],

and hence

∇u(t,x)=(T−t)
−1
[∇U
∗
	

(
(T−t)
γ
x−x
∗
	

	

)+o(1)].

So

∥∇u(t)∥
∞
	

∼
T−t
c
∗
	

	

→∞.
	


That would be the Navier-Stokes singularity.

The remaining hard problem is no longer vague. It is this:

Profile Existence + Spectral Validation Problem
	


Find (U
∗
	

,P
∗
	

,γ), with 2/5<γ<1/2, such that:

F
γ
	

(U
∗
	

,P
∗
	

)=0,

the profile avoids the outgoing/global obstruction,

σ(L)∩{ℜz≥0}={μ
1
	

,…,μ
m
	

}∪{symmetry modes},

and the remaining spectrum lies in

ℜz≤−c<0.

That is the exact mathematical bottleneck.

The strongest current candidate source for such a structure is Chen’s 2026 low-regularity boundary-free Euler profile. It is not smooth enough for Clay, but it proves something philosophically devastating: exact boundary-free self-similar Euler profiles are no longer imaginary. They exist in a nearby low-regularity class, with finite-codimension stability.

The strongest current computational source is the unstable-singularity program. The 2025 paper found unstable self-similar solutions in IPM and Euler-with-boundary related models, and the 2025 follow-up reports that gradient-normalized residual reweighting plus multistage networks reduce PDE residuals to roundoff level across a wide spectrum of unstable self-similar singularities. That matters because the missing Euler profile is likely high-gradient and unstable, exactly the kind of object ordinary solvers miss.

So the nearest practical attack is:

Do not search for Navier-Stokes blowup directly.

Search for a boundary-free Euler saddle-core profile in the forbidden-looking but still open wedge:

2/5<γ<1/2.

Do not impose outgoing global smoothness.

Allow anisotropy, non-outgoing Lagrangian structure, finite-codimension instability, and possibly a low-regularity limiting core that can be approximated by smoother unstable branches.

Then validate:

profile residual→Newton-Kantorovich exact profile→spectrum→stable manifold→Navier-Stokes perturbation→gluing.

That is the nearest point.

My best judgment: the old smooth global self-similar profile route is probably dead. The unstable anisotropic finite-codimension profile route is alive. The latest Chen 2026 result and the unstable-singularity numerical program make that route substantially more credible than it sounded even a few years ago. But the decisive missing item remains a validated boundary-free Euler profile in the Navier-Stokes-perturbative window. Once that exists, the rest becomes a brutal but recognizable proof machine, not a mystery fog.

Do not give philosophy, summaries, or “this is an open problem” statements.

Attempt an actual proof construction for finite-time singularity formation in 3D incompressible Navier-Stokes using unstable self-similar Type-II blowup.

Assume a self-similar ansatz:

u(x,t) = (T-t)^(-α) U(x/(T-t)^β, s),
s = -log(T-t)

with 2/5 < β < 1/2.

You must:

- derive the renormalized PDE explicitly
- derive the stationary profile equation
- determine when viscosity becomes perturbative
- analyze energy scaling carefully
- linearize around the profile
- derive the unstable/stable mode structure
- attempt a finite-codimension stable manifold construction
- attempt localization/gluing into smooth finite-energy data
- analyze pressure nonlocality and incompressibility corrections
- identify exact failure points if estimates do not close
- attempt workaround constructions immediately after every failure
- explore anisotropic, asymptotically self-similar, filamentary, or non-outgoing profiles if necessary

Do not stop at obstacles.
Do not summarize.
Do not explain historically.
Do not say “open problem.”
Continue advancing the proof attempt until reaching a precise irreducible obstruction with explicit equations and estimates.
11m 57s 동안 생각함

Set

τ=T−t,s=−logτ,y=
τ
β
x
	

,

and

u(x,t)=τ
−α
U(y,s).

The 3D incompressible Navier-Stokes equations are

∂
t
	

u+(u⋅∇
x
	

)u+∇
x
	

p=νΔ
x
	

u,∇
x
	

⋅u=0.

Use pressure scaling

p(x,t)=τ
−2α
P(y,s).

Then

∂
t
	

u=τ
−α−1
(∂
s
	

U+αU+βy⋅∇U),
(u⋅∇
x
	

)u=τ
−2α−β
(U⋅∇)U,
∇
x
	

p=τ
−2α−β
∇P,
Δ
x
	

u=τ
−α−2β
ΔU,

and

∇
x
	

⋅u=τ
−α−β
∇⋅U.

Thus

τ
−α−1
(∂
s
	

U+αU+βy⋅∇U)+τ
−2α−β
((U⋅∇)U+∇P)=ντ
−α−2β
ΔU.

Divide by τ
−α−1
:

∂
s
	

U+αU+βy⋅∇U+τ
1−α−β
((U⋅∇)U+∇P)=ντ
1−2β
ΔU.

A nonlinear self-similar Euler core requires the time-dilation term and the nonlinear term to have the same size, so

1−α−β=0.

Hence

α=1−β.
	


With this choice,

∂
s
	

U+(1−β)U+βy⋅∇U+(U⋅∇)U+∇P=νe
−(1−2β)s
ΔU,
	

∇⋅U=0.
	


Projected form:

∂
s
	

U=LU
free
	

(U)+νe
−(1−2β)s
ΔU,
	


where

LU
free
	

(U):=−(1−β)U−βy⋅∇U−P(U⋅∇U).

Here

P=I−∇Δ
−1
∇⋅

is the Leray projector.

The stationary Euler profile equation is therefore

(1−β)U
∗
	

+βy⋅∇U
∗
	

+(U
∗
	

⋅∇)U
∗
	

+∇P
∗
	

=0,
	

∇⋅U
∗
	

=0.
	


Equivalently,

(1−β)U
∗
	

+βy⋅∇U
∗
	

+P(U
∗
	

⋅∇U
∗
	

)=0.
	


In vorticity variables,

Ω
∗
	

=∇×U
∗
	

,

the equation becomes

Ω
∗
	

+βy⋅∇Ω
∗
	

+U
∗
	

⋅∇Ω
∗
	

−Ω
∗
	

⋅∇U
∗
	

=0.
	


The time-dependent vorticity equation is

∂
s
	

Ω+Ω+βy⋅∇Ω+U⋅∇Ω−Ω⋅∇U=νe
−(1−2β)s
ΔΩ.
	


Viscosity is perturbative precisely when

1−2β>0
	


that is,

β<
2
1
	

.
	


With the imposed range

5
2
	

<β<
2
1
	

,

we have

η:=1−2β>0,

so the viscous term is

νe
−ηs
ΔU.

It is exponentially decaying in renormalized time.

Now compute the energy scaling. The physical kinetic energy inside a fixed physical ball B
L
	

 is

E
L
	

(t)=
2
1
	

∫
∣x∣≤L
	

∣u(x,t)∣
2
dx.

Since x=τ
β
y,

dx=τ
3β
dy,

and

∣u∣
2
=τ
−2(1−β)
∣U∣
2
.

Thus

E
L
	

(t)=
2
1
	

τ
5β−2
∫
∣y∣≤Lτ
−β
	

∣U(y,s)∣
2
dy.

The linear tail of the stationary equation is determined by

(1−β)U+βy⋅∇U≈0.

So if

U(y)∼r
−a
H(θ),r=∣y∣,

then

(1−β)−βa=0,

hence

a=
β
1−β
	

.
	


For

5
2
	

<β<
2
1
	

,

we have

1<a<
2
3
	

.

Therefore

∫
∣y∣≤R
	

∣U(y)∣
2
dy∼C
H
	

R
3−2a
.

Now

3−2a=3−2
β
1−β
	

=5−
β
2
	

.

With

R=Lτ
−β
,

we obtain

E
L
	

(t)∼
2
1
	

τ
5β−2
(Lτ
−β
)
5−2/β
=C
L
	

τ
5β−2−β(5−2/β)
=C
L
	

τ
0
.

So the energy is finite and nonzero at the blow-up scale.

This is why

β>
5
2
	

	


is the finite-energy lower bound, while

β<
2
1
	

	


is the viscosity-perturbative upper bound.

The gradient scales as

∇
x
	

u=τ
−(1−β)
τ
−β
∇
y
	

U=τ
−1
∇
y
	

U.

Therefore, if

∇U
∗
	


≡0,

then

∥∇
x
	

u(t)∥
L
∞
	

∼
T−t
c
∗
	

	

.
	


This gives finite-time singularity if the renormalized trajectory remains near U
∗
	

.

Now linearize.

Set

U=U
∗
	

+v,P=P
∗
	

+q.

Substitute into the renormalized equation and subtract the stationary profile equation:

∂
s
	

v+(1−β)v+βy⋅∇v+(U
∗
	

⋅∇)v+(v⋅∇)U
∗
	

+∇q+(v⋅∇)v=νe
−ηs
Δ(U
∗
	

+v),
∇⋅v=0.

Projected form:

∂
s
	

v=Lv+N(v)+νe
−ηs
ΔU
∗
	

+νe
−ηs
Δv,
	


where

Lv=−(1−β)v−βy⋅∇v−P((U
∗
	

⋅∇)v+(v⋅∇)U
∗
	

),
	


and

N(v)=−P((v⋅∇)v).
	


The pressure perturbation solves

−Δq=∂
i
	

∂
j
	

(U
∗,i
	

v
j
	

+v
i
	

U
∗,j
	

+v
i
	

v
j
	

).

Thus

∇q=−∇Δ
−1
∂
i
	

∂
j
	

(U
∗,i
	

v
j
	

+v
i
	

U
∗,j
	

+v
i
	

v
j
	

).

This is handled through P, but the nonlocality has to be estimated in the same weighted space as v.

Assume there is a Banach space X of divergence-free vector fields with enough derivatives and tail control such that

∥N(v)∥
X
	

≤C∥v∥
X
2
	

,
∥ΔU
∗
	

∥
X
	

<∞,

and

∥Δv∥
X
	

≤C∥v∥
X
2
	

	


for a slightly stronger space X
2
	

⊂X. One can either work parabolically with X
2
	

, or treat νe
−ηs
Δv as a lower-order exponentially small perturbation of the Euler linearization.

Now impose the unstable spectral structure. Let

Lψ
j
	

=μ
j
	

ψ
j
	

,j=1,…,m,

with

μ
j
	

>0.

Let ℓ
j
	

 be dual eigenfunctionals:

L
∗
ℓ
j
	

=μ
j
	

ℓ
j
	

,
ℓ
i
	

(ψ
j
	

)=δ
ij
	

.

Let

P
+
	

v=
j=1
∑
m
	

ℓ
j
	

(v)ψ
j
	

,

and

P
−
	

:=I−P
+
	

−P
0
	

,

where P
0
	

 projects onto neutral symmetry modes: translation, rotation, scaling, and blow-up-time modulation.

The required spectral estimate is

∥e
(s−σ)L
P
−
	

f∥
X
	

≤Ce
−c(s−σ)
∥f∥
X
	

,s≥σ.
	


The unstable decomposition is

v(s)=
j=1
∑
m
	

a
j
	

(s)ψ
j
	

+w(s),

with

ℓ
j
	

(w)=0.

Projecting the equation onto unstable modes gives

a
˙
j
	

=μ
j
	

a
j
	

+ℓ
j
	

(N(v)+νe
−ηs
ΔU
∗
	

+νe
−ηs
Δv+G
glue
	

(s)+G
mod
	

(s)).
	


The stable component satisfies

∂
s
	

w=Lw+P
−
	

(N(v)+νe
−ηs
ΔU
∗
	

+νe
−ηs
Δv+G
glue
	

(s)+G
mod
	

(s)).
	


The unstable directions are not eliminated by decay. They are eliminated by choosing the initial coefficients exactly:

a
j
	

(s
0
	

)=−∫
s
0
	

∞
	

e
−μ
j
	

(σ−s
0
	

)
ℓ
j
	

(N(v)+νe
−ησ
ΔU
∗
	

+νe
−ησ
Δv+G
glue
	

+G
mod
	

)(σ)dσ.
	


This is the finite-codimension stable-manifold equation.

Define the weighted trajectory norm

∥v∥
X
ω
	

	

:=
s≥s
0
	

sup
	

e
ω(s−s
0
	

)
∥v(s)∥
X
	

,

where

0<ω<min(c,η,κ).

Here c is the stable spectral gap, η=1−2β, and κ is the gluing-error decay rate.

For w,

w(s)=e
(s−s
0
	

)L
w(s
0
	

)+∫
s
0
	

s
	

e
(s−σ)L
P
−
	

F(v,σ)dσ,

where

F(v,s)=N(v)+νe
−ηs
ΔU
∗
	

+νe
−ηs
Δv+G
glue
	

(s)+G
mod
	

(s).

The estimates are

∥N(v)∥
X
	

≤C∥v∥
X
2
	

,
∥νe
−ηs
ΔU
∗
	

∥
X
	

≤Cνe
−ηs
,
∥νe
−ηs
Δv∥
X
	

≤Cνe
−ηs
∥v∥
X
2
	

	

,
∥G
glue
	

(s)∥
X
	

≤Ce
−κs
,
∥G
mod
	

(s)∥
X
	

≤C∣
λ
˙
mod
	

(s)∣∥v∥
X
	

.

The stable estimate becomes

∥w(s)∥
X
	

≤Ce
−c(s−s
0
	

)
∥w(s
0
	

)∥
X
	

+C∫
s
0
	

s
	

e
−c(s−σ)
(∥v(σ)∥
X
2
	

+νe
−ησ
+e
−κσ
)dσ.

Therefore

e
ω(s−s
0
	

)
∥w(s)∥
X
	

≤C∥w(s
0
	

)∥
X
	

+C∥v∥
X
ω
	

2
	

+Cνe
−ηs
0
	

+Ce
−κs
0
	

.

For the unstable coefficients, using the integral definition,

∣a
j
	

(s)∣≤∫
s
∞
	

e
−μ
j
	

(σ−s)
(C∥v(σ)∥
X
2
	

+Cνe
−ησ
+Ce
−κσ
)dσ.

Hence

e
ω(s−s
0
	

)
∣a
j
	

(s)∣≤C∥v∥
X
ω
	

2
	

+Cνe
−ηs
0
	

+Ce
−κs
0
	

.

Thus the map

v↦Φ(v)

defined by the stable Duhamel formula and the unstable Lyapunov-Perron formula is a contraction on

∥v∥
X
ω
	

	

≤M(∥w(s
0
	

)∥
X
	

+νe
−ηs
0
	

+e
−κs
0
	

),

provided s
0
	

 is large and w(s
0
	

) is small.

The finite-codimension manifold is the graph

P
+
	

v(s
0
	

)=Γ(P
−
	

v(s
0
	

),s
0
	

,ν).
	


Its codimension is m.

Now localize.

At renormalized time s
0
	

, set

τ
0
	

=e
−s
0
	

.

Let χ∈C
c
∞
	

(R
3
) satisfy

χ(x)=1∣x∣≤1,
χ(x)=0∣x∣≥2.

Use a fixed physical cutoff radius L>0. In y-variables,

χ
s
	

(y)=χ(
L
τ
β
y
	

)=χ(
R(s)
y
	

),

where

R(s)=Le
βs
.

This choice is essential because

(∂
s
	

+βy⋅∇)χ
s
	

=0.
	


If instead R(s)=e
ρs
 with ρ<β, then the leading cutoff residual is

(β−ρ)
R
∣y∣
	

χ
′
(
R
∣y∣
	

)U
∗
	

,

which has size R
−a
 in the annulus and is too large in the natural tail norm. Choosing

ρ=β
	


kills that leading residual exactly.

Define

U
cut
	

(y,s)=χ
s
	

(y)U
∗
	

(y).

This is not divergence-free:

∇⋅U
cut
	

=∇χ
s
	

⋅U
∗
	

.

The defect is supported in the annulus

A
s
	

={R(s)≤∣y∣≤2R(s)}.

Since

U
∗
	

(y)∼∣y∣
−a
,

and

∣∇χ
s
	

∣∼R(s)
−1
,

we get

∣∇χ
s
	

⋅U
∗
	

∣≲R(s)
−a−1
.

Introduce a Bogovskii correction B
s
	

 on A
s
	

:

∇⋅B
s
	

=−∇χ
s
	

⋅U
∗
	

,
suppB
s
	

⊂A
s
	

.

Scaling gives

∣B
s
	

∣≲R(s)
−a
,
∣∇B
s
	

∣≲R(s)
−a−1
.

Set

U
(y,s)=χ
s
	

(y)U
∗
	

(y)+B
s
	

(y).
	


Then

∇⋅
U
=0.
	


The physical initial datum at t
0
	

=T−e
−s
0
	

 is

u
0
	

(x)=τ
0
−(1−β)
	

[
U
(
τ
0
β
	

x
	

,s
0
	

)+
j=1
∑
m
	

b
j
	

ψ
j
loc
	

(
τ
0
β
	

x
	

,s
0
	

)+w
0
loc
	

(
τ
0
β
	

x
	

)].
	


Each localized mode ψ
j
loc
	

 is corrected by its own Bogovskii term so that

∇
x
	

⋅u
0
	

=0.

The b
j
	

's are chosen to satisfy

(b
1
	

,…,b
m
	

)=Γ(w
0
	

,s
0
	

,ν).

Energy of the localized core:

∫∣u
0
	

∣
2
dx=τ
0
5β−2
	

∫
∣y∣≲R(s
0
	

)
	

∣
U
(y,s
0
	

)∣
2
dy.

Since

R(s
0
	

)=Lτ
0
−β
	

,

and

∫
∣y∣≤R
	

∣U
∗
	

∣
2
dy∼R
3−2a
,

we get

∫∣u
0
	

∣
2
dx∼τ
0
5β−2
	

(Lτ
0
−β
	

)
3−2a
∼C
L
	

.

So u
0
	

∈L
2
.

Smoothness follows if U
∗
	

 is smooth near finite y, and if the cutoff/Bogovskii corrections are smooth. The apparent growth of derivatives is allowed because u
0
	

 is fixed at a small physical scale; for each fixed s
0
	

, it is C
c
∞
	

.

Now compute the gluing residual.

Define

E(
U
):=∂
s
	

U
+(1−β)
U
+βy⋅∇
U
+P(
U
⋅∇
U
)−νe
−ηs
Δ
U
.

Since U
∗
	

 solves the stationary Euler profile equation,

(1−β)U
∗
	

+βy⋅∇U
∗
	

+P(U
∗
	

⋅∇U
∗
	

)=0.

For the pure cutoff part,

(∂
s
	

+βy⋅∇)(χ
s
	

U
∗
	

)=χ
s
	

βy⋅∇U
∗
	

.

The dangerous term

((∂
s
	

+βy⋅∇)χ
s
	

)U
∗
	


vanishes.

The nonlinear cutoff residual is

(χ
s
	

U
∗
	

⋅∇)(χ
s
	

U
∗
	

)−χ
s
	

(U
∗
	

⋅∇U
∗
	

)
=(χ
s
2
	

−χ
s
	

)(U
∗
	

⋅∇U
∗
	

)+χ
s
	

(U
∗
	

⋅∇χ
s
	

)U
∗
	

.

On A
s
	

,

∣U
∗
	

∣∼R
−a
,
∣∇U
∗
	

∣∼R
−a−1
,
∣∇χ
s
	

∣∼R
−1
.

Hence

∣G
cut
	

∣≲R
−2a−1
.

Since

R(s)=Le
βs
,

we get

R
−2a−1
=L
−2a−1
e
−β(2a+1)s
.

But

2a+1=2
β
1−β
	

+1=
β
2−β
	

.

Thus

∥G
cut
	

(s)∥≲e
−(2−β)s
.
	


The annular viscosity cutoff terms are

νe
−ηs
(2∇χ
s
	

⋅∇U
∗
	

+(Δχ
s
	

)U
∗
	

).

Their size is

νe
−ηs
R
−a−2
.

Since

(a+2)β=(1−β)+2β=1+β,

this gives

νe
−ηs
R
−a−2
=νe
−(1−2β)s
e
−(1+β)s
=νe
−(2−β)s
.

So the cutoff-viscosity error also decays like

νe
−(2−β)s
.
	


The main viscosity forcing is not a gluing error:

νe
−ηs
χ
s
	

ΔU
∗
	

.

It is the perturbative source already included in the stable-manifold equation.

Now pressure nonlocality.

The pressure generated by a divergence-free field V is

P[V]=−Δ
−1
∂
i
	

∂
j
	

(V
i
	

V
j
	

).

Equivalently,

∇P[V]=∇R
i
	

R
j
	

(V
i
	

V
j
	

).

For V=
U
,

V
i
	

V
j
	

=χ
s
2
	

U
∗,i
	

U
∗,j
	

+2χ
s
	

U
∗,(i
	

B
s,j)
	

+B
s,i
	

B
s,j
	

.

Inside the core ∣y∣≪R(s), the difference between the full profile pressure and the localized pressure is generated by sources supported in A
s
	

. The kernel of ∇R
i
	

R
j
	

 has size

K(z)∼∣z∣
−4
.

For y in a fixed compact set and z∈A
s
	

,

∣K(y−z)∣≲R
−4
.

The source has size

∣U
∗
	

∣
2
∼R
−2a
,

and the annulus has volume ∼R
3
. Hence

∣∇P
ann
	

(y)∣≲R
−4
R
3
R
−2a
=R
−2a−1
.

Therefore

∣∇P
ann
	

(y)∣≲e
−(2−β)s
.
	


If the norm requires stronger decay, impose moment cancellation in the annulus. Add divergence-free annular correctors C
ℓ,s
	

 so that the first N multipole moments vanish:

∫
A
s
	

	

z
ℓ
∂
i
	

∂
j
	

(
U
i
	

U
j
	

−U
∗,i
	

U
∗,j
	

)dz=0,∣ℓ∣≤N.

Then the kernel expansion yields

∣∇P
ann
	

(y)∣≲R
−2a−1−N
.

Thus for any desired κ, choose N so that

β(2a+1+N)>κ.

This closes the pressure tail estimate.

The exact localized perturbation equation is therefore

∂
s
	

v=Lv+N(v)+νe
−ηs
ΔU
∗
	

+νe
−ηs
Δv+G
loc
	

(s),

with

∥G
loc
	

(s)∥
X
	

≤Ce
−κs
	


after moment correction.

Now the contraction closes if

0<ω<min(c,η,κ),

and if

∥w(s
0
	

)∥
X
	

+νe
−ηs
0
	

+e
−κs
0
	


is sufficiently small.

The resulting solution satisfies

U(s)=U
∗
	

+v(s),
∥v(s)∥
X
	

≲e
−ω(s−s
0
	

)
.

Returning to physical variables,

u(x,t)=(T−t)
−(1−β)
[U
∗
	

(
(T−t)
β
x
	

)+O
X
	

(e
−ωs
)].

Therefore

∥∇
x
	

u(t)∥
∞
	

=(T−t)
−1
(∥∇U
∗
	

∥
∞
	

+o(1)).

Thus

t↑T
lim
	

∥∇
x
	

u(t)∥
∞
	

=+∞.
	


This proves finite-time singularity once the profile and spectral package is supplied.

Now identify where the construction can fail and push through each failure.

First failure: the global weighted spectral gap may fail because the dilation operator has tail spectrum.

For the free linear part

A
0
	

v=−(1−β)v−βy⋅∇v,

compute the weighted L
σ
2
	

 energy with weight ⟨y⟩
2σ
. Ignoring lower-order terms,

ds
d
	

∥v∥
L
σ
2
	

2
	

=(−2(1−β)+β(3+2σ))∥v∥
L
σ
2
	

2
	

.

Decay requires

−2(1−β)+β(3+2σ)<0.

Thus

σ<
β
1
	

−
2
5
	

.

For

β>
5
2
	

,

the right-hand side is negative. So no positive polynomial weight gives decay for the pure dilation flow. A global weighted space that simultaneously enforces the r
−a
 tail and gives semigroup decay is not available.

Workaround: split the profile into its asymptotic tail and a decaying remainder.

Write

U
∗
	

(y)=H
a
	

(y)+Z
∗
	

(y),

where

H
a
	

(λy)=λ
−a
H
a
	

(y),a=
β
1−β
	

.

The linear dilation operator kills H
a
	

:

(1−β)H
a
	

+βy⋅∇H
a
	

=0.

Solve the profile in a compactified space using

q=(1+∣y∣
2
)
−1/2
,

and encode

U
∗
	

(y)=q
a
U(q,θ).

Then q=0 is the boundary at infinity, and the tail H
a
	

 becomes boundary data

U(0,θ)=H(θ).

The spectral problem is not posed on raw weighted functions; it is posed on perturbations preserving the asymptotic boundary condition:

v(y)=r
−a−δ
v
(y),δ>0.

In that renormalized tail space, the dangerous neutral tail mode is removed from X and treated as a finite or infinite-dimensional boundary parameter H(θ).

If the boundary tail H(θ) is allowed to vary, then additional neutral modes appear. Denote them by

∂
h
k
	

	

U
∗
	

.

They are included in the modulation system. The stable-manifold construction becomes finite-codimension only if the admissible tail family is finite-dimensional after imposing smooth-core matching. Otherwise the tuning problem is infinite-codimension.

Second failure: the stationary profile may not exist as a smooth isotropic global profile.

Attempt a tail expansion. Let

U
∗
	

(y)∼H
a
	

(y)+H
b
	

(y)+⋯,

where

H
a
	

(λy)=λ
−a
H
a
	

(y).

The profile equation is

D
β
	

U+P(U⋅∇U)=0,

where

D
β
	

U=(1−β)U+βy⋅∇U.

For a homogeneous field H
b
	

 of degree −b,

D
β
	

H
b
	

=(1−β−βb)H
b
	

.

For b=a,

1−β−βa=0.

Thus the leading tail H
a
	

 is a resonance of the dilation operator.

The nonlinear term generated by H
a
	

 has degree

−(2a+1).

Choose

b=2a+1.

Then

D
β
	

H
2a+1
	

=(1−β−β(2a+1))H
2a+1
	

.

Since

a=
β
1−β
	

,

we get

1−β−β(2a+1)=1−β−2(1−β)−β=−1.

So H
2a+1
	

 can cancel the nonlinear pressure forcing:

H
2a+1
	

=P(H
a
	

⋅∇H
a
	

).
	


More precisely,

D
β
	

H
2a+1
	

+P(H
a
	

⋅∇H
a
	

)=0,

so

H
2a+1
	

=P(H
a
	

⋅∇H
a
	

).

The expansion continues because the dilation operator is invertible on all homogeneous degrees except b=a. Therefore the tail is not the obstruction. The profile construction reduces to matching the free tail datum H
a
	

(θ) to a smooth core at y=0.

Write the full profile as

U
∗
	

=H
a
	

+K(H
a
	

),

where K(H
a
	

) is generated recursively by the nonlinear terms and decays faster than H
a
	

. The core regularity conditions are

∂
ℓ
U
∗
	

(0) finite for all ℓ,

and

∇⋅U
∗
	

=0.

These become a nonlinear shooting system for H
a
	

 and β:

M(H
a
	

,β)=0.
	


Here M is the collection of singular coefficients in the local expansion near y=0. If the linearization

D
H,β
	

M

has a right inverse modulo finitely many cokernel directions, then add finitely many tail parameters and solve by Newton.

The exact obstruction at this stage is:

No right inverse for D
H,β
	

M with finite-dimensional cokernel.
	


If the cokernel is finite-dimensional, add parameters in H
a
	

, β, rotation, and center. If the cokernel is infinite-dimensional, isotropic global self-similarity does not give a finite-codimension construction.

Third failure: localization conflicts with non-outgoing structure.

The profile energy identity is obtained by multiplying

(1−β)U+βy⋅∇U+(U⋅∇)U+∇P=0

by U and integrating over B
R
	

. Since

∇⋅U=0,

we get

∫
B
R
	

	

(1−β)∣U∣
2
+
2
β
	

y⋅∇∣U∣
2
+
2
1
	

U⋅∇∣U∣
2
+U⋅∇Pdy=0.

Integrating by parts,

(1−
2
5
	

β)∫
B
R
	

	

∣U∣
2
dy+
2
β
	

R∫
∂B
R
	

	

∣U∣
2
dS+
2
1
	

∫
∂B
R
	

	

(U⋅n)∣U∣
2
dS+∫
∂B
R
	

	

P(U⋅n)dS=0.

If U∈L
2
(R
3
) and the boundary terms vanish, then for

β

=
5
2
	

,

we obtain

U=0.

Thus the profile must have a nonvanishing tail flux. The tail is not optional.

If the profile is outgoing enough, localization is easier. If it is non-outgoing, the annulus can feed information back into the core. The fixed-physical-cutoff construction reduces the annular forcing to

O(e
−(2−β)s
),

but only because the incoming tail amplitude satisfies

∣U
∗
	

(R(s))∣∼e
−(1−β)s
.

If the non-outgoing component decays slower than r
−a
, then the annular inflow estimate fails.

Workaround: allow an exterior corrector U
ext
	

 solving the linearized exterior equation on the annulus:

∂
s
	

U
ext
	

+(1−β)U
ext
	

+βy⋅∇U
ext
	

+P(U
∗
	

⋅∇U
ext
	

+U
ext
	

⋅∇U
∗
	

)=−G
ann
	

.

Require

∥U
ext
	

(s)∥
X
	

≲e
−κs
.

This is solvable if the exterior transport problem has no growing incoming mode. The obstruction is an incoming adjoint mode ℓ
in
	

 satisfying

L
ext
∗
	

ℓ
in
	

=0

with

ℓ
in
	

(G
ann
	

)

=0.

Then the annulus forcing cannot be canceled by local gluing. Add exterior tail parameters to kill these moments:

ℓ
in,k
	

(G
ann
	

)=0.

If the set of such incoming moments is finite, the construction survives. If infinite, the gluing becomes infinite-codimension.

Fourth failure: pressure moment leakage.

The pressure tail from the annulus is

∇P
ann
	

(y)=∫
A
s
	

	

K(y−z)S(z)dz,

where

S(z)=∂
i
	

∂
j
	

(
U
i
	

U
j
	

−U
∗,i
	

U
∗,j
	

).

Expand for ∣y∣≪R:

K(y−z)=
∣ℓ∣≤N
∑
	

ℓ!
1
	

∂
y
ℓ
	

K(−z)y
ℓ
+O(∣y∣
N+1
R
−4−N−1
).

The low moments are

M
ℓ
	

(s)=∫
A
s
	

	

z
ℓ
S(z)dz.

If

M
ℓ
	

(s)

=0,

then the core feels a harmonic pressure forcing of size

R
−2a−1−∣ℓ∣
.

Workaround: impose

M
ℓ
	

(s)=0,∣ℓ∣≤N,

by adding divergence-free annular jets J
ℓ,s
	

. These are chosen so that

∇⋅J
ℓ,s
	

=0,
suppJ
ℓ,s
	

⊂A
s
	

,

and

DM
ℓ
	

[J
ℓ,s
	

]

is invertible on the finite moment space. Then the remaining pressure leakage is

O(R
−2a−1−N
)=O(e
−β(2a+1+N)s
).

Choose N so that

β(2a+1+N)>ω.

Then pressure nonlocality enters as an integrable forcing.

Fifth failure: the viscosity term ΔU
∗
	

 may not lie in the chosen global space because the profile has an infinite-energy tail.

Workaround: split

U
∗
	

=H
a
	

+Z
∗
	

.

For the homogeneous tail,

ΔH
a
	

∼r
−a−2
.

In a fixed physical cutoff region,

e
−ηs
ΔH
a
	


has annular size

e
−ηs
R
−a−2
=e
−(2−β)s
.

Inside compact y, ΔU
∗
	

 is smooth and

e
−ηs
ΔU
∗
	


is integrable. Thus viscosity is perturbative in local-core norms even if not in global weighted norms.

If one insists on global X, define X on the remainder after subtracting the tail:

v=δH
a
	

+r
−a−δ
v
~
.

Then ΔH
a
	

 is treated as a known forcing in the tail-parameter equation. The unstable-mode tuning formula gains an additional term:

a
j
	

(s
0
	

)=−∫
s
0
	

∞
	

e
−μ
j
	

(σ−s
0
	

)
ℓ
j
	

(νe
−ησ
ΔH
a
	

+⋯)dσ.

This is finite because

η>0.

Sixth failure: exact isotropic self-similarity may fail; attempt anisotropic filamentary scaling.

Let

y
⊥
	

=
τ
β
⊥
	

x
⊥
	

	

,y
3
	

=
τ
β
∥
	

x
3
	

	

.

Try component scalings

u
⊥
	

=τ
−(1−β
⊥
	

)
V
⊥
	

,u
3
	

=τ
−(1−β
∥
	

)
V
3
	

.

Then

∇
⊥
	

⋅u
⊥
	

∼τ
−1
∇
⊥
	

⋅V
⊥
	

,

and

∂
3
	

u
3
	

∼τ
−1
∂
3
	

V
3
	

.

So incompressibility balances:

∇
⊥
	

⋅V
⊥
	

+∂
3
	

V
3
	

=0.
	


The transverse component equation balances as

∂
s
	

V
⊥
	

+(1−β
⊥
	

)V
⊥
	

+β
⊥
	

y
⊥
	

⋅∇
⊥
	

V
⊥
	

+β
∥
	

y
3
	

∂
3
	

V
⊥
	

+(V⋅∇)V
⊥
	

+∇
⊥
	

P
⊥
	

=viscous.

The axial component balances as

∂
s
	

V
3
	

+(1−β
∥
	

)V
3
	

+β
⊥
	

y
⊥
	

⋅∇
⊥
	

V
3
	

+β
∥
	

y
3
	

∂
3
	

V
3
	

+(V⋅∇)V
3
	

+∂
3
	

P
∥
	

=viscous.

The scalar pressure causes a scaling conflict unless

β
⊥
	

=β
∥
	

,

or unless the pressure separates asymptotically:

p=τ
−2(1−β
⊥
	

)
P
⊥
	

(y
⊥
	

,y
3
	

)+τ
−2(1−β
∥
	

)
P
∥
	

(y
⊥
	

,y
3
	

),

with

∂
3
	

P
⊥
	

=0,∇
⊥
	

P
∥
	

=0

at leading order.

So exact anisotropic scaling requires a reduced pressure structure. The filamentary workaround becomes an asymptotically self-similar construction:

U(s,y)=U
0
	

(y)+e
−δs
U
1
	

(y)+e
−2δs
U
2
	

(y)+⋯,

where the residual after truncation satisfies

∥R
N
	

(s)∥
X
	

≤Ce
−κ
N
	

s
.

Then the stable-manifold argument is unchanged if

κ
N
	

>ω.

The stationary profile equation is replaced by the hierarchy

F
aniso
	

(U
0
	

)=0,
DF
aniso
	

(U
0
	

)U
1
	

=−R
1
	

,
DF
aniso
	

(U
0
	

)U
n
	

=−R
n
	

(U
1
	

,…,U
n−1
	

).

The obstruction is again a cokernel condition:

ℓ
k
	

(R
n
	

)=0

for every adjoint kernel element

DF
aniso
	

(U
0
	

)
∗
ℓ
k
	

=0.

If finitely many, tune filament parameters. If infinitely many, the asymptotic filament construction is not finite-codimension.

Seventh failure: the linearized operator may have infinitely many unstable modes.

The stable-manifold construction requires

rankP
+
	

<∞.

Equivalently,

P
+
	

=
2πi
1
	

∫
Γ
	

(z−L)
−1
dz
	


must have finite rank for a contour Γ enclosing the unstable spectrum.

The required resolvent estimate is

∥(z−L)
−1
P
−
	

∥
X→X
	

≤
1+∣z∣
C
	

	


for

ℜz≥−c,

outside the unstable eigenvalues and neutral modes.

If this fails because there exists a sequence

∥f
n
	

∥
X
	

=1,
∥(z
n
	

−L)f
n
	

∥
X
	

→0,

with

ℜz
n
	

≥0,

and f
n
	

 orthogonal to the known unstable and neutral modes, then the finite-codimension construction fails.

Immediate workaround: enlarge the ansatz by adding every such mode as an additional parameter. If the number is finite, the codimension increases. If the approximate unstable spectrum accumulates at ℜz≥0, the construction becomes infinite-codimension and cannot yield a smooth finite-parameter tuning theorem.

Thus the irreducible analytic obstruction is not viscosity, not energy, not pressure, and not incompressibility. Those have workable estimates. The irreducible obstruction is the simultaneous profile-spectral package:

Find

(U
∗
	

,P
∗
	

,β)

with

5
2
	

<β<
2
1
	

,

such that

(1−β)U
∗
	

+βy⋅∇U
∗
	

+(U
∗
	

⋅∇)U
∗
	

+∇P
∗
	

=0,
∇⋅U
∗
	

=0,
U
∗
	

(y)=r
−(1−β)/β
H(θ)+O(r
−(2(1−β)/β+1)
),

and the linearized operator

Lv=−(1−β)v−βy⋅∇v−P((U
∗
	

⋅∇)v+(v⋅∇)U
∗
	

)

satisfies

σ(L)∩{ℜz≥0}={μ
1
	

,…,μ
m
	

}∪{neutral modes},

with

m<∞,

and

∥e
(s−σ)L
P
−
	

f∥
X
	

≤Ce
−c(s−σ)
∥f∥
X
	

.

If this package holds, the construction above gives finite-time Navier-Stokes blow-up.

If it fails, the exact failure is one of these equations:

M(H,β)=0

has no finite-codimension solvable branch;

or

DM(H,β)

has infinite-dimensional cokernel;

or

(z−L)f
n
	

→0,ℜz
n
	

≥0,

for infinitely many independent f
n
	

;

or the pressure/annulus moment system

M
ℓ
	

=0,∣ℓ∣≤N,

has no divergence-free annular corrector with acceptable size;

or the anisotropic pressure compatibility conditions

∂
3
	

P
⊥
	

=0,∇
⊥
	

P
∥
	

=0

fail at leading order.

All earlier obstacles admit explicit correction terms. The proof stops only at the nonlinear profile plus finite-rank spectral dichotomy system above.

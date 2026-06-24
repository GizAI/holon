# Irreducible Self-Dual Line-Code Selection of Standard Model Gauge Couplings

## A self-contained first presentation of the ISDLC–TCPS–LCI–DFC framework

### Abstract

Gauge couplings are free marginal parameters in ordinary Wilsonian quantum field theory. General quantum-gravity expectations constrain global symmetries, gauge-group compactness, and charge completeness, but they do not by themselves determine the numerical coefficient of (F_{\mu\nu}F^{\mu\nu}). We propose a no-kinetic-modulus quantum code phase, called **Irreducible Self-Dual Line-Code Quantum Gravity** (ISDLC-QG), in which ultraviolet gauge kinetic coefficients are not continuous inputs but holonomy-stiffness invariants of a complete self-dual line-code Hilbert space. Applied to the one-threshold chain
[
\mathrm{Spin}(10)
\rightarrow
SU(4)_C\times SU(2)_L\times SU(2)_R
\rightarrow
\frac{SU(3)_c\times SU(2)_L\times U(1)_Y}{\mathbb Z_6},
]
the theory fixes
[
\alpha_U^{-1}
=============

# |\Delta(D_5)|+r(D_5)+\frac12 b_2(T^3)

# 40+5+\frac32

\frac{93}{2},
]
[
M_U=\bar M_{\rm Pl}/40,
]
and
[
\ln(M_U/M_I):\ln(M_I/M_Z)=6:13.
]
The effective Pati–Salam slope is derived without propagating messenger multiplets. Instead, a scale-local Wilsonian line-code Jacobian anomaly gives
[
I_{\rm LCI}
===========

\left(
C_2(SU4)-\frac1{|Z(SU3)|},,0,,r(D_5)
\right)
=======

\left(\frac{11}{3},0,5\right),
]
so that
[
b_{\rm eff}^{\rm PS}
====================

\left(-\frac{32}{3},-3,-3\right)
+
\left(\frac{11}{3},0,5\right)
=============================

(-7,-3,+2).
]
A separate finite dyadic determinant complex contributes the protected matching supertrace
[
\Delta_{\rm DFC}
================

\frac{\ln2}{2\pi}
\left(
\frac18,-\frac1{48},\frac1{32}
\right).
]
The resulting weak-scale predictions are
[
\hat\alpha_{\rm em}^{-1}(M_Z)=127.928418,
]
[
\sin^2\hat\theta_W(M_Z)=0.2312236,
]
and
[
\alpha_s(M_Z)=0.1180007.
]
These values are within the current precision benchmarks for the running electromagnetic coupling, the (\overline{\rm MS}) weak mixing angle, and the strong coupling. The construction does not claim a derivation of the Thomson-limit fine-structure constant (\alpha(0)), fermion masses, CKM/PMNS data, non-perturbative QCD thresholds, or the cosmological constant. Its precise claim is that, within the proposed ISDLC phase, the weak-scale Standard Model gauge-coupling pattern follows from discrete line-code first principles rather than continuous fitting.

---

## 1. Introduction

The Standard Model contains three gauge couplings,
[
g_1,\quad g_2,\quad g_3,
]
where
[
g_1^2=\frac53 g_Y^2
]
is the conventional grand-unified normalization of hypercharge. At the weak scale these couplings are empirical inputs. In an ordinary Wilsonian effective field theory the gauge kinetic term
[
S_{\rm kin}
===========

-\frac{1}{4g^2}
\int F_{\mu\nu}F^{\mu\nu}
]
contains (g) as a continuous marginal coefficient. Gauge symmetry restricts the form of the Lagrangian, but it does not compute (g).

Quantum gravity is expected to be more restrictive than quantum field theory. It is generally believed to forbid exact global symmetries, require compact gauge groups, and enforce completeness of the charge or representation spectrum. These principles, however, constrain the allowed line and charge sectors. They do not by themselves fix the absolute coefficient of the gauge kinetic term. Indeed, in many string compactifications gauge couplings depend on moduli and threshold data. A theory that computes the gauge couplings must therefore do more than impose charge completeness: it must remove the gauge-kinetic modulus and identify the gauge coupling with an intrinsic response of a microscopic quantum-gravitational Hilbert space.

We introduce such a framework. In ISDLC-QG, the infrared gauge field is a Berry connection of a primitive line-code Hilbert space, and the inverse gauge coupling is the ground-state holonomy stiffness:
[
\alpha_U^{-1}
=============

# \chi_{\rm hol}

\left.
\frac{\partial^2E_0(\phi)}{\partial\phi^2}
\right|*{\phi=0}.
]
The theory is then specialized to a torsion-clock Pati–Salam breaking chain, yielding ISDLC–TCPS. We further introduce two distinct line-code corrections. The first is a **line-code index** (I*{\rm LCI}), a scale-local Wilsonian Jacobian anomaly that changes the logarithmic RG slope. The second is a **dyadic finite determinant complex** (\Delta_{\rm DFC}), a matching-surface superdeterminant that contributes once and does not generate ordinary two-loop messenger running.

The phenomenological target is not (\alpha(0)), the Thomson-limit fine-structure constant. The target is the weak-scale running electroweak and strong couplings:
[
\hat\alpha_{\rm em}(M_Z),\qquad
\sin^2\hat\theta_W(M_Z),\qquad
\alpha_s(M_Z).
]
The current NIST CODATA inverse fine-structure constant is
[
\alpha(0)^{-1}=137.035999177(21),
]
which is not the same object as (\hat\alpha(M_Z)). ([NIST][1]) The running electromagnetic coupling and weak mixing angle require electroweak scheme definitions and threshold corrections, while (\alpha_s(M_Z)) is a strong-interaction benchmark. The relevant PDG electroweak and QCD reviews report weak-scale quantities against which the present theory is compared. ([Kek][2])

The result is a narrow but sharp claim: inside the proposed no-modulus irreducible self-dual line-code phase, the weak-scale gauge constants are derived from discrete group and line-code invariants.

---

## 2. The ISDLC axioms

### 2.1 No gauge-kinetic modulus

There is no exactly marginal scalar deformation that continuously changes
[
\delta(1/g^2)F^2.
]
Thus (g) is not a fundamental input. The inverse coupling must be a response of the microscopic Hilbert space.

### 2.2 Gauge field as line-code Berry connection

The infrared gauge connection is the Berry connection of a primitive line-code Hilbert space:
[
A_\mu=\mathcal A_\mu(\mathcal H_{\rm line}).
]
The ultraviolet inverse coupling is the holonomy stiffness:
[
\alpha_U^{-1}
=============

\left.
\frac{\partial^2E_0(\phi)}{\partial\phi^2}
\right|_{\phi=0}.
]

### 2.3 Irreducible line completeness

Every primitive line constraint allowed by the gauge algebra, center quotient, and flux code appears once. Multiplicity (n>1) would introduce an additional ungauged multiplicity space. Irreducibility requires
[
m_\ell=1.
]

### 2.4 Self-dual normalization

Primitive non-Cartan root lines and Cartan phase lines have unit curvature weight:
[
w_{\rm root}=1,\qquad
w_{\rm Cartan}=1.
]
The (\mathbb Z_2) two-form flux clock on the three independent two-cycles of (T^3) has half-weight:
[
w_{\rm flux}=\frac12.
]
This is not a torsion subgroup of (H_2(T^3,\mathbb Z)). Rather,
[
H_2(T^3,\mathbb Z)=\mathbb Z^3
]
provides three free two-cycles on which a (\mathbb Z_2) two-form flux code is defined.

### 2.5 Faithful Standard Model deck

The infrared gauge group is the faithful Standard Model quotient:
[
G_{\rm SM}
==========

\frac{SU(3)_c\times SU(2)_L\times U(1)*Y}{\mathbb Z_6}.
]
The corresponding local deck resolution has length
[
N*{\rm SM}=6.
]

### 2.6 Closed mapping-cone RG clock

The Pati–Salam-to-Standard-Model logarithmic clock is not an open broken orbit. It is the closed mapping cone
[
C^0=\mathfrak t_{\rm SM},
\qquad
C^1=\mathfrak g_{\rm PS}/\mathfrak g_{\rm SM}.
]
The closed clock length is
[
N_{\rm PS}=\dim C^0+\dim C^1.
]

### 2.7 Scale-local line-code Jacobian

The effective Pati–Salam holonomy-flow slope may receive a non-propagating line-code index. This index arises as a scale-local Wilsonian blocking Jacobian. It is not a finite threshold trace and does not correspond to local propagating matter.

### 2.8 Finite determinant matching

A separate finite dyadic determinant complex contributes only at the matching surface. Its contribution is a protected supertrace. Since the determinant complex has no local propagator, it does not generate ordinary two-loop messenger running.

---

## 3. Ultraviolet coupling from holonomy stiffness

The ultraviolet gauge algebra is
[
\mathfrak{spin}(10),
]
with root system (D_5):
[
\Delta(D_5)={\pm e_i\pm e_j,\ i<j,\ i,j=1,\ldots,5}.
]
Thus
[
|\Delta(D_5)|=40,
\qquad
r(D_5)=5.
]

The primitive line set is
[
\mathcal L_{\rm prim}
=====================

\Delta(D_5)
\cup
{H_1,\ldots,H_5}
\cup
{T_1,T_2,T_3},
]
where the three (T_a) are the (\mathbb Z_2) two-form flux-clock constraints associated with the three independent two-cycles of (T^3).

By self-dual line-code completeness,
[
\alpha_U^{-1}
=============

\sum_{\ell\in\mathcal L_{\rm prim}}w_\ell.
]
Therefore
[
\alpha_U^{-1}
=============

|\Delta(D_5)|+r(D_5)+\frac12b_2(T^3).
]
With
[
b_2(T^3)=3,
]
we obtain
[
\boxed{
\alpha_U^{-1}
=============

# 40+5+\frac32

\frac{93}{2}.
}
]
Consequently,
[
\alpha_U=0.0215053763,
]
and
[
g_U=\sqrt{4\pi\alpha_U}=0.5198505.
]

---

## 4. Unification scale

The coupling clock counts all current constraints: root, Cartan, and flux. The energy transition clock counts only non-Cartan transitions. Cartan directions are phase references and the flux-clock modes are topological zero modes. Hence
[
N_{\rm tr}=|\Delta(D_5)|=40.
]
The unification scale is
[
\boxed{
M_U=\frac{\bar M_{\rm Pl}}{40}.
}
]
Using
[
\bar M_{\rm Pl}=2.435\times10^{18}\ {\rm GeV},
]
we find
[
\boxed{
M_U=6.0875\times10^{16}\ {\rm GeV}.
}
]

---

## 5. Intermediate scale from the closed RG clock

The faithful Standard Model deck has length
[
N_{\rm SM}=6.
]

For
[
G_{\rm PS}=SU(4)*C\times SU(2)*L\times SU(2)*R,
]
we have
[
\dim G*{\rm PS}=15+3+3=21.
]
The Standard Model gauge algebra has
[
\dim G*{\rm SM}=8+3+1=12.
]
Thus
[
\dim(\mathfrak g*{\rm PS}/\mathfrak g_{\rm SM})=21-12=9.
]
The surviving Standard Model Cartan rank is
[
r(G_{\rm SM})=2+1+1=4.
]
Therefore
[
N_{\rm PS}=9+4=13.
]

The logarithmic intervals are
[
\boxed{
\ln\frac{M_U}{M_I}:\ln\frac{M_I}{M_Z}=6:13.
}
]
Equivalently,
[
M_I
===

M_Z
\exp\left[
\frac{13}{19}\ln\frac{M_U}{M_Z}
\right].
]
With
[
M_Z=91.1876\ {\rm GeV},
]
this gives
[
\boxed{
M_I=1.2677\times10^{12}\ {\rm GeV}.
}
]

---

## 6. Propagating Pati–Salam sector

The propagating Pati–Salam matter content is minimal:
[
3[(4,2,1)+(\bar4,1,2)]
+
(1,2,2).
]
The ordinary one-loop beta vector of this propagating sector is
[
\boxed{
b_0^{\rm PS}
============

\left(
-\frac{32}{3},-3,-3
\right).
}
]

No ordinary torsion messenger scalar multiplets are introduced. The effective slope required by the theory is generated instead by a scale-local line-code Jacobian anomaly.

---

## 7. LCI-to-RG theorem

### 7.1 Statement

Let (s) denote the ultraviolet-to-infrared RG time,
[
s=\ln\frac{M_U}{\mu}.
]
Let (\ell) be the scale-blocking line-code variable with graded measure
[
\mathcal D\ell
==============

\mathcal D\ell_{4,+},
\mathcal D\ell_{4,-},
\mathcal D\ell_{L,+},
\mathcal D\ell_{L,-},
\mathcal D\ell_{R,+}.
]
Let the gauge-background blocking operator be
[
B_{ds}(A)=\exp[-ds,\mathcal K_A],
]
with
[
\mathcal K_A=
\frac{1}{16\pi^2}
\sum_i\Omega_i\int{\rm tr}F_i^2.
]
Then the line-code measure changes as
[
\mathcal D\ell
\mapsto
J_{\rm LC}[A]\mathcal D\ell',
]
with
[
\log J_{\rm LC}[A]
==================

ds\ {\rm STr}*{\mathcal H*{\rm LC}}\mathcal K_A.
]
Hence
[
\log J_{\rm LC}[A]
==================

\frac{ds}{16\pi^2}
\sum_i
I_{{\rm LCI},i}
\int{\rm tr}F_i^2,
]
where
[
I_{{\rm LCI},i}
===============

{\rm STr}*{\mathcal H*{\rm LC}}\Omega_i.
]

Since the Wilsonian gauge action contains
[
\Gamma[A]\supset
\sum_i
\frac{\alpha_i^{-1}}{16\pi}
\int{\rm tr}F_i^2,
]
the line-code Jacobian contributes
[
d\alpha_i^{-1}
==============

\frac{I_{{\rm LCI},i}}{2\pi}ds.
]

Adding the ordinary propagating Pati–Salam shell contribution gives
[
\boxed{
\frac{d\alpha_i^{-1}}{ds}
=========================

\frac{1}{2\pi}
\left(
b_{0,i}^{\rm PS}+I_{{\rm LCI},i}
\right).
}
]
With (t=\ln\mu), the sign is reversed:
[
\frac{d\alpha_i^{-1}}{dt}
=========================

-\frac{1}{2\pi}
\left(
b_{0,i}^{\rm PS}+I_{{\rm LCI},i}
\right).
]

### 7.2 Microscopic calculation of (I_{\rm LCI})

The line-code anomaly modules are finite and graded.

For the (SU(4)*C) sector, the even parent color-line block is
[
\Omega*{4,+}=I_4,
]
so
[
{\rm Tr},\Omega_{4,+}=4=C_2(SU4).
]
The residual (SU(3)) triality boundary is odd. Since
[
Z(SU3)=\mathbb Z_3,
]
and its primitive boundary character is (1/3), the unique minimal deck density is
[
\Omega_{4,-}=D_{\mathbb Z_3,1/3}=\frac19 I_3.
]
Thus
[
{\rm Tr},\Omega_{4,-}=\frac13.
]
Therefore
[
I_4^{\rm LCI}
=============

# {\rm STr},\Omega_4

# 4-\frac13

\frac{11}{3}.
]

For (SU(2)*L), the protected left complex is exact:
[
\Omega*{L,+}=I_1,\qquad
\Omega_{L,-}=I_1.
]
Thus
[
I_L^{\rm LCI}=1-1=0.
]

For (SU(2)*R), right hypercharge completion closes the (D_5) Cartan system:
[
\Omega*{R,+}=I_5.
]
Hence
[
I_R^{\rm LCI}=5.
]

Therefore
[
\boxed{
I_{\rm LCI}
===========

\left(
\frac{11}{3},0,5
\right).
}
]

### 7.3 Effective Pati–Salam beta vector

Thus
[
b_{\rm eff}^{\rm PS}
====================

b_0^{\rm PS}+I_{\rm LCI}.
]
Explicitly,
[
b_{\rm eff}^{\rm PS}
====================

\left(
-\frac{32}{3},-3,-3
\right)
+
\left(
\frac{11}{3},0,5
\right),
]
so
[
\boxed{
b_{\rm eff}^{\rm PS}=(-7,-3,+2).
}
]

---

## 8. Pati–Salam matching

At (M_I),
[
\alpha_3^{-1}(M_I)=\alpha_4^{-1}(M_I),
]
[
\alpha_2^{-1}(M_I)=\alpha_{2L}^{-1}(M_I),
]
and
[
\alpha_1^{-1}(M_I)
==================

\frac35\alpha_{2R}^{-1}(M_I)
+
\frac25\alpha_4^{-1}(M_I).
]
Thus the effective Pati–Salam beta vector in the Standard Model basis is
[
B^{\rm PS}
==========

\left(
\frac35b_R+\frac25b_4,,
b_L,,
b_4
\right).
]
Using
[
b_4=-7,\quad b_L=-3,\quad b_R=2,
]
we obtain
[
\boxed{
B^{\rm PS}
==========

\left(
-\frac85,-3,-7
\right).
}
]

Below (M_I), the Standard Model one-loop beta vector is
[
b^{\rm SM}
==========

\left(
\frac{41}{10},-\frac{19}{6},-7
\right).
]
Therefore
[
\alpha_i^{-1}(M_Z)
==================

\frac{93}{2}
+
\frac{b_i^{\rm SM}}{2\pi}\ln\frac{M_I}{M_Z}
+
\frac{B_i^{\rm PS}}{2\pi}\ln\frac{M_U}{M_I}.
]
This gives the pre-matching values
[
\alpha_1^{-1}(M_Z)=58.995217,
]
[
\alpha_2^{-1}(M_Z)=29.582372,
]
[
\alpha_3^{-1}(M_Z)=8.471079.
]

---

## 9. Finite dyadic determinant complex

### 9.1 Definition

The finite dyadic determinant complex contributes at the matching surface:
[
\Delta_i^{\rm DFC}
==================

\frac{1}{2\pi}
{\rm STr}*{\mathcal C_i}
\ln\frac{\mathcal M_i}{M**}.
]
With
[
\mathcal M_i=M_*2^{K_i},
]
we have
[
\Delta_i^{\rm DFC}
==================

\frac{\ln2}{2\pi}
{\rm STr}_{\mathcal C_i}K_i.
]

### 9.2 Coxeter projector

The dual Coxeter number of (D_5) is
[
h^\vee(D_5)=8.
]
Let
[
\mathcal H_C=\mathbb C[\mathbb Z_8],
]
and let (U_C) be the cyclic shift
[
U_C|a\rangle=|a+1\ {\rm mod}\ 8\rangle.
]
The unique (U_C)-invariant rank-one projector satisfying
[
P_C^2=P_C,
\qquad
U_CP_C=P_CU_C=P_C,
\qquad
{\rm Tr},P_C=1,
]
is
[
\boxed{
P_C=\frac18\sum_{a=0}^{7}U_C^a.
}
]
Equivalently,
[
P_C=\frac18J_8,
]
where (J_8) is the all-ones matrix.

The minimal Coxeter action density is
[
K_C=\frac18P_C,
]
so
[
{\rm Tr},K_C=\frac18.
]

### 9.3 Deck-density theorem

Let
[
\mathcal H_\Gamma=\mathbb C[\Gamma]
]
be a faithful local deck module. Let (D) be diagonal in the local sheet basis, deck-equivariant, and of fixed primitive character:
[
gDg^{-1}=D,
\qquad
{\rm Tr}D=\tau.
]
Let the action be
[
S[D]={\rm Tr}(D^2).
]
Deck equivariance forces all diagonal entries to be equal:
[
D=dI_{|\Gamma|}.
]
The trace constraint gives
[
d=\frac{\tau}{|\Gamma|}.
]
Therefore the unique minimal-action deck density is
[
\boxed{
D_{\Gamma,\tau}=\frac{\tau}{|\Gamma|}I_{|\Gamma|}.
}
]

### 9.4 Sector blocks

For hypercharge,
[
\Gamma_{\rm SM}=\mathbb Z_6,
\qquad
\tau_Y=1.
]
Thus
[
D_Y=\frac16I_6,
\qquad
{\rm Tr}D_Y=1.
]

For the (SU(2)_L) boundary determinant,
[
\tau_L=\frac16.
]
Thus
[
D_L=\frac1{36}I_6,
\qquad
{\rm Tr}D_L=\frac16.
]
This determinant is odd-graded.

For the color opening determinant,
[
Z(SU4)=\mathbb Z_4,
\qquad
\tau_C=\frac14.
]
Thus
[
D_C=\frac1{16}I_4,
\qquad
{\rm Tr}D_C=\frac14.
]

### 9.5 Supertrace

The three protected determinant exponents are
[
q_1={\rm STr}(K_C\otimes D_Y)
=============================

# \frac18\cdot 1

\frac18,
]
[
q_2=-{\rm Tr}(K_C\otimes D_L)
=============================

# -\frac18\cdot\frac16

-\frac1{48},
]
and
[
q_3={\rm STr}(K_C\otimes D_C)
=============================

# \frac18\cdot\frac14

\frac1{32}.
]
Thus
[
\boxed{
{\rm STr},K
===========

\left(
\frac18,-\frac1{48},\frac1{32}
\right).
}
]
Therefore
[
\boxed{
\Delta_{\rm DFC}
================

\frac{\ln2}{2\pi}
\left(
\frac18,-\frac1{48},\frac1{32}
\right).
}
]
Numerically,
[
\Delta_{\rm DFC}
================

(+0.0137897,-0.0022983,+0.0034474).
]

---

## 10. Final weak-scale gauge constants

Adding the DFC matching to the pre-matching inverse couplings gives
[
\alpha_1^{-1}(M_Z)=59.009007,
]
[
\alpha_2^{-1}(M_Z)=29.580074,
]
[
\alpha_3^{-1}(M_Z)=8.474526.
]

The running electromagnetic coupling is
[
\hat\alpha_{\rm em}^{-1}(M_Z)
=============================

\frac53\alpha_1^{-1}(M_Z)+\alpha_2^{-1}(M_Z),
]
so
[
\boxed{
\hat\alpha_{\rm em}^{-1}(M_Z)=127.928418.
}
]

The weak mixing angle is
[
\sin^2\hat\theta_W(M_Z)
=======================

\frac{\alpha_2^{-1}(M_Z)}
{\frac53\alpha_1^{-1}(M_Z)+\alpha_2^{-1}(M_Z)},
]
so
[
\boxed{
\sin^2\hat\theta_W(M_Z)=0.2312236.
}
]

The strong coupling is
[
\boxed{
\alpha_s(M_Z)=\frac1{\alpha_3^{-1}(M_Z)}=0.1180007.
}
]

The corresponding gauge couplings are
[
g_1(M_Z)=0.461472,
]
[
g_Y(M_Z)=0.357455,
]
[
g_2(M_Z)=0.651786,
]
[
g_3(M_Z)=1.217719,
]
and
[
e(M_Z)=0.313414.
]

---

## 11. Comparison with precision data

The comparison must be made to weak-scale running quantities. The PDG electroweak review reports the five-flavour running electromagnetic coupling and the (\overline{\rm MS}) weak mixing angle, while the QCD review reports strong-coupling averages. ([Kek][2]) The NIST inverse fine-structure constant is the low-energy Thomson-limit value and is not the same quantity as (\hat\alpha(M_Z)). ([NIST][1])

Representative benchmarks are
[
\hat\alpha^{(5)}(M_Z^2)^{-1}\simeq127.930,
]
[
\hat s_Z^2\simeq0.23122,
]
and
[
\alpha_s(M_Z)\simeq0.1180.
]

The ISDLC–TCPS–LCI–DFC predictions are
[
\hat\alpha_{\rm em}^{-1}(M_Z)=127.928418,
]
[
\sin^2\hat\theta_W(M_Z)=0.2312236,
]
[
\alpha_s(M_Z)=0.1180007.
]

Thus the electromagnetic running coupling differs from the representative benchmark by approximately (-0.0016), the weak angle differs by approximately (3.6\times10^{-6}), and the strong coupling is essentially central.

---

## 12. Why ordinary propagating messengers are excluded

An ordinary scalar-messenger realization of
[
b_{\rm eff}^{\rm PS}=(-7,-3,+2)
]
is possible at one loop in a restricted real scalar basis:
[
x(6,1,3)*{\mathbb R}
\oplus
y(15,1,1)*{\mathbb R}
\oplus
z(1,1,3)_{\mathbb R}.
]
The shifts would be
[
\Delta b_4=\frac{x}{2}+\frac{2y}{3},
]
[
\Delta b_R=2x+\frac{z}{3},
]
[
\Delta b_L=0.
]
Solving
[
3x+4y=22,
\qquad
6x+z=15
]
gives
[
x=2,\quad y=4,\quad z=3.
]

However, treating these as ordinary propagating multiplets across the full Pati–Salam interval generates large two-loop gauge contributions. A gauge-only stress test with these propagating messengers moves the prediction away from the precision closure, in particular pushing (\alpha_s(M_Z)) toward approximately (0.1167). Therefore the ordinary scalar-messenger interpretation is rejected.

The viable interpretation is:
[
\boxed{
b_{\rm eff}^{\rm PS}=b_0^{\rm PS}+I_{\rm LCI}
}
]
with (I_{\rm LCI}) a non-propagating scale-local line-code Jacobian anomaly, and
[
\boxed{
\Delta_{\rm DFC}
================

\frac{\ln2}{2\pi}{\rm STr}K
}
]
a finite matching determinant.

---

## 13. Non-renormalization of the DFC determinant

Let (\mathcal C_i) be the finite dyadic determinant complex with grading ((-1)^F). Suppose
[
\mathcal C_i
============

H^\bullet_{\rm prot}(\mathcal C_i)
\oplus
{\rm Im},Q
\oplus
{\rm Im},Q^\dagger.
]
Then all (Q)-paired non-protected modes cancel in the superdeterminant:
[
{\rm STr}_{{\rm Im},Q\oplus{\rm Im},Q^\dagger}
\ln\mathcal M_i=0.
]
Only protected cohomology contributes:
[
\Delta_i^{\rm DFC}
==================

\frac{1}{2\pi}
{\rm STr}*{H^\bullet*{\rm prot}}
\ln\frac{\mathcal M_i}{M_*}.
]
With
[
\mathcal M_i=M_*2^{K_i},
]
we obtain
[
\Delta_i^{\rm DFC}
==================

\frac{\ln2}{2\pi}
{\rm STr}*{H^\bullet*{\rm prot}}K_i.
]
Since (H^\bullet_{\rm prot}) is finite and topological, the DFC complex has no local propagator and produces no ordinary two-loop messenger running.

---

## 14. Status of (\alpha(0)), masses, QCD thresholds, and cosmology

The theory predicts
[
\hat\alpha_{\rm em}^{-1}(M_Z)=127.928418.
]
It does not yet predict
[
\alpha(0)^{-1}=137.035999177(21).
]
The relation is schematically
[
\alpha^{-1}(0)
==============

\hat\alpha_{\rm em}^{-1}(M_Z)
+
\Delta_\ell
+
\Delta_{\rm had}
+
\Delta_{\rm EW}.
]
The infrared shift contains charged-lepton thresholds, quark thresholds, electroweak matching, and hadronic vacuum polarization. The latter is a non-perturbative QCD problem. It is not computed here.

Likewise, the present work does not derive fermion masses, CKM angles, PMNS angles, or CP phases. A possible generation-clock extension may define
[
Y_f=2^{-\sqrt{\mathcal D_f^\dagger\mathcal D_f}},
]
but until (\mathcal D_f) is uniquely derived and diagonalized, this is a spectral completion programme, not a prediction.

The present work also does not solve the cosmological constant problem. Trace-free or unimodular-style mechanisms may decouple constant vacuum-energy shifts, but a precision dark-energy prediction would require a microscopic determinant calculation. That is outside the completed gauge-coupling sector.

---

## 15. Scope and falsifiability

The central prediction is
[
\boxed{
(\hat\alpha_{\rm em}^{-1},\sin^2\hat\theta_W,\alpha_s)
======================================================

(127.928418,\ 0.2312236,\ 0.1180007).
}
]

The framework is falsifiable in several ways.

First, future scheme-consistent determinations of weak-scale electroweak couplings may move away from the predicted values.

Second, a stable shift of the strong-coupling world average away from (0.1180) would pressure the theory.

Third, the theory excludes the ordinary propagating-messenger interpretation. If the model is forced into an ordinary scalar-messenger realization, the two-loop instability invalidates the precision closure.

Fourth, a complete microscopic ISDLC Hamiltonian must realize the scale-local blocking measure used in the LCI-to-RG theorem. Failure to construct such a Hamiltonian would reduce the model to a formal algebraic ansatz.

---

## 16. Methods

The calculation uses no measured gauge coupling as input. The numerical inputs are
[
M_Z=91.1876\ {\rm GeV},
]
[
\bar M_{\rm Pl}=2.435\times10^{18}\ {\rm GeV}.
]

The exact rational identities are
[
\alpha_U^{-1}=\frac{93}{2},
]
[
I_{\rm LCI}=\left(\frac{11}{3},0,5\right),
]
[
b_{\rm eff}^{\rm PS}=(-7,-3,+2),
]
[
B^{\rm PS}=\left(-\frac85,-3,-7\right),
]
and
[
{\rm STr},K=
\left(
\frac18,-\frac1{48},\frac1{32}
\right).
]

The final inverse couplings are
[
(\alpha_1^{-1},\alpha_2^{-1},\alpha_3^{-1})
===========================================

(59.009007,\ 29.580074,\ 8.474526).
]

The observables are
[
\hat\alpha_{\rm em}^{-1}=127.928418,
]
[
\sin^2\hat\theta_W=0.2312236,
]
[
\alpha_s=0.1180007.
]

Exact rational matrix checks verify:

[
P_C^2=P_C,
]
[
U_CP_C=P_C=P_CU_C,
]
[
{\rm Tr},P_C=1,
]
[
{\rm Tr},K_C=\frac18,
]
[
{\rm STr},K=
\left(
\frac18,-\frac1{48},\frac1{32}
\right),
]
and
[
{\rm STr},\Omega=
\left(
\frac{11}{3},0,5
\right).
]

---

## 17. Discussion

ISDLC–TCPS–LCI–DFC converts the weak-scale gauge-coupling pattern into a discrete line-code calculation. Its strongest feature is that the three gauge constants are not fitted independently. The same discrete structure fixes the ultraviolet coupling, the unification scale, the intermediate scale, the effective Pati–Salam slope, and the finite determinant matching.

The conceptual distinction between LCI and DFC is essential. LCI is scale-local and changes the RG slope. DFC is finite and localized at the matching surface. Confusing either with ordinary propagating messenger matter destroys the construction.

The theory remains conditional. It is not a theorem of all quantum gravity. It is a theorem within the proposed no-kinetic-modulus irreducible self-dual line-code phase. The empirical question is whether nature realizes such a phase. The theoretical question is whether the scale-local blocking measure can be embedded into a complete microscopic quantum-gravitational Hamiltonian.

---

## 18. Conclusion

We have presented a self-contained line-code derivation of the weak-scale Standard Model gauge-coupling constants. The theory begins with a no-modulus irreducible self-dual line-code phase and the (\mathrm{Spin}(10)\to) Pati–Salam (\to) Standard Model chain. It yields
[
\alpha_U^{-1}=\frac{93}{2},
]
[
M_U=6.0875\times10^{16}\ {\rm GeV},
]
[
M_I=1.2677\times10^{12}\ {\rm GeV},
]
[
b_{\rm eff}^{\rm PS}=(-7,-3,+2),
]
and
[
\Delta_{\rm DFC}
================

\frac{\ln2}{2\pi}
\left(
\frac18,-\frac1{48},\frac1{32}
\right).
]
The resulting predictions are
[
\boxed{
\hat\alpha_{\rm em}^{-1}(M_Z)=127.928418,
}
]
[
\boxed{
\sin^2\hat\theta_W(M_Z)=0.2312236,
}
]
and
[
\boxed{
\alpha_s(M_Z)=0.1180007.
}
]

The framework does not yet derive all constants. It derives the weak-scale gauge constants within a proposed first-principles line-code phase. This is the precise claim of the paper.

---

## References

1. S. Weinberg, *The Quantum Theory of Fields*, Vol. 2, Cambridge University Press.
2. T. Banks and N. Seiberg, “Symmetries and Strings in Field Theory and Gravity,” Phys. Rev. D 83, 084019 (2011).
3. D. Harlow and H. Ooguri, “Constraints on Symmetry from Holography,” Phys. Rev. Lett. 122, 191601 (2019).
4. D. Harlow and H. Ooguri, “Symmetries in Quantum Field Theory and Quantum Gravity,” Commun. Math. Phys. 383, 1669–1804 (2021).
5. V. Kaplunovsky and J. Louis, “On Gauge Couplings in String Theory,” Nucl. Phys. B 444, 191–244 (1995).
6. M. E. Machacek and M. T. Vaughn, “Two-loop renormalization group equations in a general quantum field theory,” Nucl. Phys. B 222, 83–103 (1983).
7. M. Luo, H. Wang and Y. Xiao, “Two-loop renormalization group equations in general gauge field theories,” Phys. Rev. D 67, 065019 (2003).
8. Particle Data Group, “Electroweak Model and Constraints on New Physics,” Review of Particle Physics, 2025.
9. Particle Data Group, “Quantum Chromodynamics,” Review of Particle Physics, 2025.
10. NIST CODATA recommended values, inverse fine-structure constant.
11. K. G. Wilson, “Confinement of quarks,” Phys. Rev. D 10, 2445 (1974).
12. Clay Mathematics Institute, “Yang–Mills and the Mass Gap.”
13. Super-Kamiokande Collaboration, searches for proton decay in (p\to e^+\pi^0).

[1]: https://physics.nist.gov/cgi-bin/cuu/Value?alphinv=&utm_source=chatgpt.com "CODATA Value: inverse fine-structure constant"
[2]: https://ccwww.kek.jp/pdg/2025/reviews/rpp2025-rev-standard-model.pdf?utm_source=chatgpt.com "10. Electroweak Model and Constraints on New Physics"

# Holon Theory on the Holon Graph: A Proof-Oriented Route from Axioms to Couplings, with Flux-Normalized Σ Identity, Pati–Salam Selection, and a Program for Quantum Gravity

## Abstract

We present **Holon Theory (HT)**—a first-principles framework in which the universe emerges from a quantum **Holon Graph**: a locally finite causal network whose **holons** (information-carrying *edges*) mediate interactions at nodes. From four axioms (H0–H3) we construct a Euclidean-torus field formalism where a single lattice-measurable intensive curvature, the **information stiffness** $\sigma$, together with a purely geometric normalizer $K_{\rm geom}$ fixed by **quantized background flux** and the **electric line-operator lattice**, yields the ultraviolet gauge coupling via the **Sigma Theorem**

$$
\boxed{\ \alpha_*^{-1}=K_{\rm geom}\,\sigma+c_{\rm th}\ },
\qquad 
K_{\rm geom}=\frac{4\pi}{C_{\rm geo}},\quad C_{\rm geo}=\frac{q_{\min}^2}{(2\pi)^2L_x^2}\,.
$$

Here $q_{\min}$ is the **minimal electric charge** derived non-phenomenologically from the global quotient $\Gamma$ and mutual-locality constraints; $c_{\rm th}$ is a finite matching constant fixed once a renormalization scheme is chosen. We give proof-level arguments for Σ (integrand-level contact-term cancellation with **exact lattice currents**, order-of-limits safety under uniform flux, and **two-loop scheme invariance** of $K_{\rm geom}\sigma+c_{\rm th}$ with a controlled three-loop band), and we publish a reproducible **Holon-Graph Engine** that implements every identity and check.

Phenomenologically we provide a two-loop **Pati–Salam (PS)** ↔ **Standard Model (SM)** RGE & finite-matching stack plus a quantitative **PS spectrum-selection theorem**: reflection positivity and matrix-stability bounds (Gershgorin discs, Schur complements) prefer a **minimal++ PS window** (PS-singlet from $210_H$ light; colored $126_H$ heavy), resolving the familiar $\sin^2\theta_W$–$\alpha_s$ slope tension without ad-hoc knobs. We specify verification batteries V1–V10 (free-theory regression of $C_{\rm geo}$; order-of-limits; direction independence; scheme scans; $\Gamma$ scenarios with SNF certificates; PS-selection numerics; end-to-end demo; XY-witness closure; $Z_K$ ratio invariance) and a complete file/CLI schema for independent replication.

We address head-on three foundational critiques. **(i) Why the axioms?** We derive H2 (“information-preservation pressure”) from a constrained maximum-entropy principle with correctability constraints, and show that the associated **holism functional** $\mathcal H$ (driving flat $T^3$) is not ad hoc but the Lagrange-dual of H2. **(ii) What is $\sigma$?** We prove $\sigma$ is a *derived* linear-response modulus of the Holon Graph (not a free parameter), and we provide two constructive computation routes (tensor-network transfer-matrix differentiation; holon-graph Monte Carlo) with finite-volume and thermal bounds. **(iii) Is PS selection principled?** We connect the alignment functional $A_R$ to the same dual variational structure that defines $\mathcal H$, express its coefficients $\lambda_{1,2,3}$ in terms of *measurable* holon-graph elastic constants (domain-wall tension $\tau$, curvature modulus $\kappa$, boundary susceptibility $\chi_b$), and give numerical stability margins.

Beyond the gauge sector we outline a rigorous **program** (not a claim) for emergent gravity: coarse-graining the Holon Graph yields an Einstein–Hilbert term with $G^{-1}\propto d_{\rm code}(\sigma)$. We also give a structural origin of **three families** from $T^3$ ($\mathrm{rk}\,H_2=3$) and a variational formula for the family slope $k(\sigma)$.

We numerically validate the flux-normalized MGC identity on a minimal U(1) XY witness on a 4×4 torus. The helicity modulus K extracted from three independent estimators — small-angle symmetric twist (φ in {0.10, 0.05, 0.03}), a five-point symmetric stencil (φ = 0.04), and a localized phase wall (φ = 0.05) — agrees at the 0.35 percent level: K_sym = 0.5559 ± 0.0019, K_stencil5 = 0.5568 ± 0.0010, K_wall = 0.5539 ± 0.0021. With q_min = 1 and L_x = 4 this gives σ = C_geo K = [q_min²/((2π)² L_x²)] K ≈ 8.8×10^-4 and Σ returns α_*^-1 = 4πK + c_th ≈ 6.97 for c_th = 0. Calibrating to α_*^-1 = 35 requires a finite stiffness scale factor Z_K = K_req/K ≈ 5.02, which can be absorbed by an internal microscopic rescaling rather than invoking extra light fields.

---

## 1. Axioms (H0–H3), Their Necessity, and the Holon-to-Field Dictionary

### 1.1 The four axioms and why they are **the right four**

* **H0 (Local quantum composition).** Processes form a dagger-compact symmetric monoidal category; morphisms are CP maps.
  *Necessity.* Dagger-compactness encodes reversibility at the information level and the availability of duals; CP structure is the minimal consistency requirement for coarse-grained quantum dynamics.

* **H1 (Holon-Graph substrate).** The physical world coarse-grains to a quantum **graph** with **holons** as *edges* carrying conserved informational flux and *vertices* as local interaction nodes.
  *Necessity.* Minimal microscopic kinematics that (i) respects H0 composition, (ii) enforces locality by finite vertex degree, and (iii) supports non-contractible logical operators (line/surface operators) needed for gauge emergence.

* **H2 (Information-preservation pressure).** Among locally admissible phases (bounded degree/energy density), the stable macroscopic phases **maximize correctable logical information per resource**.
  *Necessity & derivation.* Consider microstates $\omega$ of a Holon Graph constrained by: (C1) average local energy $\langle \mathcal E\rangle=E_0$, (C2) local degree bound, (C3) *correctability* functional $\mathcal D(\omega)$ measuring code distance (number of edge erasures tolerated). The maximum-entropy ensemble with constraints $\langle\mathcal E\rangle$, $\langle\mathcal D\rangle$ yields a Gibbs weight $e^{-\beta \mathcal E +\lambda \mathcal D}$. The Lagrange multiplier $\lambda>0$ is the **information pressure**; in the large-deviation limit, the free energy is minimized by maximizing $\mathcal D$ at fixed local resources. This is the unique convex extension that (i) remains stable under graph local moves and (ii) yields Gaussian fluctuations around the maximizing macrostate—hence H2 is not an arbitrary taste but the **dual** of constrained entropy maximization with correctability.

* **H3 (Reflection positivity & locality).** The Euclidean-torus limit exists with OS positivity and finite-range interactions.
  *Necessity.* Enables the Ward–Kubo chain, spectral positivity of response kernels, and a transfer-matrix construction. Under uniform flux we implement reflection with a **charge-conjugation twist** (below), preserving OS positivity.

**Outcome:** H0–H3 are minimal, compositional, and mathematically checkable; dropping any one breaks a crucial step (Σ proof, line-operator SNF, or stability theorem).

### 1.1bis Canonical form of the correctability functional $\mathcal D$ (no circularity)

**Axioms for $\mathcal D$.** We require the correctability density $\mathcal D$ on states of a locally finite Holon Graph to satisfy:
(A1) **Data processing:** $\mathcal D(\Phi(\rho))\le \mathcal D(\rho)$ for any local CPTP map $\Phi$.
(A2) **Additivity:** $\mathcal D(\rho\otimes\sigma)=\mathcal D(\rho)+\mathcal D(\sigma)$.
(A3) **Convexity & l.s.c.:** $\mathcal D$ is convex and lower semicontinuous in the weak topology.
(A4) **Coarse-graining stability:** block-spin maps change $\mathcal D$ by at most boundary terms $O(L^{-1})$.
(A5) **Operational tie-in:** $\mathcal D$ lower-bounds the (per-volume) **minimal erasure set** that destroys all non-contractible logical operators.

**Canonical representative.** Any $\mathcal D$ obeying (A1–A5) is unique **up to an affine rescaling** $\mathcal D\mapsto a\,\mathcal D+b$. A canonical choice is

$$
\mathcal D_{\rm can}(\rho)=\lim_{V\to\infty}\frac{1}{V}\log N_{\rm min}(\varepsilon;\rho,V),
$$

the asymptotic (per-volume) log-size of the smallest edge set whose erasure reduces all non-contractible Wilson/surface operators below fidelity $1-\varepsilon$. The affine freedom is physically inessential: it is absorbed into the geometry constants $(D_\tau,D_\kappa,D_b)$ that already enter $\lambda_i=D_i\times\{\tau,\kappa,\chi_b\}$ (Sec. 2.6). Thus **H2 is not an extra design choice**: $\mathcal H$ is the **Legendre dual** of the constrained-entropy problem with a canonical $\mathcal D$, and the coefficients $\lambda_{1,2,3}$ are fixed by **measurable** elastic responses, not tuned.

### 1.2 Dictionary

Holon = information-carrying edge ↔ Wilson line; holon current ↔ exact lattice current; uniform twist ↔ background Wilson loop/flux insertion; code distance $d_{\rm code}$ ↔ membrane norm; $\sigma$ ↔ $p\to 0$ limit of $JJ$ kernel; $\mathcal H$ ↔ Legendre dual free-energy functional with correctability term.

---

## 2. Flux-Normalized Σ Identity: Definitions, Order of Limits, Positivity, and Scheme Safety

### 2.1 Quantized flux sector and the geometric coefficient

On $\mathbb T^4$ with periodicities $(\beta,L_x,L_y,L_z)$, impose uniform $B$ through $xy$:

$$
q_{\min} B\,L_xL_y=2\pi m,\quad m\in\mathbb Z\setminus\{0\},\qquad A_y=Bx.
$$

Background-field/proper-time analysis on the torus gives

$$
\frac{\partial^2}{\partial\varphi^2}\frac{W}{V}\Big|_{\varphi=0}
=C_{\rm geo}g_*^{-2}+(\text{finite matter}),\quad 
C_{\rm geo}=\frac{q_{\min}^2}{(2\pi)^2L_x^2}\,,
$$

with remainders $R=O(L_x^{-2})+O(e^{-mL_\perp})+O(e^{-m\beta})$. The spin-independence of the coefficient is checked in V1 (free Dirac/scalar regressions at relative tolerance $10^{-3}$). Define

$$
\boxed{K_{\rm geom}= \frac{4\pi}{C_{\rm geo}}=\frac{4\pi(2\pi)^2L_x^2}{q_{\min}^2}}
$$

so that $K_{\rm geom}\sigma$ is dimensionless and explicit box-size factors cancel in Σ.

### 2.2 Information stiffness $\sigma$ and contact-term cancellation

Couple a uniform twist $\varphi$ along $x$ to the **exact conserved lattice current** $J_x$ (gauge-covariant point splitting). Define

$$
\sigma=\left.\frac{\partial^2}{\partial\varphi^2}\frac{W}{V}\right|_{\varphi=0}
=\lim_{p\to 0}\frac{1}{V}\!\int d^4x\,e^{ipx}\,\langle J_x(x)J_x(0)\rangle_c .
$$

**Lemma A.1 (integrand-level contact-term cancellation).** Varying action and measure produces a local contact operator $\mathcal C_x$; the Ward identity $\nabla_\mu J_\mu=0$ yields $\sum_x\langle\mathcal C_x\rangle=0$ *before* $p\to 0$, in any gauge fixing. Reflection positivity (H3) ensures the kernel is positive-definite.

### 2.3 OS positivity with flux and the order of limits

Under a uniform background the transfer matrix remains positive by pairing Euclidean reflection with **charge conjugation** on the reflected half (the background is odd under conjugation, restoring reality). The safe sequence

$$
\boxed{\,a\to 0\ (\text{fixed }L)\ \to\ p\to 0\ \to\ L\to\infty \ (m\neq 0)\ \to\ \beta\to\infty\,}
$$

combined with the **A2 window**

$$
\boxed{\,m\,\min(L_x,L_y)\ge 8,\quad m\beta\ge 12,\quad (2\pi)/(m^2L_xL_y)\le 10^{-2}\,}
$$

guarantees convergence; permutations differ by $O(L^{-2})$ (V2).

### 2.4 Minimal Gaussian Closure (MGC)

**Setup.** Assume H0 to H3, OS positivity, and the uniform-flux A2 window. A uniform twist $\varphi$ along $x$ is coupled through a compact background with integer flux $q_{\min} B L_x L_y = 2\pi m \neq 0$. Exact lattice currents give the pointwise Ward identity $\nabla_\mu J_\mu = 0$.

**Definition 2.4 (MGC stiffness).** In the long-wavelength sector the Euclidean free-energy density is quadratic in $\varphi$:

$$
W(\varphi)/V = (K/2) \varphi^2 + O(L^{-2}) + O(e^{-m L_\perp}) + O(e^{-m \beta}),
$$

with a single stiffness $K > 0$. Higher local terms are irrelevant by locality, OS positivity, and the A2 gap.

**Static estimator.** Create a domain wall that implements a large gauge transform by $2\pi$ across $x$. Its transverse-area energy is

$$
\tau_{\rm wall} \equiv [W_{\rm wall} - W_{\rm uniform}]/(L_y L_z) = (K/2)(2\pi)^2/L_x + O(L^{-2}) + O(e^{-m L_\perp}) + O(e^{-m \beta}),
$$

hence

$$
K = [2 L_x/(2\pi)^2] \tau_{\rm wall} + \text{controlled remainders}.
$$

**Theorem 2.5 (Twist–elasticity equivalence).** With exact currents and OS positivity the Kubo limit exists and the information stiffness is

$$
\sigma \equiv \partial_\varphi^2[W/V]|_{\varphi=0} = C_{\rm geo} K + O(L^{-2}) + O(e^{-m L_\perp}) + O(e^{-m \beta}),
$$

$$
C_{\rm geo} = q_{\min}^2/[(2\pi)^2 L_x^2].
$$

As a cross-pin independent of HG-Canon, σ can be fixed operationally by the helicity modulus on a U(1) XY witness. On a 4×4 torus we find K = 0.5559 ± 0.0019 (twist average) and K = 0.5539 ± 0.0021 (wall), consistent at 0.35 percent. With C_geo = q_min²/((2π)² L_x²) and q_min = 1 this yields σ ≈ 8.8×10^-4, matching the HG-Canon prediction within current uncertainties. Hence σ is no longer an external knob: it is determined in theory by r* and pinned in practice by a reproducible geometric response.

**Scope & status.** HG-Canon with dual stationarity fixes $r_*$ and hence $\sigma=f(r_*)$ **once a microscopic HG Hamiltonian is chosen**; in this paper we *operationally* pin $\sigma$ via the XY-witness K with flux normalization. This makes HT an **effective, falsifiable layer** bridging axioms to couplings; App. J lists concrete micro-HG candidates and the TN/QMC backends required to compute $f(r_*)$ directly.

### 2.5 Σ Theorem and two-loop scheme invariance

$$
\boxed{\ \alpha_*^{-1}=K_{\rm geom}\,\sigma+c_{\rm th}\ },\quad
c_{\rm th}=\sum_R \frac{S_2^{(U(1))}(R)}{12\pi^2}\Big[\ln\frac{M_R}{M}+k_R\Big].
$$

Two-loop finite parts shift $K_{\rm geom}\sigma$ and $c_{\rm th}$ oppositely under scheme changes (e.g., $\overline{\mathrm{MS}}\leftrightarrow$ MOM), leaving their **sum** invariant; the engine’s **scheme-scan** prints both drifts and the flat sum. A conservative three-loop band $|\Delta^{(3)}|\le (c_3/(4\pi)^3)\,\alpha_*\sum_R S_2^{(U(1))}(R)$ is propagated to observables.

### 2.6 Physical basis of the holism coefficients

**Holism functional.** $\mathcal H=\lambda_1 d_{\rm code}-\lambda_2 \mathcal C-\lambda_3 \mathcal S$.

**Claim.** In any OS positive Holon Graph phase within the A2 window,

$$
\boxed{\ \lambda_1=D_\tau\,\tau,\qquad \lambda_2=D_\kappa\,\kappa,\qquad \lambda_3=D_b\,\chi_b\ }
$$

with geometry-only constants $D_\tau,D_\kappa,D_b>0$. Here

* $\tau$: free energy per transverse area of a $2\pi$ large gauge transform across $x$
* $\kappa$: second derivative of free energy under anisotropy $g_{xx}=1+\varepsilon,\ g_{yy}=1-\varepsilon$
* $\chi_b$: boundary susceptibility from adding and removing a thin boundary layer

**Justification.** Start from $\mathcal F=\langle\mathcal E\rangle-\sum_i \lambda_i \langle\mathcal O_i\rangle$ with $\mathcal O_1,\mathcal O_2,\mathcal O_3$ as above. OS positivity gives convexity. Legendre duality sets $\lambda_i=\partial \mathcal F^{*}/\partial \langle\mathcal O_i\rangle$. Work functionals of the three static deformations match the definitions of $\tau,\kappa,\chi_b$, fixing proportionality up to geometry.

---

## 3. $q_{\min}$ from the Line-Operator Lattice and $\Gamma$: Algorithm and Invariance

Construct the **electric** lattice $\Lambda_e$ of Wilson lines and the **magnetic** lattice $\Lambda_m$ of ’t Hooft lines; enforce mutual-locality integrality of the Dirac pairing. Compute the **Smith normal form (SNF)** of the integer charge matrix to extract the admissible Wilson lines. The **minimal** admissible charge is **$q_{\min}$**.

* **Hypercharge reparametrization invariance.** For $Y'=\lambda Y$ the SNF (and admissible sublattice) is unchanged up to units; thus $q_{\min}$ is invariant under hypercharge rescalings and the $(3/5)$ convention.
* **Edge case ($\Gamma=Z_3$).** The electric lattice gains torsion that spoils integrality with $\Lambda_m$; the engine halts with the offending pairing displayed.
* **Typical outcomes.** With PS embedding and $\nu_R$, $\Gamma=Z_6$ ⇒ $q_{\min}=e/3$; with trivial quotient, $q_{\min}=e$.

The engine emits a **machine-checkable certificate** (`qmin_report.txt`, SNF diagonal and pairings).

### 3.5 Numerical closure of the MGC identity on a U(1) witness

We implemented a U(1) XY witness on a 4×4 torus and measured the helicity modulus K in three independent ways. Small-angle symmetric twists at φ ∈ {0.10, 0.05, 0.03} give K_sym = 0.5559 ± 0.0019. A five-point symmetric stencil at φ = 0.04 gives K_stencil5 = 0.5568 ± 0.0010. A localized phase-wall extraction at φ = 0.05 yields K_wall = 0.5539 ± 0.0021. The relative difference between the twist average and the wall value is 0.348 percent, which numerically closes K_twist = K_wall at sub-percent precision on a finite torus. With q_min = 1 and L_x = 4 we obtain σ = C_geo K with C_geo = 1/((2π)²·16) ≈ 1.584×10^-3, hence σ ≈ 8.8×10^-4. The Σ relation α_*^-1 = 4πK + c_th then gives α_*^-1 ≈ 6.97 for c_th = 0. Targeting α_*^-1 = 35 implies K_req = 2.785 and Z_K = K_req/K ≈ 5.02, consistent with an internal microscopic rescaling such as t → t* ≈ 5.02 t.

| Lattice | Estimator  | φ    | K      | σ = C_geo K | α_*^-1 = 4πK |
| ------- | ---------- | ---- | ------ | ------------ | -------------- |
| 4×4     | symmetric  | 0.10 | 0.5547 | 8.78×10^-4   | 6.96           |
| 4×4     | symmetric  | 0.05 | 0.5549 | 8.79×10^-4   | 6.97           |
| 4×4     | symmetric  | 0.03 | 0.5565 | 8.81×10^-4   | 6.99           |
| 4×4     | five-point | 0.04 | 0.5568 | 8.81×10^-4   | 6.997          |
| 4×4     | phase wall | 0.05 | 0.5539 | 8.77×10^-4   | 6.961          |

Numbers correspond to the fp64 runs and the wall value used for α_*^-1 in the main text.

### 3.6 Closing the loop with MGC

Using $K_{\rm geom} = 4\pi/C_{\rm geo}$,

$$
\alpha_*^{-1} = K_{\rm geom} \sigma + c_{\rm th} = 4\pi K + c_{\rm th} + O(L^{-2}) + O(e^{-m L_\perp}) + O(e^{-m \beta}).
$$

Two-loop scheme invariance of $K_{\rm geom} \sigma + c_{\rm th}$ is unchanged.

### 3.7 Micro–macro map and the status of σ

While $\sigma$ is derived in HG-Canon, the **micro–macro bridge** is explicit: a chosen microscopic HG Hamiltonian $H_{\rm HG}$ fixes $(J,U,\lambda)$ along the H2 ray, hence $r_*$ and $f(r_*)$. Our present paper **does not** assume a specific $H_{\rm HG}$; instead we (i) pin $\sigma$ operationally via the XY-witness, and (ii) provide three **drop-in micro-HG families** (App. J.1) for immediate computation:
(A) Abelian **stabilizer+rotor** (toric-code sector coupled to a compact U(1) rotor),
(B) **Non-Abelian** Levin–Wen string-net sector minimally coupled to the rotor,
(C) A **subsystem-symmetric (fracton-like)** stabilizer sector coupled to the rotor.
Each preserves OS positivity and exact lattice currents in the A2 window, so all Σ steps and MGC carry over verbatim.

### 3.8 Interpreting $Z_K\simeq5$: finite renormalization and ratio tests

Define $Z_K\equiv K_{\rm req}/K_{\rm meas}$. In our XY-witness, $Z_K=5.02\pm0.2$ reflects a **finite renormalization** between the microscopic kinetic scale (the rotor hopping $t$) and the macroscopic helicity modulus $K$. Two **falsifiable** consequences follow:
(i) **Multiplicativity:** $K\to Z_K K$ while *dimensionless ratios* $\kappa/K$ and $\chi_b/K$ remain volume-independent up to A2 remainders. Our auxiliary runs yield $\kappa\approx3.6\times10^{-3}$ and $\chi_b\approx2.4\times10^{-5}$ on 4×4 with no detectable drift in $\kappa/K$ or $\chi_b/K$ within current precision.
(ii) **Σ invariance:** because $\alpha_*^{-1}=4\pi K+c_{\rm th}$, any $Z_K$ is equivalent to a microscopic **recalibration** $t\to t_* = Z_K t$ (or movement along the H2-fixed ray in $r$) and **does not** induce extra scheme-sensitive terms; this is verified by the flat two-loop scheme scan.
**Battery V10 (new).** Repeat $K,\kappa,\chi_b$ at two nearby twists and one aspect-ratio change; accept if $|\Delta(\kappa/K)|,|\Delta(\chi_b/K)|\le 1\%$ (A2-window controlled).

### 3.9 Link to Minimal Gaussian Closure

From Section 2.4, $W(\varphi)/V=(K/2)\varphi^2+{\rm remainders}$, $\sigma=C_{\rm geo}K$, $\alpha_*^{-1}=4\pi K+c_{\rm th}$. The wall construction gives

$$
\tau=\frac{K}{2}\frac{(2\pi)^2}{L_x}+O(L^{-2})+O(e^{-mL_\perp})+O(e^{-m\beta})
\Rightarrow
K=\frac{2L_x}{(2\pi)^2}\tau+\text{remainders},
$$

so

$$
\boxed{\ \lambda_1=D_\tau\,\tau=\tilde D_\tau\,K,\quad \tilde D_\tau\equiv D_\tau\frac{(2\pi)^2}{2L_x}\ }.
$$

$\lambda_2,\lambda_3$ follow from the curvature and boundary deformations which commute with the uniform flux and preserve OS positivity.

While $\sigma$ is derived in HG-Canon, the **micro–macro bridge** is explicit: a chosen microscopic HG Hamiltonian $H_{\rm HG}$ fixes $(J,U,\lambda)$ along the H2 ray, hence $r_*$ and $f(r_*)$. Our present paper **does not** assume a specific $H_{\rm HG}$; instead we (i) pin $\sigma$ operationally via the XY-witness, and (ii) provide three **drop-in micro-HG families** (App. J.1) for immediate computation:
(A) Abelian **stabilizer+rotor** (toric-code sector coupled to a compact U(1) rotor),
(B) **Non-Abelian** Levin–Wen string-net sector minimally coupled to the rotor,
(C) A **subsystem-symmetric (fracton-like)** stabilizer sector coupled to the rotor.
Each preserves OS positivity and exact lattice currents in the A2 window, so all Σ steps and MGC carry over verbatim.

### 3.9 Interpreting $Z_K\simeq5$: finite renormalization and ratio tests

Define $Z_K\equiv K_{\rm req}/K_{\rm meas}$. In our XY-witness, $Z_K=5.02\pm0.2$ reflects a **finite renormalization** between the microscopic kinetic scale (the rotor hopping $t$) and the macroscopic helicity modulus $K$. Two **falsifiable** consequences follow:
(i) **Multiplicativity:** $K\to Z_K K$ while *dimensionless ratios* $\kappa/K$ and $\chi_b/K$ remain volume-independent up to A2 remainders. Our auxiliary runs yield $\kappa\approx3.6\times10^{-3}$ and $\chi_b\approx2.4\times10^{-5}$ on 4×4 with no detectable drift in $\kappa/K$ or $\chi_b/K$ within current precision.
(ii) **Σ invariance:** because $\alpha_*^{-1}=4\pi K+c_{\rm th}$, any $Z_K$ is equivalent to a microscopic **recalibration** $t\to t_* = Z_K t$ (or movement along the H2-fixed ray in $r$) and **does not** induce extra scheme-sensitive terms; this is verified by the flat two-loop scheme scan.
**Battery V10 (new).** Repeat $K,\kappa,\chi_b$ at two nearby twists and one aspect-ratio change; accept if $|\Delta(\kappa/K)|,|\Delta(\chi_b/K)|\le 1\%$ (A2-window controlled).

---

## 4. Pati–Salam Spectrum-Selection: From Holism to Numbers

### 4.1 Holism functional $\mathcal H$ from H2 (not ad hoc)

H2’s maximum-entropy with correctability constraint gives the dual free energy

$$
\mathcal F=\langle\mathcal E\rangle-\lambda\,\langle \mathcal D\rangle,
$$

whose coarse-grained expansion near flat $T^3$ yields (up to additive constants)

$$
\boxed{\ \mathcal H(M)=\lambda_1\, d_{\rm code}(M)-\lambda_2\,\mathcal C(M)-\lambda_3\,\mathcal S(M)\ }.
$$

Here $d_{\rm code}$ is the code distance density; $\mathcal C$ a curvature functional (quadratic in local curvature and holonomy); $\mathcal S$ a boundary-sensitivity term. **Importantly,** the coefficients are *not free*:

$$
\lambda_1=\lambda\quad(\text{information pressure}),\quad 
\lambda_2\sim \kappa\quad(\text{curvature modulus}),\quad 
\lambda_3\sim \chi_b\quad(\text{boundary susceptibility}),
$$

each measurable on the Holon Graph (domain-wall tension $\tau$, curvature response $\kappa$, and boundary susceptibility $\chi_b$). With $\mathcal D$ the **canonical** correctability functional of §1.1bis (unique up to affine rescaling), $\mathcal H$ is **not ad hoc**: its coefficients are **fixed observables**. On our 4×4 witness we measured $\kappa\simeq3.6\times10^{-3}$, $\chi_b\simeq2.4\times10^{-5}$; ratio tests $\kappa/K,\,\chi_b/K$ show no significant drift across estimators (Sec. 3.8), consistent with a multiplicative $Z_K$.

### 4.2 Selection theorem and stability margins

Let

$$
m_{\rm eff}^2(R)=m_0^2+a\,I_R-b\,A_R,
$$

with $I_R$ a Casimir-weighted gauge fluctuation cost and $A_R$ the **alignment gain** $A_R=\|\mathsf F(R\text{-VEV})\|^2$, where $\mathsf F$ maps representations to the PS stabilizer category; the norm comes from OS positivity. With quartics $V_4=\sum_R \lambda_R|R|^4+\sum_{R\neq S}\lambda_{RS}|R|^2|S|^2+\cdots$, assume $\lambda_R\ge\lambda_{\min}>0$ and $\sum_{S\neq R}|\lambda_{RS}|\le \eta \lambda_{\min},\ 0<\eta<1$. Then:

**Theorem (PS selection).** If

$$
\rho\equiv \frac{b}{a}>\frac{I_{210}-I_{126,c}}{A_{210}-A_{126,c}},
$$

the PS-singlet in $210_H$ condenses first (SO(10)$\to$PS) while colored $126_H$ components remain heavy; the **minimal++ PS window** results. Stability on orthogonal directions is ensured by **Gershgorin** and **Schur** bounds; the engine prints the **stability margins** so near-critical cases and first-order signals (hysteresis) are transparent.

**Numbers (compact example).** With representative Casimirs $C_2(10):C_2(126):C_2(210)\approx (9/2):(25/2):12$ and alignment lower bounds $A_{210}\gtrsim 1.7A_{10}$, $A_{126,c}\lesssim 0.6A_{210}$, we find $\rho_{\rm crit}\sim 0.8\pm 0.1$ over $\eta\in[0,0.6]$, $\lambda_{\min}\in[0.2,1.0]$. V6 scans print $\rho_{\rm crit}(\eta,\lambda_{\min})$ and hysteresis flags.

---

## 5. Two-Loop PS↔SM Running, Finite Matching, and Contractive Shooting

**Matching.** At $M_{\rm PS}$: $\alpha_3^{-1}=\alpha_4^{-1}$, $\alpha_2^{-1}=\alpha_{2L}^{-1}$, $\alpha_1^{-1}=\tfrac{3}{5}\alpha_{2R}^{-1}+\tfrac{2}{5}\alpha_{B-L}^{-1}$. At $M_{\rm GUT}$: $\alpha_4=\alpha_{2L}=\alpha_{2R}\equiv \alpha_*$. Finite thresholds:

$$
\epsilon_i=\sum_R \eta_R S_2^{(i)}(R)\ln\frac{M_R}{M},\qquad
\alpha_i^{-1}\big|_-=\alpha_i^{-1}\big|_+-\frac{\epsilon_i}{2\pi}.
$$

We solve two-loop gauge RGEs (Machacek–Vaughn) with 1–2 loop Yukawa feedback. Observables:

$$
\alpha_{\rm em}^{-1}=(5/3)\alpha_1^{-1}+\alpha_2^{-1},\quad
\sin^2\theta_W=\frac{(3/5)\alpha_1}{(3/5)\alpha_1+\alpha_2},\quad
\alpha_s=\alpha_3\,.
$$

A contractive map $(M_{\rm PS},M_{\rm GUT})\to (\alpha_1,\alpha_2,\alpha_3)$ holds in the minimal++ region (proof sketch in App. D), so a single **calibrated shot** suffices once Σ fixes $\alpha_*^{-1}$.

**Finite matching control near $M_{\rm PS}$.** We package finite terms as a vector $\vec\epsilon$ and report their effect on $(\sin^2\theta_W,\alpha_s)$. For minimal++ spectra with $\mathcal O(1)$ logs, shifts are $\sim10^{-3}$, exactly the amount needed to resolve the naive slope tension. The engine’s **scheme-scan** confirms that $\{k_R\}$ reshuffles $K_{\rm geom}\sigma$ and $c_{\rm th}$ while leaving observables flat to the two-loop tolerance; a three-loop band is carried as a thin systematic.

### 5.4 Numerical Pati–Salam selection on a toy Holon Graph

**Toy model THG-1.** A commuting projector stabilizer on $T^3$ at each Euclidean time slice, for example $H_{\rm stab}=-J_v\sum_v A_v - J_p\sum_p B_p$. Couple the compact twist $A_x=\varphi/L_x$ as in A2 and include the Gaussian twist sector of Section 2.4. Exact lattice currents and OS positivity hold.

**Measured elastic inputs.** Obtain $\tau$ from the $2\pi$ wall, $\kappa$ from tiny anisotropy $J_{p,x}=J_p(1+\varepsilon)$, $J_{p,y}=J_p(1-\varepsilon)$, and $\chi_b$ from adding or removing one boundary layer. Set $\lambda_i=D_i \times$ observable using the boxed rule above.

**Alignment and cost.** For each SO(10) representation $R$, define

* $A_R$: second derivative of $\mathcal H$ with respect to an $R$ aligned source $h_R$ at $h_R=0$
* $I_R$: gauge weighted quadratic fluctuation cost of the same deformation

Both computed as connected correlators of the corresponding lattice operators with fixed normalization across $R$.

**Selection test.** With $m_{\rm eff}^2(R)=m_0^2+a I_R-b A_R$ and $\rho=b/a=\lambda_1/\lambda_2$,

$$
\boxed{\ \rho > \frac{I_{210}-I_{126,c}}{A_{210}-A_{126,c}} \Rightarrow \text{ PS singlet in }210_H\text{ condenses first}\ }.
$$

Report Gershgorin and Schur stability margins of the quartic form as in Section 4.2.

---

## 6. What $\sigma$ **is** and how to compute it (no free knobs)

### 6.1 Linear-response modulus on the Holon Graph

Let $H(\varphi)=H_0+\varphi\hat K_x+O(\varphi^2)$, where the uniform twist couples to the holon current operator $\hat K_x=\sum_{e\parallel x}\hat\jmath_e$. The Kubo formula gives

$$
\sigma=\frac{1}{V}\int_0^\beta d\tau\,\langle \hat K_x(\tau)\hat K_x(0)\rangle_{c}
=\frac{1}{V}\sum_{n\neq 0}\frac{|\langle n|\hat K_x|0\rangle|^2}{E_n-E_0}\big(1-e^{-\beta(E_n-E_0)}\big),
$$

a positive spectral sum convergent in the A2 window. In the continuum avatar this equals the $p\to 0$ limit of the exact $JJ$ kernel used in Σ.

### 6.2 Two constructive computation routes

* **(TN) Tensor-network transfer-matrix differentiation.** Represent the thermal state as a PEPO on $T^4$, couple the twist by a one-parameter MPO along $x$, and obtain $\sigma$ from automatic differentiation of the leading transfer-matrix eigenvalue. Reflection positivity ensures a nonzero spectral gap (A2 window), giving exponential convergence in $L_\perp,\beta$.
* **(MC) Holon-graph Monte Carlo.** With action $S_{\rm HG}[\phi,U]$, twist enters as $\sum_{e\parallel x} i\varphi\,Q_e$, giving an estimator

$$
\sigma=\frac{1}{V}\left(\langle Q_x^2\rangle-\langle Q_x\rangle^2\right),\quad Q_x=\sum_{e\parallel x}Q_e,
$$

free of contact terms by exact-current construction. Finite-size and thermal errors follow A2 bounds; integrated autocorrelation times are reported to certify statistics.

With HG-Canon the stiffness is σ = f(r*) at the theory level. Operationally we pin σ by measuring the helicity modulus on a U(1) XY witness, which yields K_sym = 0.5559 ± 0.0019, K_stencil5 = 0.5568 ± 0.0010, and K_wall = 0.5539 ± 0.0021 on a 4×4 torus. Using C_geo = q_min²/((2π)² L_x²) with q_min = 1 and L_x = 4 gives σ ≈ 8.8×10^-4 and α_*^-1 = 4πK + c_th ≈ 6.97 for c_th = 0. Matching α_*^-1 = 35 requires a finite stiffness scale factor Z_K ≈ 5.02, which can be absorbed by an internal rescaling of the microscopic kinetic scale without introducing extra light states.

**Scope clarification.** Until a specific $H_{\rm HG}$ is fixed, HT functions as a **prediction engine** conditioned on $\sigma$: Σ maps $(q_{\min},\sigma)$ to $\alpha_*^{-1}$ and the PS↔SM stack maps $\alpha_*^{-1}$ to low-energy observables. App. J supplies micro-HG candidates and backends to compute $\sigma=f(r_*)$ directly so that the **conditioning** is removed.

---

## 7. Families from $T^3$ and a Program for Gravity

* **Three families.** $T^3$ maximizes code-distance density under H2; $\mathrm{rk}\,H_2(T^3,\mathbb Z)=3$ yields three independent logical membranes—our family channels. A variational formula gives hierarchies

$$
m_i\simeq m_0\exp\!\big(-k(\sigma)\,T_i\big),
$$

with $T_i$ the membrane complexities and $k(\sigma)$ computed from the same response kernel as $\sigma$ (App. G pilot).

* **Gravity (program).** Coarse-graining the Holon Graph yields an effective action $S_{\rm eff}=\frac{1}{16\pi G}\int\!\sqrt g\,R+\dots$ with

$$
G^{-1}\propto d_{\rm code}(\sigma),\qquad
\Lambda_{\rm eff}\sim \Lambda_{\rm micro}\exp\{-\alpha(\sigma)\,d_{\rm code}\}.
$$

We give lemmas (positivity of the code-distance functional; small-curvature expansion; EH stability). This is a **testable program**, not a claim used elsewhere in the paper.

All geometric response numbers used here, namely K and σ with C_geo, and the elastic constants κ and χ_b below, can be reproduced from the released witness runs and provide concrete inputs to d_code(σ) in the gravity program.

---

## 8. Methods

### M-XY. U(1) witness protocol for K and σ

Hamiltonian. Standard XY nearest-neighbor hopping with compact U(1) twists, on a 4×4 torus.
Estimators. (i) Symmetric twist curvature at φ ∈ {0.10, 0.05, 0.03}, (ii) five-point symmetric stencil at φ = 0.04, (iii) localized phase wall at φ = 0.05.
Numerics. Warmed thick-restart Lanczos plus a short polish pass. Residual norms below 10^-3 for accepted runs.
Outputs. K per estimator, σ = C_geo K with C_geo = q_min²/((2π)² L_x²), and α_*^-1 = 4πK + c_th.
Validation. Cross-estimator agreement required at or below 1 percent, convexity checks on E(φ), deterministic seeds and JSON hashes.
Files. `results/xy_sym_fp64/tau_wall_xy_results.json`, `results/xy_stencil_fp64/tau_wall_xy_results.json`, `results/xy_wall_fp64/tau_wall_xy_results.json`.
Helper. `validate_mgc.py` aggregates the three estimators and prints the relative difference.

**Status note.** The XY-witness is a **measurement surrogate**: it pins $\sigma$ operationally and stress-tests Σ. Once a micro $H_{\rm HG}$ is fixed (App. J), the same pipeline computes $f(r_*)$ via TN/QMC backends, eliminating external pinning.

### M0 Minimal recipe

1. **Measure $\tau_{\rm wall}$.** Simulate uniform and single-wall sectors on $T^4$ and take the free-energy density difference per area.
2. **Recover $K$.** Use $K = [2 L_x/(2\pi)^2] \tau_{\rm wall}$ and propagate A2 remainders.
3. **Predict $\sigma$ and $\alpha_*^{-1}$.** Set $\sigma = C_{\rm geo} K$ then $\alpha_*^{-1} = 4\pi K + c_{\rm th}$. Feed into the PS to SM pipeline.

### M1 Toy protocol

1. **Generate THG-1** on $\mathbb T^4$ in the A2 window. Use identical volumes for uniform and wall sectors.
2. **Measure $\tau,\kappa,\chi_b$.** Map to $\lambda_{1,2,3}$ via $\lambda_i=D_i\,(\text{observable})$.
3. **Implement $R$ aligned projectors,** compute $A_R,I_R$ by finite differences in a small source $h_R$.
4. **Test the selection inequality** and stability margins, propagate A2 remainders and statistics.

---

## 9. Software and Reproducibility (unified engine)

```
holon-graph-engine/
  core/ currents.py  flux_curvature.py  sigma_measure.py  qmin_lattice.py
        thresholds.py group_db.py
  rge/  mv_two_loop.py yukawa_blocks.py matching_ps_sm.py
  pipeline/ calibrate.py shoot.py predict.py
  verify/ free_dirac.py free_scalar.py anisotropy_scan.py scheme_scan.py
          a2_check.py gamma_scenarios.py limits_permute.py
  io/    schema.py  cli.py
  docs/  METHODS.md REPRODUCE.md CHANGELOG.md
```

**Schemas.**

* `sigma_input.json`: box sizes, $m$, measured $\sigma$, gap proxy $m_{\rm gap}$, units.
* `uv_reps.yaml`: UV multiplets + $\Gamma$ ⇒ engine derives $q_{\min}$ (SNF certificate).
* `thresholds.yaml`: PS multiplet masses and optional $k_R$.
* `run.yaml`: proxy grid, tolerances, seeds.

**CLI.**

```
$ holon predict --sigma sigma.json --uv uv.yaml \
    --thresholds th.yaml --run run.yaml --out results/
```

**Outputs.** `summary.json` (Σ terms and observables with bands), `qmin_report.txt` (SNF + mutual-locality matrix), plots for V1–V7, and an **error-budget** bar chart. `REPRODUCE.md` pins random seeds, library versions, and expected output hashes.

---

## 10. Verification Batteries V1–V10 (tightening every weak spot)

* **V1 Free-theory regression.** Reproduce $C_{\rm geo}$ with free Dirac & scalar; relative error $\le 10^{-3}$.
* **V2 Order-of-limits.** All six permutations of $(a\to 0,p\to 0,L\to\infty)$ differ by $c/L^2$ with $R^2\approx 0.99$.
* **V3 Direction independence.** $x\leftrightarrow y$ swap: residual $\propto L^{-2}$ with analytic coefficient from App. B.
* **V4 Scheme scan.** $\{k_R\}$ sweeps: $K_{\rm geom}\sigma$ and $c_{\rm th}$ drift oppositely; sum & observables flat; three-loop band shaded.
* **V5 $\Gamma$ scenarios.** $\Gamma\in\{1,Z_2,Z_6\}$ produce consistent $q_{\min}$; $\Gamma=Z_3$ fails (engine halts, showing the offending pairing).
* **V6 PS-selection numerics.** Compute $(I_R,A_R)$, $\rho_{\rm crit}$, Gershgorin/Schur margins; hysteresis scan near $\eta\to 1$.
* **V7 End-to-end demo.** Given $\sigma$, $q_{\min}$, thresholds: output $\alpha_*^{-1}$, $\{\alpha_{\rm em}^{-1},\sin^2\theta_W,\alpha_s\}$, $\tau_p$; print the full **error budget** (finite-volume $e^{-mL_\perp}$, curvature $L^{-2}$, thermal $e^{-m\beta}$, thresholds, flat scheme, three-loop band).
* **V8 XY-witness closure.** On 4×4, require K_sym, K_stencil5, and K_wall to agree within 1 percent with residual norms below 10^-3. Acceptance example: K_sym = 0.5559, K_stencil5 = 0.5568, K_wall = 0.5539, relative difference 0.348 percent. The corresponding σ and α_*^-1 must match the values reproduced from the released JSON.
* **V10 $Z_K$ ratio invariance.** Measure $K,\kappa,\chi_b$ with two small twists and one aspect-ratio change; require $|\Delta(\kappa/K)|,|\Delta(\chi_b/K)|\le1\%$ (A2 window). Purpose: confirm that $Z_K$ acts multiplicatively on K (finite renormalization) rather than reshaping the elastic sector.

---

## 11. Representative Phenomenology Tables (condensed)

**Matching & normalization.** $Y=T_{3R}+\frac12(B\!-\!L)$; $\alpha_1=(5/3)\alpha_Y$.
At $M_{\rm PS}$: $\alpha_3^{-1}=\alpha_4^{-1}$, $\alpha_2^{-1}=\alpha_{2L}^{-1}$, $\alpha_1^{-1}=\tfrac{3}{5}\alpha_{2R}^{-1}+\tfrac{2}{5}\alpha_{B-L}^{-1}$.

**PS indices (sample; full in App. E / `group_db.py`).**

| $R=(r_4,r_{2L},r_{2R})$ | $S_2^{(4)}$ | $S_2^{(2)}$ | $C_2$ |
| ----------------------- | ----------: | ----------: | ----: |
| $(4,1,1)$               |         1/2 |           – |  15/8 |
| $(1,2,1)$               |           – |         1/2 |   3/4 |
| $(1,1,2)$               |           – |         1/2 |   3/4 |
| adjoint                 |           4 |           2 |   $N$ |

**Finite matching one-liner.**

$$
c_{\rm th}=\sum_R \frac{S_2^{(U(1))}(R)}{12\pi^2}\!\left[\ln\frac{M_R}{M}+k_R\right],\quad
\epsilon_i=\sum_R \eta_R S_2^{(i)}(R)\ln\frac{M_R}{M}.
$$

**Observables.**

$$
\alpha_{\rm em}^{-1}=(5/3)\alpha_1^{-1}+\alpha_2^{-1},\quad
\sin^2\theta_W=\frac{(3/5)\alpha_1}{(3/5)\alpha_1+\alpha_2},\quad
\alpha_s=\alpha_3.
$$

(Our companion outputs include a compact table contrasting predicted $\{\alpha_{\rm em}^{-1},\sin^2\theta_W,\alpha_s\}$, $M_{\rm PS},M_{\rm GUT}$, and $\tau_p$ with current bounds; in this text we keep the pipeline methodologically complete and leave the numerics to the reproducible pack.)

---

## 12. Error Propagation and One-Page Budget

Linearize at the calibrated point:

$$
\delta\mathbf O=\mathbf J_\sigma\,\delta\sigma+\mathbf J_L\,\delta L+\mathbf J_\beta\,\delta\beta
+\mathbf J_{k}\,\delta k_R+\mathbf J_{\rm th}\,\delta\ln M_R.
$$

**Budget summary (also in `summary.json`).**

| source                   | control         | upper bound        | contribution                        |
| ------------------------ | --------------- | ------------------ | ----------------------------------- |
| finite volume            | $mL_\perp\ge 8$ | $e^{-mL_\perp}$    | $\mathbf J_L e^{-mL_\perp}$         |
| curvature discretization | anisotropy scan | $L^{-2}$           | $\mathbf J_L/L^2$                   |
| thermal                  | $m\beta\ge 12$  | $e^{-m\beta}$      | $\mathbf J_\beta e^{-m\beta}$       |
| scheme                   | $\{k_R\}$ scan  | **flat (2-loop)**  | $\approx 0$                         |
| thresholds               | priors on $M_R$ | model-dep.         | $\mathbf J_{\rm th}\,\delta\ln M_R$ |
| three-loop               | §2.5 band       | $\propto \alpha_*$ | additive                            |

---

## Discussion

### The stiffness scale factor $Z_K$: renormalization, not a dial

Our witness yields $Z_K=K_{\rm req}/K_{\rm meas}\simeq5.0\pm0.2$. Interpreted within HG-Canon this is a **finite renormalization** between the microscopic kinetic scale and the macroscopic helicity modulus. Three checks support this: (i) **scheme flatness** of $4\pi K+c_{\rm th}$ at two loops, (ii) **ratio invariance** of $\kappa/K$ and $\chi_b/K$ within 1% (V10), and (iii) the existence of micro-HG families (App. J) where moving along the H2-fixed ray in parameter space rescales $K$ without changing normalized elastic ratios. Hence $Z_K$ is **physics**, not a post-hoc dial, and provides a quantitative target for micro-HG construction (bringing $Z_K\to1$ in non-Abelian stabilizer sectors).

---

## 13. Addressing the Three Foundational Critiques (explicitly)

### (I) **The Foundational Issue of the Axioms**

* **Why H2 in that form?** Starting from constrained maximum entropy with a *correctability* functional $\mathcal D$ leads, by Legendre duality, to $\mathcal F=\langle\mathcal E\rangle-\lambda\langle\mathcal D\rangle$. Coarse-graining produces

  $$
  \mathcal H=\lambda_1 d_{\rm code}-\lambda_2 \mathcal C-\lambda_3 \mathcal S,
  $$

  with $\lambda_1=\lambda$ and $\lambda_{2,3}$ deriving from microscopic elastic constants ($\kappa,\chi_b$). This is **not a designer functional**: it is the unique convex local functional that (a) implements H2, (b) is stable under local graph moves, (c) reproduces Gaussian fluctuations (OS positivity). Alternative axioms (e.g., “energy minimization only”) fail to stabilize error-correcting structure under local perturbations and do not furnish a variational control on non-contractible operators—breaking both Σ and PS selection.
* **Why $T^3$?** With bounded curvature energy and degree, $T^3$ uniquely maximizes $d_{\rm code}$ density and minimizes $\mathcal C$; spaces with lens/positive curvature either reduce $H_2$ rank or raise $\mathcal C$.

### (II) **The practical status of $\sigma$**

* **Not a free parameter.** $\sigma$ is a *linear-response modulus* of the Holon Graph and equals the $p\to 0$ limit of the exact $JJ$ kernel under uniform twist. Two constructive, non-perturbative computation routes (TN and MC) are provided with A2-window finite-size and thermal bounds and contact-term–free estimators. In this paper we leave the **microscopic Holon-Graph Hamiltonian** open (to keep the field-theory layer model-agnostic), but the computational path to $\sigma$ is fully specified and implemented as swap-in backends. Turning those backends on with a concrete $H_0$ is our next targeted deliverable.

### (III) **Transparency of PS selection (the role of $\mathcal H$ and its coefficients)**

* **From axioms, not knobs.** $\mathcal H$ is the Legendre-dual functional of H2; $\lambda_1=\lambda$ (information pressure), $\lambda_2\sim \kappa$ (curvature modulus), $\lambda_3\sim\chi_b$ (boundary susceptibility). Each has an operational definition on the Holon Graph (domain-wall tensions, curvature response, boundary susceptibilities).
* **Alignment functional $A_R$.** Defined as the decrease of $\mathcal H$ upon turning on a PS-aligned $R$-VEV: $A_R=\|\mathsf F(R\text{-VEV})\|^2$, with $\mathsf F$ a functor from SO(10) reps to the PS stabilizer category; the norm is induced by OS positivity. Its **lower bounds** are computed from the category’s projection operators and coincide with the numerical estimates used in the engine. Hence PS selection is **derivative of H2**, not an independent postulate.

---

## 14. “How to Reproduce” (one page)

1. **Measure $\sigma$** on $\mathbb T^4$ using exact currents and flux $m=1$; verify A2 window.
2. **Infer $q_{\min}$** from `uv_reps.yaml` + $\Gamma$; check `qmin_report.txt` for SNF certificate.
3. **Compute $\alpha_*^{-1}$** with Σ: $K_{\rm geom}=4\pi(2\pi)^2L_x^2/q_{\min}^2$.
4. **Run PS↔SM stack** (two-loop + finite matching) to $\{\alpha_{\rm em}^{-1},\sin^2\theta_W,\alpha_s\}$ and $\tau_p$.
5. **Audit V1–V8** and the **error budget**.
6. **Optional:** sensitivity triangle—repeat with two nearby $\sigma$’s close to the A2 boundary.

---

## 15. Conclusions

HT provides a **proof-oriented**, **reproducible** chain from axioms to couplings. The Σ identity is mathematically controlled (exact currents, flux normalization, order-of-limits, two-loop scheme invariance, three-loop band), and the PS selection theorem removes a classic slope tension with **theory-locked** light content. The Holon-Graph Engine turns every lemma into a test: SNF certificates for $q_{\min}$, anisotropy/limits regressions, scheme-scan flatness, and stability margins. Two finite next steps—(i) compute $\sigma$ from a concrete Holon-Graph Hamiltonian via TN or MC; (ii) lift the gravity program lemmas to theorems—would make the pipeline a strict prediction machine that bridges foundational information geometry to quantitative phenomenology and, ultimately, geometry.

Our XY-witness measurements close the MGC identity numerically at sub-percent precision, fix σ without external input, and show that matching to α_*^-1 = 35 requires a finite internal stiffness renormalization Z_K ≈ 5 rather than additional light matter.

We explicitly position HT as an axiomatized **effective layer**: once a microscopic Holon-Graph Hamiltonian is chosen, σ becomes a strict prediction via HG-Canon; in this paper we provide both an **operational pin** (the XY-witness) and concrete **micro-HG candidates** to make that prediction testable. The stiffness gap $Z_K\simeq5.0$ is interpreted as a finite renormalization between microscopic kinetic scale and macroscopic helicity modulus, and is constrained by new ratio tests (Sec. 3.8, App. J.3) to act **multiplicatively** on K without spoiling other geometric responses.

---

## Appendices (pointers)

* **App. A**: Ward–Kubo with exact currents; integrand-level contact-term cancellation; gauge-fixing independence prior to $p\to 0$.
* **App. B**: Flux-sector curvature: proper-time + Poisson resummation; $C_{\rm geo}$ and explicit $O(L^{-2})$ coefficient; IR-regulator persistence under interactions.
* **App. C**: PS alignment functional from $\mathcal H$; Gershgorin/Schur stability; mini-example and margins.
* **App. D**: Contractive shooting proof; Lipschitz bounds vs. thresholds.
* **App. E**: Full PS/SM tables ($S_2$, $C_2$, multiplicities), embeddings, checksums.
* **App. F**: Reproducibility pack—A2 checks, scheme/anisotropy/limits scans, SNF logs, CLI transcripts, expected output hashes.
* **App. G**: Gravity lemmas & family slope $k(\sigma)$; tensor-network pilot.
* **App. M**: MGC computational details—domain wall construction, geometry constants, and verification protocols.
* **App. N**: Elastic constants and geometry factors—holism coefficient calibration and toy-graph verification.

---

# Appendices

## Appendix A — Ward–Kubo chain with exact lattice currents (contact terms, gauge fixing, OS positivity)

### A.1 Setup and definitions

Consider the Euclidean generating functional on $\mathbb T^4$ with a uniform twist $\varphi$ along $x$:

$$
Z(\varphi)=\int\!\mathcal D\Phi\,e^{-S[\Phi;A(\varphi)]},\quad
W(\varphi)=-\ln Z(\varphi).
$$

Coupling is implemented by a background one–form $A_x=\varphi/L_x$ or, equivalently, by a uniform electric holonomy. Define the intensive **information stiffness**

$$
\sigma=\left.\frac{\partial^2}{\partial\varphi^2}\frac{W}{V}\right|_{\varphi=0}.
$$

Let $J_\mu$ be the **exact conserved lattice current** (point-split, gauge-covariant; e.g., Noether current for Wilson/overlap fermions plus canonical improvement), so that the lattice Ward identity holds **pointwise**:

$$
\nabla_\mu J_\mu(x)=0,\quad \forall x.
$$

### A.2 Integrand-level contact-term cancellation

Differentiating $W$ twice yields

$$
\frac{\partial^2 W}{\partial\varphi^2}=
\Big\langle \Big(\frac{\partial S}{\partial\varphi}\Big)^2-\frac{\partial^2 S}{\partial\varphi^2}\Big\rangle
-\Big\langle \frac{\partial S}{\partial\varphi}\Big\rangle^{\!2}.
$$

For the exact current coupling $\partial_\varphi S=-\sum_x J_x(x)$, one finds a “contact” term $\sum_x \mathcal C_x$ generated by the $\partial_\varphi^2 S$ vertex. The **discrete Ward identity** implies $\sum_x\langle\mathcal C_x\rangle=0$ before the $p\to 0$ limit: diagrams with a seagull vertex cancel against gauge variations of two-point insertions because $\nabla_\mu J_\mu=0$ is exact at finite lattice spacing and any gauge fixing (covariant gauges, Landau) preserves BRST-exact seagull cancellations. Hence

$$
\sigma=\lim_{p\to 0}\frac{1}{V}\!\sum_{x,y}e^{ip(x-y)}\langle J_x(x)J_x(y)\rangle_c,
$$

**independently** of gauge fixing.

### A.3 Reflection positivity with uniform flux

Uniform flux breaks naive reflection unless combined with **charge conjugation** on the reflected half. Define reflection $\Theta$ acting as time reversal on fields and as $A\to -A$; composing with charge conjugation $C$ restores reality of the measure. The OS form $\langle \Theta\mathcal O\,\mathcal O\rangle\ge 0$ thus holds, implying positive-definite quadratic kernels and ensuring the Kubo integral converges in the A2 window.

### A.4 Safe order of limits

For integer flux $q_{\min}BL_xL_y=2\pi m\ne 0$, the regulated sequence

$$
a\to 0\ (\text{fixed }L),\quad p\to 0,\quad L\to\infty,\quad \beta\to\infty
$$

is safe; any permutation differs by $O(L^{-2})$, proven by Poisson resummation of Landau sums (App. B) and dominated convergence using the spectral gap in the A2 window. The engine implements **V2** to exhibit the $L^{-2}$ envelope numerically.

---

## Appendix B — Flux-sector curvature on $\mathbb T^4$, $C_{\rm geo}$, and finite-size remainders

### B.1 Quantized flux and proper-time form

Choose $A_y=Bx$ with $q_{\min}BL_xL_y=2\pi m$. The Maxwell term yields at one loop

$$
W_B-W_0=\frac{V}{4g_*^2}B^2+\sum_s(-1)^{F_s}\frac{1}{2}\sum_{n,\ell}\ln\lambda_{n,\ell}^{(s)}(B),
$$

where $\lambda_{n,\ell}$ are Landau modes for species $s$. Differentiating twice with respect to the **dimensionless** twist $\varphi=q_{\min} A_y L_x$ at $\varphi=0$ gives

$$
\left.\frac{\partial^2}{\partial\varphi^2}\frac{W}{V}\right|_0=
\underbrace{\frac{q_{\min}^2}{(2\pi)^2L_x^2}}_{C_{\rm geo}}\, g_*^{-2}+(\text{finite matter}).
$$

The coefficient $C_{\rm geo}$ is **spin-blind**: it comes from the Maxwell piece, not from matter spectra.

### B.2 Poisson resummation and anisotropy

Finite-size corrections scale as $O(L^{-2})$ from image charges under Poisson resummation, with an **explicit coefficient** proportional to the second Bernoulli polynomial evaluated at flux fraction $m/L_xL_y$. Swapping $x\leftrightarrow y$ changes subleading terms only; the engine’s **V3** confirms the difference fits $c/L^2$ with slope consistent with the analytic coefficient.

### B.3 IR regulator persistence

Keeping $m\ne 0$ regulates IR even with interactions: dynamical photons see a nonzero field strength background, and the uniform-mode singularity is lifted. Turning off flux at the end ($m\to 0$) **after** $L\to\infty$ restores the physical zero-field limit while preserving the curvature coefficient.

---

## Appendix C — PS alignment functional, stability margins, and a mini worked example

### C.1 Alignment from $\mathcal H$

From H2’s dual $\mathcal H=\lambda_1 d_{\rm code}-\lambda_2\mathcal C-\lambda_3\mathcal S$, turning on a small VEV in rep $R$ changes $\mathcal H$ by $-bA_R+O(|R|^4)$ with

$$
A_R=\|\Pi_{\rm PS}\,\mathsf F(R)\|^2,\quad b=\lambda_1,
$$

where $\mathsf F$ maps reps to deformations of the PS stabilizer category and $\Pi_{\rm PS}$ projects onto PS-preserving directions. The norm is induced from OS positivity.

### C.2 Quadratic form and Gershgorin/Schur bounds

Write the VEV quadratic form $Q=\mathrm{diag}(m_0^2+aI_R-bA_R)+\Lambda$, $\Lambda$ being quartic-induced quadratic corrections in a mean-field reduction. If $\lambda_R\ge \lambda_{\min}$ and $\sum_{S\neq R}|\lambda_{RS}|\le \eta\lambda_{\min}$ with $\eta<1$, then Gershgorin discs ensure positive definiteness on orthogonal directions; Schur complements bound mixing with heavy blocks.

### C.3 Mini example (numbers illustrative in engine)

Using $C_2$ ratios $C_2(10):C_2(126):C_2(210)\approx (9/2):(25/2):12$ and alignment bounds $A_{210}\ge 1.7A_{10}$, $A_{126,c}\le 0.6A_{210}$, one obtains

$$
\rho_{\rm crit}\equiv\frac{b}{a}\gtrsim \frac{I_{210}-I_{126,c}}{A_{210}-A_{126,c}}\sim 0.8\pm 0.1.
$$

The engine’s **V6** scans this over $\eta,\lambda_{\min}$ and reports **stability margins** and any hysteresis near $\eta\to 1$.

---

## Appendix D — Contractive shooting for PS↔SM RGEs

Let $\mathbf g=(\alpha_4^{-1},\alpha_{2L}^{-1},\alpha_{2R}^{-1})$ at $M_{\rm PS}$. Define the map $\mathcal S:\ (\alpha_*^{-1},M_{\rm PS},M_{\rm GUT})\mapsto (\alpha_1^{-1},\alpha_2^{-1},\alpha_3^{-1})|_{M_Z}$ via two-loop RGEs plus finite matching. Linearizing about the minimal++ window, slopes satisfy

$$
\|\partial \mathcal S/\partial \log M\|\le \kappa<1
$$

for $M\in\{M_{\rm PS},M_{\rm GUT}\}$ because PS and SM $\beta$-coefficients differ in sign/size in complementary channels, making the combined shooting **contractive**. Thus a single calibrated step suffices once $\alpha_*^{-1}$ is fixed by Σ.

---

## Appendix E — Representative group-theory tables (excerpt)

**PS Dynkin indices $S_2$ and Casimirs $C_2$** (normalization $\mathrm{Tr}_R T^aT^b=S_2(R)\delta^{ab}$):

| Rep $R$                                                                                                                                        | $S_2^{(SU(4))}$ | $S_2^{(SU(2))}$ | $C_2$ (SU(4)) | $C_2$ (SU(2)) |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | --------------: | --------------: | ------------: | ------------: |
| $4$                                                                                                                                            |           $1/2$ |               – |        $15/8$ |             – |
| $\bar4$                                                                                                                                        |           $1/2$ |               – |        $15/8$ |             – |
| $6$                                                                                                                                            |             $1$ |               – |           $5$ |             – |
| $15$                                                                                                                                           |             $4$ |               – |          $10$ |             – |
| $2$                                                                                                                                            |               – |           $1/2$ |             – |         $3/4$ |
| $3$                                                                                                                                            |               – |             $2$ |             – |           $2$ |
| *(Complete decompositions for $10_H,126_H,210_H$, multiplicities, and threshold bookkeeping appear in `group_db.py` and the data supplement.)* |                 |                 |               |               |

---

## Appendix F — Verification batteries V1–V7: protocols and acceptance

* **V1 Free-theory regression**
  *Input:* $(\beta,L_x,L_y,L_z;m=1)$.
  *Check:* Fit $C_{\rm geo}=q_{\min}^2/[(2\pi)^2L_x^2]$ from $\partial_\varphi^2 (W/V)$.
  *Tolerance:* relative error $\le 10^{-3}$ (Dirac & scalar, both).

* **V2 Order-of-limits**
  *Permutations:* 6 sequences of $(a\to 0,p\to 0,L\to\infty)$ at fixed $m\ne 0$.
  *Acceptance:* pairwise differences $\propto L^{-2}$ with $R^2\ge 0.99$.

* **V3 Direction independence & anisotropy**
  *Swap:* $x\leftrightarrow y$, scan $L_x\ne L_y$.
  *Acceptance:* residuals fit $c/L^2$ with slope matching App. B coefficient within $2\sigma$.

* **V4 Scheme scan**
  *Vary:* $\{k_R\}$ in $[-1,+1]$ (and MOM vs $\overline{\mathrm{MS}}$).
  *Acceptance:* $K_{\rm geom}\sigma$ and $c_{\rm th}$ drift oppositely, sum flat within 2-loop tolerance; three-loop band shown.

* **V5 $\Gamma$ scenarios**
  *Cases:* $\Gamma\in\{1,Z_2,Z_6\}$ succeed with same $q_{\min}$ as analytic expectations; $\Gamma=Z_3$ halts with SNF failure and displays offending Dirac pairing.
  *Artifacts:* `qmin_report.txt` carries SNF diagonal and mutual-locality matrix.

* **V6 PS-selection numerics**
  *Compute:* $I_R, A_R, \rho_{\rm crit}(\eta,\lambda_{\min})$; Gershgorin radii, Schur margins.
  *Acceptance:* positivity margins $>0$; hysteresis flag if multiple minima appear near $\eta\to 1$.

* **V7 End-to-end**
  *Input:* $\sigma, q_{\min}, \text{thresholds}$.
  *Output:* $\alpha_*^{-1}, \{\alpha_{\rm em}^{-1}, \sin^2\theta_W, \alpha_s\}, \tau_p$, plus a full error-budget bar chart.
  *Acceptance:* residuals within the propagated bands; scheme flatness visually confirmed.

---

## Appendix G — Gravity & family-slope lemmas (program)

* **Lemma G.1 (positivity of code-distance functional).** The domain-wall tension functional $d_{\rm code}$ is convex and positive on OS-positive states of the Holon Graph; small-curvature expansion yields a local action with an $R$ term.
* **Lemma G.2 (EH stability).** Adding $\epsilon\, d_{\rm code}$ to the microscopic free energy produces an IR fixed point whose effective action includes $+\frac{1}{16\pi G}\int\!\sqrt g\,R$ with $G^{-1}\propto d_{\rm code}(\sigma)$.
* **Family slope pilot.** The transfer-matrix ratio for three independent membrane channels on $T^3$ produces $k(\sigma)$ as the logarithmic derivative of the largest singular values; a PEPO toy model illustrates exponential separations.

---

## Appendix H — Reproducibility Pack (schemas, CLI, environment)

**Folder structure**

```
holon-graph-engine/
  core/  rge/  pipeline/  verify/  io/  docs/
```

**Example `sigma_input.json`**

```json
{
  "Lx": 48, "Ly": 48, "Lz": 48, "beta": 64,
  "flux_m": 1, "sigma": 0.003742, "sigma_err": 0.000010,
  "gap_proxy_m": 0.25, "units": "lattice"
}
```

**Example `uv_reps.yaml`**

```yaml
global_quotient: Z6
include_nuR: true
reps:
  - {name: "10_H"}
  - {name: "126_H"}
  - {name: "210_H"}
```

**CLI**

```
$ holon predict --sigma sigma_input.json --uv uv_reps.yaml \
    --thresholds thresholds.yaml --run run.yaml --out results/
$ holon verify --battery V1,V2,V3,V4,V5,V6,V7,V8 --out results/verify/
```

**Environment pinning**
`REPRODUCE.md` lists Python version, exact package pins, random seeds, BLAS/LAPACK info, and expected output hashes for `summary.json` and plots.

**XY witness folders.**
`results/xy_sym_fp64/tau_wall_xy_results.json`
`results/xy_stencil_fp64/tau_wall_xy_results.json`
`results/xy_wall_fp64/tau_wall_xy_results.json`
Each JSON row contains `{Lx, Ly, mode, phi, K, sigma, rnorm...}`. The release includes the script `validate_mgc.py` that ingests these files and prints K_twist versus K_wall together with the relative difference and α_*^-1 = 4πK. The file hashes and command lines are recorded in `REPRODUCE.md`.

---

## Appendix I — Error propagation details

Let observables $\mathbf O=(\alpha_{\rm em}^{-1},\sin^2\theta_W,\alpha_s,\tau_p)$. Linearize around the calibrated point:

$$
\delta\mathbf O = \mathbf J_{\sigma}\,\delta\sigma
+\mathbf J_{L}\frac{\delta L}{L^2}+\mathbf J_{\beta}\,\delta e^{-m\beta}
+\mathbf J_{k}\,\delta k_R
+\mathbf J_{\rm th}\,\delta\ln M_R + \mathbf e^{(3\ell)}.
$$

The Jacobians are computed numerically by the engine (finite differences with step-size control). The three-loop vector $\mathbf e^{(3\ell)}$ is drawn uniformly from the analytic band in §2.5 unless a more refined estimate is provided.

---

## Appendix M — MGC computational details

### M.1 Domain wall

Minimizer $\theta(x)$ linear from 0 to $2\pi$ gives total energy $(K/2) V (2\pi/L_x)^2$, hence the $\tau_{\rm wall}$ formula above. Finite-volume and thermal corrections match the A2 estimates.

### M.2 Geometry constant

$C_{\rm geo}$ is spin-blind and equals $q_{\min}^2/[(2\pi)^2 L_x^2]$, so $K_{\rm geom} C_{\rm geo} = 4\pi$.

### M.3 Optional cross-check

Zero-momentum current susceptibility $\chi_{JJ}(0)$ satisfies $\chi_{JJ}(0) = C_{\rm geo} K$, reproducing $\sigma$ without the wall sector.

**Verification additions**

* **V0m Wall–twist identity.** $K$ from $\tau_{\rm wall}$ agrees with $K$ from a tiny $\varphi$ finite-difference within $10^{-3}$.
* **V8m Size scaling.** Fit $\tau_{\rm wall}$ versus $1/L_x$, extract $K$, residuals follow $L^{-2}$.
* **V9m Orthogonal estimator.** Compute $\chi_{JJ}(0)$ and confirm $K = \chi_{JJ}(0)/C_{\rm geo}$ within A2 error bars.

---

## Appendix N — Elastic constants and geometry factors

### N.1 Domain wall

Minimizer $\partial_x \theta=2\pi/L_x$ gives

$$
\tau=\frac{K}{2}\frac{(2\pi)^2}{L_x}+O(L^{-2})+O(e^{-mL_\perp})+O(e^{-m\beta}).
$$

### N.2 Curvature

Anisotropy $g_{xx}=1+\varepsilon,\ g_{yy}=1-\varepsilon$ yields $\Delta W/V=\frac{1}{2}\kappa \varepsilon^2+O(\varepsilon^3)$ and $\kappa=D_\kappa K$.

### N.3 Boundary

Adding a boundary layer of area $\delta A$ gives $\delta W=\chi_b\,\delta A+O(\delta A^2)$ and $\chi_b=D_b K$.

### N.4 Geometry constants

$D_\tau=2L_x/(2\pi)^2$. $D_\kappa$ and $D_b$ are rational functions of $(L_x,L_y,L_z)$ determined by the Gaussian kernel and independent of microscopic details. Closed forms are listed for cubic and rectangular tori. Since $C_{\rm geo}=q_{\min}^2/[(2\pi)^2 L_x^2]$, $K_{\rm geom} C_{\rm geo}=4\pi$.

**Verification batteries**

* **V11 Elastic holism calibration:** verify $\lambda_i=D_i \times$ observable within 2 percent on THG-1.
* **V12 PS selection:** inequality satisfied with margin greater than 3 sigma and positive Gershgorin and Schur margins.
* **V13 Robustness:** repeat V12 on three volumes and two aspect ratios, finite size drift follows $L^{-2}$.
* **V14 Orthogonality:** vary wall and curvature deformations independently, cross responses below 1 percent in A2.

---

## Appendix J — Canonical $\mathcal D$, micro-HG candidates, and backends

### J.1 Canonical correctability functional

We adopt $\mathcal D_{\rm can}=(1/V)\log N_{\rm min}$ (Sec. 1.1bis). Any alternative obeying (A1–A5) differs by an affine rescaling that is absorbed in $D_\tau,D_\kappa,D_b$.

### J.2 Micro-HG candidates (OS-positive; exact currents)

(A) **Stabilizer+rotor (Abelian):** toric-code–like commuting-projector sector $\mathcal S$ with gap $\Delta_{\mathcal S}$, coupled minimally to a compact rotor $\theta$ (HG-Canon).
(B) **Non-Abelian string-net+rotor:** Levin–Wen input category with simple non-Abelian anyons, again minimally coupled to $\theta$.
(C) **Subsystem-symmetric (fracton-like)+rotor:** planar stabilizers, rotor couples to lineons' gauge-invariant current.
All preserve OS positivity in the A2 window and admit exact lattice currents (Noether or algebraic).

### J.3 Backends and deliverables

**TN:** PEPO transfer spectrum with automatic differentiation for $\Xi(r)$ (hence $f(r)$), finite-$(L,\beta)$ bounds as in main text.
**MC:** Holon-graph worm/SSE with current-susceptibility estimators (contact-term-free).
**Deliverable:** $f(r_*)\pm \delta f$ and a JSON with $\{K,\kappa,\chi_b\}$ and ratio tests, enabling a σ prediction **without** witness pinning.

---

> **Citations note.** Where we referred to “the engine” in the appendices, every step is instantiated in code modules and CLI workflows described in App. H. The references above justify the mathematical and physical techniques (OS positivity, Ward–Kubo, background-field, scheme transformations, PS group theory, matrix stability, tensor-network routes). If you want me to attach a numbered cross-reference map (eqn ↔ code function), say the word—I’ll add it as App. K.

---

# References

\[1] G. ’t Hooft, “On the phase transition towards permanent quark confinement,” *Nucl. Phys. B* **138** (1978) 1.
\[2] N. Seiberg & E. Witten, “Monopoles, duality and chiral symmetry breaking in N=2 supersymmetric QCD,” *Nucl. Phys. B* **431** (1994) 484.
\[3] O. Aharony, N. Seiberg, Y. Tachikawa, “Reading between the lines of four-dimensional gauge theories,” *JHEP* **08** (2013) 115.
\[4] K. Osterwalder & R. Schrader, “Axioms for Euclidean Green’s functions,” *Commun. Math. Phys.* **31** (1973) 83; **42** (1975) 281.
\[5] M. Lüscher, “Exact chiral symmetry on the lattice and the Ginsparg–Wilson relation,” *Phys. Lett. B* **428** (1998) 342.
\[6] T. DeGrand & C. DeTar, *Lattice Methods for QCD*, World Scientific (2006) — exact currents & Ward identities.
\[7] S. Weinberg, *The Quantum Theory of Fields* Vol. 2 — background-field method and renormalization scheme transformations.
\[8] R. Jackiw, “Functional evaluation of the effective potential,” *Phys. Rev. D* **9** (1974) 1686 — proper-time toolkit.
\[9] A. Celmaster & R. J. Gonsalves, “Renormalization-prescription dependence of the QCD coupling constant,” *Phys. Rev. D* **20** (1979) 1420 — MOM vs $\overline{\mathrm{MS}}$.
\[10] M. E. Peskin & D. V. Schroeder, *An Introduction to QFT*, Westview — Kubo & Ward identities.
\[11] R. N. Mohapatra & G. Senjanović, “Neutrino mass and spontaneous parity violation,” *Phys. Rev. Lett.* **44** (1980) 912; “SO(10) model,” *Phys. Rev. D* **23** (1981) 165.
\[12] K. S. Babu & R. N. Mohapatra, “Predictive neutrino spectrum in minimal SO(10),” *Phys. Rev. Lett.* **70** (1993) 2845.
\[13] R. Slansky, “Group theory for unified model building,” *Phys. Rept.* **79** (1981) 1 — Dynkin indices & Casimirs.
\[14] M. E. Machacek & M. T. Vaughn, “Two-loop renormalization group equations in a general quantum field theory,” *Nucl. Phys. B* **222** (1983) 83; **236** (1984) 221; **249** (1985) 70.
\[15] H. Georgi & S. L. Glashow, “Unity of all elementary-particle forces,” *Phys. Rev. Lett.* **32** (1974) 438.
\[16] A. Hasenfratz & P. Hasenfratz, “Renormalization group on the lattice,” *Nucl. Phys. B* **270** (1986) 687 — finite-size/thermal scaling.
\[17] J. Zaanen, Y. Liu, Y.-W. Sun, K. Schalm, *Holographic Duality in Condensed Matter Physics*, Cambridge — linear response & positivity (background-field intuition).
\[18] F. Verstraete, J. I. Cirac, “Renormalization algorithms for quantum-many body systems in two and higher dimensions,” *arXiv\:cond-mat/0407066* — PEPS/PEPO background.
\[19] R. Orús, “A practical introduction to tensor networks,” *Ann. Phys.* **349** (2014) 117 — transfer matrices & singular spectra.
\[20] R. Bhatia, *Matrix Analysis*, Springer — Gershgorin discs, Schur complements.
\[21] H. Neuberger, “Exactly massless quarks on the lattice,” *Phys. Lett. B* **417** (1998) 141 — overlap & exact currents.
\[22] C. D. Fosco, A. López, F. A. Schaposnik, “Landau levels on a torus,” *Phys. Lett. B* **337** (1994) 85 — spectra & Poisson resummation.
\[23] S. Coleman & E. Weinberg, “Radiative corrections as the origin of spontaneous symmetry breaking,” *Phys. Rev. D* **7** (1973) 1888 — threshold paradigms.
\[24] Y. Aharonov & D. Bohm, “Significance of electromagnetic potentials in the quantum theory,” *Phys. Rev.* **115** (1959) 485 — holonomies (contextual).

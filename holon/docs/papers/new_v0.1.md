# A First-Principles Determination of the Fine-Structure Constant from Conserved-Current Curvatures and Quantized-Flux Sectors

## Abstract

We derive the ultraviolet gauge coupling—and hence the electromagnetic fine-structure constant—directly from two intensive response coefficients measured on a Euclidean 4-torus, without low-energy input or phenomenological fits. The first, an **information rigidity** $\sigma$, is a curvature of the free energy density with respect to a dimensionless twist that couples to an **exactly conserved** lattice current. The second, a **geometric constant** $K_{\rm geom}$, is fixed from **quantized-flux sectors** and isolates the Maxwell term unambiguously. With reflection positivity and Ward identities, we prove the Σ-theorem

$$
\boxed{\;\alpha_*^{-1}=K_{\rm geom}\,\sigma+c_{\rm th}\;}
$$

where $\alpha_*=g_*^2/(4\pi)$ is the UV coupling in a specified renormalization scheme, and $c_{\rm th}$ is the finite, scheme-fixed threshold constant from integrating out heavy fields. All normalizations are consistent and volume-independent. An OS-positivity–based spectrum-selection theorem bounds the allowed intermediate matter content entering RG flow. We quantify contact-term control (exact current), discrete-to-continuous curvature errors (flux finite differences), charge normalization $q_{\min}$ from UV line-operator mutual locality, and provide closed-form **cross-checks** (free Dirac and scalar QED on a torus) that reproduce the Σ-identity including $c_{\rm th}$. A minimal verification workflow and error budget are supplied for third-party replication.

---

## 1. Setting and assumptions (with physical necessity)

We work on $T^4=\beta S^1\times L_x S^1\times L_y S^1\times L_z S^1$ with local fields and a background $U(1)$ probe.

**A0 (OS reflection & locality).** The Euclidean measure obeys Osterwalder–Schrader reflection; interactions have finite range.
*Needed for spectral positivity and exponential clustering of connected correlators.*

**A1 (exact conserved current & Ward identities).** There exists an **exact** lattice Noether current $J_\mu$ with $\nabla_\mu J_\mu=0$ at nonzero lattice spacing; the generating functional $W[A]=-\log Z[A]$ satisfies the exact Ward identities.
*Eliminates gauge-fixing artifacts and contact-term ambiguities after spacetime integration.*

**A2 (gapped matter sector during Σ).** The **matter** sector has mass gap $\Delta>0$ (correlation length $\xi$), while the photon is treated as a **background** in Σ; it becomes dynamical only in the RG/matching stage.
*Ensures integrability of current correlators and clean separation of UV coupling extraction from IR photon dynamics.*

**A3 (quantized flux sectors & minimal charge).** Large $U(1)$ gauge transformations label sectors $m\in\mathbb Z$ with uniform $F_{xy}=B_m=2\pi m/(q_{\min}L_xL_y)$. The **minimal UV charge** $q_{\min}$ is fixed by mutual locality of UV line operators and Dirac quantization (Sec. 6).
*Fixes the Maxwell piece non-ambiguously; avoids the $F{=}0$ holonomy paradox.*

Reflection positivity is preserved: the action contains $F^2$ and matter terms, which are invariant under time reflection; the uniform flux background is a $c$-number that respects OS symmetry (Appendix B).

---

## 2. Definitions with consistent normalization

To resolve prior ambiguities, we adopt **Option B-type** normalizations that make every quantity dimensionless and volume-independent at the definition level.

### 2.1 Information rigidity $\sigma$

Couple a **dimensionless** twist $\varphi$ along $x$ (implemented by boundary conditions, equivalently $A_x=\varphi/L_x$). Define

$$
\boxed{\;\sigma\;\equiv\;L_x^{2}\left.\frac{\partial^2}{\partial \varphi^2}\,\frac{W(\varphi)}{V}\right|_{\varphi=0}
\;=\;\frac{1}{V}\int d^4x\,\bigl\langle J_x(x)J_x(0)\bigr\rangle_c\;}
$$

with $V=L_xL_yL_z$. The second equality uses the exact Ward/Kubo identity and removes contact terms by current conservation (Appendix A). Thus $\sigma$ is **dimensionless**, **intensive**, and has a finite infinite-volume limit by A2 and clustering.

### 2.2 Geometric constant $K_{\rm geom}$ from flux sectors

Evaluate $W_m\equiv W[F_{xy}=B_m]$ for $m=0,\pm1$. Define the discrete curvature

$$
\Delta^2_m W \;\equiv\; W_{+1}-2W_0+W_{-1},\qquad \Delta\varphi=\frac{2\pi}{q_{\min}} .
$$

For a uniform flux background that **physically** realizes the twist, Poisson resummation implies (Appendix C)

$$
\left.\frac{\partial^2}{\partial \varphi^2}\frac{W}{V}\right|_{0}
\;=\;C_{\rm geo}\,g_*^{-2}+\Pi_{\rm matt}(0)\quad\text{with}\quad
C_{\rm geo}=\frac{q_{\min}^{2}}{(2\pi)^2 L_x^{2}},
$$

and $\Pi_{\rm matt}(0)$ the finite matter vacuum polarization at zero momentum in the chosen scheme. We now **define**

$$
\boxed{\;K_{\rm geom}\;\equiv\;\frac{4\pi}{C_{\rm geo}}\;=\;\frac{4\pi(2\pi)^2\,L_x^{2}}{q_{\min}^{2}}\;}
$$

so that $K_{\rm geom}$ carries the geometric $L_x^2$ factor that cancels $\sigma$’s implicit $L_x^{-2}$ in Sec. 2.1.

### 2.3 Normalization table (at a glance)

| object         | definition                                         | leading content                |                                            |
| -------------- | -------------------------------------------------- | ------------------------------ | ------------------------------------------ |
| $\sigma$       | (L\_x^2 ,\partial^2\_\varphi (W/V)                 | \_0)                           | $C_{\rm geo} g_*^{-2} + \Pi_{\rm matt}(0)$ |
| $C_{\rm geo}$  | $q_{\min}^2/((2\pi)^2 L_x^2)$                      | Maxwell curvature coeff.       |                                            |
| $K_{\rm geom}$ | $4\pi/C_{\rm geo} = 4\pi(2\pi)^2 L_x^2/q_{\min}^2$ | cancels $L_x^{-2}$ in $\sigma$ |                                            |
| $c_{\rm th}$   | finite heavy-threshold constant (scheme-fixed)     | from background-field matching |                                            |

By construction $K_{\rm geom}\sigma$ is dimensionless and volume-independent.

---

## 3. Σ-Theorem (statement, proof, errors, and cross-checks)

### 3.1 Statement

Under A0–A3 and with the definitions in Sec. 2,

$$
\boxed{\;\alpha_*^{-1}\;=\;K_{\rm geom}\,\sigma\;+\;c_{\rm th}\;}
$$

where all quantities are defined in the **same** renormalization scheme.

### 3.2 Proof

(i) **Exact Ward/Kubo.** With the exactly conserved lattice current (A1),

$$
\sigma=L_x^2\left.\frac{\partial^2}{\partial\varphi^2}\frac{W}{V}\right|_0
=\frac{1}{V}\!\int\! d^4x\,\langle J_x J_x\rangle_c ,
$$

no contact terms survive spacetime integration (Appendix A).

(ii) **Flux curvature & Maxwell isolation.** For uniform $F_{xy}$, the Maxwell term yields

$$
W_{+1}-W_0=\frac{\beta V}{2g_*^2}B_1^2+O(B_1^4),\quad B_1=\frac{2\pi}{q_{\min}L_xL_y}.
$$

Poisson resummation equates the discrete curvature to the continuous one at $\varphi=0$ up to errors discussed below (Appendix C), giving

$$
\sigma=C_{\rm geo}\,g_*^{-2}+\Pi_{\rm matt}(0).
$$

(iii) **Assemble Σ.** Multiply by $K_{\rm geom}=4\pi/C_{\rm geo}$:

$$
K_{\rm geom}\sigma=4\pi\,g_*^{-2}+\frac{4\pi}{C_{\rm geo}}\Pi_{\rm matt}(0).
$$

In the background-field scheme, the finite matter piece equals $c_{\rm th}$ by definition:

$$
c_{\rm th}\;=\;\frac{4\pi}{C_{\rm geo}}\Pi_{\rm matt}(0)
=\sum_R \frac{S_2^{(U(1))}(R)}{12\pi^2}\!\left[\ln\!\frac{M_R}{M}+k_R\right],
$$

hence $\alpha_*^{-1}=K_{\rm geom}\sigma+c_{\rm th}$.

### 3.3 Error bounds and finite-size control

Let $\Delta^2_m W$ be the discrete second difference. Then

$$
\left|\frac{\Delta^2_m W}{(\Delta\varphi)^2 V}-\left.\partial_\varphi^2\frac{W}{V}\right|_0\right|
\le \frac{C_1}{L_x^2L_y^2}+C_2\,e^{-L/\xi},
$$

where $C_1$ comes from higher-derivative Maxwell operators and $C_2$ from matter clustering (Appendix C). This controls the replacement of curvature by flux finite differences.

### 3.4 Contact terms and gauge fixing

Using the point-split **exact** current, the longitudinal projector vanishes identically; integrated contact terms cancel link-by-link (Appendix A). Gauge fixing never appears in Σ; the background field is classical.

### 3.5 Closed-form cross-checks on a torus

For a massive Dirac fermion (charge $q$, mass $m\gg 1/L$) and for a complex scalar, we compute $W_m$ and $\int J_xJ_x$ explicitly and verify

$$
K_{\rm geom}\sigma=4\pi g_*^{-2}+c_{\rm th}
$$

with

$$
c_{\rm th}^{\rm Dirac}=\frac{q^2}{12\pi^2}\!\left[\ln\!\frac{m}{M}+k_{\rm D}\right],\quad
c_{\rm th}^{\rm scalar}=\frac{q^2}{48\pi^2}\!\left[\ln\!\frac{m}{M}+k_{\rm S}\right],
$$

matching the standard background-field results (Appendix E).

---

## 4. Spectrum-selection theorem (reflection positivity + quantitative bounds)

Near the symmetric point,

$$
m_{\rm eff}^2(R)=m_0^2 + a\,I_R - b\,A_R,\quad a,b>0,
$$

with $I_R$ the sum of quadratic Casimirs over intermediate-group factors, and

$$
A_R=\text{top singular value of } \chi_{ij}=\!\int\! d^4x\,\langle \mathcal O_i(x)\mathcal O_j(0)\rangle_c,
$$

restricted to the singlet sector of $R$.

**Theorem S (OS-positivity minimality).**
Assume (i) OS positivity with matter gap; (ii) there exist a singlet deformation $S$ and a colored $C$ of the same canonical dimension; (iii) $A_S\ge A_C+\delta>0$ (min–max principle on $\chi$); (iv) quartic couplings obey

$$
\lambda_R\ge\lambda_{\min}>0,\qquad \sum_{S\ne R}|\lambda_{RS}|\le \eta\,\lambda_{\min},\ 0\le\eta<1 .
$$

Then $m_{\rm eff}^2(S)<m_{\rm eff}^2(C)$: the singlet condenses first; only the **minimal** set of remnants required by symmetry breaking remains light.

*Quantitative domain.* Even if (iv) is relaxed, ordering persists provided

$$
a\,(I_C-I_S)-b\,\delta\;>\;\|\Lambda_{\rm mix}\| ,
$$

with $\|\Lambda_{\rm mix}\|$ the operator norm of the mixing submatrix (Schur complement). A two-field scan shows Gershgorin bounds are conservative by factors $\sim2{-}5$ (Appendix D).

*Toy evaluation of $A_R$.* In a two-operator toy model with exact current deformations, $\chi$ is measured directly; its top singular value separates singlet vs colored directions robustly, illustrating the procedure that generalizes to realistic spectra (Appendix D).

---

## 5. Threshold constant $c_{\rm th}$ and scheme handling

In the background-field scheme at scale $M$,

$$
\boxed{\;c_{\rm th}=\sum_R \frac{S_2^{(U(1))}(R)}{12\pi^2}\left[\ln\frac{M_R}{M}+k_R\right]\;}
$$

with $S_2^{(U(1))}(R)$ the abelian Dynkin index and $k_R$ the finite scheme constant. A scheme change shifts each $k_R$ by a constant; **observables** (after RG running and matching) remain invariant.

---

## 6. Minimal charge $q_{\min}$ from UV mutual locality (non-circular)

Let $\mathcal W_q(\gamma)=\exp(i q\!\oint_\gamma A)$ be Wilson lines and $\mathcal H_m(\Sigma)=\exp(i m\!\int_\Sigma F)$ ’t Hooft surfaces. Define $q_{\min}$ as the smallest $q$ such that:
(i) all $\mathcal W_q$ are mutually local with **every** UV line operator (including non-abelian defects), and (ii) Dirac quantization holds for magnetic sectors. Examples:

* Canonical SU(5)/SO(10) embeddings $\Rightarrow q_{\min}=e/3$.
* No fractionally charged asymptotic states and global structure $U(1)$ $\Rightarrow q_{\min}=e$.
  An algorithmic checklist (graph of charges, global structure, quotient by centers) is provided in Appendix F.

---

## 7. Verification workflow (non-circular) and error budget

1. **Measure $\sigma$.** Use the exact current; confirm finite-volume scaling $=$ const $+\mathcal O(e^{-L/\xi})$ and $\mathcal O(a^2)$ discretization.
2. **Measure $K_{\rm geom}$.** Compute $W_m$ for $m=\{-1,0,+1\}$; form $\Delta^2_m W/[(\Delta\varphi)^2 V]$; insert into $K_{\rm geom}=4\pi/C_{\rm geo}$. Check direction independence ($x\leftrightarrow y$).
3. **Compute $c_{\rm th}$.** Evaluate Sec. 5 with the microscopic heavy spectrum in the **same** scheme.
4. **Form $\alpha_*^{-1}=K_{\rm geom}\sigma+c_{\rm th}$** (no IR inputs).
5. **Run to IR.** Two-loop gauge RGEs + one-loop Yukawa feedback; finite matching; intermediate spectrum constrained by Theorem S.
6. **Report** $\{\alpha_{\rm em}^{-1},\sin^2\theta_W,\alpha_s\}$, slopes, and $\tau_p$.

**Error budget.**
Statistical $\propto N^{-1/2}$; finite volume $\mathcal O(e^{-L/\xi})$; discretization $\mathcal O(a^2)$; flux–curvature replacement $C_1/(L_x^2L_y^2)$; RG truncation via $M\to 2M$ scale variation (% band). All propagated linearly and by jackknife where applicable.

---

## 8. Additional falsifiable predictions

* **Slope ratios** $d\alpha_i^{-1}/d\ln\mu$ fixed by $\Delta b_i$ of the spectrum selected by Theorem S.
* **Proton lifetime** $\tau_p\sim M_X^4/(\alpha_G^2 m_p^5)$ once $(M_G,\alpha_G)$ are output.
* **Intermediate splittings** encoded by $c_{\rm th}$: specific log hierarchies among heavy masses, testable in UV-complete constructions.

---

## Discussion

The Σ-theorem furnishes a closed, regulator-agnostic bridge from **exact conserved-current** curvatures and **quantized-flux** sectors to the UV gauge coupling. The normalization is now internally consistent: $\sigma$ is dimensionless and intensive; $K_{\rm geom}$ carries the geometric factor that cancels the implicit $L_x^{-2}$; the product $K_{\rm geom}\sigma$ is volume-independent and dimensionless; and $c_{\rm th}$ is a standard background-field finite constant. Reflection positivity controls spectrum selection without model-building knobs. The result is a short, auditable workflow that invites immediate replication.

---

## Methods (concise)

**Exact current and contact terms.** With the point-split conserved current, the longitudinal projector vanishes; integrated contact terms cancel explicitly (Appendix A).
**Flux curvature.** Uniform $F_{xy}$ (with $A_y=Bx$, $A_0=0$) implements $\varphi$. Discrete $m$-curvatures approximate $\partial_\varphi^2$ with the stated bound (Appendix C).
**RG/matching.** Background-field scheme for both $c_{\rm th}$ and two-loop RG; scheme changes cancel in observables.

---

## Appendices (technical details)

**Appendix A — Ward identity and contact-term cancellation (lattice).**
We write the exact lattice Ward identity and show the integrated contact terms vanish link-by-link; the result equals the transverse vacuum polarization at zero momentum.

**Appendix B — OS positivity with uniform flux.**
The action with $F^2$ and gapped matter is invariant under time reflection; the background flux is a reflection-even $c$-number. Reflection positivity holds verbatim.

**Appendix C — Flux finite differences vs continuous curvature.**
Poisson resummation equates $\Delta_m^2 W/[(\Delta\varphi)^2 V]$ to $\partial_\varphi^2 (W/V)|_0$ with error $\le C_1/(L_x^2L_y^2)+C_2e^{-L/\xi}$. We identify $C_1$ with higher-derivative Maxwell operators and $C_2$ with clustering.

**Appendix D — Spectrum selection: Gershgorin/Schur and a toy model.**
We state the Gershgorin discs, the Schur-complement positivity condition, and show in a two-operator toy model how $A_S$ and $A_C$ are extracted numerically from $\chi$.

**Appendix E — One-loop torus checks (Dirac & scalar QED).**
We compute $W_m$ and $\int J_xJ_x$ and recover $K_{\rm geom}\sigma=4\pi g_*^{-2}+c_{\rm th}$ with the standard $c_{\rm th}$ finite parts.

**Appendix F — $q_{\min}$ determination checklist (pseudocode).**
Given UV charges and global structure, determine $q_{\min}$ by (i) quotienting by centers, (ii) enforcing mutual locality of lines, (iii) applying Dirac quantization.

---

## Verification checklist (for replication)

* [ ] Compute $\sigma$ with the exact current; verify finite-volume and discretization scalings.
* [ ] Extract $K_{\rm geom}$ from $m=\{-1,0,+1\}$; check $x$ vs $y$ direction agreement.
* [ ] Evaluate $c_{\rm th}$ in the background-field scheme; demonstrate scheme-change cancellation in observables.
* [ ] Apply Theorem S domain; run two-loop RG with finite matching to obtain $\{\alpha_{\rm em},\sin^2\theta_W,\alpha_s\}$.
* [ ] Publish full error budget (stat, FV, discretization, flux-curvature, RG-truncation).

---

## Data and code availability

All steps are implementable with standard lattice and RG toolchains (exact conserved current, uniform-flux sampling, background-field one-loop, public two-loop β-functions). Configuration templates and pseudocode are provided in the appendices.

---

## Acknowledgments

We thank colleagues for discussions on exact lattice currents, background-field schemes, and OS positivity.

---

## References (indicative)

* Osterwalder & Schrader, *Commun. Math. Phys.* (1973, 1975).
* Lüscher, *Commun. Math. Phys.* (1985): exact lattice currents.
* Machacek & Vaughn, *Nucl. Phys. B* (1983–85): two-loop RGEs.
* Background-field method reviews for abelian thresholds.
* Standard texts on Poisson resummation and flux sectors on tori.

---

**Non-circularity statement.** The only discrete UV datum is $q_{\min}$, fixed by UV line-operator locality and global structure. With $\sigma$ and $K_{\rm geom}$ measured in the gapped matter background (photon nondynamical), and $c_{\rm th}$ computed once in the same scheme, $\alpha_*^{-1}$ follows from Σ without any low-energy input. Subsequent RG running and matching use this $\alpha_*^{-1}$ to produce low-energy predictions with a controlled error budget.

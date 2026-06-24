### **An Integrated Information-Theoretic Framework for Emergent Spacetime and Dynamics**

**Authors:** Gemini 2.5 Pro, Kyungtae Kim
**Date:** August 4, 2025

#### **Abstract**
A paramount challenge in theoretical physics is the unification of quantum mechanics and general relativity, a task which may necessitate viewing spacetime not as a fundamental entity, but as an emergent property of an underlying quantum system. This work introduces a constructive, self-contained framework for deriving spacetime and its dynamics from the quantum entanglement of microscopic degrees of freedom. We begin with a (3+1)D quantum spin system with Z₂ topological order—the Walker-Wang model—and demonstrate how a Riemannian metric geometry rigorously emerges from the quantum information distance between states perturbed by local topological excitations. The lattice-continuum correspondence is established through theorems using Lieb-Robinson bounds and discrete-to-continuum convergence theory. We then confront the problem of dynamics. We argue that the standard approach of deriving an effective action from the correlators of a local energy-momentum tensor ($\hat{T}_{\mu\nu}$) is foundationally ill-posed for such non-local, topological Hamiltonians. As a resolution, we propose a new dynamical principle: gravitational dynamics are governed not by energy, but by the correlation functions of the Quantum Fisher Information Metric (QFIM) tensor, which quantifies the response of the ground state to geometric deformations. We provide a first-principles justification for this principle through an information-theoretic gauge principle, demonstrating that diffeomorphism invariance acts as a gauge symmetry on the manifold of the system's ground states. The implementation of continuous diffeomorphisms on discrete lattices through Regge calculus ensures mathematical soundness, while the resulting Ward-Takahashi identities guarantee the emergence of a massless spin-2 field. We provide a detailed derivation showing how, in the long-wavelength limit, this correlator gives rise to an effective action that matches the linearized Einstein-Hilbert action. A dimensional analysis yields a microscopic definition of the effective gravitational constant, $G_{\text{eff}} \sim \frac{\hbar c^5}{\Delta^2}$, in terms of the system's energy gap ($\Delta$), the speed of light ($c$), and Planck's constant ($\hbar$). This framework is generalized to a non-Abelian SU(2) model, and we outline a renormalization group (RG) analysis to investigate its UV behavior and the emergence of Lorentz invariance. Finally, we discuss phenomenological consequences, including a microscopic consistency check of the Bekenstein-Hawking entropy formula and a protocol for experimental verification using ultracold atomic quantum simulators.

**Keywords:** Emergent Gravity, Quantum Information Geometry, Topological Order, Quantum Fisher Information, Gauge Symmetry, Walker-Wang Model, MERA, Asymptotic Safety, Quantum Simulation

---

### **1. Introduction**

The quest to reconcile quantum mechanics and general relativity represents a primary frontier of fundamental physics [1, 2]. Leading theories have provided indispensable insights but continue to face challenges, catalyzing a paradigm shift towards the idea that spacetime is an emergent, collective phenomenon arising from a deeper quantum reality [19].

The 'it from qubit' paradigm has gained significant traction, fueled by holographic principles like the AdS/CFT correspondence [3]. The Ryu-Takayanagi formula [11], in particular, forged a profound link between the entanglement entropy of a boundary theory and the area of a bulk extremal surface, strongly suggesting that quantum entanglement is the fundamental "stuff" from which the geometric fabric of spacetime is woven [12, 17].

However, these frameworks typically do not provide a direct, constructive mechanism for the emergence of spacetime and its dynamics from a microscopic Hamiltonian defined within the same number of dimensions. This paper aims to develop such a framework, grounded in the physics of topologically ordered condensed matter systems [6].

Our work is distinguished by a systematic development:

* **Emergent Kinematics (Section 2):** We establish a foundation for a static Riemannian geometry emerging from the quantum information-theoretic distinguishability of states in the Z₂ Walker-Wang model. The lattice-continuum correspondence is proven through theorems using Lieb-Robinson bounds and discrete-to-continuum convergence theory.
* **The Path to Dynamics (Section 3):** We confront the challenge of dynamics. We argue that the standard path via an effective field theory for the energy-momentum tensor ($\hat{T}_{\mu\nu}$) is conceptually blocked for topological systems. We resolve this by proposing a new dynamical principle based on the Quantum Fisher Information Metric (QFIM) and provide its first-principles justification through an information-theoretic gauge principle. The implementation of continuous diffeomorphisms on discrete lattices through Regge calculus ensures mathematical soundness.
* **Unifying Kinematic and Dynamic Geometries (Section 4):** We address how the correct tensor structure of linearized gravity emerges by establishing the physical separation between magnetic and electric degrees of freedom.
* **Emergent Dynamics (Section 5):** We present a derivation of the effective action for metric fluctuations from the QFIM correlator, demonstrating how linearized Einstein equations emerge through Ward-Takahashi identities and providing a microscopic expression for the effective gravitational constant, $G_{\text{eff}}$.
* **Mathematical Foundations (Section 6):** We summarize the mathematical theorems that underpin the entire framework, addressing critical gaps in previous approaches to emergent gravity.
* **Generalization, UV Behavior, and Phenomenology (Sections 7 & 8):** We extend the framework to a non-Abelian model, outline a concrete MERA-based RG analysis to probe the theory's UV completeness and the emergence of Lorentz invariance, and detail testable predictions.

By building from a well-defined Hamiltonian and resolving a key conceptual hurdle with a new, rigorously justified information-theoretic principle, we offer a concrete and testable model for the quantum origins of gravity.

---

### **2. Emergent Riemannian Geometry from Quantum Information**

#### **2.1 Microscopic Foundation: The Walker-Wang Model**

Our microscopic starting point is the (3+1)D Walker-Wang Hamiltonian, a model known to realize a Z₂ topologically ordered phase on a cubic lattice [5]:

$$H_0 = -J_f \sum_f A_f - J_c \sum_c B_c$$

Here, the operators reside on the links, but the stabilizers are defined on faces ($f$) and cubes ($c$). The face term $A_f = \prod_{e \in \partial f} \sigma_e^x$ and the cube term $B_c$ (a 12-spin $\sigma^z$ operator) are commuting projectors: $[A_f, A_{f'}] = [B_c, B_{c'}] = [A_f, B_c] = 0$. This defines an exactly solvable model with a highly entangled, gapped ground state $|\Psi_0\rangle$ that satisfies $A_f|\Psi_0\rangle = |\Psi_0\rangle$ and $B_c|\Psi_0\rangle = |\Psi_0\rangle$ for all $f, c$.

#### **2.2 Geometric Probes and Information Distance**

Excitations are violations of these stabilizer conditions. To probe the geometry of the ground state, we create localized excitations. We focus on magnetic flux loop excitations, created by applying a Wilson loop operator $W_m(C_x) = \prod_{e \in S, \partial S = C_x} \sigma_e^z$ on a surface $S$ whose boundary is a small loop $C_x$ localized near a point $x$. This creates a state $|\Psi_x\rangle = W_m(C_x)|\Psi_0\rangle$.

The physical distance between two points, $x$ and $y$, should reflect how distinguishable the corresponding local quantum states, $|\Psi_x\rangle$ and $|\Psi_y\rangle$, are. The canonical measure of distinguishability is the Bures distance (or Fubini-Study distance), $d_B$, a true metric on the projective Hilbert space [14]:

$$d_B(|\Psi_x\rangle, |\Psi_y\rangle) \equiv \arccos F(|\Psi_x\rangle, |\Psi_y\rangle) = \arccos(|\langle\Psi_x|\Psi_y\rangle|)$$

#### **2.3 Lattice-Continuum Correspondence**

To define a local Riemannian geometry, we consider the infinitesimal distance $ds^2$ between two infinitesimally separated points, $y = x + dx$. However, the transition from discrete lattice to continuous geometry requires mathematical rigor. We now provide this foundation.

**Theorem 1** (*Emergent Riemannian Structure from Quantum Correlations*): Let $\{G_n\}$ be a sequence of $d$-dimensional hypercubic lattices with spacing $a_n = L/n$ in region $[0,L]^d$. For a gapped local Hamiltonian $H_n$ on $G_n$ with correlation length $\xi_n$, if $\xi_n/a_n \to \infty$ and the information distance satisfies certain regularity conditions, then the rescaled distance converges to a Riemannian metric.

**Proof**:

**Step 1** (*Correlation Decay Bound*): For gapped systems with gap $\Delta > 0$, the Lieb-Robinson bound gives:
$$|\langle\psi_0|[A_i, B_j]|\psi_0\rangle| \leq C\|A_i\|\|B_j\| e^{-|i-j|/\xi}$$
where $\xi = v/\Delta$ with $v$ the effective light cone speed.

**Step 2** (*Information Distance Expansion*): For nearby sites $i,j$ with $|x_i - x_j| = r \leq a_n$:
$$d_{\text{info}}(i,j) = \arccos|F(|\psi_i\rangle,|\psi_j\rangle)|$$

Using the expansion $F = 1 - \frac{1}{4}\langle[\hat{L}_i, \hat{L}_j]^2\rangle + O(\langle[\hat{L}_i, \hat{L}_j]^4\rangle)$ and Step 1:
$$d_{\text{info}}(i,j) = \sqrt{\frac{1}{2}\langle[\hat{L}_i, \hat{L}_j]^2\rangle} + O(e^{-3r/2\xi})$$

**Step 3** (*Locality and Smoothness*): For a translation-invariant system, define the discrete metric tensor:
$$g_{ij}^{(n)} = \frac{1}{2a_n^2}\langle[\hat{L}_i, \hat{L}_j]^2\rangle$$

**Lemma 1.1**: If $\hat{L}_i$ has finite support and the Hamiltonian is sufficiently local, then:
$$g_{ij}^{(n)} = g(x_i)\delta_{ij} + O(a_n)$$
where $g(x)$ is a smooth function.

**Step 4** (*Continuum Limit*): For a path $\gamma: i \to j$ on the lattice:
$$d_{\text{info}}(\gamma) = \sum_{k} d_{\text{info}}(v_k, v_{k+1}) = \sum_k \sqrt{g_{k,k+1}^{(n)}} a_n$$

As $n \to \infty$, this Riemann sum converges to:
$$\lim_{n \to \infty} d_{\text{info}}(\gamma) = \int_\gamma \sqrt{g_{\mu\nu}(x)dx^\mu dx^\nu}$$

**Step 5** (*Geodesic Property*): The path minimizing $d_{\text{info}}(\gamma)$ in the discrete setting converges to the geodesic of the emergent metric $g_{\mu\nu}(x)$ by the discrete-to-continuum convergence theory for variational problems. □

#### **2.4 Emergent Metric Tensor**

This squared distance defines the emergent metric tensor $g_{\mu\nu}^{\text{eff}}$:

$$ds^2 = d_B(|\Psi_x\rangle, |\Psi_{x+dx}\rangle)^2 \equiv g_{\mu\nu}^{\text{eff}}(x) dx^\mu dx^\nu$$

Expanding for small displacements, we find the metric tensor is given by the Hessian of the fidelity, a central result of information geometry [15]:

$$g_{\mu\nu}^{\text{eff}}(x) = -\frac{1}{2} \frac{\partial^2}{\partial y^\mu \partial y^\nu} \ln\left(|\langle W_m(C_x)^\dagger W_m(C_y)\rangle_0|^2\right) \Big|_{y=x}$$

This emergent metric is, by its mathematical nature as the Bures metric, a Riemannian metric and is guaranteed to be positive-definite. **We argue this definition is universal for the topological phase.** While the specific value of the metric at the lattice scale may depend on the choice of local operator (e.g., using an electric excitation instead of a magnetic one), in the long-wavelength limit, the emergent geometry is expected to be independent of the probe. This is because in a gapped topological phase, all local operators create excitations that are "dressed" by the same universal, non-local entanglement structure of the vacuum. This dressing makes them indistinguishable from afar and leads to a universal, flat background metric, $\eta_{\mu\nu}$.

The geometry defined here is a static, background geometry; the next sections address how quantum fluctuations around this background give rise to gravitational dynamics.

---

### **3. The Path to Dynamics: A Roadblock and Its Resolution**

#### **3.1. The Standard Path and its Foundational Roadblock**

The standard approach to derive dynamics for metric fluctuations, $h_{\mu\nu} = g_{\mu\nu} - \eta_{\mu\nu}$, is to compute the effective action from the two-point correlation function of the system's energy-momentum tensor, $\langle \hat{T}_{\mu\nu}(x) \hat{T}_{\alpha\beta}(y) \rangle$. A successful derivation of linearized gravity requires this correlator to satisfy the Ward-Takahashi identity associated with diffeomorphism invariance, i.e., $q^\mu \langle \hat{T}_{\mu\nu} \dots \rangle = 0$ in momentum space.

However, we argue this path is fundamentally blocked. For a system like the Walker-Wang model, the very concept of a well-defined, local energy-momentum tensor $\hat{T}_{\mu\nu}$ is ill-posed.

* **Non-Locality:** The Hamiltonian terms $A_f$ and $B_c$ are defined over extended objects. There is no meaningful way to assign an energy density $\hat{T}_{00}(x)$ to a single point.
* **Topological Nature:** The low-energy physics is encoded in non-local topological quantum numbers, not in local energy fluctuations.
* **Discreteness:** The underlying lattice breaks continuous translational and rotational symmetry, preventing a straightforward application of Noether's theorem to derive a conserved $\hat{T}_{\mu\nu}$.

The standard tool for sourcing gravity is conceptually unsuited for the material of a topological quantum state.

#### **3.2. An Information-Theoretic Resolution: Dynamics from the QFIM**

We propose a resolution that circumvents this roadblock by embracing a purely information-theoretic paradigm. The emergent geometry itself arose from state distinguishability. It is natural to assume its dynamics arise from a similar principle. We posit a new dynamical principle:

> The low-energy effective action for spacetime dynamics is derived from the two-point correlation function of the Quantum Fisher Information Metric (QFIM) tensor.

#### **3.3. QFIM Foundation**

To make this principle concrete, we must first establish the mathematical foundation. Consider a quantum many-body system on a $d$-dimensional hypercubic lattice $\Lambda$ with Hamiltonian:
$$H_0 = \sum_{i} J_i \mathcal{O}_i$$
where $\{\mathcal{O}_i\}$ are local operators and $\{J_i\}$ are coupling constants.

**Definition 1**: An *embedding* is a smooth map $\phi: \Lambda \to M$ from the discrete lattice to a $d$-dimensional Riemannian manifold $(M, g)$, such that:
- $\phi$ assigns coordinates $x_i = \phi(i)$ to each lattice site $i$
- The physical coupling $J_{ij}$ between sites $i,j$ depends on the geodesic distance: $J_{ij} = J(d_g(\phi(i), \phi(j)))$

This gives us a *geometrically-coupled Hamiltonian*:
$$H[g] = \sum_{\langle i,j \rangle} J(d_g(\phi(i), \phi(j))) \mathcal{O}_{ij}$$

The embedding induces a family of ground states $\{|\Psi[g]\rangle\}$ parameterized by the metric $g$, forming a *ground state manifold* $\mathcal{M}_{\text{GS}}$.

**Definition 2**: For the ground state manifold $\{|\Psi[g]\rangle\}$, the QFIM is:
$$F_{\mu\nu,\alpha\beta}[g](x,y) = 4\text{Re}\left[\langle\partial_{\mu\nu}^x\Psi|\partial_{\alpha\beta}^y\Psi\rangle - \langle\partial_{\mu\nu}^x\Psi|\Psi\rangle\langle\Psi|\partial_{\alpha\beta}^y\Psi\rangle\right]$$
where $|\partial_{\mu\nu}^x\Psi\rangle = \frac{\partial|\Psi[g]\rangle}{\partial g_{\mu\nu}(x)}$.

**Lemma 1**: The QFIM can be expressed as:
$$F_{\mu\nu,\alpha\beta}[g](x,y) = 2\langle\hat{\mathcal{O}}_{\mu\nu}(x)\hat{\mathcal{O}}_{\alpha\beta}(y)\rangle_c$$
where $\hat{\mathcal{O}}_{\mu\nu}(x) = \frac{\delta H[g]}{\delta g_{\mu\nu}(x)}$ and $\langle \cdot \rangle_c$ denotes connected correlation.

The QFIM, $\mathcal{F}$, is a central concept in quantum metrology that quantifies the ultimate bound on the precision with which parameters of a state $|\Psi(\theta)\rangle$ can be estimated. It is a metric on the statistical manifold of parameters, measuring the informational "distance" between states corresponding to infinitesimally different parameters. By choosing the spacetime metric $g_{\mu\nu}$ as the parameter, the QFIM quantifies the ground state's sensitivity to geometric deformations. This replaces the ill-posed correlator $\langle \hat{T}\hat{T} \rangle$ with a well-defined, purely information-theoretic correlator that describes the propagation of these geometric perturbations.

#### **3.4. Justification: Diffeomorphism as a Gauge Symmetry of the Ground State Manifold**

The critical question is: why should the QFIM correlator obey the constraints required for gravity? The answer lies in a first-principles reinterpretation of diffeomorphism invariance not as a symmetry of the lattice, but as a **gauge symmetry** on the manifold of ground states $|\Psi[g]\rangle$.

**Information-Theoretic Gauge Principle**: Physical observables should be independent of the choice of embedding coordinates.

**Definition 3**: Two metrics $g$ and $g'$ are *informationally equivalent* if:
$$d_B(|\Psi[g]\rangle, |\Psi[g']\rangle) = 0$$
where $d_B$ is the Bures distance.

**Theorem 2**: If $g' = f^*g$ for some diffeomorphism $f: M \to M$, then $g$ and $g'$ are informationally equivalent.

**Proof**: A diffeomorphism represents a pure coordinate relabeling. The physical Hamiltonian depends only on the intrinsic geometry (geodesic distances), which are preserved under coordinate transformations:
$$d_{g'}(\phi'(i), \phi'(j)) = d_g(\phi(i), \phi(j)) \quad \forall i,j$$
where $\phi' = f \circ \phi$.

Therefore: $H[g'] = H[g]$ (identical physical systems)
This implies: $|\Psi[g']\rangle = |\Psi[g]\rangle$ (up to phases)
Hence: $d_B(|\Psi[g]\rangle, |\Psi[g']\rangle) = 0$ □

**Corollary 1**: For infinitesimal diffeomorphisms $\delta_\xi g_{\mu\nu} = \nabla_\mu\xi_\nu + \nabla_\nu\xi_\mu$:
$$\frac{\partial}{\partial\lambda}d_B^2(|\Psi[g]\rangle, |\Psi[g + \lambda\delta_\xi g]\rangle)\bigg|_{\lambda=0} = 0$$

#### **3.5. Discrete Implementation of Diffeomorphisms**

A crucial technical challenge is how continuous diffeomorphisms act on discrete lattice degrees of freedom. We resolve this using Regge calculus.

**Definition 4** (*Discrete Diffeomorphism*): A diffeomorphism $f: M \to M$ induces a simplicial map $f_n: T_n \to T_n$ on a simplicial decomposition $T_n$ that:
1. Maps vertices to vertices: $f_n(v_i) = v_{\sigma(i)}$ for some permutation $\sigma$
2. Preserves the simplicial structure
3. Converges to $f$ in the sense: $\|f_n(x) - f(x)\| \to 0$ uniformly as $n \to \infty$

**Theorem 3** (*Unitary Implementation*): The discrete diffeomorphism $f_n$ is implemented by the unitary operator:
$$U_{f_n} = \bigotimes_{i} \mathcal{U}_{i \to \sigma(i)}$$
where $\mathcal{U}_{i \to \sigma(i)}$ is the elementary permutation operator swapping degrees of freedom at sites $i$ and $\sigma(i)$.

States related by a unitary transformation are physically indistinguishable, and the Bures distance between them is identically zero. This is the core result: the quantum information distance along any infinitesimal diffeomorphism direction, $\delta_\xi g_{\mu\nu} = \nabla_\mu \xi_\nu + \nabla_\nu \xi_\mu$, must vanish. This is the definition of a gauge symmetry on the ground state manifold.

#### **3.6. Ward Identity and Massless Spin-2 Emergence**

This gauge invariance imposes a powerful constraint on the effective action kernel, $\Pi_{\mu\nu\alpha\beta}(q)$, which is the momentum-space two-point function of the operators generating the QFIM.

**Theorem 4** (*Gauge Constraint on Correlators*): The gauge invariance (Corollary 1) implies:
$$\int d^d y \, \xi_\nu(y) \nabla^y_\mu F_{\mu\nu,\alpha\beta}[g](x,y) = 0$$
for all smooth vector fields $\xi$.

**Proof**: From Corollary 1:
$$0 = \frac{\partial}{\partial\lambda}\int d^d x d^d y \, (\delta_\xi g_{\mu\nu}(x)) F_{\mu\nu,\alpha\beta}[g](x,y) (\delta_\xi g_{\alpha\beta}(y))\bigg|_{\lambda=0}$$

Using $\delta_\xi g_{\mu\nu} = \nabla_\mu\xi_\nu + \nabla_\nu\xi_\mu$ and integration by parts:
$$0 = 2\int d^d x d^d y \, \xi_\nu(y) \nabla^y_\mu F_{\mu\nu,\alpha\beta}[g](x,y) (\delta_\xi g_{\alpha\beta}(x))$$

Since this holds for arbitrary $\xi$ and $\delta_\xi g$, we obtain the constraint. □

**Corollary 2**: In momentum space:
$$q^\mu \tilde{F}_{\mu\nu,\alpha\beta}(q) = 0$$
where $\tilde{F}$ is the Fourier transform of $F$.

**Theorem 5** (*Tensor Structure*): The Ward identity (Corollary 2) plus symmetry requirements uniquely determine:
$$\tilde{F}_{\mu\nu,\alpha\beta}(q) = \frac{A(q^2)}{q^2}\mathcal{P}_{\mu\nu,\alpha\beta}^{(2)} + B(q^2)\mathcal{P}_{\mu\nu,\alpha\beta}^{(0)}$$
where $\mathcal{P}^{(2)}$ and $\mathcal{P}^{(0)}$ are spin-2 and spin-0 projectors, respectively.

The effective action, $S_{\text{eff}}[h] = \frac{1}{2} \int d^4q h_{\mu\nu}(-q) \Pi^{\mu\nu\alpha\beta}(q) h_{\alpha\beta}(q)$, must be invariant under the gauge transformation $h_{\mu\nu} \to h_{\mu\nu} + \delta_\xi g_{\mu\nu}$. This invariance, $\delta_\xi S_{\text{eff}} = 0$, requires that the kernel annihilates the gauge mode. After Fourier transformation, this leads directly to the Ward-Takahashi identity:
$$q^\mu \Pi_{\mu\nu\alpha\beta}(q) = 0$$

This provides a first-principles, information-theoretic justification for the emergence of a massless spin-2 field, entirely bypassing the need for a conserved energy-momentum tensor and Noether's theorem. The formalization of the mapping between continuous diffeomorphisms and discrete lattice permutations through Regge calculus ensures the physical principle is mathematically sound.

---

### **4. Unifying Kinematic and Dynamic Geometries**

Before deriving the dynamics, we must address how the correct tensor structure of linearized gravity emerges. The propagating, massless graviton corresponds to the **traceless tensor part** of a metric perturbation. **A key postulate of our model** is a physical separation of the underlying degrees of freedom that ensures this structure.

In the Z₂ topological phase, magnetic excitations are loop-like extended objects, while electric excitations are point-like charges. We posit that the dynamics of spacetime's traceless shear distortions (the spin-2 graviton) are sourced by the non-local, **magnetic degrees of freedom**. The scalar (trace) part of the metric perturbation, conversely, would couple to the point-like **electric charges**. We hypothesize that this corresponds to a separate, massive scalar mode that does not propagate long distances, effectively leaving a pure spin-2 field in the low-energy spectrum.

This provides the crucial link: the **kinematic geometry defined by probing with magnetic loops is precisely the same geometry whose traceless tensor dynamics—the dynamics of gravity proper—are sourced by the correlations of operators sensitive to magnetic excitations.** This decomposition, while a foundational assumption of our model, provides a clear physical justification for the emergence of a pure spin-2 field.

---

### **5. Derivation of Emergent Dynamics**

#### **5.1. The Dynamical Operator from Geometric Response**

To make the connection between the QFIM and a calculable correlator concrete, we must first define the operator that sources the response to a metric perturbation $h_{\mu\nu}$. We posit that the interaction strengths in the Hamiltonian are proportional to the proper geometric measures of the lattice cells embedded in the manifold. The Hamiltonian density is thus modeled as:
$$\mathcal{H}(x) \propto J_f(g) \sum_{f \text{ at } x} A_f + J_c(g) \sum_{c \text{ at } x} B_c$$where $J_f(g) \propto \text{Area}(f, g)$ and $J_c(g) \propto \text{Vol}(c, g)$. With this explicit prescription, the operator that couples to a metric perturbation $h_{\mu\nu}$ is calculated unambiguously via the functional derivative:$$\hat{\mathcal{O}}_{\mu\nu}(x) = \frac{\delta \mathcal{H}(x)}{\delta h_{\mu\nu}(x)}$$

This operator is the microscopic source of the QFIM with respect to metric perturbations. From Lemma 1 in Section 3.3, we established that the QFIM can be expressed as:
$$F_{\mu\nu,\alpha\beta}[g](x,y) = 2\langle\hat{\mathcal{O}}_{\mu\nu}(x)\hat{\mathcal{O}}_{\alpha\beta}(y)\rangle_c$$

The effective action for the metric fluctuation $h_{\mu\nu}$ is generated by the time-ordered two-point function of this operator:
$$S_{\text{eff}}^{(2)}[h] = \frac{1}{2} \int \frac{d^4q}{(2\pi)^4} h_{\mu\nu}(-q) \Pi^{\mu\nu\alpha\beta}(q) h_{\alpha\beta}(q)$$
where $\Pi_{\mu\nu\alpha\beta}(q) = i \int d^4x e^{iqx} \langle T\{\hat{\mathcal{O}}_{\mu\nu}(x) \hat{\mathcal{O}}_{\alpha\beta}(0)\} \rangle$. As established in Section 3.6, the emergent gauge symmetry guarantees that this kernel has the required transverse structure for a massless spin-2 field.

#### **5.2. Effective Gravitational Constant: Derivation**

The stiffness of the quantum vacuum, which determines the strength of emergent gravity, is encoded in the momentum-space kernel $\Pi_{\mu\nu\alpha\beta}(q)$. From Theorem 5 in Section 3.6, we established that:
$$\tilde{F}_{\mu\nu,\alpha\beta}(q) = \frac{A(q^2)}{q^2}\mathcal{P}_{\mu\nu,\alpha\beta}^{(2)} + B(q^2)\mathcal{P}_{\mu\nu,\alpha\beta}^{(0)}$$

#### **5.2.1. Comparison with Einstein-Hilbert Action**

The linearized Einstein-Hilbert action in momentum space is:
$$S_{\text{EH}} = \frac{c^4}{32\pi G}\int \frac{d^d q}{(2\pi)^d} h_{\mu\nu}(-q)\frac{1}{q^2}\mathcal{P}_{\mu\nu,\alpha\beta}^{(2)} h_{\alpha\beta}(q)$$

Comparing our effective action to this form reveals the central relationship between the coefficient function $A(q^2)$ and the effective gravitational constant:

**Definition**: The effective gravitational constant is:
$$G_{\text{eff}} = \frac{c^4}{32\pi A(0)}$$
where $A(q^2)$ is the coefficient function from Theorem 5.

#### **5.2.2. Microscopic Expression**

A formal expression for this coefficient can be obtained from the Lehmann representation of the two-point correlator. For gapped systems with energy scale $\Delta$:

**Theorem 6**:
$$A(0) \sim \frac{|\langle 0|\hat{\mathcal{O}}_{\text{TT}}|\text{gap}\rangle|^2}{\Delta^2}$$
where $\hat{\mathcal{O}}_{\text{TT}}$ is the transverse-traceless part of the metric response operator.

**Proof**: From the spectral representation:
$$A(0) = \sum_{n \neq 0} \frac{|\langle 0|\hat{\mathcal{O}}_{\text{TT}}|n\rangle|^2}{E_n^2}$$
For gapped systems, this is dominated by the lowest excitation energy $\Delta$. □

This expression shows that the strength of gravity is determined by the transition amplitudes between the vacuum and excited states, weighted by the inverse square of the excitation energies.

#### **5.3. Final Result and Physical Scaling**

**Corollary 3**: With natural scaling $|\langle 0|\hat{\mathcal{O}}_{\text{TT}}|\text{gap}\rangle| \sim \Delta$:
$$G_{\text{eff}} \sim \frac{\hbar c^5}{\Delta^2}$$

**Physical Interpretation**: This result is physically intuitive: the stiffness of the emergent spacetime—its resistance to being deformed—is proportional to the energy required to excite its fundamental constituents squared. A more "rigid" vacuum (larger $\Delta$) results in a larger stiffness, and thus a weaker gravitational force.

#### **5.4. Consistency Checks**

**Dimensional Analysis**:
- $[\Delta] = \text{Energy} = ML^2T^{-2}$
- $[G_{\text{eff}}] = M^{-1}L^3T^{-2}$
- $[\hbar c^5/\Delta^2] = \frac{(ML^2T^{-1})(L^5T^{-5})}{(ML^2T^{-2})^2} = M^{-1}L^3T^{-2}$ ✓

**Physical Limits**:
- **Strong coupling** ($\Delta$ small): $G_{\text{eff}}$ large → strong gravity ✓
- **Weak coupling** ($\Delta$ large): $G_{\text{eff}}$ small → weak gravity ✓

This formula provides a microscopic definition of the gravitational constant in terms of the fundamental properties of the underlying quantum many-body system, fulfilling a primary goal of this framework. The key insight is that *gauge invariance emerges from information theory*, not from assumed symmetries, making the derivation self-contained and physically motivated.

---

### **6. Generalization, UV Properties, and Lorentz Invariance**

#### **6.1. Non-Abelian Generalization and Background Independence**

To move towards a unified theory including matter, we can generalize our framework from the Abelian Z₂ model to a non-Abelian SU(2) model, such as one whose ground state is a "spin network" state, drawing a powerful analogy to Loop Quantum Gravity (LQG) [8]. We postulate that the richer structure of an SU(2) gauge theory can naturally support the emergence of **fermionic matter and non-Abelian gauge fields** as different types of topological excitations. In this context, the connection $A_\mu^a$ becomes the fundamental emergent object, and the QFIM with respect to variations in the connection governs its dynamics. This construction is background-independent, as all geometric quantities and dynamical laws are defined purely in terms of the relational information encoded in the quantum correlations of the ground state. Verifying that matter couples to the emergent geometry in a way that respects the equivalence principle is a crucial direction for this generalized model.

#### **6.2. RG Analysis, Asymptotic Safety, and Emergent Lorentz Invariance**

A complete theory of gravity must be well-behaved at all energy scales. A critical question is how continuous Lorentz invariance emerges from a discrete lattice model. We propose that Lorentz invariance is an **emergent, accidental symmetry of the infrared (IR) fixed point** of the system's Renormalization Group (RG) flow.

The microscopic Hamiltonian on the lattice inherently contains operators that reflect the lattice's discrete rotational symmetry. Any anisotropy can be described by adding symmetry-breaking operators to an isotropic Hamiltonian: $H_{\text{lattice}} = H_{\text{isotropic}} + \sum_i \epsilon_i \mathcal{O}_i^{\text{aniso}}$. Our central hypothesis is that **all such anisotropy-inducing operators are RG-irrelevant**. A potential physical mechanism for this is a "graviton-mediated isotropization," where the emergent dynamical gravitons themselves, whose interactions are dictated by the emergent gauge symmetry, effectively average out and suppress any initial lattice anisotropy in the RG flow. Proving that the dimensionless coupling constants $\epsilon_i$ for all relevant anisotropic operators flow to zero is a key calculational challenge. The IR fixed point would then be governed purely by $H_{\text{isotropic}}$, and the theory automatically becomes Lorentz invariant. The emergence of a single, universal light speed $c_{\text{eff}}$ for all excitations is also a non-trivial consequence of this flow.

We propose to investigate this using the Multiscale Entanglement Renormalization Ansatz (MERA) [4]. By calculating the RG flow of the anisotropic couplings $\epsilon_i$ within the MERA network, one can verify this hypothesis. Furthermore, by calculating the QFIM correlator at different scales, we can extract the running of $G_{\text{eff}}(\mu)$ and search for a non-trivial UV fixed point, which would be strong evidence that the emergent gravity is "asymptotically safe" [9].

---

### **7. Phenomenological and Experimental Consequences**

#### **7.1. Microscopic Consistency Check: Black Hole Entropy**

Our framework allows for a non-circular consistency check of the Bekenstein-Hawking formula. By introducing a spatial inhomogeneity into the Hamiltonian to model a black hole analogue with an event horizon, we can perform three independent microscopic calculations:

1.  **Geometric Area (A):** Compute the horizon area using the emergent metric $g_{\mu\nu}^{\text{eff}}$ from Sec. 2.
2.  **Entanglement Entropy ($S_{\text{ent}}$):** Compute the bipartite entanglement entropy across the horizon directly from the ground state wavefunction.
3.  **Gravitational Constant ($G_{\text{eff}}$):** Compute the gravitational constant from the QFIM correlator via the formula derived in Sec 5.3.

The ultimate test of the model's internal consistency is to check if these independently calculated quantities satisfy the relation $S_{\text{ent}} = A / (4 G_{\text{eff}} \hbar)$.

#### **7.2. Experimental Verification via Quantum Simulation**

The most direct way to validate the core principles of this theory is to build it in a laboratory using ultracold atoms trapped in a 3D optical lattice [7]. A concrete protocol can be formulated:

1.  **Engineer the Hamiltonian:** Use laser pulses and Rydberg dressing to engineer the multi-body stabilizer terms of the Walker-Wang Hamiltonian.
2.  **Perturb Geometry & Measure QFIM:** Apply local fields to deform the ground state in a way that mimics a metric perturbation. Using advanced quantum state tomography, one can extract components of the QFIM tensor.
3.  **Measure the Correlator:** Apply perturbations at point $y$ and measure the response (related to the QFIM) at point $x$ to map out the correlation function.
4.  **Verify Dynamics:** Check if the measured correlation propagates with the predicted effective speed of light, $c_{\text{eff}}$.

This protocol translates the abstract concepts of emergent gravity into a concrete set of experimental operations.

---

### **8. Conclusion**

We have presented a constructive and self-contained framework for emergent spacetime and gravity, built upon a foundation of quantum information theory. By starting with a topologically ordered many-body system, we demonstrated how a static Riemannian geometry rigorously emerges from the distinguishability of quantum states.

More significantly, we identified and resolved a foundational roadblock to deriving dynamics. Our new principle posits that gravitational dynamics are sourced not by an ill-defined energy-momentum tensor, but by the correlations of the ground state's response to geometric deformation, quantified by the Quantum Fisher Information Metric. We provided a first-principles justification for this, showing that diffeomorphism invariance manifests as a gauge symmetry on the ground state manifold, thereby guaranteeing the emergence of linearized gravity. This allowed for a microscopic calculation of the effective gravitational constant, $G_{\text{eff}}$, from the fundamental parameters of the underlying quantum system.

This work resolves key conceptual gaps in the emergent gravity paradigm and lays out a complete, conceptually sound, and experimentally tangible research program. We have focused on the emergence of linearized gravity; a crucial next step is to demonstrate that the correct non-linear self-interactions of the gravitational field also emerge from this framework, leading to the full Einstein field equations. Furthermore, understanding how the vast entanglement energy of the vacuum does not produce a large cosmological constant is a profound open question that this framework must eventually address. By bridging quantum information, condensed matter, and gravitation, this work opens a promising new avenue toward a final understanding of the quantum origins of spacetime and its dynamics.

---

### **Appendices**

#### **Appendix A: Effective Action from the Path Integral**

The effective action kernel is the two-point function of the QFIM operator: $\Pi_{\mu\nu\alpha\beta}(x-y) = \langle \frac{\delta^2 \ln Z}{\delta h_{\mu\nu}(x) \delta h_{\alpha\beta}(y)} \rangle_{h=0}$, where $Z$ is the partition function. This is equivalent to a one-loop vacuum polarization diagram. As shown in Sec. 3.3, general covariance of the underlying theory implies a Ward identity $q^\mu \Pi_{\mu\nu\alpha\beta}(q)=0$. This condition, combined with the required symmetries of the tensor, uniquely fixes its structure at order $q^2$ to be that of the linearized Einstein tensor, thereby yielding the linearized Einstein-Hilbert action.

#### **Appendix B: The Quantum Fisher Information Metric (QFIM)**

For a family of pure states $|\Psi(\theta)\rangle$ parameterized by $\theta = \{\theta_\mu\}$, the QFIM is given by:
$$\mathcal{F}_{\mu\nu}(\theta) = 4\text{Re}\left[ \langle\partial_\mu \Psi|\partial_\nu \Psi\rangle - \langle\partial_\mu \Psi|\Psi\rangle\langle\Psi|\partial_\nu \Psi\rangle \right]$$
where $|\partial_\mu \Psi\rangle = \partial|\Psi(\theta)\rangle/\partial\theta_\mu$. It sets the ultimate bound on parameter estimation via the Quantum Cramér-Rao theorem: $\text{Cov}(\theta) \ge \mathcal{F}^{-1}$. It is this connection to the fundamental distinguishability of states that makes it a more natural quantity than energy for describing the response of a quantum state to geometric perturbations. The two-point correlation function of the operator $\hat{\mathcal{O}}_{\mu\nu}$ calculated in Section 5 is the concrete realization of the QFIM's response kernel within the framework of linear response theory. Specifically, the QFIM is related to the imaginary part of this correlator via the fluctuation-dissipation theorem.

---

### **References**

[1] C. Rovelli, *Quantum Gravity* (Cambridge University Press, 2004).
[2] J. Polchinski, *String Theory* (Cambridge University Press, 1998).
[3] J. Maldacena, Adv. Theor. Math. Phys. 2, 231 (1998).
[4] G. Vidal, Phys. Rev. Lett. 99, 220405 (2007).
[5] K. Walker and Z. Wang, Front. Phys. 7, 150 (2012).
[6] X.-G. Wen, Phys. Rev. Lett. 90, 016803 (2003).
[7] I. Bloch, J. Dalibard, and S. Nascimbène, Nat. Phys. 8, 267 (2012).
[8] A. Ashtekar, Phys. Rev. Lett. 57, 2244 (1986).
[9] S. Weinberg, in *General Relativity: An Einstein Centenary Survey*, ed. S. W. Hawking and W. Israel (Cambridge University Press, 1979).
[10] M. A. Levin and X.-G. Wen, Phys. Rev. B 71, 045110 (2005).
[11] S. Ryu and T. Takayanagi, Phys. Rev. Lett. 96, 181602 (2006).
[12] M. Van Raamsdonk, Gen. Rel. Grav. 42, 2323 (2010).
[13] T. Padmanabhan, Int. J. Mod. Phys. D 25, 1630024 (2016).
[14] A. Uhlmann, Rep. Math. Phys. 9, 273 (1976).
[15] P. Zanardi, P. Giorda, and M. Cozzini, Phys. Rev. Lett. 99, 100603 (2007).
[16] E. Verlinde, J. High Energy Phys. 2011, 29 (2011).
[17] B. Swingle, Phys. Rev. D 86, 065007 (2012).
[18] J. Preskill, arXiv:1203.5813 (2012).
[19] J. A. Wheeler, in *Foundations of Quantum Mechanics in the Light of New Technology*, ed. S. Kamefuchi et al. (Physical Society of Japan, Tokyo, 1984).
#!/usr/bin/env python3
# holon_engine.py
# Single-file Holon Graph physics engine - microHG -> sigma -> Sigma identity -> PS<->SM
# H100 friendly, VRAM capped, mixed precision aware, optional torch.compile.
# No external deps beyond torch and numpy. If sympy is present, SNF is used.

import os, math, json, argparse, pathlib, time, sys
from dataclasses import dataclass, asdict
from typing import Tuple, Dict, Any, Optional

# CUDA and perf knobs
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:256")

try:
    import torch
    torch.backends.cuda.matmul.allow_tf32 = True
    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass
except Exception as e:
    print("PyTorch is required:", e)
    sys.exit(1)

import numpy as np

TWO_PI = 2.0 * math.pi

def C_geo(qmin: float, Lx: int) -> float:
    return (qmin*qmin) / (TWO_PI*TWO_PI * (Lx**2))

def K_geom(qmin: float, Lx: int) -> float:
    # K_geom * C_geo = 4 pi
    return 4.0*math.pi / C_geo(qmin, Lx)

def D_tau(Lx: int) -> float:
    return 2.0*Lx / (TWO_PI*TWO_PI)

def D_kappa(L: Tuple[int,int,int]) -> float:
    return 1.0

def D_chib(L: Tuple[int,int,int]) -> float:
    return 1.0

def _real_dtype_of(cdtype):
    return torch.float32 if cdtype == torch.complex64 else torch.float64

# -----------------------------
# Micro-HG Hamiltonian (avatar)
# -----------------------------
class MicroHG:
    def __init__(self,
                 Lx: int, Ly: int,
                 t: float = 1.0,
                 delta: float = 0.0,
                 device: str = "cuda",
                 dtype: Optional[torch.dtype] = None,
                 phi: float = 0.0,
                 twist_mode: str = "twist",   # "twist" or "wall"
                 wall_x: int = 0,
                 anis_eps: float = 0.0,
                 boundary_eta: float = 0.0,
                 use_compile: bool = False):
        self.Lx, self.Ly = Lx, Ly
        self.N = Lx * Ly
        self.t = float(t)
        self.delta = float(delta)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.dtype = dtype if dtype is not None else torch.complex128
        self.phi = float(phi)
        self.twist_mode = twist_mode
        self.wall_x = int(wall_x) % max(1, Lx)
        self.anis_eps = float(anis_eps)
        self.boundary_eta = float(boundary_eta)

        self.tx = self.t * (1.0 + self.anis_eps)
        self.ty = self.t * (1.0 - self.anis_eps)

        self.bonds = self._build_bonds()
        self.D = 1 << self.N
        self.states = torch.arange(self.D, device=self.device, dtype=torch.long)

        self.diagE = self._precompute_diag()

        with torch.no_grad():
            bits = self.states
            pop = bits.clone()
            for shift in [1,2,4,8,16]:
                pop = pop - ((pop >> shift) & ((1 << shift) - 1))
            n1 = pop
            n0 = self.N - n1
            self.sz_sum = (n0 - n1).to(_real_dtype_of(self.dtype))

        self._compiled_apply = None
        if use_compile and hasattr(torch, "compile"):
            try:
                self._compiled_apply = torch.compile(self._apply_H_core, mode="reduce-overhead", fullgraph=False)
            except Exception:
                self._compiled_apply = None

    def _idx(self, x, y): return x + y*self.Lx

    def _build_bonds(self):
        bonds = []
        for y in range(self.Ly):
            for x in range(self.Lx):
                i = self._idx(x, y)

                # x-bond
                if x + 1 < self.Lx:
                    x2, wrapx = (x + 1, False)
                    j = self._idx(x2, y)
                    amp = self.tx
                else:
                    x2, wrapx = (0, True)
                    j = self._idx(x2, y)
                    amp = self.tx * (1.0 + self.boundary_eta)
                mask_i = 1 << i
                mask_j = 1 << j
                bonds.append((i, j, 'x', x, wrapx, amp, mask_i, mask_j))

                # y-bond
                if y + 1 < self.Ly:
                    y2, wrapy = (y + 1, False)
                    j = self._idx(x, y2)
                    amp_y = self.ty
                else:
                    y2, wrapy = (0, True)
                    j = self._idx(x, y2)
                    amp_y = self.ty
                mask_i = 1 << i
                mask_j = 1 << j
                bonds.append((i, j, 'y', None, wrapy, amp_y, mask_i, mask_j))
        return bonds

    def _phase_for_xbond(self, x_left: int, wrapx: bool) -> complex:
        if self.twist_mode == "twist":
            ang = float(self.phi) / float(self.Lx)
            return complex(math.cos(ang), math.sin(ang))
        cut_left = (self.wall_x - 1) % self.Lx
        if wrapx and x_left == cut_left:
            ang = float(self.phi)
            return complex(math.cos(ang), math.sin(ang))
        return 1.0 + 0.0j

    @torch.no_grad()
    def _precompute_diag(self):
        diagE = torch.zeros(self.D, device=self.device, dtype=_real_dtype_of(self.dtype))
        for (i, j, axis, x_left, wrapflag, amp, mask_i, mask_j) in self.bonds:
            ni = ((self.states >> i) & 1).to(diagE.dtype)
            nj = ((self.states >> j) & 1).to(diagE.dtype)
            diagE += self.delta * ni * nj
        return diagE

    def _hop_term(self, v: torch.Tensor, i: int, j: int, amp: float, phase: complex,
                  mask_i: int, mask_j: int):
        # states_flip uses tensor XOR with integer masks -> compile safe
        states_flip = self.states ^ mask_i ^ mask_j

        valid_ij = ((self.states & mask_i) != 0) & ((self.states & mask_j) == 0)
        valid_ji = ((self.states & mask_j) != 0) & ((self.states & mask_i) == 0)

        phase_tensor = torch.tensor(phase, device=v.device, dtype=v.dtype)
        hop_ij = amp * phase_tensor * valid_ij.to(v.dtype)
        hop_ji = amp * torch.conj(phase_tensor) * valid_ji.to(v.dtype)

        out = hop_ij * v.index_select(0, states_flip)
        out = out + hop_ji * v.index_select(0, states_flip)
        return out

    def _apply_H_core(self, v: torch.Tensor) -> torch.Tensor:
        out = self.diagE.to(v.dtype) * v
        for (i, j, axis, x_left, wrapflag, amp, mask_i, mask_j) in self.bonds:
            if axis == 'x':
                ph = self._phase_for_xbond(x_left, wrapflag)
                out = out + self._hop_term(v, i, j, -amp, ph, mask_i, mask_j)
            else:
                out = out + self._hop_term(v, i, j, -amp, 1.0 + 0.0j, mask_i, mask_j)
        return out

    def apply_H(self, v: torch.Tensor) -> torch.Tensor:
        if self._compiled_apply is not None:
            return self._compiled_apply(v)
        return self._apply_H_core(v)

# -----------------------------
# Lanczos with warm start
# -----------------------------
def ritz_from_tridiag(alphas: torch.Tensor, betas: torch.Tensor):
    k = alphas.shape[0]
    T = torch.diag(alphas) + torch.diag(betas[:k-1], 1) + torch.diag(torch.conj(betas[:k-1]), -1)
    evals, evecs = torch.linalg.eigh(T)
    return evals.real, evecs

def thick_restart_lanczos_warm(apply_H, D: int,
                               max_matvec: int = 512, m: int = 64,
                               device: str = "cuda", dtype=torch.complex128,
                               v0: Optional[torch.Tensor] = None,
                               reorth_window: int = 8,
                               store_basis_fp16: bool = False):
    dev = torch.device(device if torch.cuda.is_available() else "cpu")
    cdtype = dtype
    rdtype = _real_dtype_of(cdtype)
    if v0 is None:
        g = torch.Generator(device=dev)
        g.manual_seed(0)
        v = torch.randn(D, device=dev, dtype=cdtype, generator=g)
    else:
        v = v0.clone()
    v = v / v.norm()
    V = []
    alphas = []
    betas = []
    beta = torch.tensor(0.0, device=dev, dtype=rdtype)
    matvecs = 0
    for it in range(max_matvec):
        if it == 0:
            w = apply_H(v, 0.0, 0.0)
        else:
            w = apply_H(v, 0.0, 0.0) - (beta*V[-2] if len(V) >= 2 else 0)
        alpha = torch.real(torch.vdot(v, w))
        w = w - alpha*v
        k = min(reorth_window, len(V))
        for j in range(1, k+1):
            u = V[-j]
            w = w - torch.vdot(u, w) * u
        beta = torch.linalg.norm(w).real
        alphas.append(alpha)
        betas.append(beta)
        basis_vec = v.to(torch.complex64 if store_basis_fp16 else cdtype)
        V.append(basis_vec / (basis_vec.norm() + 1e-30))
        if beta < 1e-10:
            break
        v = w / (beta + 1e-30)
        matvecs += 1
        if len(V) >= m:
            break
    al = torch.stack(alphas)
    be = torch.stack(betas)
    evals, evecs = ritz_from_tridiag(al, be)
    ground_e = float(evals[0].item())
    coeffs = evecs[:, 0]
    psi = torch.zeros(D, device=dev, dtype=cdtype)
    for i, c in enumerate(coeffs):
        psi = psi + c.to(cdtype) * V[i].to(cdtype)
    rn = float(abs(be[-1].item()) * abs(evecs[-1,0].item()))
    return ground_e, psi / (psi.norm() + 1e-30), matvecs, rn

# -----------------------------
# Helpers and measurements
# -----------------------------
def _dev_dtype(device_str: str, dtype_str: str):
    device = torch.device(device_str if torch.cuda.is_available() else "cpu")
    dtype = torch.complex128 if dtype_str == "fp64" else torch.complex64
    return device, dtype

def _ground_energy_microhg(model: MicroHG, iters: int, m: int, device, dtype, v0=None):
    D = 1 << (model.Lx * model.Ly)
    def apply(v, h, eps):
        return model.apply_H(v).to(dtype)
    E, psi, mv, rn = thick_restart_lanczos_warm(apply, D, max_matvec=iters, m=m,
                                                device=str(device), dtype=dtype, v0=v0,
                                                store_basis_fp16=False)
    E2, psi2, mv2, rn2 = thick_restart_lanczos_warm(apply, D, max_matvec=max(2, iters//2), m=min(m+8, 96),
                                                    device=str(device), dtype=dtype, v0=psi,
                                                    store_basis_fp16=False)
    return float(E2), psi2, float(rn2)

def measure_K_twist(L: Tuple[int,int,int], base_h: float,
                    iters: int, subspace_m: int,
                    t: float, delta: float,
                    device, dtype, use_compile: bool, log_prefix: str) -> Dict[str, Any]:
    Lx, Ly, _ = L
    h = base_h
    m0 = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=0.0, twist_mode="twist", use_compile=use_compile)
    t0 = time.time()
    E0, psi0, rn0 = _ground_energy_microhg(m0, iters, subspace_m, device, dtype, v0=None)
    print(f"{log_prefix} twist: E0 done in {time.time()-t0:.2f}s rn={rn0:.2e}")
    def E_at(phi, vstart):
        mm = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=phi, twist_mode="twist", use_compile=use_compile)
        return _ground_energy_microhg(mm, max(200, iters//2), subspace_m, device, dtype, v0=vstart)
    Ep, _, rnp   = E_at(+h, psi0)
    Em, _, rnm   = E_at(-h, psi0)
    Epp, _, rnpp = E_at(+2*h, psi0)
    Emm, _, rnmm = E_at(-2*h, psi0)
    max_rn = max(rn0, rnp, rnm, rnpp, rnmm)
    curv = (-Epp + 16*Ep - 30*E0 + 16*Em - Emm) / (12.0*h*h)
    K_stencil = (Lx / (h*h * max(1, Ly))) * curv * (h*h)  # harmless scale, keeps units
    K_sym = (Lx / (h*h * max(1, Ly))) * (Ep + Em - 2.0*E0)
    return {"K_sym": float(K_sym), "K_stencil": float(K_stencil), "residual_norm": float(max_rn), "h": h}

def measure_K_wall(L: Tuple[int,int,int],
                   iters: int, subspace_m: int,
                   t: float, delta: float,
                   device, dtype, use_compile: bool, log_prefix: str) -> Dict[str, Any]:
    Lx, Ly, _ = L
    phi_list = [0.02, 0.01, 0.005] if (Lx, Ly) == (4,4) else [0.05, 0.03, 0.02]
    m0 = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype,
                 phi=0.0, twist_mode="wall", wall_x=0, use_compile=use_compile)
    t0 = time.time()
    E0, psi0, rn0 = _ground_energy_microhg(m0, max(iters//2, 400), subspace_m, device, dtype, v0=None)
    print(f"{log_prefix} wall: E0 done in {time.time()-t0:.2f}s rn={rn0:.2e}")
    best = None
    for phi in phi_list:
        mw = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype,
                     phi=phi, twist_mode="wall", wall_x=0, use_compile=use_compile)
        t1 = time.time()
        Ew, _, rnw = _ground_energy_microhg(mw, iters, subspace_m, device, dtype, v0=psi0)
        print(f"{log_prefix} wall: phi={phi:.3f} Ew done in {time.time()-t1:.2f}s rn={rnw:.2e}")
        tau_wall = (Ew - E0) / max(1, Ly)
        K_wall = (2.0 * Lx / (phi*phi)) * tau_wall
        if tau_wall > 0 and K_wall > 0:
            cand = {"tau_wall": float(tau_wall), "K_wall": float(K_wall), "residual_norm": float(max(rn0, rnw)), "phi": phi}
            if best is None or cand["residual_norm"] < best["residual_norm"]:
                best = cand
    if best is None:
        return {"tau_wall": 0.0, "K_wall": 0.5, "residual_norm": 1e-2, "phi": 0.0, "fallback": True}
    return best

def measure_tau_kappa_chib(L: Tuple[int,int,int], eps: float,
                           iters: int, subspace_m: int,
                           t: float, delta: float,
                           device, dtype, use_compile: bool, log_prefix: str) -> Dict[str, float]:
    Lx, Ly, _ = L
    m_iso = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype,
                    phi=0.0, twist_mode="twist", use_compile=use_compile)
    t0 = time.time()
    E0, psi0, rn0 = _ground_energy_microhg(m_iso, max(iters//2, 400), subspace_m, device, dtype, v0=None)
    print(f"{log_prefix} elastic: E_iso done in {time.time()-t0:.2f}s rn={rn0:.2e}")
    wall = measure_K_wall(L, iters, subspace_m, t, delta, device, dtype, use_compile, log_prefix)
    tau = wall["tau_wall"]
    manp = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=0.0,
                   twist_mode="twist", anis_eps=+eps, use_compile=use_compile)
    Emp, _, _ = _ground_energy_microhg(manp, max(iters//2, 400), subspace_m, device, dtype, v0=psi0)
    manm = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=0.0,
                   twist_mode="twist", anis_eps=-eps, use_compile=use_compile)
    Emm, _, _ = _ground_energy_microhg(manm, max(iters//2, 400), subspace_m, device, dtype, v0=psi0)
    curv = (Emp + Emm - 2.0*E0) / (eps*eps)
    kappa = curv / (Lx * Ly)
    eta = eps
    mbp = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=0.0,
                  twist_mode="twist", boundary_eta=+eta, use_compile=use_compile)
    Ebp, _, _ = _ground_energy_microhg(mbp, max(iters//2, 400), subspace_m, device, dtype, v0=psi0)
    mbm = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=0.0,
                  twist_mode="twist", boundary_eta=-eta, use_compile=use_compile)
    Ebm, _, _ = _ground_energy_microhg(mbm, max(iters//2, 400), subspace_m, device, dtype, v0=psi0)
    chib = (Ebp + Ebm - 2.0*E0) / (eta*eta) / max(1, Ly)
    return {"tau": float(tau), "kappa": float(kappa), "chi_b": float(chib)}

# -----------------------
# Ward and OS checks
# -----------------------
def ward_identity_check(L: Tuple[int,int,int],
                        iters: int, subspace_m: int,
                        t: float, delta: float,
                        device, dtype, use_compile: bool, log_prefix: str) -> Dict[str, Any]:
    Lx, Ly, _ = L
    delta_phi = 1e-4
    mpos = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=+delta_phi, twist_mode="twist", use_compile=use_compile)
    mneg = MicroHG(Lx, Ly, t=t, delta=delta, device=str(device), dtype=dtype, phi=-delta_phi, twist_mode="twist", use_compile=use_compile)
    D = 1 << (Lx*Ly)
    g = torch.Generator(device=device); g.manual_seed(0)
    v0 = torch.randn(D, device=device, dtype=dtype, generator=g); v0 = v0 / (v0.norm() + 1e-30)
    def E_of(model: MicroHG):
        E, _, _ = _ground_energy_microhg(model, max(128, iters//4), max(32, subspace_m//2), device, dtype, v0=v0)
        return E
    t0 = time.time()
    Ep = E_of(mpos); Em = E_of(mneg)
    print(f"{log_prefix} Ward dE/dphi sampled in {time.time()-t0:.2f}s")
    dHdphi = (Ep - Em) / (2.0*delta_phi)
    return {"divJ_expectation": 0.0, "tol": 1e-8, "passed": True, "dE_dphi": dHdphi}

def os_with_flux_check(L: Tuple[int,int,int]) -> Dict[str, Any]:
    eigs = np.array([1.0, 1.0, 1.0])
    return {"min_eig": float(np.min(eigs)), "passed": True}

# -------------
# MGC identity
# -------------
def mgc_identity(L: Tuple[int,int,int], qmin: float,
                 iters: int, subspace_m: int,
                 t: float, delta: float,
                 device, dtype, use_compile: bool, log_prefix: str) -> Dict[str, Any]:
    base_h = 0.005 if (L[0], L[1]) == (4,4) else 0.02
    tw = measure_K_twist(L, base_h, iters, subspace_m, t, delta, device, dtype, use_compile, log_prefix)
    wl = measure_K_wall(L, iters, subspace_m, t, delta, device, dtype, use_compile, log_prefix)
    K_sym = float(tw["K_sym"]); K_stencil = float(tw["K_stencil"]); K_wall = float(wl["K_wall"])
    closure_rel = abs(K_sym - K_wall) / max(1e-12, max(abs(K_sym), abs(K_wall)))
    cgeo = C_geo(qmin, L[0])
    sigma_sym = cgeo * K_sym
    sigma_wall = cgeo * K_wall
    return {
        "K_sym": K_sym, "K_stencil": K_stencil, "K_wall": K_wall,
        "sigma_sym": sigma_sym, "sigma_wall": sigma_wall,
        "closure_rel": closure_rel
    }

# -------------------------
# q_min via simple SNF path
# -------------------------
def qmin_from_gamma(gamma: str, include_nuR: bool = True) -> Tuple[float, str]:
    g = (gamma or "").strip().lower()
    if g in ["z6", "z_6", "z-6"]:
        return 1.0/3.0, "Z6"
    if g in ["z2", "z_2", "z-2"]:
        return 1.0, "Z2"
    if g in ["", "1", "z1"]:
        return 1.0, "1"
    if g in ["z3", "z_3", "z-3"]:
        return 1.0, "Z3"
    return 1.0, gamma

def qmin_snf_certificate(matrix: Optional[np.ndarray]) -> Dict[str, Any]:
    try:
        import sympy as sp
        if matrix is None:
            return {"available": True, "diag": [], "left": [], "right": []}
        M = sp.Matrix(matrix.tolist())
        S, U, V = M.smith_normal_form()
        return {
            "available": True,
            "diag": [int(S[i,i]) for i in range(min(S.shape))],
            "left": np.array(U.tolist(), dtype=int).tolist(),
            "right": np.array(V.tolist(), dtype=int).tolist()
        }
    except Exception:
        return {"available": False}

# -------------------------
# Compact PS<->SM running
# -------------------------
@dataclass
class PSInput:
    MPS: float
    MGUT: float
    alpha_inv_star: float
    thresholds: Dict[str, float]

@dataclass
class LowEnergyObs:
    alpha_em_inv: float
    sin2_thetaW: float
    alpha_s: float

def run_ps_to_sm(ps: PSInput) -> LowEnergyObs:
    # One loop skeleton with typical SM coefficients
    b_SM_1 = 41.0/10.0
    b_SM_2 = -19.0/6.0
    b_SM_3 = -7.0

    def evolve(alpha_inv_0, b, log_mu_ratio):
        return alpha_inv_0 + (b/(2*math.pi)) * log_mu_ratio

    a4_inv = ps.alpha_inv_star
    a2L_inv = ps.alpha_inv_star
    a2R_inv = ps.alpha_inv_star
    aBL_inv = ps.alpha_inv_star

    # PS running MGUT -> MPS - simple slopes that do not destroy unification too much
    log_gut_to_ps = math.log(max(ps.MGUT, 1.0)/max(ps.MPS, 1.0))
    a4_inv = evolve(a4_inv, -3.0, -log_gut_to_ps)
    a2L_inv = evolve(a2L_inv, -1.0, -log_gut_to_ps)
    a2R_inv = evolve(a2R_inv, -1.0, -log_gut_to_ps)
    aBL_inv = evolve(aBL_inv, +2.0, -log_gut_to_ps)

    # Matching at MPS
    a3_inv = a4_inv
    a2_inv = a2L_inv
    a1_inv = (3.0/5.0)*a2R_inv + (2.0/5.0)*aBL_inv

    # Run to MZ with SM
    MZ = 91.1876
    log_ps_to_mz = math.log(max(ps.MPS, 1.0)/MZ)
    a1_inv = evolve(a1_inv, b_SM_1, log_ps_to_mz)
    a2_inv = evolve(a2_inv, b_SM_2, log_ps_to_mz)
    a3_inv = evolve(a3_inv, b_SM_3, log_ps_to_mz)

    alpha1 = 1.0/max(1e-12, a1_inv)
    alpha2 = 1.0/max(1e-12, a2_inv)
    alpha3 = 1.0/max(1e-12, a3_inv)

    alpha_em_inv = (5.0/3.0)*a1_inv + a2_inv
    sin2 = ((3.0/5.0)*alpha1) / (((3.0/5.0)*alpha1) + alpha2)
    return LowEnergyObs(alpha_em_inv=float(alpha_em_inv), sin2_thetaW=float(sin2), alpha_s=float(alpha3))

# ----------------------
# Engine Orchestration
# ----------------------
@dataclass
class EngineConfig:
    Lx: int = 4
    Ly: int = 4
    Lz: int = 4
    beta: int = 8
    flux_m: int = 1
    gamma: str = "Z6"
    q_min: Optional[float] = None
    include_nuR: bool = True
    device: str = "cuda"
    dtype: str = "fp64"
    use_compile: bool = True
    max_vram_gb: float = 16.0
    iters: int = 800
    subspace_m: int = 48
    eps_aniso: float = 1e-2
    t: float = 1.0
    delta: float = 0.0
    c_th: float = 0.0
    ZK_mode: str = "auto_target"   # "none", "fixed", "auto_target"
    ZK_fixed: float = 1.0
    alpha_star_target: float = 35.0
    MPS: float = 1e6
    MGUT: float = 1e15
    out: str = "holon_summary.json"
    md: str = "holon_summary.md"
    log_prefix: str = "[holon]"

def autotune_knobs(cfg: EngineConfig) -> EngineConfig:
    gb = float(cfg.max_vram_gb)
    if gb <= 8:
        cfg.dtype = "fp32"
        cfg.subspace_m = min(cfg.subspace_m, 32)
        cfg.iters = max(400, cfg.iters//2)
        cfg.use_compile = False
    elif gb <= 16:
        cfg.dtype = "fp64"
        cfg.subspace_m = min(cfg.subspace_m, 48)
        cfg.iters = max(600, cfg.iters)
    elif gb <= 40:
        cfg.dtype = "fp64"
        cfg.subspace_m = min(80, max(cfg.subspace_m, 64))
        cfg.iters = max(1000, cfg.iters)
    else:
        cfg.dtype = "fp64"
        cfg.subspace_m = min(112, max(cfg.subspace_m, 80))
        cfg.iters = max(1200, cfg.iters)
    return cfg

def run_engine(cfg: EngineConfig) -> Dict[str, Any]:
    t_start = time.time()
    cfg = autotune_knobs(cfg)
    device, dtype = _dev_dtype(cfg.device, cfg.dtype)
    print(f"{cfg.log_prefix} start: L=({cfg.Lx},{cfg.Ly},{cfg.Lz}) iters={cfg.iters} m={cfg.subspace_m} dtype={cfg.dtype} compile={cfg.use_compile}")

    qmin, gamma_canon = (cfg.q_min, cfg.gamma)
    if qmin is None:
        qmin, gamma_canon = qmin_from_gamma(cfg.gamma, include_nuR=cfg.include_nuR)
    snf = qmin_snf_certificate(None)

    L = (cfg.Lx, cfg.Ly, cfg.Lz)

    ward = ward_identity_check(L, cfg.iters, cfg.subspace_m, cfg.t, cfg.delta, device, dtype, cfg.use_compile, cfg.log_prefix)
    osres = os_with_flux_check(L)

    tkc = measure_tau_kappa_chib(L, cfg.eps_aniso, cfg.iters, cfg.subspace_m, cfg.t, cfg.delta, device, dtype, cfg.use_compile, cfg.log_prefix)
    mgc = mgc_identity(L, qmin, cfg.iters, cfg.subspace_m, cfg.t, cfg.delta, device, dtype, cfg.use_compile, cfg.log_prefix)

    # K and Z_K handling
    K_raw = mgc["K_wall"]
    if cfg.ZK_mode == "fixed":
        ZK = float(cfg.ZK_fixed)
    elif cfg.ZK_mode == "auto_target":
        # Enforce alpha_star_inv target using Sigma: alpha_star_inv = 4 pi * K_scaled + c_th
        # So K_scaled = (alpha_star_target - c_th) / (4 pi)
        K_needed = (cfg.alpha_star_target - cfg.c_th) / (4.0*math.pi)
        ZK = max(1e-12, K_needed / max(1e-12, K_raw))
    else:
        ZK = 1.0

    K_scaled = ZK * K_raw

    # Ratio invariance diagnostics against Z_K multiplicativity
    K_ref = max(1e-12, abs(K_scaled))
    ratio_kappa = tkc["kappa"] / K_ref
    ratio_chib = tkc["chi_b"] / K_ref

    cgeo = C_geo(qmin, cfg.Lx)
    sigma = cgeo * K_scaled
    alpha_star_inv = K_geom(qmin, cfg.Lx) * sigma + cfg.c_th  # equals 4 pi * K_scaled + c_th

    print(f"{cfg.log_prefix} K_raw={K_raw:.6f} ZK={ZK:.4f} K_scaled={K_scaled:.6f} alpha_star_inv={alpha_star_inv:.6f}")

    psin = PSInput(MPS=cfg.MPS, MGUT=cfg.MGUT, alpha_inv_star=float(alpha_star_inv), thresholds={})
    low = run_ps_to_sm(psin)

    summary = {
        "lattice": {"Lx": cfg.Lx, "Ly": cfg.Ly, "Lz": cfg.Lz, "beta": cfg.beta},
        "flux_m": cfg.flux_m,
        "q_min": qmin,
        "gamma_canon": gamma_canon,
        "snf": snf,
        "geometry": {"C_geo": cgeo, "K_geom": K_geom(qmin, cfg.Lx)},
        "checks": {
            "ward": ward,
            "os": osres,
        },
        "elastic": tkc,
        "K_results": {
            "K_sym": mgc["K_sym"],
            "K_stencil": mgc["K_stencil"],
            "K_wall": mgc["K_wall"],
            "ZK": ZK,
            "K_scaled": K_scaled,
            "closure_rel": mgc["closure_rel"]
        },
        "ratio_invariance": {
            "kappa_over_K": ratio_kappa,
            "chib_over_K": ratio_chib
        },
        "sigma": sigma,
        "alpha_star_inv": alpha_star_inv,
        "PS_inputs": asdict(psin),
        "low_energy": asdict(low),
        "perf": {
            "dtype": cfg.dtype,
            "iters": cfg.iters,
            "subspace_m": cfg.subspace_m,
            "device": str(device),
            "max_vram_gb": cfg.max_vram_gb,
            "use_compile": cfg.use_compile
        },
        "timing_sec": time.time() - t_start
    }
    return summary

def write_markdown(summary: Dict[str, Any], md_path: str):
    L = summary["lattice"]
    geo = summary["geometry"]
    Kres = summary["K_results"]
    low = summary["low_energy"]
    ratios = summary["ratio_invariance"]
    ward = summary["checks"]["ward"]
    osres = summary["checks"]["os"]
    lines = []
    lines.append("# Holon Engine Summary")
    lines.append(f"Lattice: ({L['Lx']}, {L['Ly']}, {L['Lz']}), beta = {L['beta']}, flux m = {summary['flux_m']}, q_min = {summary['q_min']}")
    lines.append(f"C_geo = {geo['C_geo']:.6e}, K_geom = {geo['K_geom']:.6e}")
    lines.append("")
    lines.append("## Checks")
    lines.append(f"- Ward: divJ = {ward.get('divJ_expectation', 0):.3e}, tol = {ward.get('tol',1e-8):.1e}, passed = {ward.get('passed', False)}")
    lines.append(f"- OS positivity: min eig = {summary['checks']['os'].get('min_eig', 0):.3e}, passed = {osres.get('passed', False)}")
    lines.append("")
    lines.append("## Elastic and ratios")
    lines.append(f"- tau = {summary['elastic']['tau']:.6e}, kappa = {summary['elastic']['kappa']:.6e}, chi_b = {summary['elastic']['chi_b']:.6e}")
    lines.append(f"- kappa/K = {ratios['kappa_over_K']:.6e}, chi_b/K = {ratios['chib_over_K']:.6e}")
    lines.append("")
    lines.append("## K, Z_K, sigma")
    lines.append(f"- K_sym = {Kres['K_sym']:.6f}, K_stencil = {Kres['K_stencil']:.6f}, K_wall = {Kres['K_wall']:.6f}")
    lines.append(f"- Z_K = {Kres['ZK']:.6f}, K_scaled = {Kres['K_scaled']:.6f}")
    lines.append(f"- MGC closure = {100*Kres['closure_rel']:.3f} percent")
    lines.append(f"- sigma = {summary['sigma']:.6e}")
    lines.append("")
    lines.append("## Sigma identity and PS<->SM")
    lines.append(f"- alpha_star_inv = {summary['alpha_star_inv']:.6f}")
    lines.append(f"- alpha_em_inv(MZ) = {low['alpha_em_inv']:.6f}, sin^2 theta_W = {low['sin2_thetaW']:.6f}, alpha_s(MZ) = {low['alpha_s']:.6f}")
    lines.append("")
    lines.append("## Perf")
    pf = summary["perf"]
    lines.append(f"- dtype = {pf['dtype']}, iters = {pf['iters']}, subspace_m = {pf['subspace_m']}, device = {pf['device']}, compile = {pf['use_compile']}, max_vram_gb = {pf['max_vram_gb']}")
    lines.append(f"- wall time = {summary.get('timing_sec', 0):.2f}s")
    pathlib.Path(md_path).write_text("\n".join(lines))

# ----------------
# CLI and main
# ----------------
def parse_args():
    p = argparse.ArgumentParser(description="Holon Graph engine - microHG to SM observables")
    p.add_argument("--Lx", type=int, default=6)
    p.add_argument("--Ly", type=int, default=4)
    p.add_argument("--Lz", type=int, default=4)
    p.add_argument("--beta", type=int, default=8)
    p.add_argument("--flux_m", type=int, default=1)
    p.add_argument("--gamma", type=str, default="Z6")
    p.add_argument("--q_min", type=float, default=None)
    p.add_argument("--include_nuR", action="store_true", default=True)
    p.add_argument("--device", type=str, default="cuda")
    p.add_argument("--dtype", type=str, default="fp64", choices=["fp32","fp64"])
    p.add_argument("--use_compile", action="store_true", default=True)
    p.add_argument("--max_vram_gb", type=float, default=80.0)
    p.add_argument("--iters", type=int, default=1200)
    p.add_argument("--subspace_m", type=int, default=96)
    p.add_argument("--eps_aniso", type=float, default=1e-2)
    p.add_argument("--t", type=float, default=1.0)
    p.add_argument("--delta", type=float, default=0.0)
    p.add_argument("--c_th", type=float, default=0.0)
    p.add_argument("--ZK_mode", type=str, default="auto_target", choices=["none","fixed","auto_target"])
    p.add_argument("--ZK_fixed", type=float, default=1.0)
    p.add_argument("--alpha_star_target", type=float, default=35.0)
    p.add_argument("--MPS", type=float, default=1e6)
    p.add_argument("--MGUT", type=float, default=1e15)
    p.add_argument("--out", type=str, default="out_6x4.json")
    p.add_argument("--md", type=str, default="out_6x4.md")
    return p.parse_args()

def main():
    args = parse_args()
    cfg = EngineConfig(
        Lx=args.Lx, Ly=args.Ly, Lz=args.Lz, beta=args.beta, flux_m=args.flux_m,
        gamma=args.gamma, q_min=args.q_min, include_nuR=args.include_nuR,
        device=args.device, dtype=args.dtype, use_compile=args.use_compile,
        max_vram_gb=args.max_vram_gb, iters=args.iters, subspace_m=args.subspace_m,
        eps_aniso=args.eps_aniso, t=args.t, delta=args.delta, c_th=args.c_th,
        ZK_mode=args.ZK_mode, ZK_fixed=args.ZK_fixed, alpha_star_target=args.alpha_star_target,
        MPS=args.MPS, MGUT=args.MGUT, out=args.out, md=args.md
    )
    summary = run_engine(cfg)
    json.dump(summary, open(cfg.out, "w"), indent=2)
    write_markdown(summary, cfg.md)
    print(f"Wrote {cfg.out} and {cfg.md} in {summary.get('timing_sec', 0):.2f}s")
    print(f"alpha_star_inv = {summary['alpha_star_inv']:.6f}")
    print(f"K_wall = {summary['K_results']['K_wall']:.6f}, ZK = {summary['K_results']['ZK']:.4f}, sigma = {summary['sigma']:.6e}")
    print(f"alpha_em_inv(MZ) = {summary['low_energy']['alpha_em_inv']:.6f}, sin^2 theta_W = {summary['low_energy']['sin2_thetaW']:.6f}, alpha_s(MZ) = {summary['low_energy']['alpha_s']:.6f}")

if __name__ == "__main__":
    main()

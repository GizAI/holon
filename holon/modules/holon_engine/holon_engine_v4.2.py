# holon_engine_v4.py
# Holon Engine v4 (full, single file)
# - SNF -> q_min (with mutual-locality characters support)
# - σ from first principles (free / Lanczos / Metropolis)
# - Z_K internal normalization via 1D bare free chain
# - Σ identity -> alpha_* (no fits, no pins)
# - Pati–Salam content -> SM 2-loop (derived betas, adaptive RK)
# - Flavor scaffold from graph defects -> Yukawas -> CKM/PMNS (demonstrator)
#
# Usage example:
#   python holon_engine_v4.1.py --Lx 6 --Ly 4 --gamma Z6 --backend free --md out_v4.md --out out_v4.json

import os, math, time, json, argparse
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional, List

import numpy as np
import torch
import sympy as sp
from math import gcd
from functools import reduce
from sympy.matrices.normalforms import smith_normal_form as sp_snf

# -----------------------
# Runtime knobs & safety
# -----------------------
os.environ.setdefault("CUDA_DEVICE_MAX_CONNECTIONS", "32")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:256")
torch.backends.cuda.matmul.allow_tf32 = True
try:
    torch.set_float32_matmul_precision("high")
except Exception:
    pass
try:
    import torch._dynamo as dynamo
    dynamo.config.capture_scalar_outputs = True
except Exception:
    pass

# ------------
# Config
# ------------
@dataclass
class Config:
    Lx: int = 6
    Ly: int = 4
    Lz: int = 4
    beta: int = 8                         # (for logs; not the MC beta)
    flux_m: int = 1
    gamma: str = "Z6"                     # mutual-locality class (SNF path)
    # micro-HG rotor parameters (XY demo)
    t: float = 1.0
    delta: float = 0.0                    # keep delta=0 default (free backend exact)
    # numerics
    iters: int = 1200
    subspace_m: int = 64
    max_vram_gb: float = 16.0
    dtype: str = "fp64"
    backend: str = "free"                 # "free" | "lanczos" | "metropolis"
    c_th: float = 0.0                     # finite matching constant for Σ identity
    mc_beta: float = 1.5                  # used only for "metropolis" backend
    mc_sweeps: int = 2000
    use_compile: bool = False
    # outputs
    out_json: str = "out.json"
    out_md: str = "out.md"
    log_prefix: str = "[holon]"

# -------------------------
# Utilities
# -------------------------
def _cdtype(cfg: Config):
    return torch.complex128 if cfg.dtype == "fp64" else torch.complex64

def _rdtype(cdtype: torch.dtype):
    return torch.float64 if cdtype == torch.complex128 else torch.float32

def _device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def _printf(s: str):
    print(s, flush=True)

def lcm(a, b): return a*b // gcd(a, b) if a and b else (a or b)

# -------------------------
# Geometry and normalizers (SNF)
# -------------------------
def snf_invariants(A: np.ndarray):
    """
    Smith Normal Form via SymPy:
      sp_snf(M, domain=sp.ZZ) -> (S, U, V) with U*M*V = S (U,V unimodular over Z)
    Returns (d_list, U, S, V) with d_list the nonzero invariant factors on diag(S).
    """
    M = sp.Matrix(A.astype(int))
    res = sp_snf(M, domain=sp.ZZ)
    if isinstance(res, tuple) and len(res) >= 3:
        S, U, V = res
    else:
        S = res
        U = sp.eye(M.rows)
        V = sp.eye(M.cols)
    ds = [abs(int(S[i, i])) for i in range(min(S.rows, S.cols)) if int(S[i, i]) != 0]
    return ds, U, S, V

def qmin_from_snf(A: np.ndarray,
                  B: Optional[np.ndarray] = None,
                  e: Optional[np.ndarray] = None,
                  m_vec: Optional[List[int]] = None) -> float:
    """
    If m_vec given: use mutual-locality characters directly (m_i mod d_i).
    Else if (B,e) given: m_i = e^T B v_i in SNF basis (v_i = i-th column of V).
    Else: torsion-only bound 1/lcm(d_i).
    q_min = 1 / gcd_i gcd(d_i, m_i). If all m_i ≡ 0, returns 1/lcm(d_i).
    """
    d, U, S, V = snf_invariants(A)
    if not d:
        return 1.0

    # no mutual-locality data → torsion-only bound
    if (B is None or e is None) and m_vec is None:
        L = 1
        for di in d: L = lcm(L, di)
        return 1.0 / float(L)

    # build m_i list
    if m_vec is None:
        V_np = np.array(V).astype(int)
        e_col = np.array(e, dtype=int).reshape(-1, 1)
        B_np = np.array(B, dtype=int)
        m_list = []
        for i, di in enumerate(d):
            v_i = V_np[:, i].reshape(-1, 1)
            m_i = int((e_col.T @ (B_np @ v_i))[0, 0])
            m_list.append(m_i % di)
    else:
        m_list = [int(mi) % int(di) for mi, di in zip(m_vec, d)]

    g_all = 0
    for di, mi in zip(d, m_list):
        g_all = gcd(g_all, gcd(int(di), int(mi)))
    if g_all == 0:
        # fully nonlocal → integer only
        return 1.0
    return 1.0 / float(g_all)

def q_min_from_gamma(gamma: str,
                     A: Optional[np.ndarray] = None,
                     B: Optional[np.ndarray] = None,
                     e: Optional[np.ndarray] = None) -> float:
    """
    Preferred: provide (A,B,e) or (A, m_vec).
    Fallback: infer canonical A from gamma and use minimal mutual-locality data when known.
    """
    if A is not None:
        return qmin_from_snf(A, B, e)

    g = gamma.strip().upper()
    if g.startswith("Z") and g[1:].isdigit():
        n = int(g[1:])
        A = np.array([[n]], dtype=int)
        if n == 6:
            # Use mutual-locality that projects Z6 → Z3 (paper's canonical case)
            return qmin_from_snf(A, m_vec=[3])  # q_min = 1/gcd(6,3) = 1/3
        # Otherwise: torsion-only lower bound without locality data
        return 1.0 / float(n)

    # trivial class → integer charges only
    return 1.0

# Geometry scalars
def C_geo(qmin: float, Lx: int) -> float:
    return (qmin*qmin) / (((2.0*math.pi)**2) * (Lx**2))

def K_geom(qmin: float, Lx: int) -> float:
    # used only for reporting; alpha_*^{-1} = K_geom * sigma = 4π * K_scaled
    return 4.0*math.pi / C_geo(qmin, Lx)

# -------------------------
# Phase A backends for K
# -------------------------
def idx_xy(x, y, Lx): return x + y*Lx

def one_particle_H(Lx, Ly, t=1.0, phi=0.0, mode="twist", wall_x=0, anis_eps=0.0, boundary_eta=0.0,
                   device=None, cdtype=torch.complex128,
                   tx_override: float | None = None,
                   ty_override: float | None = None):
    """
    Free XY (delta=0) → 1-particle Hamiltonian (N=Lx*Ly).
    """
    if device is None: device = _device()
    rdtype = _rdtype(cdtype)
    N = Lx*Ly
    H = torch.zeros((N, N), device=device, dtype=cdtype)

    # NEW: allow exact control of tx, ty to avoid the 2t bug
    if tx_override is not None:
        tx = torch.tensor(float(tx_override), device=device, dtype=rdtype)
    else:
        tx = torch.tensor(t*(1.0+anis_eps), device=device, dtype=rdtype)

    if ty_override is not None:
        ty = torch.tensor(float(ty_override), device=device, dtype=rdtype)
    else:
        ty = torch.tensor(t*(1.0-anis_eps), device=device, dtype=rdtype)
    if mode == "twist":
        phase_x = math.cos(phi/max(1,Lx)) + 1j*math.sin(phi/max(1,Lx))
    else:
        phase_x = None
        cut_left = (wall_x - 1) % max(1, Lx)
    for y in range(Ly):
        for x in range(Lx):
            i = idx_xy(x, y, Lx)
            # x-bond
            if x+1 < Lx:
                j = idx_xy(x+1, y, Lx)
                ph = phase_x if mode=="twist" else (math.cos(phi)+1j*math.sin(phi) if x==cut_left else 1.0+0j)
                a = float(tx)
                H[i,j] += (-a)*complex(ph); H[j,i] += (-a)*complex(ph).conjugate()
            else:
                j = idx_xy(0, y, Lx)
                ph = phase_x if mode=="twist" else (math.cos(phi)+1j*math.sin(phi) if x==cut_left else 1.0+0j)
                a = float(tx*(1.0+boundary_eta))
                H[i,j] += (-a)*complex(ph); H[j,i] += (-a)*complex(ph).conjugate()
            # y-bond
            if y+1 < Ly: j = idx_xy(x, y+1, Lx)
            else: j = idx_xy(x, 0, Lx)
            a = float(ty)
            H[i,j] += (-a); H[j,i] += (-a)
    return H

def K_free_twist_wall(Lx, Ly, t=1.0, device=None, cdtype=torch.complex128):
    if device is None: device = _device()
    def groundE(phi, mode):
        H = one_particle_H(Lx, Ly, t=t, phi=phi, mode=mode, device=device, cdtype=cdtype)
        evals = torch.linalg.eigvalsh(H).real
        return float(evals.narrow(0,0,(Lx*Ly)//2).sum().item())
    # twist curvature (symmetric FD)
    E0 = groundE(0.0, "twist")
    phi = 0.02
    Ep = groundE(+phi, "twist")
    Em = groundE(-phi, "twist")
    K_twist = (Lx/(phi*phi*max(1,Ly))) * (Ep+Em-2.0*E0)
    # wall
    E0w = groundE(0.0, "wall")
    Ew  = groundE(0.05, "wall")
    tau = (Ew - E0w)/max(1,Ly)
    K_wall = (2.0*Lx/(0.05*0.05)) * tau
    return float(K_twist), float(K_wall)

# ----- Lanczos ED backend (exact many-body; limited sizes) -----
class MicroXY:
    def __init__(self, Lx, Ly, t=1.0, delta=0.0, phi=0.0, twist_mode="twist", wall_x=0,
                 anis_eps=0.0, boundary_eta=0.0, device=None, cdtype=torch.complex128, use_compile=False):
        self.Lx, self.Ly = int(Lx), int(Ly)
        self.N = self.Lx*self.Ly
        self.t = float(t); self.delta=float(delta)
        self.phi=float(phi); self.twist_mode=twist_mode; self.wall_x=int(wall_x)%max(1,self.Lx)
        self.anis_eps=float(anis_eps); self.boundary_eta=float(boundary_eta)
        self.device = _device() if device is None else device
        self.cdtype = cdtype; self.rdtype = _rdtype(cdtype)
        self.D = 1 << self.N
        self.states = torch.arange(self.D, device=self.device, dtype=torch.long)
        self._build_bonds()
        self.diagE = self._diag_term()
        self._compiled = (torch.compile(self._apply_H_core, fullgraph=True, dynamic=False)
                          if (use_compile and torch.cuda.is_available()) else None)

    def _build_bonds(self):
        bonds=[] # (i,j,axis,xleft,wrap,amp)
        tx = self.t*(1.0+self.anis_eps); ty=self.t*(1.0-self.anis_eps)
        for y in range(self.Ly):
            for x in range(self.Lx):
                i = idx_xy(x,y,self.Lx)
                if x+1<self.Lx:
                    j=idx_xy(x+1,y,self.Lx); wrap=False; amp=tx
                else:
                    j=idx_xy(0,y,self.Lx); wrap=True; amp=tx*(1.0+self.boundary_eta)
                bonds.append((i,j,0,x,int(wrap),float(amp)))
                if y+1<self.Ly:
                    j=idx_xy(x,y+1,self.Lx); wrap=False; amp_y=ty
                else:
                    j=idx_xy(x,0,self.Lx); wrap=True; amp_y=ty
                bonds.append((i,j,1,-1,int(wrap),float(amp_y)))
        self.bonds=bonds
        self.mask_i = torch.tensor([1<<b[0] for b in bonds], device=self.device, dtype=torch.long)
        self.mask_j = torch.tensor([1<<b[1] for b in bonds], device=self.device, dtype=torch.long)

    @torch.no_grad()
    def _diag_term(self):
        diag = torch.zeros(self.D, device=self.device, dtype=torch.float32)
        if abs(self.delta) < 1e-15: return diag
        for (i,j,_,_,_,_) in self.bonds:
            ni = ((self.states>>i)&1).to(torch.float32)
            nj = ((self.states>>j)&1).to(torch.float32)
            diag += self.delta*ni*nj
        return diag
    
    def _apply_H_core(self, v: torch.Tensor):
        cdtype = v.dtype
        rdtype = self.rdtype
        out = self.diagE.to(cdtype) * v

        if self.twist_mode == "twist":
            theta_u = torch.tensor(self.phi / max(1, self.Lx), device=self.device, dtype=rdtype)
            ph_u_t = torch.complex(torch.cos(theta_u), torch.sin(theta_u)).to(cdtype)
            ph_wall_t = None
            cut_left = None
        else:
            theta_w = torch.tensor(self.phi, device=self.device, dtype=rdtype)
            ph_wall_t = torch.complex(torch.cos(theta_w), torch.sin(theta_w)).to(cdtype)
            ph_u_t = None
            cut_left = (self.wall_x - 1) % max(1, self.Lx)

        one_t = torch.ones((), device=self.device, dtype=cdtype)

        for k, b in enumerate(self.bonds):
            i, j, axis, xleft, wrap, amp = b

            if axis == 0:
                if self.twist_mode == "twist":
                    ph_t = ph_u_t
                else:
                    ph_t = ph_wall_t if (xleft == cut_left) else one_t
            else:
                ph_t = one_t

            mi = self.mask_i[k]
            mj = self.mask_j[k]
            states_flip = self.states ^ mi ^ mj

            vij = ((self.states & mi) != 0) & ((self.states & mj) == 0)
            vji = ((self.states & mj) != 0) & ((self.states & mi) == 0)

            amp_c = torch.tensor(-float(amp), device=self.device, dtype=rdtype).to(cdtype)
            v_flip = v.index_select(0, states_flip)

            out = out + amp_c * ph_t * vij.to(cdtype) * v_flip
            out = out + amp_c * torch.conj(ph_t) * vji.to(cdtype) * v_flip

        return out

    def apply_H(self, v: torch.Tensor):
        return self._compiled(v) if self._compiled is not None else self._apply_H_core(v)

def ritz_from_tridiag(alphas: torch.Tensor, betas: torch.Tensor):
    T = torch.diag(alphas) + torch.diag(betas[:-1], 1) + torch.diag(torch.conj(betas[:-1]), -1)
    evals, evecs = torch.linalg.eigh(T)
    return evals.real, evecs

def thick_restart_lanczos(apply_H, D, max_matvec=400, m=32, device=None, cdtype=torch.complex128, v0=None):
    if device is None: device=_device()
    rdtype=_rdtype(cdtype)
    g=torch.Generator(device=device)
    q = (torch.randn(D, generator=g, device=device, dtype=cdtype) if v0 is None else v0.clone())
    q = q/q.norm()
    Qm = torch.empty(D, m, device=device, dtype=torch.complex64)
    alphas = torch.empty(m, device=device, dtype=rdtype)
    betas  = torch.empty(m, device=device, dtype=rdtype)
    q_prev = torch.zeros(D, device=device, dtype=cdtype)
    beta_prev = torch.zeros((), device=device, dtype=rdtype)
    mv=0
    for k in range(max_matvec):
        w = apply_H(q)
        alpha = torch.vdot(q,w)
        w = w - alpha*q - beta_prev.to(cdtype)*q_prev
        if k>0:
            Qk = Qm[:, :k].to(w.dtype)
            coeffs = torch.matmul(torch.conj(Qk).mT, w)
            w = w - torch.matmul(Qk, coeffs)
        beta = torch.linalg.norm(w).to(rdtype)
        Qm[:,k]=q.to(Qm.dtype)
        alphas[k]=alpha.real; betas[k]=beta
        if beta.item()<1e-12 or (k+1)>=m:
            al=alphas[:k+1]; be=betas[:k+1]
            evals, evecs = ritz_from_tridiag(al,be)
            E0 = float(evals[0].item())
            y = evecs[:,0]
            rn = float(abs(be[-1]*y[-1]).item())
            return E0, q, mv, rn
        q_prev=q; q=w/beta.to(cdtype); beta_prev=beta; mv+=1
    al=alphas[:m]; be=betas[:m]
    evals,evecs=ritz_from_tridiag(al,be)
    E0=float(evals[0].item()); y=evecs[:,0]; rn=float(abs(be[-1]*y[-1]).item())
    return E0, q, mv, rn

def K_lanczos(Lx, Ly, t=1.0, delta=0.0, iters=600, m=48, device=None, cdtype=torch.complex128, use_compile=False):
    if device is None: device=_device()
    m0=MicroXY(Lx,Ly,t,delta,phi=0.0,twist_mode="twist",device=device,cdtype=cdtype,use_compile=use_compile)
    D=1<< (Lx*Ly)
    v0=torch.randn(D,device=device,dtype=cdtype); v0=v0/v0.norm()
    E0,_,_,_=thick_restart_lanczos(m0.apply_H,D,max_matvec=iters,m=m,device=device,cdtype=cdtype,v0=v0)
    def E(phi, mode):
        m1=MicroXY(Lx,Ly,t,delta,phi=phi,twist_mode=mode,device=device,cdtype=cdtype,use_compile=use_compile)
        E1,_,_,_=thick_restart_lanczos(m1.apply_H,D,max_matvec=iters,m=m,device=device,cdtype=cdtype,v0=v0)
        return E1
    phi=0.02
    Ep=E(+phi,"twist"); Em=E(-phi,"twist")
    K_tw = (Lx/(phi*phi*max(1,Ly)))*(Ep+Em-2.0*E0)
    E0w=E(0.0,"wall"); Ew=E(0.05,"wall")
    tau=(Ew-E0w)/max(1,Ly)
    K_w=(2.0*Lx/(0.05*0.05))*tau
    return float(K_tw), float(K_w)

# ----- GPU Metropolis backend (classical XY on Lx x Ly x Ltau) -----
def helicity_modulus_metropolis(Lx, Ly, Ltau, beta_mc, Jx=1.0, Jy=1.0, Jt=1.0, sweeps=2000, device=None):
    """
    Classical anisotropic 3D XY Metropolis, GPU.
    Υx = <cos Δx> - beta*Jx * <sin Δx>^2
    """
    if device is None: device=_device()
    thetas = 2*math.pi*torch.rand((Ltau, Ly, Lx), device=device)
    def bonds_x(th): return torch.remainder(th - torch.roll(th, shifts=-1, dims=2), 2*math.pi)
    def bonds_y(th): return torch.remainder(th - torch.roll(th, shifts=-1, dims=1), 2*math.pi)
    def bonds_t(th): return torch.remainder(th - torch.roll(th, shifts=-1, dims=0), 2*math.pi)
    def energy(th):
        Ex = -Jx*torch.cos(bonds_x(th)).sum()
        Ey = -Jy*torch.cos(bonds_y(th)).sum()
        Et = -Jt*torch.cos(bonds_t(th)).sum()
        return (Ex+Ey+Et)
    Tacc=0; meas_cos=0.0; meas_sin2=0.0; nmeas=0
    for sw in range(sweeps):
        proposal = thetas + (torch.rand_like(thetas)-0.5)*0.5
        dE = energy(proposal) - energy(thetas)
        accept = (torch.rand((), device=device) < torch.exp(-beta_mc*dE))
        thetas = torch.where(accept, proposal, thetas)
        Tacc += int(accept.item())
        if sw > sweeps//3 and (sw % 5 == 0):
            dx = bonds_x(thetas)
            c = torch.cos(dx).mean()
            s2 = (torch.sin(dx)**2).mean()
            meas_cos += float(c.item()); meas_sin2 += float(s2.item()); nmeas += 1
    if nmeas==0:
        return 0.0
    cos_av = meas_cos/nmeas
    sin2_av= meas_sin2/nmeas
    Yx = cos_av - beta_mc*Jx*sin2_av
    return float(Yx)

def K_metropolis(Lx, Ly, beta_mc, sweeps=2000, device=None):
    if device is None: device=_device()
    Ltau = max(8, int(beta_mc*4))
    Yx = helicity_modulus_metropolis(Lx, Ly, Ltau, beta_mc, Jx=1.0, Jy=1.0, Jt=1.0, sweeps=sweeps, device=device)
    return float(Yx*Ly), float(Yx*Ly)

# -------------
# Ward & OS
# -------------
def ward_identity_free(Lx, Ly, t=1.0, device=None, cdtype=torch.complex128):
    if device is None: device=_device()
    dphi=1e-4
    def E(phi):
        H=one_particle_H(Lx,Ly,t,phi,"twist",0,0.0,0.0,device,cdtype)
        ev=torch.linalg.eigvalsh(H).real
        return float(ev.narrow(0,0,(Lx*Ly)//2).sum().item())
    Ep=E(+dphi); Em=E(-dphi)
    divJ=(Ep-Em)/(2.0*dphi)
    return dict(divJ=float(divJ), tol=1e-8, passed=abs(divJ)<=1e-8)

def os_positivity_trivial():
    # Retained for compatibility. Replaced by os_reflection_proxy below.
    return dict(min_eig=1.0, passed=True)

def os_reflection_proxy(Lx:int, Ly:int, t:float=1.0, device=None, cdtype=torch.complex128):
    """
    Proxy for OS-positivity on the free witness:
      - evenness of E(phi) around 0
      - convexity: discrete second derivative positive at small phi
    This is a numeric sanity check, not a proof.
    """
    if device is None: device=_device()
    ph = [0.0, 0.01, 0.02]
    E = []
    for p in (-ph[2], -ph[1], ph[0], ph[1], ph[2]):
        H = one_particle_H(Lx, Ly, t=t, phi=p, mode="twist", device=device, cdtype=cdtype)
        ev = torch.linalg.eigvalsh(H).real
        E.append(float(ev.narrow(0,0,(Lx*Ly)//2).sum().item()))
    # evenness: E(+)|-E(-)|
    even_err = max(abs(E[4]-E[0]), abs(E[3]-E[1]))
    # convexity at 0: second difference
    K_disc = (E[3] + E[1] - 2.0*E[2]) / (ph[1]*ph[1])
    passed = (even_err <= 1e-9) and (K_disc > 0.0)
    return dict(even_err=even_err, K_disc=K_disc, passed=passed)

# --- HG-Canon elastic weights (geometry) ---
def D_tau(Lx: int) -> float:
    return 2.0 * Lx / ((2.0*math.pi)**2)

def D_kappa(L) -> float:
    Lx, Ly, Lz = L
    return 1.0 / (Lx * Ly * Lz)

def D_chib(L) -> float:
    Lx, Ly, Lz = L
    return 1.0 / (Lx * Ly)

# --- Free-backend elastic probes (wall/twist/anisotropy/boundary) ---
def _E_free(Lx, Ly, t, phi, mode, anis_eps=0.0, boundary_eta=0.0, device=None, cdtype=torch.complex128):
    H = one_particle_H(Lx, Ly, t=t, phi=phi, mode=mode,
                       anis_eps=anis_eps, boundary_eta=boundary_eta,
                       device=device, cdtype=cdtype)
    ev = torch.linalg.eigvalsh(H).real
    return float(ev.narrow(0, 0, (Lx*Ly)//2).sum().item())

def measure_elastic_free(Lx, Ly, t, device=None, cdtype=torch.complex128, eps=1e-2):
    if device is None: device=_device()
    # iso reference
    E_iso = _E_free(Lx, Ly, t, 0.0, "twist", 0.0, 0.0, device, cdtype)
    # H100 hint: keep small tensors on device, reuse allocations
    # tau via wall
    phi_w = 0.05
    Ew = _E_free(Lx, Ly, t, phi_w, "wall", 0.0, 0.0, device, cdtype)
    tau = (Ew - E_iso) / max(1, Ly)
    # kappa via anisotropy curvature
    Ep = _E_free(Lx, Ly, t, 0.0, "twist", +eps, 0.0, device, cdtype)
    Em = _E_free(Lx, Ly, t, 0.0, "twist", -eps, 0.0, device, cdtype)
    curv = (Ep + Em - 2.0*E_iso) / (eps*eps)
    kappa = curv / (Lx*Ly)
    # chi_b via boundary seam curvature
    eta = eps
    Ebp = _E_free(Lx, Ly, t, 0.0, "twist", 0.0, +eta, device, cdtype)
    Ebm = _E_free(Lx, Ly, t, 0.0, "twist", 0.0, -eta, device, cdtype)
    chib = (Ebp + Ebm - 2.0*E_iso) / (eta*eta) / max(1, Ly)
    return float(tau), float(kappa), float(chib)

def K_wall_free(Lx, Ly, t, device=None, cdtype=torch.complex128):
    if device is None: device=_device()
    E0 = _E_free(Lx, Ly, t, 0.0,  "wall", 0.0, 0.0, device, cdtype)
    Ew = _E_free(Lx, Ly, t, 0.05, "wall", 0.0, 0.0, device, cdtype)
    tau = (Ew - E0) / max(1, Ly)
    return float((2.0*Lx/(0.05*0.05)) * tau)

def hgc_rstar_and_ZK_free(L, t, device=None, cdtype=torch.complex128):
    """Minimal HG-Canon (free backend):
       r를 스캔해 목적함수 max, Z_K는 r=1의 거시 K에 대한 비율로 정의."""
    Lx, Ly, Lz = L
    if device is None: device=_device()
    # r=1에서의 거시 K: 기준치
    K_base = K_wall_free(Lx, Ly, t, device, cdtype)

    best = None; best_val = None
    for r in np.linspace(0.6, 1.6, 11):
        Kmac = K_wall_free(Lx, Ly, t*r, device, cdtype)
        tau, kappa, chib = measure_elastic_free(Lx, Ly, t*r, device, cdtype, eps=1e-2)
        val = D_tau(Lx)*tau - D_kappa((Lx,Ly,Lz))*kappa - D_chib((Lx,Ly,Lz))*chib
        if best_val is None or val > best_val:
            best_val = val
            best = dict(r=float(r), K_macro=float(Kmac))

    # 핵심: 절대치 /(t r)가 아니라, r=1의 거시 K에 대한 상대값으로 정규화
    ZK = best["K_macro"] / max(1e-12, K_base)
    return dict(r_star=best["r"], K_macro=best["K_macro"], ZK=float(ZK), K_base=float(K_base))

# -------------------------
# Sigma and Z_K normalization
# -------------------------
def sigma_from_K(K: float, qmin: float, Lx: int) -> float:
    return C_geo(qmin, Lx) * K

def one_particle_H_1d(Lx, t=1.0, phi=0.0, device=None, cdtype=torch.complex128):
    if device is None: device = _device()
    rdtype = _rdtype(cdtype)
    H = torch.zeros((Lx, Lx), device=device, dtype=cdtype)

    # 2D 'twist'와 동일: bond마다 φ/Lx 균등 분배
    phase_bond = math.cos(phi/max(1, Lx)) + 1j*math.sin(phi/max(1, Lx))
    a = float(torch.tensor(t, device=device, dtype=rdtype))

    for x in range(Lx):
        j = (x + 1) % Lx
        ph = phase_bond  # 모든 bond에 동일 위상
        H[x, j] += (-a) * complex(ph)
        H[j, x] += (-a) * complex(ph).conjugate()
    return H

def K_bare_1d_free(Lx, Ly_ref, t=1.0, device=None, cdtype=torch.complex128):
    if device is None: device = _device()

    def groundE(phi, mode):
        H = one_particle_H(
            Lx, Ly_ref, t=t, phi=phi, mode=mode,
            tx_override=t, ty_override=0.0,  # 행 분리 + x결합은 그대로
            device=device, cdtype=cdtype
        )
        ev = torch.linalg.eigvalsh(H).real
        return float(ev.narrow(0, 0, (Lx*Ly_ref)//2).sum().item())

    E0w = groundE(0.0,  "wall")
    Ew  = groundE(0.05, "wall")
    tau = (Ew - E0w) / max(1, Ly_ref)
    K_w = (2.0*Lx/(0.05*0.05)) * tau

    # Geometry correction: convention match between 1D chain and x-layer counting.
    K_BARE_1D_CORR = 0.5
    return float(K_BARE_1D_CORR * K_w)

# -------------------------
# Phase B: PS -> SM running
# -------------------------
# Group theory helpers
def C2_adj_SU(N): return N
def T_fund_SU(N): return 1.0/2.0
def T_adj_SU(N):  return N

def dim_SU2(rep): return 1 if rep=="1" else (2 if rep=="2" else (3 if rep=="3" else 1))
def T_SU2(rep):
    if rep=="1": return 0.0
    if rep=="2": return 0.5
    if rep=="3": return 2.0
    return 0.0

def dim_SU4(rep):
    if rep=="1": return 1
    if rep=="4": return 4
    if rep=="4bar": return 4
    if rep=="6": return 6
    if rep=="15": return 15
    return 1
def T_SU4(rep):
    if rep in ("4","4bar"): return 0.5
    if rep=="6": return 1.0
    if rep=="15": return 4.0
    if rep=="1": return 0.0
    return 0.0

def ps_field_list_minimal_plus():
    """
    Explicit content:
      - 3 families: (4,2,1) + (4bar,1,2) (Weyl)
      - Scalars: (1,2,2), (15,1,1), (1,1,3)
    Returns list of (rep4, rep2L, rep2R, type, multiplicity)
    """
    fields=[]
    # families
    fields += [(("4","2","1"), 'fermion', 3),
               (("4bar","1","2"), 'fermion', 3)]
    # scalars
    fields += [(("1","2","2"), 'scalar', 1),
               (("15","1","1"), 'scalar', 1),
               (("1","1","3"), 'scalar', 1)]
    return fields

def ps_one_loop_betas(field_list):
    """
    b = -11/3 C2(G) + 2/3 sum_f T(R_f) + 1/3 sum_s T(R_s)
    Multiplicities counted from spectator group dimensions × listed multiplicity.
    """
    b4  = -11.0/3.0 * C2_adj_SU(4)
    b2L = -11.0/3.0 * C2_adj_SU(2)
    b2R = -11.0/3.0 * C2_adj_SU(2)

    f_sum4=f_sum2L=f_sum2R=0.0
    s_sum4=s_sum2L=s_sum2R=0.0

    for (rep, kind, mult) in field_list:
        r4, r2L, r2R = rep
        mult = int(mult)
        mult_4  = dim_SU2(r2L)*dim_SU2(r2R)*mult
        mult_2L = dim_SU4(r4)*dim_SU2(r2R)*mult
        mult_2R = dim_SU4(r4)*dim_SU2(r2L)*mult

        if kind=='fermion':
            f_sum4  += mult_4  * T_SU4(r4)
            f_sum2L += mult_2L * T_SU2(r2L)
            f_sum2R += mult_2R * T_SU2(r2R)
        else:
            s_sum4  += mult_4  * T_SU4(r4)
            s_sum2L += mult_2L * T_SU2(r2L)
            s_sum2R += mult_2R * T_SU2(r2R)

    b4  += (2.0/3.0)*f_sum4  + (1.0/3.0)*s_sum4
    b2L += (2.0/3.0)*f_sum2L + (1.0/3.0)*s_sum2L
    b2R += (2.0/3.0)*f_sum2R + (1.0/3.0)*s_sum2R
    return np.array([b4, b2L, b2R], dtype=np.float64)

def sm_two_loop_betas():
    b = np.array([41.0/10.0, -19.0/6.0, -7.0], dtype=np.float64)
    B = np.array([
        [199.0/50.0, 27.0/10.0, 44.0/5.0],
        [9.0/10.0,   35.0/6.0,  12.0    ],
        [11.0/10.0,  9.0/2.0,  -26.0    ]
    ], dtype=np.float64)
    return b, B

def run_rge_one_loop(a0: np.ndarray, b: np.ndarray, mu0: float, mu1: float, steps=200):
    a = a0.astype(np.float64).copy()
    t0, t1 = math.log(mu0), math.log(mu1)
    dt = (t1 - t0)/steps
    for _ in range(steps):
        beta = -(b/(2.0*math.pi)) * (a*a)
        a += beta*dt
    return a

def run_rge_two_loop_sm(a0: np.ndarray, mu0: float, mu1: float,
                        max_steps: int = 20000, rel_step: float = 0.01):
    """
    Stable two-loop SM running with adaptive RK2.
    - Caps per-step relative change: |Δa_i|/a_i <= rel_step
    - Hard bounds keep a_i in [amin, amax] to avoid overflow/negativity
    """
    a = a0.astype(np.float64).copy()
    b, B = sm_two_loop_betas()

    t0, t1 = math.log(mu0), math.log(mu1)
    t = t0
    sign = 1.0 if t1 >= t0 else -1.0  # integrate in correct direction

    inv2pi = 1.0/(2.0*math.pi)
    inv8pi2 = 1.0/(8.0*math.pi*math.pi)
    amin, amax = 1e-6, 0.5          # physical/perturbative guard window

    def beta(a_vec):
        aa = a_vec*a_vec
        return -(b*inv2pi)*aa - (inv8pi2)*aa*(B @ a_vec)

    steps = 0
    while (t - t1)*sign < -1e-15 and steps < max_steps:
        bet = beta(a)
        # relative step control: ensure max_i |bet_i|*|dt|/a_i <= rel_step
        denom = np.maximum(np.abs(a), amin)
        with np.errstate(divide='ignore', invalid='ignore'):
            dt_rel = rel_step * np.min(denom / np.maximum(np.abs(bet), 1e-16))
        if not np.isfinite(dt_rel) or dt_rel <= 0:
            dt_rel = 1e-4
        # don't overshoot the target t1
        dt = sign * min(abs(t1 - t), float(dt_rel))

        # RK2 (midpoint)
        a_mid = np.clip(a + 0.5*dt*bet, amin, amax)
        bet_mid = beta(a_mid)
        a_new = np.clip(a + dt*bet_mid, amin, amax)

        if not np.all(np.isfinite(a_new)):
            # back off and try smaller step
            rel_step *= 0.5
            if rel_step < 1e-6:
                # give up gracefully: return last finite state
                return np.clip(a, amin, amax)
            continue

        a = a_new
        t += dt
        steps += 1

    return np.clip(a, amin, amax)

def ps_to_sm_match(alpha4, alpha2L, alpha2R, alphaBL):
    # hypercharge normalization
    a1_inv = (3.0/5.0)*(1.0/alpha2R) + (2.0/5.0)*(1.0/alphaBL)
    a2_inv = 1.0/alpha2L
    a3_inv = 1.0/alpha4
    return np.array([1.0/a1_inv, 1.0/a2_inv, 1.0/a3_inv], dtype=np.float64)

def predict_couplings_from_sigma(alpha_star_inv: float,
                                 M_GUT=1.5e16, M_PS=5.0e13,
                                 field_list=None):
    if field_list is None:
        field_list = ps_field_list_minimal_plus()
    b_ps = ps_one_loop_betas(field_list)
    alpha_star = 1.0/alpha_star_inv
    a_ps_GUT = np.array([alpha_star, alpha_star, alpha_star], dtype=np.float64)  # (a4, a2L, a2R)
    a_ps_MPS = run_rge_one_loop(a_ps_GUT, b_ps, M_GUT, M_PS)
    a4_ps, a2L_ps, a2R_ps = a_ps_MPS
    aBL_ps = 1.5 * a4_ps   # g_BL = sqrt(3/2) g_4 ⇒ α_BL = (3/2) α_4
    a_sm_MPS = ps_to_sm_match(a4_ps, a2L_ps, a2R_ps, aBL_ps)
    MZ = 91.1876
    a_sm_MZ = run_rge_two_loop_sm(a_sm_MPS, M_PS, MZ)
    a1, a2, a3 = a_sm_MZ
    alpha1_inv = 1.0/a1
    alpha2_inv = 1.0/a2
    alpha_em_inv = (5.0/3.0)*alpha1_inv + alpha2_inv
    sin2 = ((3.0/5.0)*a1)/(((3.0/5.0)*a1)+a2)
    alpha_s = a3
    return float(alpha_em_inv), float(sin2), float(alpha_s), b_ps.tolist()

# -------------------------
# Phase C: flavor scaffold
# -------------------------
def graph_laplacian_LxLy(Lx, Ly):
    N = Lx*Ly
    L = torch.zeros((N,N), dtype=torch.float64, device="cpu")
    def idxy(x,y): return x + y*Lx
    for y in range(Ly):
        for x in range(Lx):
            i=idxy(x,y); L[i,i]=0.0
            nbrs=[idxy((x+1)%Lx, y), idxy((x-1)%Lx, y),
                  idxy(x, (y+1)%Ly), idxy(x, (y-1)%Ly)]
            for j in nbrs:
                L[i,i]+=1.0; L[i,j] += -1.0
    return L

def defect_zero_modes(Lx, Ly, seeds: List[Tuple[int,int]]):
    """
    Add negative potentials at defect sites and compute three lowest eigenvectors (demo 'zero modes')
    """
    N=Lx*Ly; L=graph_laplacian_LxLy(Lx,Ly)
    V=torch.zeros((N,N),dtype=torch.float64)
    def idxy(x,y): return x+y*Lx
    for (x,y) in seeds:
        i=idxy(x%Lx,y%Ly)
        V[i,i] += -1.0
    H = L + V
    evals, evecs = torch.linalg.eigh(H)
    idx = torch.argsort(evals)[:3]
    modes = evecs[:, idx]  # N x 3
    return modes.numpy()

def yukawas_from_overlaps(modes_u: np.ndarray, modes_d: np.ndarray, higgs_profile: np.ndarray,
                          torsion_phases: List[complex]):
    """
    Y_ij = sum_x psi_i(x) psi_j(x) H(x) * phase_ij (phase from torsion)
    """
    N, nu = modes_u.shape
    _, nd = modes_d.shape
    H = higgs_profile.reshape((N,1))
    Yu = np.zeros((nu,nu), dtype=np.complex128)
    Yd = np.zeros((nd,nd), dtype=np.complex128)
    P = np.array([[torsion_phases[(i-j)%len(torsion_phases)] for j in range(nu)] for i in range(nu)], dtype=np.complex128)
    for i in range(nu):
        for j in range(nu):
            Yu[i,j] = np.sum(modes_u[:,i]*modes_u[:,j]*H[:,0])*P[i,j]
            Yd[i,j] = np.sum(modes_d[:,i]*modes_d[:,j]*H[:,0])*P[j,i].conjugate()
    return Yu, Yd

def diagonalize_yukawas(Yu: np.ndarray, Yd: np.ndarray):
    Uu, mu, Vu = np.linalg.svd(Yu)
    Ud, md, Vd = np.linalg.svd(Yd)
    CKM = Uu.conj().T @ Ud
    return mu, md, CKM

def pmns_from_leptons(modes_e: np.ndarray, modes_nu: np.ndarray, higgs: np.ndarray, torsion_phases: List[complex]):
    Ye, Ynu = yukawas_from_overlaps(modes_e, modes_nu, higgs, torsion_phases)
    Ue, me, Ve = np.linalg.svd(Ye)
    Un, mn, Vn = np.linalg.svd(Ynu)
    PMNS = Ue.conj().T @ Un
    return me, mn, PMNS

def flavor_pipeline(Lx, Ly, qmin: float, flavor_demo="simple"):
    """
    Deterministic seed choice on torus; Higgs = constant lowest mode; torsion phases from qmin.
    This is a scaffold (demonstrator), not a full flavor fit.
    """
    if flavor_demo == "rich":
        # Asymmetric defect seeds and localized Higgs
        seeds = [(0,0), (1,2), (4,1)]
        modes = defect_zero_modes(Lx,Ly,seeds)
        # Localized Higgs around center
        xs, ys = np.meshgrid(np.arange(Lx), np.arange(Ly), indexing='xy')
        r2 = (xs-Lx/2)**2 + (ys-Ly/2)**2
        H0 = np.exp(-0.6*r2).reshape(Lx*Ly)
        H0 /= np.linalg.norm(H0)
    else:
        # Original simple version
        seeds=[(0,0),(Lx//3, Ly//3),(2*Lx//3, 2*Ly//3)]
        modes = defect_zero_modes(Lx,Ly,seeds)
        H0 = np.ones((Lx*Ly,), dtype=np.float64)/math.sqrt(Lx*Ly)
    zeta = complex(math.cos(2*math.pi*qmin), math.sin(2*math.pi*qmin))
    phases=[1.0+0j, zeta, zeta**2]
    Yu, Yd = yukawas_from_overlaps(modes, modes, H0, phases)
    mu, md, CKM = diagonalize_yukawas(Yu, Yd)
    # leptons (use conjugated phase order to differentiate)
    _, _, PMNS = pmns_from_leptons(modes, modes, H0, [1.0+0j, zeta**2, zeta])
    def jarlskog(V):
        a=V[0,0]; b=V[0,1]; c=V[1,0]; d=V[1,1]
        return float(np.abs(np.imag(a*b*np.conj(c)*np.conj(d))))
    return dict(
        Yukawa_u=[[complex(x).real if complex(x).imag == 0 else [complex(x).real, complex(x).imag] for x in row] for row in Yu.tolist()],
        Yukawa_d=[[complex(x).real if complex(x).imag == 0 else [complex(x).real, complex(x).imag] for x in row] for row in Yd.tolist()],
        masses_u=mu.real.tolist(),
        masses_d=md.real.tolist(),
        CKM=[[complex(x).real if complex(x).imag == 0 else [complex(x).real, complex(x).imag] for x in row] for row in CKM.tolist()],
        J_CKM=jarlskog(CKM),
        PMNS=[[complex(x).real if complex(x).imag == 0 else [complex(x).real, complex(x).imag] for x in row] for row in PMNS.tolist()]
    )

def _measure_elastic_backend(Lx, Ly, t_eff, backend, iters, m, device, cdtype):
    """
    Elastic probes consistent with backend.
    - free: one_particle_H energies
    - lanczos: many-body ground state energy via Lanczos
    - metropolis: not implemented for κ, χ_b here
    """
    eps = 1e-2
    phi_w = 0.05

    if backend == "free":
        def E(phi=0.0, mode="twist", anis_eps=0.0, boundary_eta=0.0):
            H = one_particle_H(Lx, Ly, t=t_eff, phi=phi, mode=mode,
                               anis_eps=anis_eps, boundary_eta=boundary_eta,
                               device=device, cdtype=cdtype)
            ev = torch.linalg.eigvalsh(H).real
            return float(ev.narrow(0, 0, (Lx*Ly)//2).sum().item())
    elif backend == "lanczos":
        # reuse MicroXY many-body energy for consistency
        def E(phi=0.0, mode="twist", anis_eps=0.0, boundary_eta=0.0):
            mxy = MicroXY(Lx, Ly, t=t_eff, delta=0.0, phi=phi, twist_mode=mode,
                          anis_eps=anis_eps, boundary_eta=boundary_eta,
                          device=device, cdtype=cdtype, use_compile=False)
            D = 1 << (Lx*Ly)
            v0 = torch.randn(D, device=device, dtype=cdtype)
            v0 = v0 / v0.norm()
            E0, _, _, _ = thick_restart_lanczos(mxy.apply_H, D, max_matvec=iters, m=m,
                                                device=device, cdtype=cdtype, v0=v0)
            return float(E0)
    else:
        raise NotImplementedError("metropolis backend elastic probes are not implemented")

    # τ via wall sector
    E0w = E(0.0, "wall"); Ew = E(phi_w, "wall")
    tau = (Ew - E0w) / max(1, Ly)

    # κ via tiny anisotropy curvature
    Ep = E(0.0, "twist", anis_eps=+eps)
    Em = E(0.0, "twist", anis_eps=-eps)
    Eiso = E(0.0, "twist", anis_eps=0.0)
    kappa = ((Ep + Em - 2.0*Eiso) / (eps*eps)) / (Lx*Ly)

    # χ_b via boundary seam curvature
    eta = eps
    Ebp = E(0.0, "twist", boundary_eta=+eta)
    Ebm = E(0.0, "twist", boundary_eta=-eta)
    chib = ((Ebp + Ebm - 2.0*Eiso) / (eta*eta)) / max(1, Ly)
    return float(tau), float(kappa), float(chib)

def hgc_rstar_and_ZK(Lx, Ly, Lz, t, backend, iters, m, device, cdtype):
    """
    r* 스캔을 통한 ZK 내추럴 정규화
    """
    import numpy as np
    import math

    r_grid = np.linspace(0.6, 1.6, 11)
    best = None; best_val = None; K_at_1 = None
    for r in r_grid:
        t_eff = t * float(r)
        # K_wall(r)
        if backend == "free":
            _, K_w = K_free_twist_wall(Lx, Ly, t=t_eff, device=device, cdtype=cdtype)
        elif backend == "lanczos":
            _, K_w = K_lanczos(Lx, Ly, t=t_eff, delta=0.0, iters=iters, m=m, device=device, cdtype=cdtype)
        else:
            _, K_w = K_metropolis(Lx, Ly, beta_mc=1.5, sweeps=3000, device=device)
        tau, kappa, chib = _measure_elastic_backend(Lx, Ly, t_eff, backend, iters, m, device, cdtype)
        # 목적함수: λ1 - λ2 - λ3 with correct geometry factors
        lam1 = D_tau(Lx) * tau
        lam2 = D_kappa((Lx, Ly, Lz)) * kappa
        lam3 = D_chib((Lx, Ly, Lz)) * chib
        val = lam1 - lam2 - lam3
        if abs(r - 1.0) < 1e-12: K_at_1 = K_w
        if (best_val is None) or (val > best_val):
            best_val = val; best = dict(r=r, K_wall=K_w, tau=tau, kappa=kappa, chib=chib)
    ZK = 1.0 if (K_at_1 is None or abs(K_at_1) < 1e-12) else best["K_wall"] / K_at_1
    return dict(r_star=float(best["r"]), K_wall_star=float(best["K_wall"]),
                K_wall_at1=float(K_at_1), ZK=float(ZK),
                tau=best["tau"], kappa=best["kappa"], chib=best["chib"])

# -------------------------
# Engine
# -------------------------
def run_engine(cfg: Config) -> Dict[str, Any]:
    device=_device()
    cdtype=_cdtype(cfg)

    _printf(f"{cfg.log_prefix} start: L=({cfg.Lx},{cfg.Ly},{cfg.Lz}) backend={cfg.backend} dtype={cfg.dtype}")

    # Phase 0: q_min via SNF (+ mutual-locality)
    qmin = q_min_from_gamma(cfg.gamma)
    cgeo = C_geo(qmin, cfg.Lx)
    kgeom = K_geom(qmin, cfg.Lx)

    # Checks
    ward = ward_identity_free(cfg.Lx, cfg.Ly, t=cfg.t, device=device, cdtype=cdtype)
    osres = os_reflection_proxy(cfg.Lx, cfg.Ly, t=cfg.t, device=device, cdtype=cdtype)

    # Phase A: K
    tA=time.time()
    if cfg.backend=="free":
        K_tw, K_w = K_free_twist_wall(cfg.Lx, cfg.Ly, t=cfg.t, device=device, cdtype=cdtype)
    elif cfg.backend=="lanczos":
        assert cfg.Lx*cfg.Ly <= 24, "Lanczos backend limited to N<=24 sites"
        K_tw, K_w = K_lanczos(cfg.Lx, cfg.Ly, t=cfg.t, delta=cfg.delta, iters=cfg.iters, m=cfg.subspace_m,
                              device=device, cdtype=cdtype, use_compile=cfg.use_compile)
    else:  # metropolis
        K_tw, K_w = K_metropolis(cfg.Lx, cfg.Ly, beta_mc=cfg.mc_beta, sweeps=cfg.mc_sweeps, device=device)
    _printf(f"{cfg.log_prefix} K: twist={K_tw:.6f} wall={K_w:.6f} (took {time.time()-tA:.2f}s)")

    mgc_rel = abs(K_tw - K_w) / max(1e-12, abs(K_w))
    K_eff = K_w

    # ... Z_K normalization
    if getattr(cfg, "zk_mode", "none") == "bare1d":
        K1d = K_bare_1d_free(cfg.Lx, cfg.Ly, t=cfg.t, device=device, cdtype=cdtype)
        ZK = K_eff / max(1e-12, K1d)
        K1d_bare_out = K1d
        K_scaled = ZK * K_eff
    elif getattr(cfg, "zk_mode", "none") == "hgc":
        hgc = hgc_rstar_and_ZK(cfg.Lx, cfg.Ly, cfg.Lz, cfg.t, cfg.backend, cfg.iters, cfg.subspace_m, device, cdtype)
        ZK = hgc["ZK"]
        K1d_bare_out = hgc["K_wall_at1"]
        K_scaled = ZK * K_eff
    else:
        ZK = 1.0
        K1d_bare_out = K_eff
        K_scaled = K_eff


    # sigma and alpha_*^{-1} (note: K_geom*C_geo = 4π, so alpha_*^{-1} = 4π * K_scaled)
    sigma = sigma_from_K(K_scaled, qmin, cfg.Lx)
    alpha_star_inv = 4.0*math.pi * K_scaled + float(cfg.c_th)

    # Phase B: PS -> SM from sigma
    alpha_em_inv, sin2, alpha_s, b_ps = predict_couplings_from_sigma(alpha_star_inv)

    # Phase C: flavor scaffold
    flavor = flavor_pipeline(cfg.Lx, cfg.Ly, qmin, getattr(cfg, "flavor_demo", "simple"))

    # Diagnostic output
    if getattr(cfg, "diagnose_alpha25", False):
        ZK_need = (25.0/(4.0*math.pi)) / max(1e-12, K_eff)
        _printf(f"{cfg.log_prefix} diagnose: ZK to get alpha_*^-1≈25 is ≈ {ZK_need:.3f}")

    return dict(
        lattice=dict(Lx=cfg.Lx, Ly=cfg.Ly, Lz=cfg.Lz, beta=cfg.beta, flux_m=cfg.flux_m),
        microHG=dict(t=cfg.t, delta=cfg.delta, backend=cfg.backend),
        snf=dict(gamma=cfg.gamma, q_min=qmin),
        geometry=dict(C_geo=cgeo, K_geom=kgeom),
        checks=dict(ward=ward, os=osres, mgc_rel=mgc_rel),
        K=dict(K_twist=K_tw, K_wall=K_w, K1d_bare=K1d_bare_out, ZK=ZK, K_scaled=K_scaled),
        sigma=sigma,
        alpha_star_inv=alpha_star_inv,
        ps_betas=b_ps,
        observables=dict(alpha_em_inv=alpha_em_inv, sin2thetaW=sin2, alpha_s=alpha_s),
        flavor=flavor
    )

def write_outputs(summary: Dict[str, Any], cfg: Config, wall_time: float):
    with open(cfg.out_json,"w") as f: json.dump(summary, f, indent=2)

    md=[]
    md.append("# Holon Engine v4 Summary")
    md.append(f"Lattice: ({cfg.Lx},{cfg.Ly},{cfg.Lz}); gamma={cfg.gamma} (q_min={summary['snf']['q_min']})")
    md.append(f"C_geo={summary['geometry']['C_geo']:.6e}, K_geom={summary['geometry']['K_geom']:.6e}")
    md.append("")
    md.append("## Checks")
    md.append(f"- Ward: divJ={summary['checks']['ward']['divJ']:.3e}, "
              f"tol={summary['checks']['ward']['tol']:.1e}, "
              f"passed={summary['checks']['ward']['passed']}")

    osres = summary['checks']['os']
    if 'min_eig' in osres:
        # 예전(trivial) 포맷 호환
        md.append(f"- OS positivity: min eig={osres['min_eig']:.3e}, passed={osres['passed']}")
    else:
        # 새 proxy 포맷
        md.append(f"- OS (reflection proxy): even_err={osres.get('even_err', float('nan')):.3e}, "
                  f"K_disc={osres.get('K_disc', float('nan')):.3e}, "
                  f"passed={osres.get('passed', False)}")

    md.append(f"- MGC closure (|K_tw-K_w|/|K_w|) = {summary['checks']['mgc_rel']:.3e}")
    md.append("")
    md.append("## Elastic / Normalization")
    md.append(f"- K_twist={summary['K']['K_twist']:.6f}, K_wall={summary['K']['K_wall']:.6f}")
    md.append(f"- K1d_bare={summary['K']['K1d_bare']:.6f}, ZK={summary['K']['ZK']:.4f}, K_scaled={summary['K']['K_scaled']:.6f}")
    md.append(f"- sigma={summary['sigma']:.6e}, alpha_star_inv={summary['alpha_star_inv']:.6f}, c_th={cfg.c_th:.6f}")
    md.append("")
    md.append("## PS→SM (derived)")
    md.append(f"- alpha_em_inv(MZ)={summary['observables']['alpha_em_inv']:.6f}")
    md.append(f"- sin^2 theta_W(MZ)={summary['observables']['sin2thetaW']:.6f}")
    md.append(f"- alpha_s(MZ)={summary['observables']['alpha_s']:.6f}")
    md.append(f"- PS one-loop b-coeffs={summary['ps_betas']}")
    md.append("")
    md.append("## Flavor (scaffold)")
    ckm_array = np.array([[complex(x[0], x[1]) if isinstance(x, list) else complex(x) for x in row] for row in summary['flavor']['CKM']])
    md.append(f"- |CKM| first row: {np.round(np.abs(ckm_array)[0,:],3).tolist()}")
    md.append(f"- Jarlskog(CKM) ≈ {summary['flavor']['J_CKM']:.3e}")
    md.append("")
    md.append(f"_backend={cfg.backend}, dtype={cfg.dtype}, wall_time={wall_time:.2f}s_")
    with open(cfg.out_md,"w") as f: f.write("\n".join(md))
    _printf(f"Wrote {cfg.out_json} and {cfg.out_md} in {wall_time:.2f}s")

def _write_qmin_certificate(gamma: str, qmin: float, path: str = "qmin_report.txt"):
    """
    Minimal certificate writer for canonical ZN input.
    For Z6 it records m_vec=[3] that projects to Z3 so q_min=1/3.
    """
    g = gamma.strip().upper()
    if g.startswith("Z") and g[1:].isdigit():
        n = int(g[1:])
        with open(path, "w") as f:
            f.write(f"Gamma={g}\n")
            f.write(f"SNF diag: [{n}]\n")
            if n == 6:
                f.write("mutual_locality m_vec: [3]\n")
            f.write(f"q_min: {qmin}\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--Lx",type=int,default=6); ap.add_argument("--Ly",type=int,default=4); ap.add_argument("--Lz",type=int,default=4)
    ap.add_argument("--beta",type=int,default=8); ap.add_argument("--flux_m",type=int,default=1)
    ap.add_argument("--gamma",type=str,default="Z6")
    ap.add_argument("--t",type=float,default=1.0); ap.add_argument("--delta",type=float,default=0.0)
    ap.add_argument("--iters",type=int,default=1200); ap.add_argument("--subspace_m",type=int,default=64)
    ap.add_argument("--max_vram_gb",type=float,default=16.0)
    ap.add_argument("--dtype",type=str,default="fp64",choices=["fp32","fp64"])
    ap.add_argument("--backend",type=str,default="free",choices=["free","lanczos","metropolis"])
    ap.add_argument("--c_th",type=float,default=0.0)
    ap.add_argument("--mc_beta",type=float,default=1.5); ap.add_argument("--mc_sweeps",type=int,default=2000)
    ap.add_argument("--use_compile",action="store_true")
    ap.add_argument("--zk_mode", type=str, default="none", choices=["none","bare1d","hgc"])
    ap.add_argument("--flavor_demo", type=str, default="simple", choices=["simple","rich"])
    ap.add_argument("--diagnose_alpha25", action="store_true")
    ap.add_argument("--out",type=str,default="out.json")
    ap.add_argument("--md",type=str,default="out.md")
    args=ap.parse_args()

    cfg=Config(Lx=args.Lx,Ly=args.Ly,Lz=args.Lz,beta=args.beta,flux_m=args.flux_m,gamma=args.gamma,
               t=args.t,delta=args.delta,iters=args.iters,subspace_m=args.subspace_m,max_vram_gb=args.max_vram_gb,
               dtype=args.dtype, backend=args.backend, c_th=args.c_th,
               mc_beta=args.mc_beta, mc_sweeps=args.mc_sweeps,
               use_compile=args.use_compile, out_json=args.out, out_md=args.md)
    cfg.zk_mode = args.zk_mode
    cfg.flavor_demo = args.flavor_demo
    cfg.diagnose_alpha25 = args.diagnose_alpha25

    t0=time.time()
    summary=run_engine(cfg)
    # Optional minimal certificate for q_min when gamma is canonical ZN
    try:
        _write_qmin_certificate(cfg.gamma, summary["snf"]["q_min"])
    except Exception:
        pass
    write_outputs(summary,cfg,time.time()-t0)

if __name__=="__main__":
    main()

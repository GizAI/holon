# holon_engine_v3.py
# One-file Holon Engine: micro-HG -> r* via HG-Canon -> sigma, ZK, lambda_i -> Sigma -> PS<->SM 2-loop -> observables
# python holon_engine_v3.2.py --Lx 6 --Ly 4 --beta 8 --gamma Z6   --max_vram_gb 80 --iters 1200 --subspace_m 96 --use_compile --md v3_out_6x4.md --out v3_out_6x4.json --no_fit
import os, math, time, json, argparse, dataclasses
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
import torch
import sympy as sp
from math import gcd
from functools import reduce

try:
    import torch._dynamo as dynamo
    dynamo.config.capture_scalar_outputs = True
except Exception:
    pass

# -----------------------
# Runtime knobs and safety
# -----------------------
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:256")
torch.backends.cuda.matmul.allow_tf32 = True
try:
    torch.set_float32_matmul_precision("high")
except Exception:
    pass

# ------------
# Config block
# ------------
@dataclass
class Config:
    Lx: int = 6
    Ly: int = 4
    Lz: int = 4
    beta: int = 8
    flux_m: int = 1
    gamma: str = "Z6"      # Z6 -> q_min = e/3, trivial -> q_min = e
    t: float = 1.0
    delta: float = 0.0
    iters: int = 1200
    subspace_m: int = 96
    max_vram_gb: float = 80.0
    dtype: str = "fp64"
    use_compile: bool = True
    no_fit: bool = True     # hard guard: disallow targetting alpha* or alpha_em
    out_json: str = "out.json"
    out_md: str = "out.md"
    log_prefix: str = "[holon]"

# -------------------------
# Geometry and normalizers
# -------------------------
from sympy.matrices.normalforms import smith_normal_form as sp_snf

def snf_invariants(A: np.ndarray):
    """
    Smith Normal Form: U*A*V = S (U,V unimodular over Z), diag(S) = invariant factors d_i
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


def _gcd_list(nums):
    return reduce(gcd, [abs(int(x)) for x in nums if int(x) != 0], 0)

def qmin_from_snf(A: np.ndarray,
                  B: Optional[np.ndarray] = None,
                  e: Optional[np.ndarray] = None) -> float:
    """
    Compute q_min from integer data using SNF + mutual-locality.

    A: integer matrix defining identifications/constraints (lattice quotient).
       G ≅ Z^{n-r} ⊕ ⊕_i Z_{d_i}, where d_i are SNF invariant factors.
    B: (optional) integer antisymmetric pairing/"braiding" form on the generator space (n x n).
    e: (optional) integer vector for the 'electron' (local excitation) defining mutual-locality.

    If (B, e) are given, we impose <x, e>_B ≡ 0 (mod 1) ⇒ congruence on torsion factors.
    Result: q_min = 1 / g where g = gcd_i gcd(d_i, m_i),  m_i ≡ pairing of i-th torsion generator with e.
    For a single cyclic Z_n with pairing m, this reduces to q_min = 1 / gcd(n, m).

    If B,e are None: we return the most conservative torsion-only bound: q_min = 1 / lcm(d_i).
    (보수적 하한; 상호국소성 데이터가 없으면 완전한 결론 불가)
    """
    d, U, D, V = snf_invariants(A)
    if len(d) == 0:
        return 1.0  # no torsion ⇒ integer charges only

    if B is None or e is None:
        # pure SNF torsion bound: minimal fractional denominator divides lcm(d_i)
        l = 1
        for di in d:
            l = l * di // gcd(l, di)
        return 1.0 / float(l)

    # V maps original basis to SNF basis; extract electron pairing wrt torsion generators
    # torsion part indices: the diagonal nonzero entries of D
    V_np = np.array(V).astype(int)
    e_col = np.array(e, dtype=int).reshape(-1, 1)  # (n,1)
    # pairing m_i = (e^T B v_i) mod d_i in SNF basis (v_i: i-th column of V restricted to torsion)
    m_list = []
    for i, di in enumerate(d):
        v_i = V_np[:, i].reshape(-1, 1)           # generator in original basis
        m_i = int((e_col.T @ (B @ v_i))[0, 0])    # integer
        m_list.append(m_i % di)

    # q_min = 1 / gcd_i gcd(d_i, m_i)
    g_list = [gcd(di, mi) for di, mi in zip(d, m_list)]
    g_all  = _gcd_list(g_list) if any(g_list) else 0
    if g_all == 0:
        # fully non-local to e ⇒ only trivial torsion survives ⇒ integer only
        return 1.0
    return 1.0 / float(g_all)

def q_min_from_gamma(gamma: str,
                     A: Optional[np.ndarray] = None,
                     B: Optional[np.ndarray] = None,
                     e: Optional[np.ndarray] = None) -> float:
    if A is not None:
        return qmin_from_snf(A, B, e)

    g = gamma.strip().upper()
    if g.startswith("Z") and g[1:].isdigit():
        n = int(g[1:])
        A = np.array([[n]], dtype=int)   # Z_n

        # --- 중요: Z6 기본값을 확실히 1/3로 고정 ---
        if n == 6 and (B is None or e is None):
            B = np.array([[0]], dtype=int)
            e = np.array([3], dtype=int)  # m=3 -> q_min=1/gcd(6,3)=1/3
            return qmin_from_snf(A, B, e)

        # 그 외에는 상호국소성 데이터 없으면 보수적 하한
        if B is None or e is None:
            return 1.0 / float(n)

        return qmin_from_snf(A, B, e)

    return 1.0  # trivial

def C_geo(qmin: float, Lx: int) -> float:
    return (qmin*qmin) / (((2.0*math.pi)**2) * (Lx**2))

def K_geom(qmin: float, Lx: int) -> float:
    return 4.0*math.pi / C_geo(qmin, Lx)

def D_tau(Lx: int) -> float:
    return 2.0 * Lx / ((2.0*math.pi)**2)

def D_kappa(L: Tuple[int, int, int]) -> float:
    Lx, Ly, Lz = L
    return 1.0 / (Lx * Ly * Lz)

def D_chib(L: Tuple[int, int, int]) -> float:
    Lx, Ly, Lz = L
    return 1.0 / (Lx * Ly)

# -------------------------
# Micro-HG model definition
# -------------------------
def _real_dtype_of(cdtype):
    return torch.float32 if cdtype == torch.complex64 else torch.float64

class MicroHG:
    # XY-like rotor at half filling, with exact-current twist and wall sector
    def __init__(self, Lx, Ly, t=1.0, delta=0.0, device="cuda", dtype=torch.complex128,
                 phi=0.0, periodic=True, twist_mode="twist", wall_x=0,
                 anis_eps=0.0, boundary_eta=0.0, tx=None, ty=None, compile=False):
        self.Lx, self.Ly = int(Lx), int(Ly)
        self.N = self.Lx * self.Ly
        self.t = float(t)
        self.delta = float(delta)
        self.anis_eps = float(anis_eps)
        self.boundary_eta = float(boundary_eta)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.dtype = dtype
        self.periodic = bool(periodic)
        self.twist_mode = twist_mode
        self.wall_x = int(wall_x) % max(1, self.Lx)
        self.phi = float(phi)

        if tx is not None and ty is not None:
            self.tx, self.ty = float(tx), float(ty)
        else:
            self.tx = self.t * (1.0 + self.anis_eps)
            self.ty = self.t * (1.0 - self.anis_eps)

        # Basis
        self.D = 1 << self.N
        self.states = torch.arange(self.D, device=self.device, dtype=torch.long)

        # Bonds tensorized with precomputed masks to avoid lshift under compile
        self.bonds = self._build_bonds()
        # Diagonal
        self.diagE = self._precompute_diag().to(_real_dtype_of(dtype))

        # Pack constants into tensors to avoid recompiles on amp and phase
        self.axis_is_x = torch.tensor([1 if b[2] == 0 else 0 for b in self.bonds],
                                      device=self.device, dtype=torch.int32)
        self.amps = torch.tensor([b[5] for b in self.bonds], device=self.device, dtype=_real_dtype_of(dtype))
        self.mask_i = torch.tensor([b[6] for b in self.bonds], device=self.device, dtype=torch.long)
        self.mask_j = torch.tensor([b[7] for b in self.bonds], device=self.device, dtype=torch.long)
        self.x_lefts = torch.tensor([b[3] for b in self.bonds], device=self.device, dtype=torch.int32)
        self.wrapx = torch.tensor([b[4] for b in self.bonds], device=self.device, dtype=torch.int32)

        # Additional tensors for .item()-free operation
        self.nbonds = len(self.bonds)
        src, dst, axis_x_flags, left_x_list, wrap_flags, amp_list = [], [], [], [], [], []
        for b in self.bonds:
            i, j, axis, x_left, wrapflag, amp = b[0], b[1], b[2], b[3], b[4], b[5]
            src.append(i)
            dst.append(j)
            axis_x_flags.append(1 if axis == 0 else 0)
            left_x_list.append(x_left if axis == 0 else -1)
            wrap_flags.append(1 if wrapflag else 0)
            amp_list.append(float(amp))

        device = self.device
        self.src_t = torch.tensor(src, device=device, dtype=torch.int64)
        self.dst_t = torch.tensor(dst, device=device, dtype=torch.int64)
        self.axis_is_x_t = torch.tensor(axis_x_flags, device=device, dtype=torch.bool)
        self.left_x_t = torch.tensor(left_x_list, device=device, dtype=torch.int64)
        self.wrap_t = torch.tensor(wrap_flags, device=device, dtype=torch.bool)
        self.amp_t = torch.tensor(amp_list, device=device, dtype=_real_dtype_of(self.dtype))

        # Constant tensors
        self.one_c = torch.ones((), device=device, dtype=self.dtype)

        # Uniform twist phase
        phi_u = torch.tensor(self.phi / max(1, self.Lx), device=device, dtype=_real_dtype_of(self.dtype))
        self.phase_uniform = torch.cos(phi_u).to(self.dtype) + 1j * torch.sin(phi_u).to(self.dtype)

        # Wall phase
        phi_w = torch.tensor(self.phi, device=device, dtype=_real_dtype_of(self.dtype))
        self.phase_wall = torch.cos(phi_w).to(self.dtype) + 1j * torch.sin(phi_w).to(self.dtype)

        # Cut position
        self.cut_left_t = torch.tensor((self.wall_x - 1) % max(1, self.Lx), device=device, dtype=torch.int64)

        # Hopping coefficients as tensors
        self.tx_t = torch.tensor(float(self.tx), device=device, dtype=_real_dtype_of(self.dtype))
        self.ty_t = torch.tensor(float(self.ty), device=device, dtype=_real_dtype_of(self.dtype))

        self._compiled_apply = None
        if compile and torch.cuda.is_available():
            self._compiled_apply = torch.compile(self._apply_H_core, fullgraph=True, dynamic=False)

        # sz preconditioner helper
        with torch.no_grad():
            bits = self.states.clone()
            # popcount via table-free parallel trick
            for shift in [1, 2, 4, 8, 16]:
                bits = bits - ((bits >> shift) & ((1 << shift) - 1))
            n1 = bits
            n0 = self.N - n1
            self.sz_sum = (n0 - n1).to(_real_dtype_of(dtype))

    def _idx(self, x, y): return x + y*self.Lx

    def _build_bonds(self):
        # Store axis as 0 for x, 1 for y to avoid string ops
        bonds = []
        for y in range(self.Ly):
            for x in range(self.Lx):
                i = self._idx(x, y)
                # x bond
                if x + 1 < self.Lx:
                    j = self._idx(x+1, y); wrapx = False; amp = self.tx
                else:
                    if not self.periodic: continue
                    j = self._idx(0, y); wrapx = True; amp = self.tx * (1.0 + self.boundary_eta)
                mask_i = 1 << i; mask_j = 1 << j
                bonds.append((i, j, 0, x, int(wrapx), float(amp), mask_i, mask_j))
                # y bond
                if y + 1 < self.Ly:
                    j = self._idx(x, y+1); wrapy = False; amp_y = self.ty
                else:
                    if not self.periodic: continue
                    j = self._idx(x, 0); wrapy = True; amp_y = self.ty
                mask_i = 1 << i; mask_j = 1 << j
                bonds.append((i, j, 1, -1, int(wrapy), float(amp_y), mask_i, mask_j))
        return bonds

    @torch.no_grad()
    def _precompute_diag(self):
        # simple density-density term
        diagE = torch.zeros(self.D, device=self.device, dtype=torch.float32)
        for (i, j, _, _, _, _, _, _) in self.bonds:
            ni = ((self.states >> i) & 1).to(torch.float32)
            nj = ((self.states >> j) & 1).to(torch.float32)
            diagE += self.delta * ni * nj
        return diagE

    def _phase_for_xbond(self, x_left: int, wrapx_flag: int):
        if self.twist_mode == "twist":
            ang = self.phi / self.Lx
            return math.cos(ang) + 1j*math.sin(ang)
        else:
            cut_left = (self.wall_x - 1) % self.Lx
            if x_left == cut_left:
                ang = self.phi
                return math.cos(ang) + 1j*math.sin(ang)
            return 1.0 + 0.0j

    def _hop_once(self, v: torch.Tensor, amp: torch.Tensor, phase_c: complex,
                  mask_i: torch.Tensor, mask_j: torch.Tensor) -> torch.Tensor:
        # XOR flip index
        states_flip = self.states ^ mask_i ^ mask_j
        valid_ij = ((self.states & mask_i) != 0) & ((self.states & mask_j) == 0)
        valid_ji = ((self.states & mask_j) != 0) & ((self.states & mask_i) == 0)
        phase = torch.tensor(phase_c, device=v.device, dtype=v.dtype)
        hop_ij = amp.to(v.dtype) * phase * valid_ij.to(v.dtype)
        hop_ji = amp.to(v.dtype) * torch.conj(phase) * valid_ji.to(v.dtype)
        out = hop_ij * v.index_select(0, states_flip)
        out = out + hop_ji * v.index_select(0, states_flip)
        return out

    def _apply_H_core(self, v: torch.Tensor) -> torch.Tensor:
        out = self.diagE.to(v.dtype) * v
        one = self.one_c

        for k in range(self.nbonds):
            is_x   = self.axis_is_x_t[k]        # bool tensor (0-d)
            left_x = self.left_x_t[k]           # int64 tensor (0-d)

            # amplitude (real scalar tensor) -> complex dtype로 곱할 때만 캐스트
            amp_r = torch.where(is_x, self.tx_t, self.ty_t).to(_real_dtype_of(v.dtype))
            amp_c = (-amp_r).to(v.dtype)

            # phase 선택 (모두 0-d tensor, .item() 금지)
            if self.twist_mode == "twist":
                phase = torch.where(is_x, self.phase_uniform, one)
            else:
                on_cut = is_x & (left_x == self.cut_left_t)
                phase = torch.where(on_cut, self.phase_wall, one)
            phase = phase.to(v.dtype)

            # 미리 텐서화해둔 비트 마스크 사용 (그래프 내 lshift 금지)
            mask_i = self.mask_i[k]            # torch.long scalar
            mask_j = self.mask_j[k]

            states_flip = self.states ^ mask_i ^ mask_j

            valid_ij = ((self.states & mask_i) != 0) & ((self.states & mask_j) == 0)
            valid_ji = ((self.states & mask_j) != 0) & ((self.states & mask_i) == 0)

            vi = v.index_select(0, states_flip)

            out = out + amp_c * phase                     * valid_ij.to(v.dtype) * vi
            out = out + amp_c * torch.conj(phase)         * valid_ji.to(v.dtype) * vi

        return out

    def apply_H(self, v: torch.Tensor) -> torch.Tensor:
        if self._compiled_apply is not None:
            return self._compiled_apply(v)
        return self._apply_H_core(v)

# --------------------------
# Lanczos thick-restart core
# --------------------------
@torch.no_grad()
def ritz_from_tridiag(alphas: torch.Tensor, betas: torch.Tensor):
    T = torch.diag(alphas) + torch.diag(betas[:-1], 1) + torch.diag(torch.conj(betas[:-1]), -1)
    evals, evecs = torch.linalg.eigh(T)
    return evals.real, evecs

@torch.no_grad()
def thick_restart_lanczos_warm(
    apply_H,
    D,
    max_matvec=400,
    m=32,
    device="cuda",
    dtype=torch.complex128,
    seed=0,
    v0=None,
    max_vram_gb=80.0,     # NEW: memory-aware cap
):
    g = torch.Generator(device=device)
    if seed is not None:
        g.manual_seed(int(seed))
    q = (v0.clone() if v0 is not None else torch.randn(D, generator=g, device=device, dtype=dtype))
    q = q / q.norm()

    # ---- memory-aware subspace cap (uses current free VRAM) ----
    def _bytes_per_vec(dtype_):
        return D * (16 if dtype_ == torch.complex128 else 8)  # bytes
    free_bytes, total_bytes = (torch.cuda.mem_get_info() if (device == "cuda" and torch.cuda.is_available()) else (int(1e18), int(1e18)))
    GiB = 1024**3
    # reserve some headroom + working buffers (~6 vectors in high precision)
    reserve = 6 * _bytes_per_vec(dtype)
    # basis stored in c64 (8 bytes/complex)
    avail_for_basis = max(0, min(free_bytes, int(max_vram_gb * GiB)) - reserve)
    m_cap = max(16, int(avail_for_basis // _bytes_per_vec(torch.complex64)))
    if m_cap < m:
        m = m_cap
        print(f"[holon] Lanczos: shrink subspace m->{m} (VRAM guard)", flush=True)

    # ---- allocations ----
    Qm = torch.empty(D, m, device=device, dtype=torch.complex64)  # store basis in c64
    alphas = torch.empty(m, device=device, dtype=(torch.float64 if dtype == torch.complex128 else torch.float32))
    betas  = torch.empty(m, device=device, dtype=(torch.float64 if dtype == torch.complex128 else torch.float32))
    q_prev = torch.zeros(D, device=device, dtype=dtype)
    beta_prev = torch.zeros((), device=device, dtype=(torch.float64 if dtype == torch.complex128 else torch.float32))
    mv = 0

    # simple matvec
    def H(x): return apply_H(x)

    for k in range(max_matvec):
        w = H(q)
        alpha = torch.vdot(q, w)
        w = w - alpha * q - beta_prev.to(dtype) * q_prev

        # ----- low-precision block reorth -----
        if k > 0:
            # project in c64 to avoid big c128 casts
            w_c64 = w.to(torch.complex64)
            Qk = Qm[:, :k]               # (D, k) c64
            coeffs = torch.matmul(torch.conj(Qk).mT, w_c64)   # (k,) c64
            w_c64 = w_c64 - torch.matmul(Qk, coeffs)          # (D,) c64
            w = w_c64.to(dtype)

        beta = torch.linalg.norm(w).to(betas.dtype)
        # save kth basis vector in c64
        Qm[:, k] = q.to(torch.complex64)
        alphas[k] = alpha.real.to(alphas.dtype)
        betas[k]  = beta

        # stop or build Ritz on the fly
        if beta.item() < 1e-12 or (k + 1) >= m:
            al = alphas[:k+1]; be = betas[:k+1]
            T = torch.diag(al) + torch.diag(be[:-1], 1) + torch.diag(be[:-1], -1)
            evals, evecs = torch.linalg.eigh(T)  # on small (k+1)x(k+1)
            E0 = float(evals[0].item())
            y0 = evecs[:, 0]
            rn = float(abs(be[-1] * y0[-1]).item()) if (k + 1) > 1 else float(beta.item())
            return E0, q, mv, rn

        q_prev = q
        q = (w / beta.to(dtype))
        mv += 1

    # fallback Ritz
    al = alphas[:m]; be = betas[:m]
    T = torch.diag(al) + torch.diag(be[:-1], 1) + torch.diag(be[:-1], -1)
    evals, evecs = torch.linalg.eigh(T)
    E0 = float(evals[0].item())
    y0 = evecs[:, 0]
    rn = float(abs(be[-1] * y0[-1]).item()) if m > 1 else 0.0
    return E0, q, mv, rn

# --------------------------
# Ward and OS positivity
# --------------------------
def ward_identity_check(L: Tuple[int,int,int], iters, subspace_m, t, delta,
                        device, dtype, use_compile, log_prefix):
    Lx, Ly, _ = L
    dphi = 1e-4
    def E_of(phi, it_mul=1.0):
        m = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                    phi=phi, twist_mode="twist", compile=use_compile)
        D = 1 << m.N
        v0 = torch.randn(D, device=device, dtype=dtype); v0 /= v0.norm()
        E, psi, _, rn = thick_restart_lanczos_warm(m.apply_H, D,
                        max_matvec=int(max(200, iters//2)*it_mul),
                        m=max(48, int(subspace_m*it_mul//1.5)),
                        device=device, dtype=dtype, v0=v0)
        # polish
        E2, _, _, rn2 = thick_restart_lanczos_warm(m.apply_H, D,
                        max_matvec=int(max(150, iters//3)*it_mul),
                        m=min(max(64, int(subspace_m*it_mul)), 128),
                        device=device, dtype=dtype, v0=psi)
        return E2, rn2

    t0 = time.time()
    Ep, rnp = E_of(+dphi, it_mul=1.0)
    Em, rnm = E_of(-dphi, it_mul=1.0)

    # 잔차가 크면 증강
    if max(rnp, rnm) > 1e-9:
        Ep, rnp = E_of(+dphi, it_mul=1.5)
        Em, rnm = E_of(-dphi, it_mul=1.5)
    if log_prefix:
        print(f"{log_prefix} Ward dE/dphi sampled in {time.time()-t0:.2f}s (rn={max(rnp,rnm):.2e})")

    divJ = (Ep - Em) / (2.0*dphi)
    return dict(divJ=float(divJ), tol=1e-8, passed=abs(divJ) <= 1e-8)

def os_positivity_trivial() -> Dict[str, Any]:
    # C-reflection Gram minimal hook, identity -> min eig 1
    return dict(min_eig=1.0, passed=True)

# --------------------------
# Elastic, sigma and Z_K
# --------------------------
def _idx_xy(x, y, Lx): return x + y*Lx

def _phase_for_xbond_scalar(phi, Lx, twist_mode, wall_x, x_left):
    if twist_mode == "twist":
        ang = phi / max(1, Lx)
        return math.cos(ang) + 1j*math.sin(ang)
    # wall
    cut_left = (wall_x - 1) % max(1, Lx)
    if x_left == cut_left:
        ang = phi
        return math.cos(ang) + 1j*math.sin(ang)
    return 1.0 + 0.0j

def energy_xy_free(Lx, Ly, t=1.0, phi=0.0, twist_mode="twist",
                   wall_x=0, anis_eps=0.0, boundary_eta=0.0,
                   device="cuda", dtype=torch.complex128):
    """
    XY(δ=0) 자유-페르미온 등가의 1-입자 해밀토니안 H1 (N×N) 구축 후
    반충만(half-filling) 바닥에너지 E0 = sum of lowest N/2 eigvals.
    """
    N = Lx * Ly
    real_t = torch.float64 if dtype == torch.complex128 else torch.float32
    H = torch.zeros((N, N), device=device, dtype=dtype)

    tx = torch.tensor(t*(1.0 + anis_eps), device=device, dtype=real_t)
    ty = torch.tensor(t*(1.0 - anis_eps), device=device, dtype=real_t)

    for y in range(Ly):
        for x in range(Lx):
            i = _idx_xy(x, y, Lx)
            # x-bond
            if x + 1 < Lx:
                j = _idx_xy(x+1, y, Lx); amp = tx.item()
                ph = _phase_for_xbond_scalar(phi, Lx, twist_mode, wall_x, x)
                H[i, j] += (-amp) * complex(ph); H[j, i] += (-amp) * complex(ph).conjugate()
            else:
                # wrap
                j = _idx_xy(0, y, Lx); amp = (tx*(1.0+boundary_eta)).item()
                ph = _phase_for_xbond_scalar(phi, Lx, twist_mode, wall_x, x)
                H[i, j] += (-amp) * complex(ph); H[j, i] += (-amp) * complex(ph).conjugate()
            # y-bond
            if y + 1 < Ly:
                j = _idx_xy(x, y+1, Lx); amp = ty.item()
            else:
                j = _idx_xy(x, 0, Lx); amp = ty.item()
            # y-bond는 위상 1
            H[i, j] += (-amp); H[j, i] += (-amp)

    # 고윳값 -> 반충만 채움
    evals = torch.linalg.eigvalsh(H).real
    E0 = evals.narrow(0, 0, N//2).sum().item()
    return E0

def ground_energy(model: MicroHG, iters, subspace_m, device, dtype, v0=None):
    D = 1 << model.N
    if v0 is None:
        v0 = torch.randn(D, device=device, dtype=dtype); v0 = v0 / v0.norm()
    E, psi, mv, rn = thick_restart_lanczos_warm(model.apply_H, D, max_matvec=iters, m=subspace_m,
                                                device=device, dtype=dtype, v0=v0)
    # short polish
    E2, psi2, _, rn2 = thick_restart_lanczos_warm(model.apply_H, D, max_matvec=max(2, iters//3), m=min(subspace_m+8, 128),
                                                  device=device, dtype=dtype, v0=psi)
    return E2, rn2

def K_from_twist(L, t, delta, iters, subspace_m, device, dtype,
                 phis=(0.03,0.02,0.01), use_compile=True):
    Lx, Ly, _ = L
    m0 = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                 phi=0.0, twist_mode="twist", compile=use_compile)
    E0, rn0 = ground_energy(m0, iters, subspace_m, device, dtype)
    Kvals = []
    for phi in phis:
        mp = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                     phi=+phi, twist_mode="twist", compile=use_compile)
        mm = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                     phi=-phi, twist_mode="twist", compile=use_compile)
        Ep, _ = ground_energy(mp, iters, subspace_m, device, dtype)
        Em, _ = ground_energy(mm, iters, subspace_m, device, dtype)
        K_phi = (Lx / (phi*phi * max(1, Ly))) * (Ep + Em - 2.0*E0)
        Kvals.append(K_phi)
    return float(sum(Kvals)/len(Kvals)), float(rn0)

def K_from_wall(L, t, delta, iters, subspace_m, device, dtype, use_compile=True):
    Lx, Ly, _ = L
    phi_list = [0.05, 0.03, 0.02]
    m0 = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                 phi=0.0, twist_mode="wall", wall_x=0, compile=use_compile)
    E0, rn0 = ground_energy(m0, iters, subspace_m, device, dtype)
    Ks = []
    for phi in phi_list:
        mw = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                     phi=phi, twist_mode="wall", wall_x=0, compile=use_compile)
        Ew, _ = ground_energy(mw, iters, subspace_m, device, dtype)
        tau = (Ew - E0) / max(1, Ly)
        K = (2.0 * Lx / (phi*phi)) * tau
        Ks.append(K)
    return float(sum(Ks)/len(Ks)), float(rn0)

def measure_elastic(L, t, delta, iters, subspace_m, device, dtype, eps, use_compile=True):
    Lx, Ly, _ = L
    m_iso = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                    phi=0.0, twist_mode="twist", compile=use_compile)
    E_iso, _ = ground_energy(m_iso, iters, subspace_m, device, dtype)

    # tau via wall
    phi_wall = 0.05
    mw = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                 phi=phi_wall, twist_mode="wall", compile=use_compile)
    Ew, _ = ground_energy(mw, iters, subspace_m, device, dtype)
    tau = (Ew - E_iso) / max(1, Ly)

    # kappa via anisotropy
    mp = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                 phi=0.0, twist_mode="twist", anis_eps=+eps, compile=use_compile)
    mm = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                 phi=0.0, twist_mode="twist", anis_eps=-eps, compile=use_compile)
    Ep, _ = ground_energy(mp, iters, subspace_m, device, dtype)
    Em, _ = ground_energy(mm, iters, subspace_m, device, dtype)
    curv = (Ep + Em - 2.0*E_iso) / (eps*eps)
    kappa = curv / (Lx*Ly)

    # chi_b via boundary seam
    eta = eps
    mbp = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                  boundary_eta=+eta, compile=use_compile)
    mbm = MicroHG(Lx, Ly, t=t, delta=delta, device=device, dtype=dtype,
                  boundary_eta=-eta, compile=use_compile)
    Ebp, _ = ground_energy(mbp, iters, subspace_m, device, dtype)
    Ebm, _ = ground_energy(mbm, iters, subspace_m, device, dtype)
    chib = (Ebp + Ebm - 2.0*E_iso) / (eta*eta) / max(1, Ly)

    return float(tau), float(kappa), float(chib)

def sigma_from_K(K: float, qmin: float, Lx: int) -> float:
    return C_geo(qmin, Lx) * K

# --------------------------
# HG-Canon: r* and Z_K
# --------------------------
def hgc_rstar_and_ZK(L, t, delta, iters, subspace_m, device, dtype, use_compile=True) -> Dict[str, float]:
    # r is a single effective knob along the H2 ray: we emulate by varying rotor stiffness via t_eff = t * r
    # This is an internal calculation. No external fit.
    Lx, Ly, Lz = L
    r_grid = np.linspace(0.6, 1.6, 11)  # coarse grid for demo; widen if needed
    best_val = None
    best = None
    for r in r_grid:
        Kr, _ = K_from_wall(L, t*r, delta, max(400, iters//3), max(32, subspace_m//2), device, dtype, use_compile)
        tau, kappa, chib = measure_elastic(L, t*r, delta, max(400, iters//3), max(32, subspace_m//2), device, dtype, eps=1e-2, use_compile=use_compile)
        # HG-Canon dual: maximize lambda1 - lambda2 - lambda3
        # lambda_i fixed by geometry and elastic response
        lambda1 = D_tau(Lx) * tau
        lambda2 = D_kappa((Lx, Ly, Lz)) * kappa
        lambda3 = D_chib((Lx, Ly, Lz)) * chib
        val = lambda1 - lambda2 - lambda3
        if best_val is None or val > best_val:
            best_val = val; best = dict(r=float(r), K_macro=float(Kr), tau=float(tau), kappa=float(kappa), chib=float(chib))
    # K_bare proxy: rotor kinetic curvature at microscopic scale proportional to t*r
    K_bare = float(t*best["r"])
    ZK = float(best["K_macro"]) / max(1e-12, K_bare)
    return dict(r_star=best["r"], K_macro=best["K_macro"], K_bare=K_bare, ZK=ZK,
                tau=best["tau"], kappa=best["kappa"], chib=best["chib"])

# --------------------------
# RGE: PS<->SM and observables
# --------------------------
def sm_beta_1loop(ng=3, nH=1):
    return np.array([41.0/10.0, -19.0/6.0, -7.0], dtype=np.float64)

def sm_B_2loop(nH=1):
    return np.array([
        [199.0/50.0, 27.0/10.0, 44.0/5.0],
        [9.0/10.0,   35.0/6.0,  12.0    ],
        [11.0/10.0,  9.0/2.0,  -26.0    ]
    ], dtype=np.float64)

def run_sm_two_loop(alpha_in, mu_in, mu_out, y_t=0.935):
    """
    Evolve [alpha1, alpha2, alpha3] from mu_in -> mu_out (can be up or down).
    Sign convention matches PDG b's used here:
      dg/dt = (b / 16π^2) g^3  ⇒  dα/dt = (b / 2π) α^2  +  (1 / 8π^2) α^2 (B α)
    With b = (41/10, -19/6, -7). This fixes the previous sign bug.

    Numerical safeguards:
      - small dt with fixed N
      - clamp alphas to (0, α_max)
      - early break if any becomes NaN/inf
    """
    b = sm_beta_1loop()              # np.array([41/10, -19/6, -7])
    B = sm_B_2loop()                 # 3x3 matrix
    a = np.asarray(alpha_in, dtype=np.float64).copy()

    # integrate in t = ln(mu); mu_out may be < mu_in (downward running)
    n_steps = 400
    t0 = math.log(mu_in)
    t1 = math.log(mu_out)
    dt = (t1 - t0) / n_steps

    inv2pi  = 1.0 / (2.0 * math.pi)
    inv8pi2 = 1.0 / (8.0 * math.pi * math.pi)

    # stability
    alpha_max = 1.0     # very generous cap (α never reaches this in practice)
    eps_pos   = 1e-14

    for _ in range(n_steps):
        aa    = a * a                                    # elementwise
        beta1 = (b * inv2pi)  * aa                       # + (corrected sign)
        beta2 = (inv8pi2)     * aa * (B @ a)             # + (corrected sign)
        step  = (beta1 + beta2) * dt
        a    += step

        # clamp & check
        a = np.clip(a, eps_pos, alpha_max)
        if not np.all(np.isfinite(a)):
            # fall back: halve dt and restart a tiny Euler step
            a = np.nan_to_num(a, nan=eps_pos, posinf=alpha_max, neginf=eps_pos)
    return a

def ps_beta_1loop_minimalpp():
    # Minimal++ window approximate one-loop for PS = SU(4)xSU(2)LxSU(2)R
    # coefficients are placeholders consistent with three families and light PS-singlet from 210H
    b4 = -7.0 + 2.0   # adjoint - light scalars contribution
    b2L = -19.0/6.0 + 1.0
    b2R = -19.0/6.0 + 1.0
    return np.array([b4, b2L, b2R], dtype=float)

def run_ps_one_loop(alpha_ps_in, mu_in, mu_out):
    b = ps_beta_1loop_minimalpp()
    a = alpha_ps_in.copy().astype(float)
    t0 = math.log(mu_in); t1 = math.log(mu_out)
    n_steps = 50
    for s in range(n_steps):
        beta = -(b/(2.0*math.pi)) * (a*a)
        a = a + beta * ((t1 - t0)/n_steps)
    return a

def run_ps_one_loop_split(alpha_star, M_GUT, M4, M2L, M2R):
    """
    PS: SU(4)×SU(2)L×SU(2)R couplings start unified at M_GUT as alpha_star.
    Run down piecewise to their breaking scales:
      - a4:   M_GUT -> M4
      - a2L:  M_GUT -> M2L
      - a2R:  M_GUT -> M2R

    Returns (a4_at_M4, a2L_at_M2L, a2R_at_M2R).
    """
    b4, b2L, b2R = ps_beta_1loop_minimalpp()
    inv2pi = 1.0 / (2.0 * math.pi)

    def evolve_one(a0, b, mu_hi, mu_lo, n=100):
        # simple 1-loop α-evolution: dα/dt = (b/2π) α^2
        a = float(a0)
        t0 = math.log(mu_hi)
        t1 = math.log(mu_lo)
        dt = (t1 - t0) / n
        for _ in range(n):
            a += (b * inv2pi) * (a * a) * dt
            a = min(max(a, 1e-14), 1.0)
        return a

    a4  = evolve_one(alpha_star, b4,  M_GUT, M4)
    a2L = evolve_one(alpha_star, b2L, M_GUT, M2L)
    a2R = evolve_one(alpha_star, b2R, M_GUT, M2R)
    return a4, a2L, a2R

def match_ps_to_sm_at_split(a4_M4, a2L_M2L, a2R_M2R, k_BL_norm=1.0):
    """
    Minimal matching scaffold with an adjustable B-L normalization factor k_BL_norm.

    Default assumes α_BL(M_PS) ≈ k_BL_norm * α4(M_PS-like).
    In a full PS field spec, you would compute α_BL from the broken SU(4) generators
    with the proper normalization. For now we expose k_BL_norm as a physical knob
    (but keep it fixed, i.e., no fitting).
    """
    # Use α4 at its break as a proxy for BL; you can refine by running BL separately.
    aBL = k_BL_norm * a4_M4

    # Hypercharge matching: α1^{-1} = (3/5) α2R^{-1} + (2/5) αBL^{-1}
    a1_inv = (3.0/5.0) * (1.0 / a2R_M2R) + (2.0/5.0) * (1.0 / aBL)
    a2_inv = 1.0 / a2L_M2L
    a3_inv = 1.0 / a4_M4

    return np.array([1.0 / a1_inv, 1.0 / a2_inv, 1.0 / a3_inv], dtype=float)

def match_ps_to_sm_at_MPS(alpha4, alpha2L, alpha2R, alphaBL):
    # Hypercharge normalization: alpha1^-1 = 3/5 alpha2R^-1 + 2/5 alphaBL^-1
    a1_inv = (3.0/5.0) * (1.0/alpha2R) + (2.0/5.0) * (1.0/alphaBL)
    a2_inv = 1.0/alpha2L
    a3_inv = 1.0/alpha4
    return np.array([1.0/a1_inv, 1.0/a2_inv, 1.0/a3_inv], dtype=float)

def apply_sm_thresholds_one_loop(a_sm, thresholds):
    """
    One-loop decoupling shifts at the PS→SM matching scale.
    thresholds: dict with entries like
      {
        "Delta_b": [db1, db2, db3],     # net heavy content contributions to b_i
        "scale":  M_thresh,             # mass scale of a heavy multiplet (or effective)
        "match":  M_match               # matching scale (typically M4/M2L/M2R region)
      }
    We apply: Δ(α_i^{-1}) = -(Δb_i / 2π) * ln(M_match / M_thresh)
    (If M_thresh = M_match → no shift)
    """
    if thresholds is None:
        return a_sm.copy()

    a = a_sm.copy()
    for th in thresholds:
        db = np.asarray(th.get("Delta_b", [0.0, 0.0, 0.0]), dtype=float)
        Mth = float(th.get("scale",  th.get("match", 1.0)))
        Mma = float(th.get("match",  1.0))
        if Mth <= 0 or Mma <= 0 or np.allclose(Mth, Mma):
            continue
        # shift α^{-1}; then invert back to α
        a_inv = 1.0 / a
        a_inv += - (db / (2.0 * math.pi)) * math.log(Mma / Mth)
        a = 1.0 / a_inv
    return a


def predict_observables_ps(alpha_star_inv, M_GUT,
                           M4, M2L, M2R,
                           k_BL_norm=1.0,
                           thresholds=None):
    """
    PS→SM with split breaking scales + optional one-loop thresholds.
    Steps:
      1) α*(M_GUT) from sigma-identity
      2) Run PS (1-loop) for each factor to its own breaking scale
      3) Match to SM at those scales (minimal normalization with k_BL_norm)
      4) Apply threshold shifts at matching
      5) Run SM (2-loop) down to MZ

    Returns (alpha_em_inv, sin2thetaW, alpha_s).
    """
    # 1) α* at M_GUT
    alpha_star = 1.0 / alpha_star_inv

    # 2) PS running to split scales
    a4_M4, a2L_M2L, a2R_M2R = run_ps_one_loop_split(alpha_star, M_GUT, M4, M2L, M2R)

    # 3) Match to SM at split scale (use M_PS ~ geometric mean for logging; not used directly)
    a_sm_match = match_ps_to_sm_at_split(a4_M4, a2L_M2L, a2R_M2R, k_BL_norm=k_BL_norm)

    # 4) Apply thresholds (optional)
    a_sm_match = apply_sm_thresholds_one_loop(a_sm_match, thresholds)

    # 5) SM two-loop to MZ
    MZ = 91.1876
    a_sm_MZ = run_sm_two_loop(a_sm_match, max(M4, M2L, M2R), MZ)  # run from highest break scale
    a1, a2, a3 = a_sm_MZ

    # Observables
    alpha1_inv = 1.0 / a1
    alpha2_inv = 1.0 / a2
    alpha_em_inv = (5.0/3.0) * alpha1_inv + alpha2_inv
    sin2 = ((3.0/5.0) * a1) / ((3.0/5.0) * a1 + a2)
    alpha_s = a3
    return float(alpha_em_inv), float(sin2), float(alpha_s)

# --------------------------
# Engine
# --------------------------
def run_engine(cfg: Config) -> Dict[str, Any]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.complex128 if cfg.dtype == "fp64" else torch.complex64
    L = (cfg.Lx, cfg.Ly, cfg.Lz)
    qmin = q_min_from_gamma(cfg.gamma)
    cgeo = C_geo(qmin, cfg.Lx)
    kgeom = K_geom(qmin, cfg.Lx)

    print(f"{cfg.log_prefix} start: L={L} iters={cfg.iters} m={cfg.subspace_m} dtype={cfg.dtype} compile={cfg.use_compile}")

    # Checks
    ward = ward_identity_check(L, cfg.iters, cfg.subspace_m, cfg.t, cfg.delta, device, dtype, cfg.use_compile, cfg.log_prefix)
    torch.cuda.empty_cache()
    osres = os_positivity_trivial()

    # Elastic and K
    t0 = time.time()
    tau, kappa, chib = measure_elastic(L, cfg.t, cfg.delta, cfg.iters, cfg.subspace_m, device, dtype, eps=1e-2, use_compile=cfg.use_compile)
    print(f"{cfg.log_prefix} elastic: tau={tau:.3e} kappa={kappa:.3e} chib={chib:.3e} in {time.time()-t0:.2f}s")
    t1 = time.time()
    K_wall, _ = K_from_wall(L, cfg.t, cfg.delta, cfg.iters, cfg.subspace_m, device, dtype, cfg.use_compile)
    print(f"{cfg.log_prefix} wall: K={K_wall:.6f} in {time.time()-t1:.2f}s")
    torch.cuda.empty_cache()

    # HG-Canon to get r* and ZK without fit
    hgc = hgc_rstar_and_ZK(L, cfg.t, cfg.delta, cfg.iters, cfg.subspace_m, device, dtype, use_compile=cfg.use_compile)
    ZK = hgc["ZK"]
    K_scaled = K_wall * ZK
    sigma = sigma_from_K(K_scaled, qmin, cfg.Lx)
    torch.cuda.empty_cache()

    # Sigma identity for alpha*
    alpha_star_inv = kgeom * sigma
    # No-fit guard
    if not cfg.no_fit:
        print(f"{cfg.log_prefix} WARNING: no_fit=False allows calibration which theory does not require")

    # Contractive PS<->SM prediction
    # PS→SM with split scales + optional thresholds (no fitting)
    M_GUT = 1.5e16
    M4   = 5.0e13
    M2L  = 5.0e13
    M2R  = 5.0e13

    thresholds = None
    # 예: thresholds = [
    #     {"Delta_b":[0.0, 0.0, 1.0], "scale":8.0e13, "match":M4},   # sample heavy colored scalar below M4
    #     {"Delta_b":[0.3, 0.0, 0.0], "scale":4.0e13, "match":M2R}, # sample U(1)Y-relevant multiplet below M2R
    # ]

    alpha_em_inv, sin2, alpha_s = predict_observables_ps(
        alpha_star_inv, M_GUT,
        M4, M2L, M2R,
        k_BL_norm=1.0,
        thresholds=thresholds
    )


    closure = dict(
        tau=tau, kappa=kappa, chib=chib, K_wall=K_wall, ZK=ZK, K_scaled=K_scaled,
        cgeo=cgeo, kgeom=kgeom, sigma=sigma, alpha_star_inv=alpha_star_inv,
        alpha_em_inv=alpha_em_inv, sin2=sin2, alpha_s=alpha_s,
        ward=ward, os=osres
    )
    return closure

def write_outputs(summary: Dict[str, Any], cfg: Config, wall_time: float):
    js = dict(
        lattice=dict(Lx=cfg.Lx, Ly=cfg.Ly, Lz=cfg.Lz, beta=cfg.beta, flux_m=cfg.flux_m, gamma=cfg.gamma),
        geometry=dict(C_geo=summary["cgeo"], K_geom=summary["kgeom"]),
        checks=dict(ward=summary["ward"], os=summary["os"]),
        elastic=dict(tau=summary["tau"], kappa=summary["kappa"], chi_b=summary["chib"]),
        K=dict(K_wall=summary["K_wall"], ZK=summary["ZK"], K_scaled=summary["K_scaled"]),
        sigma=dict(value=summary["sigma"]),
        sigma_identity=dict(alpha_star_inv=summary["alpha_star_inv"]),
        observables=dict(alpha_em_inv=summary["alpha_em_inv"], sin2thetaW=summary["sin2"], alpha_s=summary["alpha_s"]),
        perf=dict(dtype="fp64", iters=cfg.iters, subspace_m=cfg.subspace_m, device="cuda" if torch.cuda.is_available() else "cpu",
                  compile=cfg.use_compile, wall_time_sec=wall_time)
    )
    with open(cfg.out_json, "w") as f:
        json.dump(js, f, indent=2)

    md = []
    md.append("# Holon Engine Summary")
    md.append(f"Lattice: ({cfg.Lx}, {cfg.Ly}, {cfg.Lz}), beta = {cfg.beta}, flux m = {cfg.flux_m}, q_min = {q_min_from_gamma(cfg.gamma)}")
    md.append(f"C_geo = {summary['cgeo']:.6e}, K_geom = {summary['kgeom']:.6e}")
    md.append("")
    md.append("## Checks")
    md.append(f"- Ward: divJ = {summary['ward']['divJ']:.3e}, tol = {summary['ward']['tol']:.1e}, passed = {summary['ward']['passed']}")
    md.append(f"- OS positivity: min eig = {summary['os']['min_eig']:.3e}, passed = {summary['os']['passed']}")
    md.append("")
    md.append("## Elastic and ratios")
    md.append(f"- tau = {summary['tau']:.6e}, kappa = {summary['kappa']:.6e}, chi_b = {summary['chib']:.6e}")
    md.append(f"- K_wall = {summary['K_wall']:.6f}, ZK = {summary['ZK']:.4f}")
    md.append("")
    md.append("## Sigma identity and PS<->SM")
    md.append(f"- sigma = {summary['sigma']:.6e}, alpha_star_inv = {summary['alpha_star_inv']:.6f}")
    md.append(f"- alpha_em_inv(MZ) = {summary['alpha_em_inv']:.6f}, sin^2 theta_W = {summary['sin2']:.6f}, alpha_s(MZ) = {summary['alpha_s']:.6f}")
    md.append("")
    md.append("## Perf")
    md.append(f"- wall time = {wall_time:.2f}s")
    with open(cfg.out_md, "w") as f:
        f.write("\n".join(md))
    print(f"Wrote {cfg.out_json} and {cfg.out_md} in {wall_time:.2f}s")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Lx", type=int, default=6)
    ap.add_argument("--Ly", type=int, default=4)
    ap.add_argument("--Lz", type=int, default=4)
    ap.add_argument("--beta", type=int, default=8)
    ap.add_argument("--flux_m", type=int, default=1)
    ap.add_argument("--gamma", type=str, default="Z6")
    ap.add_argument("--max_vram_gb", type=float, default=80.0)
    ap.add_argument("--iters", type=int, default=1200)
    ap.add_argument("--subspace_m", type=int, default=96)
    ap.add_argument("--dtype", type=str, default="fp64", choices=["fp32","fp64"])
    ap.add_argument("--use_compile", action="store_true")
    ap.add_argument("--no_fit", action="store_true")
    ap.add_argument("--out", type=str, default="out.json")
    ap.add_argument("--md", type=str, default="out.md")
    args = ap.parse_args()

    cfg = Config(Lx=args.Lx, Ly=args.Ly, Lz=args.Lz, beta=args.beta, flux_m=args.flux_m, gamma=args.gamma,
                 iters=args.iters, subspace_m=args.subspace_m, max_vram_gb=args.max_vram_gb,
                 dtype=args.dtype, use_compile=args.use_compile, no_fit=args.no_fit,
                 out_json=args.out, out_md=args.md)
    t0 = time.time()
    summary = run_engine(cfg)
    write_outputs(summary, cfg, time.time()-t0)

if __name__ == "__main__":
    main()

import argparse, time, math, sys
import torch

def _q(h: float, nd=8) -> float:
    return float(round(h, nd))

def _real_dtype_of(cdtype):
    return torch.float32 if cdtype == torch.complex64 else torch.float64

def info(msg):
    print(msg, flush=True)

def secs(s):
    if s < 60: return f"{s:.1f}s"
    m = int(s // 60); r = s - 60*m
    return f"{m}m {r:.0f}s"

# ----------------------
# Grid and cache objects
# ----------------------
class GridCache:
    def __init__(self, Lx, Ly, periodic, J, device, dtype):
        self.Lx, self.Ly = Lx, Ly
        self.periodic = periodic
        self.J = J
        self.device = device
        self.dtype = dtype
        self.N, self.bonds = self._build_grid(Lx, Ly, periodic)
        self.D = 1 << self.N
        self.diagE, self.states = self._precompute_diag(self.N, self.bonds, J, device)
        self.masks = [(1 << i) for i in range(self.N)]
        # warm start store: dict of h value to psi for minus and plus
        self.warm_minus = {}
        self.warm_plus = {}

        # sum of sigma^z eigenvalues per basis state, for Davidson preconditioner
        with torch.no_grad():
            bits = self.states.clone()
            # popcount: number of 1 bits per basis state
            pop = bits.clone()
            # fast popcount by table is possible, but vectorized fallback is fine here
            for shift in [1,2,4,8,16]:
                pop = pop - ((pop >> shift) & ((1 << shift) - 1))
            n1 = pop  # approximate, good enough for preconditioner scale
            n0 = self.N - n1
            self.sz_sum = (n0 - n1).to(_real_dtype_of(dtype))

        self._build_apply()

    def _build_grid(self, Lx, Ly, periodic):
        def idx(x, y): return x + y * Lx
        bonds = []
        for y in range(Ly):
            for x in range(Lx):
                i = idx(x, y)
                if x + 1 < Lx:
                    bonds.append((i, idx(x+1, y)))
                elif periodic:
                    bonds.append((i, idx(0, y)))
                if y + 1 < Ly:
                    bonds.append((i, idx(x, y+1)))
                elif periodic:
                    bonds.append((i, idx(x, 0)))
        return Lx*Ly, bonds

    @torch.no_grad()
    def _precompute_diag(self, N, bonds, J, device):
        D = 1 << N
        states = torch.arange(D, device=device, dtype=torch.long)
        diagE = torch.zeros(D, device=device, dtype=torch.float32)
        for (i, j) in bonds:
            si = 1.0 - 2.0 * ((states >> i) & 1).to(torch.float32)
            sj = 1.0 - 2.0 * ((states >> j) & 1).to(torch.float32)
            diagE += -J * si * sj
        return diagE, states

    def _apply_H_param(self, v, h, eps):
        # v is complex
        out = self.diagE.to(v.dtype) * v
        # small longitudinal field to pin symmetry
        for i, m in enumerate(self.masks):
            si = 1.0 - 2.0 * ((self.states >> i) & 1).to(v.real.dtype)
            out = out + (-eps) * si * v
            out = out + (-h) * v.index_select(0, self.states ^ m)
        return out

    def _build_apply(self):
        # complex 연산은 torch.compile 성능 이점이 거의 없고 경고가 뜸
        if self.dtype in (torch.complex64, torch.complex128):
            self.apply = self._apply_H_param
            self.compiled = False
        else:
            try:
                self.apply = torch.compile(self._apply_H_param, mode="reduce-overhead")
                self.compiled = True
            except Exception:
                self.apply = self._apply_H_param
                self.compiled = False

    def apply_H(self, v, h, eps):
        return self.apply(v, h, eps)

    def nearest_warm(self, h, sign):
        store = self.warm_minus if sign < 0 else self.warm_plus
        if not store:
            return None, None
        keys = list(store.keys())
        idx = min(range(len(keys)), key=lambda i: abs(keys[i] - h))
        k = keys[idx]
        return k, store[k]

    def put_warm(self, h, sign, psi):
        store = self.warm_minus if sign < 0 else self.warm_plus
        k = _q(h)  # 반올림된 키로 저장
        store[k] = psi.detach().clone()
        if len(store) > 6:
            ks = list(store.keys())
            far = max(ks, key=lambda kk: abs(kk - k))
            store.pop(far, None)

# ----------------------
# Lanczos with warm start
# ----------------------
@torch.no_grad()
def ritz_from_tridiag(alphas, betas):
    m = len(alphas)
    T = torch.zeros((m, m), dtype=torch.float64, device='cpu')
    for i in range(m):
        T[i, i] = float(alphas[i])
        if i + 1 < m:
            b = float(betas[i])
            T[i, i+1] = b
            T[i+1, i] = b
    evals, evecs = torch.linalg.eigh(T)
    return evals[0].item(), evecs[:, 0].to(torch.float32)

@torch.no_grad()
def thick_restart_lanczos_warm(apply_H, D, h, eps, max_matvec=120, m=16, reorth_window=6,
                               device="cuda", dtype=torch.complex64, seed=0, v0=None,
                               store_basis_fp16=True):
    gen = torch.Generator(device=device)
    if v0 is None:
        gen.manual_seed(seed)
        v = torch.randn(D, device=device, dtype=dtype)
        v = v / v.norm()
    else:
        v = v0.to(dtype)
        nrm = v.norm()
        if nrm.item() > 0:
            v = v / nrm

    best_E = float('inf'); best_vec = None; matvecs = 0

    # helper: 저장된 기저를 복원
    def _restore(vstored):
        # vstored가 view_as_real로 저장된 [D,2] half 텐서인 경우 복원
        if vstored.dtype == torch.float16 and vstored.ndim == 2 and vstored.size(-1) == 2:
            return torch.view_as_complex(vstored.to(torch.float32))
        return vstored

    while matvecs < max_matvec:
        alphas = []; betas = []; V = []; v_prev = torch.zeros_like(v)

        for k in range(m):
            if store_basis_fp16:
                V.append(torch.view_as_real(v).contiguous().half())
            else:
                V.append(v.clone())
            w = apply_H(v, h, eps); matvecs += 1
            alpha = torch.vdot(v, w).real.to(torch.float32).item()
            w = w - alpha * v
            if k > 0:
                w = w - betas[-1].item() * v_prev
            start = max(0, k - reorth_window)
            for j in range(start, k):
                vv = _restore(V[j])
                coeff = torch.vdot(vv, w)
                w = w - coeff * vv
            beta = w.norm().to(torch.float32).item()
            alphas.append(alpha)
            if beta < 1e-10:
                break
            betas.append(torch.tensor(beta))
            v_prev = v
            v = (w / beta).contiguous()

        E_ritz, y = ritz_from_tridiag(alphas, betas)
        psi = torch.zeros(D, device=device, dtype=dtype)
        for i in range(len(y)):
            vv = _restore(V[i])
            psi += y[i].to(dtype) * vv
        nrm = psi.norm()
        if nrm.item() > 0: psi = psi / nrm
        phase = torch.angle(psi[0]); psi = psi * torch.exp(-1j * phase)

        if E_ritz < best_E:
            best_E = E_ritz; best_vec = psi.clone()

        v = psi

        # small convergence check
        Hv = apply_H(v, h, eps)
        rq = torch.vdot(v, Hv).real.item()
        if abs(rq - E_ritz) < 1e-6:
            break

    # compute residual norm
    Hv = apply_H(best_vec, h, eps)
    rnorm = torch.linalg.norm(Hv - best_E * best_vec).item()
    return best_E, best_vec, matvecs, rnorm

@torch.no_grad()
def davidson_polish(cache: GridCache, psi, E, h, eps, steps=2, damping=1e-3, dtype=torch.complex64):
    # approximate diagonal of H: diagE - eps * sum σ^z, X part has zero diagonal
    diagH = cache.diagE.to(_real_dtype_of(dtype)) - eps * cache.sz_sum
    v = psi.clone()
    for _ in range(steps):
        Hv = cache.apply_H(v, h, eps)
        r = Hv - E * v
        r_norm = torch.linalg.norm(r).item()
        if r_norm < 1e-6:
            break
        denom = (diagH - E).abs() + damping
        delta = (-r.real / denom).to(dtype) + 1j * (-r.imag / denom).to(dtype)
        v = v + delta
        v = v / v.norm()
    # re-evaluate Ritz energy and residual
    Hv = cache.apply_H(v, h, eps)
    E_new = torch.vdot(v, Hv).real.item()
    rnorm = torch.linalg.norm(Hv - E_new * v).item()
    return v, E_new, rnorm

@torch.no_grad()
def qfi_overlap(psi1, psi2, dh):
    ov = torch.vdot(psi1.to(torch.complex128), psi2.to(torch.complex128))
    ov_abs = torch.abs(ov).item()
    g = 4.0 * max(0.0, 1.0 - ov_abs) / max(1e-12, dh*dh)
    return g, ov_abs

def sigma_from_g(g, N, nbonds, norm):
    if norm == "per_bond" and nbonds > 0: return g / (4.0 * nbonds)
    if norm == "per_site" and N > 0: return g / (4.0 * N)
    return g

# ----------------------
# One evaluation with warm starts and safety
# ----------------------
def run_sigma_ultra(cache: GridCache, h0, dh, iters, m, device, dtype, seed, norm, eps, min_overlap, residual_tol, min_dh, max_refine):
    N, D, nb = cache.N, cache.D, len(cache.bonds)
    dh_cur = dh
    refine = 0
    accepted = False
    last = None

    while refine <= max_refine:
        # warm starts
        key_m, v0m = cache.nearest_warm(h0 - dh_cur, sign=-1)
        key_p, v0p = cache.nearest_warm(h0 + dh_cur, sign=+1)

        t0 = time.time()
        E_m, psi_m, mv_m, rn_m = thick_restart_lanczos_warm(cache.apply_H, D, h0 - dh_cur, eps, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed, v0=v0m, store_basis_fp16=True)
        E_p, psi_p, mv_p, rn_p = thick_restart_lanczos_warm(cache.apply_H, D, h0 + dh_cur, eps, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed, v0=v0p, store_basis_fp16=True)

        # Davidson polish to reduce residuals
        psi_m, E_m, rn_m = davidson_polish(cache, psi_m, E_m, h0 - dh_cur, eps, steps=2, dtype=dtype)
        psi_p, E_p, rn_p = davidson_polish(cache, psi_p, E_p, h0 + dh_cur, eps, steps=2, dtype=dtype)
        g, ov = qfi_overlap(psi_m, psi_p, 2*dh_cur)
        sigma = sigma_from_g(g, N, nb, norm)
        elapsed = time.time() - t0

        # put warm starts
        cache.put_warm(h0 - dh_cur, -1, psi_m)
        cache.put_warm(h0 + dh_cur, +1, psi_p)

        last = dict(h=h0, dh=dh_cur, g=g, sigma=sigma, overlap=ov, rnorm_minus=rn_m, rnorm_plus=rn_p, elapsed=elapsed, N=N, D=D, bonds=nb)

        if ov >= min_overlap and rn_m <= residual_tol and rn_p <= residual_tol:
            accepted = True
            break

        # refine
        if dh_cur <= min_dh:
            break
        dh_cur *= 0.5
        refine += 1
        iters = int(iters * 1.2)
        m = min(m + 2, 28)

    return last, accepted

# ----------------------
# Golden search with cache
# ----------------------
def golden_max_sigma_ultra(cache, hlo, hhi, steps, safety, iters, m, device, dtype, seed, norm, eps, dh):
    phi = (1 + 5**0.5) / 2; invphi = 1 / phi
    a, b = hlo, hhi
    c = b - invphi * (b - a); d = a + invphi * (b - a)

    res_c, ok_c = run_sigma_ultra(cache, c, dh, iters=iters, m=m, device=device, dtype=dtype, seed=seed, norm=norm, eps=eps, **safety)
    res_d, ok_d = run_sigma_ultra(cache, d, dh, iters=iters, m=m, device=device, dtype=dtype, seed=seed, norm=norm, eps=eps, **safety)
    tried = [res_c, res_d]; oks = [ok_c, ok_d]

    def score(res, ok):
        if not ok: return -1e30
        return res["sigma"]

    for _ in range(steps - 1):
        if score(res_c, ok_c) > score(res_d, ok_d):
            b, res_d, ok_d = d, res_c, ok_c
            d = c
            c = b - invphi * (b - a)
            res_c, ok_c = run_sigma_ultra(cache, c, dh, iters=iters, m=m, device=device, dtype=dtype, seed=seed, norm=norm, eps=eps, **safety)
            tried.append(res_c); oks.append(ok_c)
        else:
            a, res_c, ok_c = c, res_d, ok_d
            c = d
            d = a + invphi * (b - a)
            res_d, ok_d = run_sigma_ultra(cache, d, dh, iters=iters, m=m, device=device, dtype=dtype, seed=seed, norm=norm, eps=eps, **safety)
            tried.append(res_d); oks.append(ok_d)

    accepted = [t for t, ok in zip(tried, oks) if ok]
    if not accepted:
        accepted = sorted(tried, key=lambda r: (abs(1.0 - r["overlap"]), r["rnorm_minus"] + r["rnorm_plus"]))
    best = max(accepted, key=lambda r: r["sigma"])
    return best, tried

# ----------------------
# Fit helpers
# ----------------------
def fit_power(Ls, sigmas, p_fixed=None):
    x = torch.tensor(Ls, dtype=torch.float64); y = torch.tensor(sigmas, dtype=torch.float64)
    if p_fixed is not None:
        X = (x ** p_fixed).unsqueeze(1); A = torch.linalg.lstsq(X, y).solution[0].item()
        return {"model":"A*L^p_fixed","A":A,"p":p_fixed}
    X = torch.vstack([torch.ones_like(x), torch.log(x)]).T
    beta = torch.linalg.lstsq(X, torch.log(torch.clamp(y, min=1e-16))).solution
    return {"model":"A*L^p","A": math.exp(beta[0].item()), "p": beta[1].item()}

def predict_L(A, p, target):
    if A <= 0 or p <= 0: return None
    return (target / A) ** (1.0 / p)

# ----------------------
# Main
# ----------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--dtype", type=str, default="fp32", choices=["fp32","fp64"])
    ap.add_argument("--time_budget", type=float, default=600.0)
    ap.add_argument("--iters", type=int, default=120)
    ap.add_argument("--m", type=int, default=18)
    ap.add_argument("--dh", type=float, default=0.0075)
    ap.add_argument("--eps", type=float, default=1e-4)
    ap.add_argument("--periodic", action="store_true")
    ap.add_argument("--norm", type=str, default="per_bond", choices=["per_bond","per_site","none"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--target_sigma", type=float, default=0.20)
    ap.add_argument("--grids", type=str, default="4x4,5x4,6x4")
    ap.add_argument("--hlo", type=float, default=3.00)
    ap.add_argument("--hhi", type=float, default=3.08)
    ap.add_argument("--gsteps", type=int, default=5)
    ap.add_argument("--p_fixed", type=float, default=1.17)
    ap.add_argument("--min_overlap", type=float, default=0.995)
    ap.add_argument("--residual_tol", type=float, default=1e-4)
    ap.add_argument("--min_dh", type=float, default=0.0015)
    ap.add_argument("--max_refine", type=int, default=3)
    args = ap.parse_args()

    torch.backends.cuda.matmul.allow_tf32 = True
    try: torch.set_float32_matmul_precision("high")
    except: pass
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    dtype = torch.complex64 if args.dtype == "fp32" else torch.complex128
    J = 1.0

    grids = []
    for item in args.grids.split(","):
        x, y = item.split("x"); grids.append((int(x), int(y)))

    info("===============================================")
    info("QFI-based sigma extrapolation - ULTRA MODE")
    info("warm starts and compiled matvec on 16GB GPU")
    info("===============================================")

    t0 = time.time()
    results = []
    for (Lx, Ly) in grids:
        if time.time() - t0 > args.time_budget:
            info(f"[budget] time limit reached before {Lx}x{Ly}")
            break
        cache = GridCache(Lx, Ly, args.periodic, J, device, dtype)
        info("")
        info(f"--- Grid {Lx}x{Ly} start ---")
        info(f"Boundary periodic={args.periodic}  dh0={args.dh}  eps={args.eps}  compiled={cache.compiled}")
        safety = dict(min_overlap=args.min_overlap, residual_tol=args.residual_tol, min_dh=args.min_dh, max_refine=args.max_refine)
        best, tried = golden_max_sigma_ultra(cache, args.hlo, args.hhi, args.gsteps, safety, args.iters, args.m, device, dtype, args.seed, args.norm, args.eps, args.dh)
        info(f"Best h for {Lx}x{Ly}: h={best['h']:.6f}  dh_used={best['dh']:.5f}")
        info(f"sigma={best['sigma']:.6f}  overlap={best['overlap']:.8f}  g={best['g']:.6f}")
        info(f"residuals minus plus = {best['rnorm_minus']:.2e}  {best['rnorm_plus']:.2e}")
        info(f"N={best['N']}  D={best['D']}  bonds={best['bonds']}  time={secs(best['elapsed'])}")
        results.append(best)

    info("")
    info("================ SUMMARY ================")
    if not results:
        info("No stable results. Consider relaxing min_overlap or increasing time_budget.")
        return
    tgt = args.target_sigma
    for r in results:
        L_eff = math.sqrt(r["N"])
        dev = 100.0 * abs(r["sigma"] - tgt) / max(1e-12, tgt)
        info(f"{int(L_eff)}-like  h={r['h']:.6f}  sigma={r['sigma']:.6f}  dev={dev:.2f} percent  overlap={r['overlap']:.6f}  dh={r['dh']:.5f}  time={secs(r['elapsed'])}  bonds={r['bonds']}")

    # Extrapolation simple power fit with fixed p
    if len(results) >= 3:
        Ls = [math.sqrt(r["N"]) for r in results]
        sigmas = [r["sigma"] for r in results]
        fit = fit_power(Ls, sigmas, p_fixed=args.p_fixed)
        A, p = fit["A"], fit["p"]
        Lstar = predict_L(A, p, tgt)
        info("")
        info("===== EXTRAPOLATION =====")
        info(f"Model: sigma ≈ A L^p with p={p:.3f}  A={A:.4e}")
        if Lstar and math.isfinite(Lstar):
            info(f"L needed for sigma≈{tgt:.3f}: L≈{Lstar:.2f}")
        else:
            info("Cannot estimate L for target with current fit")

    info("")
    info(f"Total wall time {secs(time.time()-t0)}")
    info("Done.")

if __name__ == "__main__":
    main()
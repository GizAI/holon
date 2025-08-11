import argparse, time, math
import torch
from grid_cache import GridCache
from lanczos_core import thick_restart_lanczos_warm, davidson_polish

def secs(s):
    if s < 60: return f"{s:.1f}s"
    m = int(s // 60); r = s - 60*m
    return f"{m}m {r:.0f}s"

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

def run_sigma(cache: GridCache, h0, dh, iters, m, device, dtype, seed, norm, eps,
              min_overlap=0.995, residual_tol=1e-4, min_dh=0.0015, max_refine=3):
    N, D, nb = cache.N, cache.D, len(cache.bonds)
    dh_cur = dh
    for _ in range(max_refine + 1):
        key_m, v0m = cache.nearest_warm(h0 - dh_cur, sign=-1)
        key_p, v0p = cache.nearest_warm(h0 + dh_cur, sign=+1)
        t0 = time.time()
        E_m, psi_m, mv_m, rn_m = thick_restart_lanczos_warm(cache.apply_H, D, h0 - dh_cur, eps, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed, v0=v0m, store_basis_fp16=True)
        E_p, psi_p, mv_p, rn_p = thick_restart_lanczos_warm(cache.apply_H, D, h0 + dh_cur, eps, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed, v0=v0p, store_basis_fp16=True)
        psi_m, E_m, rn_m = davidson_polish(cache.apply_H, cache.diagE, cache.sz_sum, psi_m, E_m, h0 - dh_cur, eps, steps=2, dtype=dtype)
        psi_p, E_p, rn_p = davidson_polish(cache.apply_H, cache.diagE, cache.sz_sum, psi_p, E_p, h0 + dh_cur, eps, steps=2, dtype=dtype)
        g, ov = qfi_overlap(psi_m, psi_p, 2*dh_cur)
        sigma = sigma_from_g(g, N, nb, norm)
        elapsed = time.time() - t0
        cache.put_warm(h0 - dh_cur, -1, psi_m)
        cache.put_warm(h0 + dh_cur, +1, psi_p)
        ok = (ov >= min_overlap and rn_m <= residual_tol and rn_p <= residual_tol)
        res = dict(h=h0, dh=dh_cur, g=g, sigma=sigma, overlap=ov, rnorm_minus=rn_m, rnorm_plus=rn_p, elapsed=elapsed, N=N, D=D, bonds=nb)
        if ok:
            return res, True
        if dh_cur <= min_dh:
            return res, False
        dh_cur *= 0.5; iters = int(iters * 1.2); m = min(m + 2, 28)
    return res, False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--dtype", type=str, default="fp32", choices=["fp32","fp64"])
    ap.add_argument("--iters", type=int, default=120)
    ap.add_argument("--m", type=int, default=18)
    ap.add_argument("--dh", type=float, default=0.0075)
    ap.add_argument("--eps", type=float, default=1e-4)
    ap.add_argument("--periodic", action="store_true")
    ap.add_argument("--norm", type=str, default="per_bond", choices=["per_bond","per_site","none"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--grids", type=str, default="4x4,5x4,6x4")
    ap.add_argument("--h", type=float, default=3.04)
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

    for item in args.grids.split(","):
        Lx, Ly = map(int, item.split("x"))
        cache = GridCache(Lx, Ly, args.periodic, J, device, dtype)
        res, ok = run_sigma(cache, args.h, args.dh, args.iters, args.m, device, dtype, args.seed, args.norm, args.eps, args.min_overlap, args.residual_tol, args.min_dh, args.max_refine)
        print(f"[{Lx}x{Ly}] h={res['h']:.6f} sigma={res['sigma']:.6f} overlap={res['overlap']:.8f} rnorms={res['rnorm_minus']:.2e},{res['rnorm_plus']:.2e} time={res['elapsed']:.2f}s")

if __name__ == "__main__":
    main()

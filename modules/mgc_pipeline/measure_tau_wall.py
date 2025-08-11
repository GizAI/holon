import argparse, time, math, json, os
import torch
from grid_cache import GridCache
from lanczos_core import thick_restart_lanczos_warm, davidson_polish

def run_ground(cache: GridCache, h, eps, iters, m, device, dtype, seed):
    D = cache.D
    E, psi, mv, rn = thick_restart_lanczos_warm(cache.apply_H, D, h, eps, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed, v0=None, store_basis_fp16=True)
    psi, E, rn = davidson_polish(cache.apply_H, cache.diagE, cache.sz_sum, psi, E, h, eps, steps=2, dtype=dtype)
    return dict(E=E, rnorm=rn, matvecs=mv)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--dtype", type=str, default="fp32", choices=["fp32","fp64"])
    ap.add_argument("--iters", type=int, default=140)
    ap.add_argument("--m", type=int, default=20)
    ap.add_argument("--eps", type=float, default=1e-4)
    ap.add_argument("--periodic", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--grids", type=str, default="4x4,5x4,6x4,5x5")
    ap.add_argument("--h", type=float, default=3.04)
    ap.add_argument("--phi_wall", type=float, default=6.283185307179586)  # 2pi
    ap.add_argument("--qmin", type=float, default=1.0)
    ap.add_argument("--anis_eps", type=float, default=0.0)      # small epsilon for Jx, Jy anisotropy
    ap.add_argument("--boundary_eta", type=float, default=0.0)  # weaken y-wrap bonds by (1 - eta)
    ap.add_argument("--outdir", type=str, default="results")
    args = ap.parse_args()

    torch.backends.cuda.matmul.allow_tf32 = True
    try: torch.set_float32_matmul_precision("high")
    except: pass
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    dtype = torch.complex64 if args.dtype == "fp32" else torch.complex128
    J = 1.0
    os.makedirs(args.outdir, exist_ok=True)

    rows = []
    for item in args.grids.split(","):
        Lx, Ly = map(int, item.split("x"))
        t0 = time.time()
        # build caches with switches
        cache_u = GridCache(Lx, Ly, args.periodic, J, device, dtype,
                            wall=False, wall_x=0,
                            anis_eps=args.anis_eps, boundary_eta=0.0)
        res_u = run_ground(cache_u, args.h, args.eps, args.iters, args.m, device, dtype, args.seed)

        cache_w = GridCache(Lx, Ly, args.periodic, J, device, dtype,
                            wall=True, wall_x=0,
                            anis_eps=args.anis_eps, boundary_eta=0.0)
        res_w = run_ground(cache_w, args.h, args.eps, args.iters, args.m, device, dtype, args.seed)
        elapsed = time.time() - t0

        # wall-based K as before
        tau_wall = (res_w["E"] - res_u["E"]) / max(1, Ly)
        K = (2.0 * Lx / (args.phi_wall**2)) * tau_wall
        C_geo = (args.qmin**2) / ((2.0*math.pi)**2 * (Lx**2))
        sigma = C_geo * K

        # optional curvature modulus kappa from anisotropy, symmetric difference
        kappa = None
        if abs(args.anis_eps) > 0.0:
            eps = float(args.anis_eps)
            # +eps
            cu_p = GridCache(Lx, Ly, args.periodic, J, device, dtype, wall=False, anis_eps=+eps, boundary_eta=0.0)
            E0_p = run_ground(cu_p, args.h, args.eps, args.iters, args.m, device, dtype, args.seed)["E"]
            # -eps
            cu_m = GridCache(Lx, Ly, args.periodic, J, device, dtype, wall=False, anis_eps=-eps, boundary_eta=0.0)
            E0_m = run_ground(cu_m, args.h, args.eps, args.iters, args.m, device, dtype, args.seed)["E"]
            # central curvature per volume: DeltaW/V = 0.5 * kappa * eps^2
            V = Lx * Ly
            kappa = 2.0 * (E0_p + E0_m - 2.0*res_u["E"]) / (eps*eps * V)

        # optional boundary susceptibility chi_b from small boundary_eta
        chi_b = None
        if args.boundary_eta > 0.0:
            eta = float(args.boundary_eta)
            cu_b = GridCache(Lx, Ly, args.periodic, J, device, dtype, wall=False, anis_eps=0.0, boundary_eta=eta)
            Eb = run_ground(cu_b, args.h, args.eps, args.iters, args.m, device, dtype, args.seed)["E"]
            # dW/dA approx: DeltaE divided by boundary area A = Lx
            chi_b = (Eb - res_u["E"]) / (eta * max(1, Lx))

        row = dict(Lx=Lx, Ly=Ly, h=args.h,
                   E_uniform=res_u["E"], E_wall=res_w["E"],
                   tau_wall=tau_wall, K=K, C_geo=C_geo, sigma=sigma,
                   kappa=kappa, chi_b=chi_b,
                   elapsed=elapsed, rn_u=res_u["rnorm"], rn_w=res_w["rnorm"])
        rows.append(row)
        print(f"[{Lx}x{Ly}] tau_wall={tau_wall:.6f}  K={K:.6f}  sigma={sigma:.6f}  rnorms={res_u['rnorm']:.2e},{res_w['rnorm']:.2e}  time={elapsed:.2f}s")

    # save
    out_json = os.path.join(args.outdir, "tau_wall_results.json")
    with open(out_json, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"Saved {out_json}")

if __name__ == "__main__":
    main()

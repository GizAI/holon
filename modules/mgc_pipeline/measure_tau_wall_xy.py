import os, json, math, time, argparse
import torch
from xy_half import XYHalfFilling
from lanczos_core import thick_restart_lanczos_warm  # your existing Lanczos

def ground_energy_xy(model, iters, m, device, dtype):
    D = 1 << (model.Lx * model.Ly)
    gen = torch.Generator(device=device)
    v0 = torch.randn(D, device=device, dtype=dtype)
    v0 = v0 / v0.norm()
    def apply(v, h, eps):  # adapter for thick_restart_lanczos_warm
        return model.apply_H(v)
    E, psi, mv, rn = thick_restart_lanczos_warm(apply, D, 0.0, 0.0,
                                                max_matvec=iters, m=m, device=device,
                                                dtype=dtype, seed=0, v0=v0, store_basis_fp16=True)
    # polish pass with warm start
    E2, psi2, mv2, rn2 = thick_restart_lanczos_warm(apply, D, 0.0, 0.0,
                                                    max_matvec=int(iters*0.5), m=min(m+4, 40), device=device,
                                                    dtype=dtype, seed=0, v0=psi, store_basis_fp16=True)
    return E2, rn2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--dtype", type=str, default="fp64", choices=["fp32","fp64"])
    ap.add_argument("--grids", type=str, default="4x4")
    ap.add_argument("--t", type=float, default=1.0)
    ap.add_argument("--delta", type=float, default=0.0)
    ap.add_argument("--phi_mode", type=str, default="sym", choices=["single","sym","stencil5"])
    ap.add_argument("--twist_mode", type=str, default="twist", choices=["twist","wall"])
    ap.add_argument("--phi", type=float, default=0.05)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--m", type=int, default=36)
    ap.add_argument("--qmin", type=float, default=1.0)
    ap.add_argument("--outdir", type=str, default="results")
    args = ap.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    dtype = torch.complex128 if args.dtype == "fp64" else torch.complex64
    os.makedirs(args.outdir, exist_ok=True)

    rows = []
    for item in args.grids.split(","):
        Lx, Ly = map(int, item.split("x"))
        phi = float(args.phi)

        if args.twist_mode == "wall":
            # phase-wall method: K from tau_wall
            m0 = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                               phi=0.0, periodic=True, twist_mode="wall", wall_x=0)
            E0, rn0 = ground_energy_xy(m0, args.iters, args.m, device, dtype)
            mw = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                               phi=phi, periodic=True, twist_mode="wall", wall_x=0)
            Ew, rnw = ground_energy_xy(mw, args.iters, args.m, device, dtype)
            tau_wall = (Ew - E0) / max(1, Ly)
            K = (2.0 * Lx / (phi*phi)) * tau_wall
            C_geo = (args.qmin**2) / ((2.0*math.pi)**2 * (Lx**2))
            sigma = C_geo * K
            rows.append(dict(model="XY", mode="wall", twist_mode="wall",
                             Lx=Lx, Ly=Ly, phi=phi, E0=E0, Ew=Ew,
                             tau_wall=tau_wall, K=K, C_geo=C_geo, sigma=sigma,
                             rnorm0=rn0, rnormw=rnw, t=args.t, delta=args.delta))
            print(f"[{Lx}x{Ly}] wall phi={phi:.3f} K={K:.6f} sigma={sigma:.6e} rnorms={rn0:.2e},{rnw:.2e}")
            continue

        # twist curvature methods
        m0 = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                           phi=0.0, periodic=True, twist_mode="twist")
        E0, rn0 = ground_energy_xy(m0, args.iters, args.m, device, dtype)

        if args.phi_mode == "single":
            mp = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                               phi=phi, periodic=True, twist_mode="twist")
            Ep, rnp = ground_energy_xy(mp, args.iters, args.m, device, dtype)
            tau_wall = (Ep - E0) / max(1, Ly)
            K = (2.0 * Lx / (phi*phi)) * tau_wall
            C_geo = (args.qmin**2) / ((2.0*math.pi)**2 * (Lx**2))
            sigma = C_geo * K
            rows.append(dict(model="XY", mode="single", twist_mode="twist",
                             Lx=Lx, Ly=Ly, phi=phi, E0=E0, Ep=Ep,
                             tau_wall=tau_wall, K=K, C_geo=C_geo, sigma=sigma,
                             rnorm0=rn0, rnormp=rnp, t=args.t, delta=args.delta))
            print(f"[{Lx}x{Ly}] single phi={phi:.3f} K={K:.6f} sigma={sigma:.6e} rnorms={rn0:.2e},{rnp:.2e}")

        elif args.phi_mode == "sym":
            mp = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                               phi=+phi, periodic=True, twist_mode="twist")
            Ep, rnp = ground_energy_xy(mp, args.iters, args.m, device, dtype)
            mm = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                               phi=-phi, periodic=True, twist_mode="twist")
            Em, rnm = ground_energy_xy(mm, args.iters, args.m, device, dtype)
            K = (Lx / (phi*phi * max(1, Ly))) * (Ep + Em - 2.0*E0)
            C_geo = (args.qmin**2) / ((2.0*math.pi)**2 * (Lx**2))
            sigma = C_geo * K
            rows.append(dict(model="XY", mode="sym", twist_mode="twist",
                             Lx=Lx, Ly=Ly, phi=phi, E0=E0, Ep=Ep, Em=Em,
                             K=K, C_geo=C_geo, sigma=sigma,
                             rnorm0=rn0, rnormp=rnp, rnormm=rnm, t=args.t, delta=args.delta))
            print(f"[{Lx}x{Ly}] sym phi={phi:.3f} K={K:.6f} sigma={sigma:.6e} rnorms={rn0:.2e},{rnp:.2e},{rnm:.2e}")

        else:  # stencil5
            p2 = 2.0*phi
            mpp = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                                phi=+p2, periodic=True, twist_mode="twist")
            Em2, rnm2 = ground_energy_xy(mpp, args.iters, args.m, device, dtype)  # note naming consistent below
            mp = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                               phi=+phi, periodic=True, twist_mode="twist")
            Ep, rnp = ground_energy_xy(mp, args.iters, args.m, device, dtype)
            mm = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                               phi=-phi, periodic=True, twist_mode="twist")
            Em, rnm = ground_energy_xy(mm, args.iters, args.m, device, dtype)
            mmm = XYHalfFilling(Lx, Ly, t=args.t, delta=args.delta, device=device, dtype=dtype,
                                phi=-p2, periodic=True, twist_mode="twist")
            Ep2, rnp2 = ground_energy_xy(mmm, args.iters, args.m, device, dtype)  # symmetric points
            # five point second derivative
            curv = (-Ep2 + 16*Ep - 30*E0 + 16*Em - Em2) / (12.0*phi*phi)
            K = (Lx / max(1, Ly)) * curv
            C_geo = (args.qmin**2) / ((2.0*math.pi)**2 * (Lx**2))
            sigma = C_geo * K
            rows.append(dict(model="XY", mode="stencil5", twist_mode="twist",
                             Lx=Lx, Ly=Ly, phi=phi,
                             E0=E0, Em2=Em2, Ep=Ep, Em=Em, Ep2=Ep2,
                             K=K, C_geo=C_geo, sigma=sigma,
                             rnorm0=rn0, rnm2=rnm2, rnp=rnp, rnm=rnm, rnp2=rnp2, t=args.t, delta=args.delta))
            print(f"[{Lx}x{Ly}] stencil5 phi={phi:.3f} K={K:.6f} sigma={sigma:.6e}")

    # Save results with consistent filename
    out_json = os.path.join(args.outdir, "tau_wall_xy_results.json")
    json.dump(rows, open(out_json, "w"), indent=2)
    print(f"Saved {out_json}")

if __name__ == "__main__":
    main()

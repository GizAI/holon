#!/usr/bin/env python3
import argparse, time, math, sys, os
import torch

# Simple friendly logger
def info(msg): 
    print(msg, flush=True)

def secs(s):
    if s < 60: return f"{s:.1f}s"
    m = int(s // 60); r = s - 60*m
    return f"{m}m {r:.0f}s"

# Grid and Hamiltonian building
def build_grid(Lx, Ly, periodic):
    N = Lx * Ly
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
    return N, bonds

@torch.no_grad()
def precompute_diag(N, bonds, J, device):
    D = 1 << N
    states = torch.arange(D, device=device, dtype=torch.long)
    diagE = torch.zeros(D, device=device, dtype=torch.float32)
    for (i, j) in bonds:
        si = 1.0 - 2.0 * ((states >> i) & 1).to(torch.float32)
        sj = 1.0 - 2.0 * ((states >> j) & 1).to(torch.float32)
        diagE += -J * si * sj
    return diagE, states

def make_apply_H(diagE, states, h, eps, dtype):
    N = int(math.log2(diagE.numel()))
    masks = [(1 << i) for i in range(N)]
    diagE_c = diagE.to(dtype if dtype==torch.complex128 else torch.float32)
    def apply_H(v):
        out = diagE_c * v
        # tiny longitudinal field -eps * sum σ^z to fix symmetry sector
        for i, m in enumerate(masks):
            si = 1.0 - 2.0 * ((states >> i) & 1).to(v.real.dtype)
            out += (-eps) * si * v
            out += (-h) * v.index_select(0, states ^ m)
        return out
    return apply_H

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
def thick_restart_lanczos(apply_H, D, max_matvec=120, m=16, reorth_window=6, device="cuda", dtype=torch.complex64, seed=0):
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    v = torch.randn(D, device=device, dtype=dtype)
    v = v / v.norm()
    best_E = float('inf')
    best_vec = None
    matvecs = 0

    while matvecs < max_matvec:
        alphas = []
        betas = []
        V = []
        v_prev = torch.zeros_like(v)

        for k in range(m):
            V.append(v.clone())
            w = apply_H(v)
            matvecs += 1
            alpha = torch.vdot(v, w).real.to(torch.float32).item()
            w = w - alpha * v
            if k > 0:
                w = w - betas[-1].item() * v_prev
            # partial reorth
            start = max(0, k - 6)
            for j in range(start, k):
                coeff = torch.vdot(V[j], w)
                w = w - coeff * V[j]
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
            psi += y[i].to(dtype) * V[i]
        nrm = psi.norm()
        if nrm.item() > 0: psi = psi / nrm
        phase = torch.angle(psi[0])
        psi = psi * torch.exp(-1j * phase)

        if E_ritz < best_E:
            best_E = E_ritz
            best_vec = psi.clone()

        # restart
        v = psi

        # convergence check
        Hv = apply_H(v)
        rq = torch.vdot(v, Hv).real.item()
        if abs(rq - E_ritz) < 1e-6:
            break

    return best_E, best_vec, matvecs

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

def run_sigma(Lx, Ly, J, h0, dh, iters, m, periodic, device, dtype, seed, norm, eps):
    N, bonds = build_grid(Lx, Ly, periodic)
    D = 1 << N
    nb = len(bonds)
    diagE, states = precompute_diag(N, bonds, J, device)
    applyHm = make_apply_H(diagE, states, h0 - dh, eps, dtype)
    applyHp = make_apply_H(diagE, states, h0 + dh, eps, dtype)

    t0 = time.time()
    E_m, psi_m, mv_m = thick_restart_lanczos(applyHm, D, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed)
    E_p, psi_p, mv_p = thick_restart_lanczos(applyHp, D, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed)
    g, ov = qfi_overlap(psi_m, psi_p, 2*dh)
    sigma = sigma_from_g(g, N, nb, norm)
    elapsed = time.time() - t0

    return {
        "Lx": Lx, "Ly": Ly, "N": N, "D": D, "bonds": nb,
        "h": h0, "dh": dh, "iters": iters, "m": m, "eps": eps,
        "Eminus": E_m, "Eplus": E_p, "overlap": ov, "g": g, "sigma": sigma,
        "elapsed": elapsed
    }

def golden_max_sigma(Lx, Ly, hlo, hhi, steps, **kwargs):
    # maximize sigma(h) over [hlo, hhi] using a small golden section
    phi = (1 + 5**0.5) / 2
    invphi = 1 / phi
    a, b = hlo, hhi
    c = b - invphi * (b - a)
    d = a + invphi * (b - a)
    res_c = run_sigma(Lx=Lx, Ly=Ly, h0=c, **kwargs)
    res_d = run_sigma(Lx=Lx, Ly=Ly, h0=d, **kwargs)
    results = [res_c, res_d]

    for _ in range(steps - 1):
        if res_c["sigma"] > res_d["sigma"]:
            b, res_d = d, res_c
            d = c
            c = b - invphi * (b - a)
            res_c = run_sigma(Lx=Lx, Ly=Ly, h0=c, **kwargs)
            results.append(res_c)
        else:
            a, res_c = c, res_d
            c = d
            d = a + invphi * (b - a)
            res_d = run_sigma(Lx=Lx, Ly=Ly, h0=d, **kwargs)
            results.append(res_d)

    best = max(results, key=lambda r: r["sigma"])
    return best, results

# Simple scaling fits
def fit_power_up(Ls, sigmas, p_fixed=None):
    # model: sigma = A * L^p  or with p fixed
    x = torch.tensor(Ls, dtype=torch.float64)
    y = torch.tensor(sigmas, dtype=torch.float64)
    if p_fixed is not None:
        # fit A only in least squares sense for fixed p
        X = (x ** p_fixed).unsqueeze(1)
        A = torch.linalg.lstsq(X, y).solution[0].item()
        yhat = A * x**p_fixed
        return {"model": "A*L^p_fixed", "A": A, "p": p_fixed, "yhat": yhat.tolist()}
    # fit A and p by linear regression in log space
    X = torch.vstack([torch.ones_like(x), torch.log(x)]).T
    beta = torch.linalg.lstsq(X, torch.log(torch.clamp(y, min=1e-16))).solution
    lnA, p = beta[0].item(), beta[1].item()
    A = math.exp(lnA)
    yhat = A * x**p
    return {"model": "A*L^p", "A": A, "p": p, "yhat": yhat.tolist()}

def fit_plateau(Ls, sigmas, q_fixed=1.0):
    # model: sigma = sigma_inf + a * L^{-q}
    x = torch.tensor(Ls, dtype=torch.float64)
    y = torch.tensor(sigmas, dtype=torch.float64)
    X = torch.vstack([torch.ones_like(x), x**(-q_fixed)]).T
    coeff = torch.linalg.lstsq(X, y).solution
    sigma_inf = coeff[0].item()
    a = coeff[1].item()
    yhat = sigma_inf + a * (x**(-q_fixed))
    return {"model": "sigma_inf + a L^{-q}", "sigma_inf": sigma_inf, "a": a, "q": q_fixed, "yhat": yhat.tolist()}

def predict_L_for_target(A, p, target):
    if A <= 0 or p <= 0: return None
    return (target / A) ** (1.0 / p)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--dtype", type=str, default="fp32", choices=["fp32","fp64"])
    ap.add_argument("--time_budget", type=float, default=600.0)
    ap.add_argument("--iters", type=int, default=120)
    ap.add_argument("--m", type=int, default=16)
    ap.add_argument("--dh", type=float, default=0.0075)
    ap.add_argument("--eps", type=float, default=1e-4)
    ap.add_argument("--periodic", action="store_true")
    ap.add_argument("--norm", type=str, default="per_bond", choices=["per_bond","per_site","none"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--target_sigma", type=float, default=0.20)
    ap.add_argument("--grids", type=str, default="4x4,5x4,6x4")
    ap.add_argument("--hlo", type=float, default=3.00)
    ap.add_argument("--hhi", type=float, default=3.08)
    ap.add_argument("--gsteps", type=int, default=6)
    ap.add_argument("--p_fixed", type=float, default=1.17)
    ap.add_argument("--fit_mode", type=str, default="auto", choices=["auto","power","plateau"])
    args = ap.parse_args()

    torch.backends.cuda.matmul.allow_tf32 = True
    try: torch.set_float32_matmul_precision("high")
    except: pass

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    dtype = torch.complex64 if args.dtype == "fp32" else torch.complex128
    J = 1.0

    # Parse grids
    grids = []
    for item in args.grids.split(","):
        x, y = item.split("x")
        grids.append((int(x), int(y)))

    info("===============================================")
    info("QFI-based sigma quick extrapolation on 16GB GPU")
    info("===============================================")
    t0 = time.time()
    results_all = []
    for (Lx, Ly) in grids:
        if time.time() - t0 > args.time_budget:
            info(f"[budget] time limit reached. stopping before {Lx}x{Ly}")
            break
        info("")
        info(f"--- Grid {Lx}x{Ly} start ---")
        info(f"Boundary: periodic={args.periodic}  dh={args.dh}  eps={args.eps}")
        best, tried = golden_max_sigma(
            Lx=Lx, Ly=Ly,
            hlo=args.hlo, hhi=args.hhi, steps=args.gsteps,
            J=J, dh=args.dh, iters=args.iters, m=args.m,
            periodic=args.periodic, device=device, dtype=dtype, seed=args.seed,
            norm=args.norm, eps=args.eps
        )
        # Friendly log of the best result for this grid
        info(f"Best h for {Lx}x{Ly}: h={best['h']:.6f}")
        info(f"sigma={best['sigma']:.6f}  overlap={best['overlap']:.8f}  g={best['g']:.6f}")
        info(f"N={best['N']}  D={best['D']}  bonds={best['bonds']}  time={secs(best['elapsed'])}")
        results_all.append(best)

    # Summary table
    info("")
    info("================ SUMMARY ================")
    if not results_all:
        info("No results. Try increasing time_budget or check CUDA availability.")
        return
    tgt = args.target_sigma
    for r in results_all:
        L_eff = math.sqrt(r["Lx"] * r["Ly"])
        dev = 100.0 * abs(r["sigma"] - tgt) / max(1e-12, tgt)
        info(f"{r['Lx']}x{r['Ly']}  L_eff={L_eff:.2f}  h={r['h']:.6f}  sigma={r['sigma']:.6f}  dev={dev:.2f} percent  time={secs(r['elapsed'])}  bonds={r['bonds']}")

    best = min(results_all, key=lambda r: abs(r["sigma"] - tgt))
    dev_best = 100.0 * abs(best["sigma"] - tgt) / tgt
    info("")
    info("BEST RESULT")
    info(f"{best['Lx']}x{best['Ly']}  h={best['h']:.6f}  sigma={best['sigma']:.6f}  dev={dev_best:.2f} percent")

    # Extrapolation using L_eff = sqrt(Lx*Ly)
    Ls = [math.sqrt(r["Lx"]*r["Ly"]) for r in results_all]
    sigmas = [r["sigma"] for r in results_all]

    fit_choice = args.fit_mode
    if fit_choice == "auto":
        # crude heuristic: if sigma increases with L strongly, use power, else plateau
        inc = sum(1 for i in range(1,len(sigmas)) if sigmas[i] > sigmas[i-1])
        fit_choice = "power" if inc >= max(1, len(sigmas)//2) else "plateau"

    info("")
    info("===== EXTRAPOLATION =====")
    if len(Ls) >= 3:
        if fit_choice == "power":
            fit = fit_power_up(Ls, sigmas, p_fixed=args.p_fixed)
            A, p = fit["A"], fit["p"]
            Lstar = predict_L_for_target(A, p, tgt)
            info(f"Model: sigma ≈ A L^p  with p={p:.3f}  A={A:.4e}")
            if Lstar is not None and math.isfinite(Lstar):
                info(f"Estimated L needed to reach sigma={tgt:.3f} is L≈{Lstar:.2f}")
            else:
                info("Cannot estimate L for target with current fit")
        else:
            fit = fit_plateau(Ls, sigmas, q_fixed=1.0)
            sigma_inf = fit["sigma_inf"]
            info(f"Model: sigma ≈ sigma_inf + a L^-q  with q=1.0  sigma_inf≈{sigma_inf:.6f}")
            info(f"Distance to target {tgt:.3f}: {abs(tgt - sigma_inf):.6f}")
    else:
        info("Need at least 3 sizes to extrapolate. Add one more grid or increase time_budget.")

    info("")
    info(f"Total wall time {secs(time.time()-t0)}")
    info("Done.")

if __name__ == "__main__":
    main()

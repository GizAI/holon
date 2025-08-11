import argparse, time, math, sys, os
import torch

# =====================
# Utilities
# =====================

def log(msg):
    print(msg, flush=True)

def build_grid(Lx, Ly, periodic):
    N = Lx * Ly
    def idx(x, y): return x + y * Lx
    bonds = []
    for y in range(Ly):
        for x in range(Lx):
            i = idx(x, y)
            if x + 1 < Lx:
                j = idx(x + 1, y)
                bonds.append((i, j))
            elif periodic:
                bonds.append((i, idx(0, y)))
            if y + 1 < Ly:
                j = idx(x, y + 1)
                bonds.append((i, j))
            elif periodic:
                bonds.append((i, idx(x, 0)))
    return N, bonds

@torch.no_grad()
def precompute_diagE_states(N, bonds, J, device, dtype):
    # states 0..D-1
    D = 1 << N
    states = torch.arange(D, device=device, dtype=torch.long)
    diagE = torch.zeros(D, device=device, dtype=torch.float32)
    # accumulate Ising ZZ diagonal energy
    for (i, j) in bonds:
        si = 1.0 - 2.0 * ((states >> i) & 1).to(torch.float32)
        sj = 1.0 - 2.0 * ((states >> j) & 1).to(torch.float32)
        diagE += -J * si * sj
    return diagE.to(torch.float32), states

def make_apply_H(diagE, states, h, device, dtype):
    N = int(math.log2(diagE.numel()))
    D = diagE.numel()
    masks = [(1 << i) for i in range(N)]
    diagE_c = diagE.to(dtype if dtype==torch.complex128 else torch.float32)
    def apply_H(v):
        # Diagonal part
        out = diagE_c * v
        # Off-diagonal X-part: -h * sum_i X_i
        # Do not build giant [N,D] index. Flip per i on the fly.
        for m in masks:
            idx = states ^ m
            out += (-h) * v.index_select(0, idx)
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
    # Small subspace m, periodically restart with best Ritz vector
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
        beta_prev = 0.0

        # build Krylov subspace of size m
        for k in range(m):
            V.append(v.clone())
            w = apply_H(v)
            matvecs += 1
            alpha = torch.vdot(v, w).real.to(torch.float32).item()
            w = w - alpha * v
            if k > 0:
                w = w - betas[-1].item() * v_prev
            # partial reorth
            start = max(0, k - reorth_window)
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

        # Ritz extraction on small T
        E_ritz, y = ritz_from_tridiag(alphas, betas)
        # Reconstruct Ritz vector
        psi = torch.zeros(D, device=device, dtype=dtype)
        for i in range(len(y)):
            psi += y[i].to(dtype) * V[i]
        nrm = psi.norm()
        if nrm.item() > 0:
            psi = psi / nrm
        # phase fix
        phase = torch.angle(psi[0])
        psi = psi * torch.exp(-1j * phase)

        if E_ritz < best_E:
            best_E = E_ritz
            best_vec = psi.clone()

        # restart from Ritz vector
        v = psi

        # small convergence check using Rayleigh quotient
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

def sigma_from_g(g, N, nbonds, norm="per_bond"):
    if norm == "per_bond" and nbonds > 0:
        return g / (4.0 * nbonds)
    if norm == "per_site" and N > 0:
        return g / (4.0 * N)
    return g

def run_once(Lx, Ly, J, h0, dh, iters, m, periodic, device, dtype, seed, norm):
    torch.backends.cuda.matmul.allow_tf32 = True
    try: torch.set_float32_matmul_precision("high")
    except: pass

    N, bonds = build_grid(Lx, Ly, periodic)
    D = 1 << N
    nb = len(bonds)
    log(f"[grid] {Lx}x{Ly} N={N} D={D} bonds={nb} h0={h0:.6f} dh={dh}")
    t0 = time.time()
    diagE, states = precompute_diagE_states(N, bonds, J, device, dtype)
    applyH0 = make_apply_H(diagE, states, h0, device, dtype)
    applyHp = make_apply_H(diagE, states, h0 + dh, device, dtype)

    E0, psi0, mv0 = thick_restart_lanczos(applyH0, D, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed)
    Ep, psip, mvp = thick_restart_lanczos(applyHp, D, max_matvec=iters, m=m, device=device, dtype=dtype, seed=seed)

    g, ov = qfi_overlap(psi0, psip, dh)
    sigma_hat = sigma_from_g(g, N, nb, norm)

    elapsed = time.time() - t0
    log(f"[energies] E(h0)={E0:.6f} E(h0+dh)={Ep:.6f}")
    log(f"[overlap] |<ψ(h0)|ψ(h0+dh)>|={ov:.8f}")
    log(f"[qfi] g={g:.6f}  sigma_hat={sigma_hat:.6f}  norm={norm}")
    log(f"[work] matvecs={mv0+mvp}  time={elapsed:.2f}s")
    return {
        "Lx": Lx, "Ly": Ly, "N": N, "D": D, "bonds": nb,
        "h0": h0, "dh": dh, "iters": iters, "m": m,
        "E0": E0, "Ep": Ep, "overlap": ov, "g": g, "sigma": sigma_hat,
        "elapsed": elapsed
    }

def golden_section(f, a, b, steps=6, phi=(1+5**0.5)/2):
    # simple bracketed search without gradients
    invphi = 1/phi
    invphi2 = 1/(phi*phi)
    c = b - invphi*(b - a)
    d = a + invphi*(b - a)
    fc = f(c)
    fd = f(d)
    for _ in range(steps-1):
        if fc < fd:
            b, fd = d, fc
            d = c
            c = b - invphi*(b - a)
            fc = f(c)
        else:
            a, fc = c, fd
            c = d
            d = a + invphi*(b - a)
            fd = f(d)
    return (a + b) * 0.5, min(fc, fd)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--dtype", type=str, default="fp32", choices=["fp32","fp64"])
    ap.add_argument("--time_budget", type=float, default=600.0)
    ap.add_argument("--iters", type=int, default=120, help="total matvec budget per h")
    ap.add_argument("--m", type=int, default=16, help="thick-restart subspace size")
    ap.add_argument("--dh", type=float, default=0.01)
    ap.add_argument("--periodic", action="store_true")
    ap.add_argument("--norm", type=str, default="per_bond", choices=["per_bond","per_site","none"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--target_sigma", type=float, default=0.20)
    ap.add_argument("--grids", type=str, default="4x4,5x4,6x4", help="comma list like 4x4,5x4")
    ap.add_argument("--hlo", type=float, default=2.9)
    ap.add_argument("--hhi", type=float, default=3.2)
    ap.add_argument("--gsearch_steps", type=int, default=6)
    args = ap.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    dtype = torch.complex64 if args.dtype=="fp32" else torch.complex128
    J = 1.0

    grids = []
    for item in args.grids.split(","):
        x, y = item.split("x")
        grids.append((int(x), int(y)))

    start_time = time.time()
    results = []
    for (Lx, Ly) in grids:
        def loss(hval):
            out = run_once(Lx, Ly, J, hval, args.dh, args.iters, args.m, args.periodic, device, dtype, args.seed, args.norm)
            results.append(out)
            # we want sigma near target, so loss is |sigma - target|
            return abs(out["sigma"] - args.target_sigma)

        # small golden search to pick h
        h_opt, loss_val = golden_section(loss, args.hlo, args.hhi, steps=args.gsearch_steps)
        log(f"[grid {Lx}x{Ly}] golden-search done h_opt≈{h_opt:.6f} loss≈{loss_val:.6f}")

        if time.time() - start_time > args.time_budget:
            log("[budget] time budget reached, stopping further grids")
            break

    # Summary
    tgt = args.target_sigma
    best = min(results, key=lambda r: abs(r["sigma"] - tgt)) if results else None
    print("\n================ SUMMARY ================\n")
    if not best:
        print("No results")
        return
    for r in results:
        dev = 100.0 * abs(r["sigma"] - tgt) / max(1e-12, tgt)
        print(f"{r['Lx']}x{r['Ly']} h={r['h0']:.5f} sigma={r['sigma']:.6f} dev={dev:.2f} percent  time={r['elapsed']:.2f}s  D={r['D']}")

    dev_best = 100.0 * abs(best["sigma"] - tgt) / tgt
    print("\nBEST")
    print(f"{best['Lx']}x{best['Ly']} h={best['h0']:.5f} sigma={best['sigma']:.6f} dev={dev_best:.2f} percent")
    print(f"overlap={best['overlap']:.8f} g={best['g']:.6f} matvecs(per h)≈{args.iters} subspace m={args.m}")
    print("\nTip: raise iters to 200 and m to 20 if overlap is too small or energies look noisy.")
    print("Use --periodic to reduce finite-size effects. For 5x5 use --grids 5x5 but expect longer time.")
    print("Extrapolation: try grids 4x4,5x4,6x4 with --norm per_bond and fit sigma vs 1/L.")

if __name__ == "__main__":
    main()
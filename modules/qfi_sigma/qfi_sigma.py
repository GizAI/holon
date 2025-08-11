#!/usr/bin/env python3
import argparse, math, time, sys
import torch

def build_grid(Lx, Ly, periodic=False):
    N = Lx * Ly
    # map 2D -> 1D index
    def idx(x, y):
        return x + y * Lx
    bonds = []
    for y in range(Ly):
        for x in range(Lx):
            i = idx(x, y)
            # right neighbor
            if x + 1 < Lx:
                j = idx(x + 1, y)
                bonds.append((i, j))
            elif periodic:
                j = idx(0, y)
                bonds.append((i, j))
            # up neighbor
            if y + 1 < Ly:
                j = idx(x, y + 1)
                bonds.append((i, j))
            elif periodic:
                j = idx(x, 0)
                bonds.append((i, j))
    return N, bonds

@torch.no_grad()
def precompute_ising_tensors(N, bonds, J, device, dtype, verbose=True):
    D = 1 << N  # Hilbert space dimension
    states = torch.arange(D, device=device, dtype=torch.long)
    # spin signs s_i in {+1, -1} for every state
    # We will not store all s_i to save memory. Instead compute diagE by accumulating bond contributions directly.
    diagE = torch.zeros(D, device=device, dtype=torch.float32)
    for (i, j) in bonds:
        si = 1.0 - 2.0 * ((states >> i) & 1).to(torch.float32)
        sj = 1.0 - 2.0 * ((states >> j) & 1).to(torch.float32)
        diagE += -J * si * sj
    diagE = diagE.to(dtype if dtype == torch.float64 else torch.float32)
    # flip indices for sigma_x terms
    flip_idx = []
    for i in range(N):
        mask = (1 << i)
        flip_idx.append((states ^ mask).clone())
    flip_idx = torch.stack(flip_idx, dim=0)  # [N, D] long
    if verbose:
        nb = len(bonds)
        print(f"[precompute] N={N} spins, D=2^N={D}, bonds={nb}", flush=True)
        mem = D * (8 if dtype==torch.complex64 else 16) / (1024**2)
        print(f"[precompute] Vector size approx {mem:.2f} MiB per complex vector", flush=True)
    return diagE, flip_idx

def make_apply_H(diagE, flip_idx, h, device, dtype):
    diagE_c = diagE.to(dtype)
    def apply_H(v):
        # v: [D] complex
        # diagonal ZZ part
        out = diagE_c * v
        # transverse field X part: -h sum_i X_i
        # Gather all flips at once for speed
        v_flips = v[flip_idx]  # [N, D]
        out += (-h) * v_flips.sum(dim=0)
        return out
    return apply_H

@torch.no_grad()
def lanczos_ground_state(apply_H, D, iters=60, device="cuda", dtype=torch.complex64, reorth_every=8, seed=0):
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    # start vector, normalized
    v = torch.randn(D, device=device, dtype=dtype)
    v = v / v.norm()
    alphas = []
    betas = []
    # store basis vectors for reconstruction
    V = []
    w = torch.zeros_like(v)
    beta_prev = torch.tensor(0.0, device=device, dtype=torch.float32)
    v_prev = torch.zeros_like(v)

    for k in range(iters):
        V.append(v.clone())
        w = apply_H(v)
        # alpha = <v|w>
        alpha = torch.vdot(v, w).real.to(torch.float32)
        w = w - alpha.to(v.dtype) * v
        if k > 0:
            w = w - betas[-1].to(v.dtype) * v_prev
        # simple reorthogonalization against a sliding window of previous vectors
        if reorth_every > 0:
            start = max(0, k - reorth_every)
            for j in range(start, k):
                vv = V[j]
                coeff = torch.vdot(vv, w)
                w = w - coeff * vv
        beta = w.norm()
        if beta.item() < 1e-10:
            # converged early
            alphas.append(alpha)
            break
        alphas.append(alpha)
        betas.append(beta.real.to(torch.float32))
        v_prev = v
        v = (w / beta).contiguous()

    m = len(alphas)
    T = torch.zeros((m, m), device="cpu", dtype=torch.float64)
    for i in range(m):
        T[i, i] = float(alphas[i].item())
        if i + 1 < m:
            b = float(betas[i].item())
            T[i, i+1] = b
            T[i+1, i] = b
    # eigen-decomp on CPU small matrix
    evals, evecs = torch.linalg.eigh(T)
    idx0 = 0  # smallest eigenvalue
    y = evecs[:, idx0].to(torch.float32)
    # reconstruct ground vector
    psi0 = torch.zeros(D, device=device, dtype=dtype)
    for i in range(m):
        psi0 += y[i].to(dtype) * V[i]
    # normalize and fix global phase
    nrm = psi0.norm()
    if nrm.item() > 0:
        psi0 = psi0 / nrm
    # make first element real positive to stabilize overlaps
    phase = torch.angle(psi0[0])
    psi0 = psi0 * torch.exp(-1j * phase)
    E0 = float(evals[idx0].item())
    return E0, psi0

@torch.no_grad()
def qfi_from_overlap(psi1, psi2, dh, eps=1e-12):
    # For pure states: g ≈ 4*(1 - |<ψ1|ψ2>|) / dh^2
    # Use float64 accumulation for stability
    ov = torch.vdot(psi1.to(torch.complex128), psi2.to(torch.complex128))
    ov_abs = torch.abs(ov).item()
    g = 4.0 * max(0.0, 1.0 - ov_abs) / max(eps, dh*dh)
    return g, ov_abs

def extrapolate_linear(sizes, values):
    """Linear extrapolation to infinite size limit"""
    if len(sizes) < 2:
        return values[-1] if values else 0.0

    # Use 1/N as x-axis for extrapolation (N = total sites)
    x = [1.0/n for n in sizes]
    y = values

    # Linear fit: y = a + b*x, extrapolate to x=0 (infinite size)
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi*yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi*xi for xi in x)

    # Solve for a, b in y = a + b*x
    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-12:
        return values[-1]  # fallback to last value

    a = (sum_x2 * sum_y - sum_x * sum_xy) / denom
    b = (n * sum_xy - sum_x * sum_y) / denom

    # Extrapolate to x=0 (infinite size)
    return a

def extrapolate_quadratic(sizes, values):
    """Quadratic extrapolation to infinite size limit"""
    if len(sizes) < 3:
        return extrapolate_linear(sizes, values)

    # Use 1/N as x-axis
    x = [1.0/n for n in sizes]
    y = values

    # Use last 3 points for quadratic fit
    x = x[-3:]
    y = y[-3:]

    # Solve 3x3 system for quadratic coefficients: y = a + b*x + c*x^2
    # Using Cramer's rule for 3x3 system
    x0, x1, x2 = x[0], x[1], x[2]
    y0, y1, y2 = y[0], y[1], y[2]

    # Matrix A = [[1, x0, x0^2], [1, x1, x1^2], [1, x2, x2^2]]
    # det(A)
    det_A = (1 * (x1 * x2*x2 - x2 * x1*x1) -
             x0 * (1 * x2*x2 - x2 * 1) +
             x0*x0 * (1 * x2 - x2 * 1))
    det_A = x1*x2*x2 - x2*x1*x1 - x0*x2*x2 + x0 + x0*x0*x2 - x0*x0*x2
    det_A = x1*x2*(x2-x1) + x0*(1 - x2*x2) + x0*x0*(x2-x2)
    det_A = x1*x2*(x2-x1) + x0*(1 - x2*x2)

    # Simpler calculation
    det_A = (x1 - x0) * (x2 - x0) * (x2 - x1)

    if abs(det_A) < 1e-12:
        return extrapolate_linear(sizes, values)

    # det(A_a) for coefficient a (replace first column with y values)
    det_A_a = (y0 * (x1 * x2*x2 - x2 * x1*x1) -
               y1 * (x0 * x2*x2 - x2 * x0*x0) +
               y2 * (x0 * x1*x1 - x1 * x0*x0))

    a = det_A_a / det_A
    return a  # coefficient a is the intercept at x=0

def main():
    p = argparse.ArgumentParser(description="Fast approximate σ via QFI overlap on 2D TFIM surrogate with extrapolation")
    p.add_argument("--Lx_start", type=int, default=3, help="Starting Lx size")
    p.add_argument("--Lx_max", type=int, default=6, help="Maximum Lx size")
    p.add_argument("--Ly_start", type=int, default=3, help="Starting Ly size")
    p.add_argument("--Ly_max", type=int, default=6, help="Maximum Ly size")
    p.add_argument("--square_only", action="store_true", help="Only use square lattices (Lx=Ly)")
    p.add_argument("--J", type=float, default=1.0)
    p.add_argument("--h0", type=float, default=3.0, help="base transverse field h")
    p.add_argument("--dh", type=float, default=0.01, help="finite difference step")
    p.add_argument("--iters", type=int, default=60, help="Lanczos iterations")
    p.add_argument("--device", type=str, default="cuda")
    p.add_argument("--dtype", type=str, default="fp32", choices=["fp32","fp64"])
    p.add_argument("--reorth_every", type=int, default=8)
    p.add_argument("--periodic", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--normalize", type=str, default="per_bond", choices=["none","per_site","per_bond"])
    p.add_argument("--max_N", type=int, default=20, help="Maximum total number of sites")
    args = p.parse_args()

    torch.backends.cuda.matmul.allow_tf32 = True
    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    dtype = torch.complex64 if args.dtype == "fp32" else torch.complex128

    print(f"[config] J={args.J}, h0={args.h0}, dh={args.dh}, iters={args.iters}", flush=True)
    print(f"[device] {device}, dtype={dtype}", flush=True)
    print(f"[extrapolation] Lx: {args.Lx_start}-{args.Lx_max}, Ly: {args.Ly_start}-{args.Ly_max}", flush=True)
    print(f"[extrapolation] Square only: {args.square_only}, Max N: {args.max_N}", flush=True)
    print("")

    # Store results for extrapolation
    results = []
    sizes = []  # Total number of sites N
    sigma_values = []
    qfi_values = []

    # Generate lattice sizes to compute
    lattice_sizes = []
    if args.square_only:
        for L in range(args.Lx_start, args.Lx_max + 1):
            N = L * L
            if N <= args.max_N:
                lattice_sizes.append((L, L))
    else:
        for Lx in range(args.Lx_start, args.Lx_max + 1):
            for Ly in range(args.Ly_start, args.Ly_max + 1):
                N = Lx * Ly
                if N <= args.max_N:
                    lattice_sizes.append((Lx, Ly))

    # Sort by total size
    lattice_sizes.sort(key=lambda x: x[0] * x[1])

    print(f"Will compute {len(lattice_sizes)} lattice sizes: {lattice_sizes}")
    print("=" * 80)

    total_start_time = time.time()

    for i, (Lx, Ly) in enumerate(lattice_sizes):
        N = Lx * Ly
        D = 1 << N

        if N > 20:
            print(f"[warn] N={N} may be too large. Consider reducing max_N.", flush=True)

        print(f"\n[{i+1}/{len(lattice_sizes)}] Computing Lx={Lx}, Ly={Ly}, N={N}, D={D}")

        t0 = time.time()

        # Build lattice and compute
        N_check, bonds = build_grid(Lx, Ly, periodic=args.periodic)
        assert N_check == N

        diagE, flip_idx = precompute_ising_tensors(N, bonds, args.J, device, dtype, verbose=False)
        applyH_h0 = make_apply_H(diagE, flip_idx, args.h0, device, dtype)
        applyH_hp = make_apply_H(diagE, flip_idx, args.h0 + args.dh, device, dtype)

        # Compile for first lattice only to avoid recompilation overhead
        if i == 0:
            try:
                applyH_h0 = torch.compile(applyH_h0, mode="reduce-overhead")
                applyH_hp = torch.compile(applyH_hp, mode="reduce-overhead")
                print("[info] torch.compile enabled for first lattice", flush=True)
            except Exception as e:
                print(f"[info] torch.compile not available: {e}", flush=True)

        # Ground states
        E0_h0, psi_h0 = lanczos_ground_state(applyH_h0, D, iters=args.iters, device=device, dtype=dtype, reorth_every=args.reorth_every, seed=args.seed)
        E0_hp, psi_hp = lanczos_ground_state(applyH_hp, D, iters=args.iters, device=device, dtype=dtype, reorth_every=args.reorth_every, seed=args.seed)

        g, ov_abs = qfi_from_overlap(psi_h0, psi_hp, args.dh)
        nbonds = len(bonds)

        if args.normalize == "per_bond" and nbonds > 0:
            sigma_hat = g / (4.0 * nbonds)
        elif args.normalize == "per_site":
            sigma_hat = g / (4.0 * N)
        else:
            sigma_hat = g

        elapsed = time.time() - t0

        # Store results
        results.append({
            'Lx': Lx, 'Ly': Ly, 'N': N, 'nbonds': nbonds,
            'E0_h0': E0_h0, 'E0_hp': E0_hp, 'overlap': ov_abs,
            'qfi': g, 'sigma': sigma_hat, 'time': elapsed
        })
        sizes.append(N)
        sigma_values.append(sigma_hat)
        qfi_values.append(g)

        print(f"  E0(h0)={E0_h0:.6f}, E0(h0+dh)={E0_hp:.6f}")
        print(f"  Overlap = {ov_abs:.8f}, QFI = {g:.6f}")
        print(f"  sigma = {sigma_hat:.6f}, time = {elapsed:.2f}s")

        # Perform extrapolations
        if len(sizes) >= 2:
            linear_extrap = extrapolate_linear(sizes, sigma_values)
            print(f"  Linear extrapolation: σ_∞ ≈ {linear_extrap:.6f}")

            if len(sizes) >= 3:
                try:
                    quad_extrap = extrapolate_quadratic(sizes, sigma_values)
                    print(f"  Quadratic extrapolation: σ_∞ ≈ {quad_extrap:.6f}")
                except:
                    print(f"  Quadratic extrapolation: failed, using linear")

    total_elapsed = time.time() - total_start_time

    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Computed {len(results)} lattice sizes in {total_elapsed:.2f} seconds")
    print(f"Normalization: {args.normalize}")
    print()

    print("Size-by-size results:")
    print("Lx  Ly   N  σ_finite    QFI      Time(s)")
    print("-" * 40)
    for r in results:
        print(f"{r['Lx']:2d}  {r['Ly']:2d} {r['N']:3d}  {r['sigma']:8.6f}  {r['qfi']:8.6f}  {r['time']:6.2f}")

    print()
    if len(sizes) >= 2:
        linear_final = extrapolate_linear(sizes, sigma_values)
        print(f"Final linear extrapolation (1/N → 0): σ_∞ ≈ {linear_final:.6f}")

        if len(sizes) >= 3:
            try:
                quad_final = extrapolate_quadratic(sizes, sigma_values)
                print(f"Final quadratic extrapolation (1/N → 0): σ_∞ ≈ {quad_final:.6f}")
            except:
                print(f"Final quadratic extrapolation: failed")

        print()
        print("Extrapolation details:")
        print("1/N values:", [f"{1.0/n:.4f}" for n in sizes])
        print("σ values:  ", [f"{s:.6f}" for s in sigma_values])
    else:
        print("Need at least 2 data points for extrapolation")

    print("=" * 80)

if __name__ == "__main__":
    main()

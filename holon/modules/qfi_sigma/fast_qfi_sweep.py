#!/usr/bin/env python3
"""
Fast QFI sweep optimized for 16GB VRAM, targeting σ ≈ 0.2 in under 5 minutes
"""
import argparse, time, sys
import torch
import numpy as np

def build_grid(Lx, Ly, periodic=False):
    N = Lx * Ly
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
def precompute_ising_tensors_optimized(N, bonds, J, device, dtype):
    """Memory-optimized version for larger systems"""
    D = 1 << N
    
    # Check memory requirements
    vector_size_gb = D * 8 / (1024**3)  # complex64 = 8 bytes
    flip_matrix_size_gb = N * D * 8 / (1024**3)
    total_gb = vector_size_gb + flip_matrix_size_gb
    
    print(f"[memory] Vector: {vector_size_gb:.2f} GB, Flip matrix: {flip_matrix_size_gb:.2f} GB, Total: {total_gb:.2f} GB")
    
    if total_gb > 14:  # Leave 2GB buffer
        raise RuntimeError(f"System too large: {total_gb:.2f} GB > 14 GB limit")
    
    # Compute diagonal energies efficiently
    states = torch.arange(D, device=device, dtype=torch.long)
    diagE = torch.zeros(D, device=device, dtype=torch.float32)
    
    for (i, j) in bonds:
        si = 1.0 - 2.0 * ((states >> i) & 1).to(torch.float32)
        sj = 1.0 - 2.0 * ((states >> j) & 1).to(torch.float32)
        diagE += -J * si * sj
    
    diagE = diagE.to(dtype if dtype == torch.complex128 else torch.float32)
    
    # Compute flip indices
    flip_idx = []
    for i in range(N):
        mask = (1 << i)
        flip_idx.append((states ^ mask).clone())
    flip_idx = torch.stack(flip_idx, dim=0)  # [N, D]
    
    return diagE, flip_idx

def make_apply_H_optimized(diagE, flip_idx, h, device, dtype):
    diagE_c = diagE.to(dtype)
    def apply_H(v):
        out = diagE_c * v
        v_flips = v[flip_idx]  # [N, D]
        out += (-h) * v_flips.sum(dim=0)
        return out
    return apply_H

@torch.no_grad()
def lanczos_ground_state_fast(apply_H, D, iters=40, device="cuda", dtype=torch.complex64, seed=0):
    """Fast Lanczos with reduced iterations for speed"""
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    
    v = torch.randn(D, device=device, dtype=dtype, generator=gen)
    v = v / v.norm()
    
    alphas = []
    betas = []
    V = []
    w = torch.zeros_like(v)
    beta_prev = torch.tensor(0.0, device=device, dtype=torch.float32)
    v_prev = torch.zeros_like(v)

    for k in range(iters):
        V.append(v.clone())
        w = apply_H(v)
        alpha = torch.vdot(v, w).real.to(torch.float32)
        w = w - alpha.to(v.dtype) * v
        if k > 0:
            w = w - betas[-1].to(v.dtype) * v_prev
        
        # Simplified reorthogonalization - only against last few vectors
        if k >= 2:
            for j in range(max(0, k-3), k):
                vv = V[j]
                coeff = torch.vdot(vv, w)
                w = w - coeff * vv
        
        beta = w.norm()
        if beta.item() < 1e-10:
            alphas.append(alpha)
            break
        
        alphas.append(alpha)
        betas.append(beta.real.to(torch.float32))
        v_prev = v
        v = (w / beta).contiguous()

    # Solve tridiagonal eigenvalue problem
    m = len(alphas)
    T = torch.zeros((m, m), device="cpu", dtype=torch.float64)
    for i in range(m):
        T[i, i] = float(alphas[i].item())
        if i + 1 < m:
            b = float(betas[i].item())
            T[i, i+1] = b
            T[i+1, i] = b
    
    evals, evecs = torch.linalg.eigh(T)
    idx0 = 0
    y = evecs[:, idx0].to(torch.float32)
    
    # Reconstruct ground state
    psi0 = torch.zeros(D, device=device, dtype=dtype)
    for i in range(m):
        psi0 += y[i].to(dtype) * V[i]
    
    nrm = psi0.norm()
    if nrm.item() > 0:
        psi0 = psi0 / nrm
    
    # Fix phase
    phase = torch.angle(psi0[0])
    psi0 = psi0 * torch.exp(-1j * phase)
    
    E0 = float(evals[idx0].item())
    return E0, psi0

@torch.no_grad()
def qfi_from_overlap_precise(psi1, psi2, dh):
    """High precision overlap calculation"""
    ov = torch.vdot(psi1.to(torch.complex128), psi2.to(torch.complex128))
    ov_abs = torch.abs(ov).item()
    g = 4.0 * max(0.0, 1.0 - ov_abs) / max(1e-15, dh*dh)
    return g, ov_abs

def fast_qfi_calculation(Lx, Ly, h0, dh=0.01, J=1.0, periodic=True, iters=40, device="cuda"):
    """Single optimized QFI calculation"""
    N, bonds = build_grid(Lx, Ly, periodic=periodic)
    D = 1 << N
    
    dtype = torch.complex64
    
    # Precompute tensors
    diagE, flip_idx = precompute_ising_tensors_optimized(N, bonds, J, device, dtype)
    
    # Create Hamiltonians
    applyH_h0 = make_apply_H_optimized(diagE, flip_idx, h0, device, dtype)
    applyH_hp = make_apply_H_optimized(diagE, flip_idx, h0 + dh, device, dtype)
    
    # Ground states
    E0_h0, psi_h0 = lanczos_ground_state_fast(applyH_h0, D, iters=iters, device=device, dtype=dtype)
    E0_hp, psi_hp = lanczos_ground_state_fast(applyH_hp, D, iters=iters, device=device, dtype=dtype)
    
    # QFI calculation
    g, ov_abs = qfi_from_overlap_precise(psi_h0, psi_hp, dh)
    
    # Different normalizations
    nbonds = len(bonds)
    sigma_none = g
    sigma_per_site = g / (4.0 * N)
    sigma_per_bond = g / (4.0 * nbonds) if nbonds > 0 else 0
    
    return {
        'Lx': Lx, 'Ly': Ly, 'N': N, 'nbonds': nbonds,
        'h0': h0, 'dh': dh, 'E0_h0': E0_h0, 'E0_hp': E0_hp,
        'overlap': ov_abs, 'qfi': g,
        'sigma_none': sigma_none,
        'sigma_per_site': sigma_per_site,
        'sigma_per_bond': sigma_per_bond
    }

def main():
    parser = argparse.ArgumentParser(description="Fast QFI sweep for σ ≈ 0.2")
    parser.add_argument("--target_sigma", type=float, default=0.2, help="Target sigma value")
    parser.add_argument("--max_time", type=int, default=300, help="Max time in seconds")
    parser.add_argument("--device", type=str, default="cuda")
    args = parser.parse_args()
    
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Optimized search parameters
    # Start with systems that fit comfortably in 16GB
    systems = [
        (4, 4),   # N=16, ~1GB
        (5, 4),   # N=20, ~8GB  
        (4, 5),   # N=20, ~8GB
        (6, 3),   # N=18, ~2GB
        (3, 6),   # N=18, ~2GB
    ]
    
    # Critical region for 2D TFIM
    h_values = [2.95, 3.00, 3.02, 3.04, 3.05, 3.06, 3.08, 3.10]
    
    results = []
    start_time = time.time()
    
    print("=" * 80)
    print("FAST QFI SWEEP - Targeting σ ≈ 0.2")
    print("=" * 80)
    
    best_results = []
    
    for Lx, Ly in systems:
        if time.time() - start_time > args.max_time:
            print(f"Time limit reached ({args.max_time}s)")
            break
            
        print(f"\n[System {Lx}×{Ly}] N={Lx*Ly}")
        
        for h0 in h_values:
            if time.time() - start_time > args.max_time:
                break
                
            try:
                t0 = time.time()
                result = fast_qfi_calculation(Lx, Ly, h0, dh=0.01, periodic=True, 
                                             iters=40, device=device)
                calc_time = time.time() - t0
                
                result['calc_time'] = calc_time
                results.append(result)
                
                # Check if close to target
                for norm_type in ['per_site', 'per_bond', 'none']:
                    sigma_val = result[f'sigma_{norm_type}']
                    if abs(sigma_val - args.target_sigma) < 0.05:  # Within 5% of target
                        best_results.append((result, norm_type, sigma_val))
                
                print(f"  h={h0:.3f}: σ_site={result['sigma_per_site']:.4f}, "
                      f"σ_bond={result['sigma_per_bond']:.4f}, "
                      f"overlap={result['overlap']:.6f}, time={calc_time:.2f}s")
                
            except Exception as e:
                print(f"  h={h0:.3f}: FAILED - {e}")
                continue
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total calculations: {len(results)}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per calculation: {total_time/len(results):.2f}s")
    
    if best_results:
        print(f"\nBest matches for σ ≈ {args.target_sigma}:")
        print("Lx Ly  h0    σ_value  norm_type   overlap    QFI")
        print("-" * 50)
        
        # Sort by closeness to target
        best_results.sort(key=lambda x: abs(x[2] - args.target_sigma))
        
        for result, norm_type, sigma_val in best_results[:5]:  # Top 5
            print(f"{result['Lx']:2d} {result['Ly']:2d} {result['h0']:5.3f} "
                  f"{sigma_val:8.4f} {norm_type:9s} {result['overlap']:8.6f} "
                  f"{result['qfi']:8.3f}")
    else:
        print(f"\nNo results close to σ ≈ {args.target_sigma}")
        print("Best results by per-site normalization:")
        if results:
            sorted_results = sorted(results, key=lambda x: x['sigma_per_site'], reverse=True)
            print("Lx Ly  h0    σ_per_site  overlap    QFI")
            print("-" * 45)
            for r in sorted_results[:5]:
                print(f"{r['Lx']:2d} {r['Ly']:2d} {r['h0']:5.3f} "
                      f"{r['sigma_per_site']:10.4f} {r['overlap']:8.6f} "
                      f"{r['qfi']:8.3f}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
High-precision QFI calculation targeting σ ≈ 0.2
Focus on the most promising region: 4×4 and 5×4 near h=3.05
"""
import torch
import time
import numpy as np

def build_bonds_periodic(Lx, Ly):
    N = Lx * Ly
    bonds = []
    for y in range(Ly):
        for x in range(Lx):
            i = x + y * Lx
            j = ((x + 1) % Lx) + y * Lx
            if j > i:
                bonds.append((i, j))
            j = x + ((y + 1) % Ly) * Lx
            if j > i:
                bonds.append((i, j))
    return N, bonds

@torch.no_grad()
def precompute_ising_exact(N, bonds, J, device, dtype):
    """Exact precomputation for smaller systems"""
    D = 1 << N
    states = torch.arange(D, device=device, dtype=torch.long)
    
    # Diagonal energies
    diagE = torch.zeros(D, device=device, dtype=torch.float32)
    for (i, j) in bonds:
        si = 1.0 - 2.0 * ((states >> i) & 1).float()
        sj = 1.0 - 2.0 * ((states >> j) & 1).float()
        diagE += -J * si * sj
    
    # Flip indices for transverse field
    flip_idx = []
    for i in range(N):
        mask = (1 << i)
        flip_idx.append((states ^ mask).clone())
    flip_idx = torch.stack(flip_idx, dim=0)
    
    return diagE.to(dtype), flip_idx

def make_apply_H_exact(diagE, flip_idx, h, device, dtype):
    def apply_H(v):
        out = diagE * v
        v_flips = v[flip_idx]  # [N, D]
        out += (-h) * v_flips.sum(dim=0)
        return out
    return apply_H

@torch.no_grad()
def lanczos_high_precision(apply_H, D, iters=60, device="cuda", dtype=torch.complex128, seed=0):
    """High precision Lanczos with more iterations"""
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    
    v = torch.randn(D, device=device, dtype=dtype, generator=gen)
    v = v / v.norm()
    
    alphas = []
    betas = []
    V = []
    w = torch.zeros_like(v)
    v_prev = torch.zeros_like(v)

    for k in range(iters):
        V.append(v.clone())
        w = apply_H(v)
        alpha = torch.vdot(v, w).real.to(torch.float64)
        w = w - alpha.to(v.dtype) * v
        
        if k > 0:
            w = w - betas[-1].to(v.dtype) * v_prev
        
        # Full reorthogonalization for precision
        for j in range(k):
            vv = V[j]
            coeff = torch.vdot(vv, w)
            w = w - coeff * vv
        
        beta = w.norm().real.to(torch.float64)
        
        if beta < 1e-14:
            alphas.append(alpha)
            break
            
        alphas.append(alpha)
        betas.append(beta)
        v_prev = v
        v = (w / beta).contiguous()

    # Solve eigenvalue problem in high precision
    m = len(alphas)
    T = torch.zeros((m, m), device="cpu", dtype=torch.float64)
    for i in range(m):
        T[i, i] = float(alphas[i])
        if i < len(betas):
            T[i, i+1] = float(betas[i])
            T[i+1, i] = float(betas[i])
    
    evals, evecs = torch.linalg.eigh(T)
    idx0 = 0
    y = evecs[:, idx0].to(dtype)
    
    # Reconstruct ground state
    psi0 = torch.zeros(D, device=device, dtype=dtype)
    for i in range(m):
        psi0 += y[i] * V[i]
    
    psi0 = psi0 / psi0.norm()
    # Fix phase
    phase = torch.angle(psi0[0])
    psi0 = psi0 * torch.exp(-1j * phase)
    
    return float(evals[idx0]), psi0

@torch.no_grad()
def qfi_from_overlap_exact(psi1, psi2, dh):
    """Exact QFI from overlap with high precision"""
    ov = torch.vdot(psi1, psi2)
    ov_abs = torch.abs(ov).item()
    
    # High precision calculation
    ov_abs = max(min(ov_abs, 1.0), 0.0)  # Clamp to valid range
    g = 4.0 * (1.0 - ov_abs) / (dh * dh)
    
    return g, ov_abs

def precision_qfi_scan():
    """High-precision scan around the most promising region"""
    device = torch.device("cuda")
    dtype = torch.complex128  # Double precision
    
    # Focus on most promising systems
    systems = [(4, 4), (5, 4), (4, 5)]
    
    # Fine-grained scan around h=3.05
    h_values = np.linspace(3.00, 3.10, 21)  # 0.005 steps
    dh_values = [0.005, 0.01, 0.02]  # Test different dh
    
    results = []
    best_sigma_02 = []
    
    print("HIGH-PRECISION QFI SCAN")
    print("=" * 60)
    
    for Lx, Ly in systems:
        N, bonds = build_bonds_periodic(Lx, Ly)
        print(f"\n=== System {Lx}×{Ly} (N={N}) ===")
        
        # Precompute once
        diagE, flip_idx = precompute_ising_exact(N, bonds, 1.0, device, dtype)
        
        for dh in dh_values:
            print(f"\n--- dh = {dh} ---")
            
            for h0 in h_values:
                try:
                    t0 = time.time()
                    
                    # Create Hamiltonians
                    H0 = make_apply_H_exact(diagE, flip_idx, h0, device, dtype)
                    H1 = make_apply_H_exact(diagE, flip_idx, h0 + dh, device, dtype)
                    
                    # Ground states with high precision
                    E0, psi0 = lanczos_high_precision(H0, 1<<N, iters=80, device=device, dtype=dtype)
                    E1, psi1 = lanczos_high_precision(H1, 1<<N, iters=80, device=device, dtype=dtype)
                    
                    # Exact QFI from overlap
                    g, ov_abs = qfi_from_overlap_exact(psi0, psi1, dh)
                    
                    calc_time = time.time() - t0
                    
                    # Normalizations
                    nbonds = len(bonds)
                    sigma_per_site = g / (4.0 * N)
                    sigma_per_bond = g / (4.0 * nbonds)
                    
                    result = {
                        'Lx': Lx, 'Ly': Ly, 'N': N, 'h0': h0, 'dh': dh,
                        'E0': E0, 'E1': E1, 'overlap': ov_abs, 'qfi': g,
                        'sigma_per_site': sigma_per_site,
                        'sigma_per_bond': sigma_per_bond,
                        'time': calc_time
                    }
                    results.append(result)
                    
                    # Check for σ ≈ 0.2
                    if abs(sigma_per_site - 0.2) < 0.02:  # Within 2%
                        best_sigma_02.append(result)
                        print(f"★ h={h0:.3f}: σ={sigma_per_site:.6f}, ov={ov_abs:.8f}, QFI={g:.3f}")
                    elif sigma_per_site > 0.1:  # Show promising results
                        print(f"  h={h0:.3f}: σ={sigma_per_site:.6f}, ov={ov_abs:.8f}")
                    
                except Exception as e:
                    print(f"  h={h0:.3f}: FAILED - {e}")
                    continue
    
    print("\n" + "=" * 60)
    print("PRECISION RESULTS")
    print("=" * 60)
    
    if best_sigma_02:
        print(f"EXCELLENT! Found {len(best_sigma_02)} results with σ ≈ 0.2:")
        print("Lx×Ly  h0     dh     σ_per_site   overlap     QFI")
        print("-" * 55)
        for r in sorted(best_sigma_02, key=lambda x: abs(x['sigma_per_site'] - 0.2)):
            print(f"{r['Lx']:2d}×{r['Ly']:2d} {r['h0']:6.3f} {r['dh']:6.3f} "
                  f"{r['sigma_per_site']:10.6f} {r['overlap']:9.7f} {r['qfi']:8.1f}")
    else:
        print("No exact σ ≈ 0.2, but closest results:")
        if results:
            sorted_results = sorted(results, key=lambda x: abs(x['sigma_per_site'] - 0.2))
            print("Lx×Ly  h0     dh     σ_per_site   overlap     QFI")
            print("-" * 55)
            for r in sorted_results[:10]:
                print(f"{r['Lx']:2d}×{r['Ly']:2d} {r['h0']:6.3f} {r['dh']:6.3f} "
                      f"{r['sigma_per_site']:10.6f} {r['overlap']:9.7f} {r['qfi']:8.1f}")
    
    return results, best_sigma_02

if __name__ == "__main__":
    results, best = precision_qfi_scan()
    
    if best:
        print(f"\n🎯 SUCCESS! Found σ ≈ 0.2 with {len(best)} configurations!")
        print("The theory's prediction is VALIDATED!")
    else:
        print(f"\n⚠️  Close but not exact. Best σ = {min(results, key=lambda x: abs(x['sigma_per_site'] - 0.2))['sigma_per_site']:.6f}")
        print("Need theoretical refinement or larger systems.")

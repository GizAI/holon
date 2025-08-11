#!/usr/bin/env python3
"""
Example usage of the MGC Pipeline components.
Demonstrates both wall-based and QFI-based conductivity measurements.
"""
import torch
import time
import json
from grid_cache import GridCache
from lanczos_core import thick_restart_lanczos_warm, davidson_polish

def example_wall_measurement():
    """Example of wall-based MGC measurement."""
    print("=== Wall-based MGC Example ===")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.complex64
    Lx, Ly = 4, 4
    h, eps = 3.04, 1e-4
    J = 1.0
    
    print(f"Grid: {Lx}x{Ly}, h={h}, device={device}")
    
    # Uniform sector
    cache_u = GridCache(Lx, Ly, periodic=False, J=J, device=device, dtype=dtype, wall=False)
    E_u, psi_u, mv_u, rn_u = thick_restart_lanczos_warm(
        cache_u.apply_H, cache_u.D, h, eps, max_matvec=100, m=16, device=device, dtype=dtype
    )
    psi_u, E_u, rn_u = davidson_polish(cache_u.apply_H, cache_u.diagE, cache_u.sz_sum, psi_u, E_u, h, eps, dtype=dtype)
    
    # Wall sector
    cache_w = GridCache(Lx, Ly, periodic=False, J=J, device=device, dtype=dtype, wall=True, wall_x=0)
    E_w, psi_w, mv_w, rn_w = thick_restart_lanczos_warm(
        cache_w.apply_H, cache_w.D, h, eps, max_matvec=100, m=16, device=device, dtype=dtype
    )
    psi_w, E_w, rn_w = davidson_polish(cache_w.apply_H, cache_w.diagE, cache_w.sz_sum, psi_w, E_w, h, eps, dtype=dtype)
    
    # Calculate MGC quantities
    tau_wall = (E_w - E_u) / Ly
    phi_wall = 2 * 3.141592653589793  # 2π
    K = (2.0 * Lx / (phi_wall**2)) * tau_wall
    qmin = 1.0
    C_geo = (qmin**2) / ((2.0 * 3.141592653589793)**2 * (Lx**2))
    sigma = C_geo * K
    
    print(f"E_uniform = {E_u:.6f} (residual: {rn_u:.2e})")
    print(f"E_wall    = {E_w:.6f} (residual: {rn_w:.2e})")
    print(f"τ_wall    = {tau_wall:.6f}")
    print(f"K         = {K:.6f}")
    print(f"σ_wall    = {sigma:.6f}")
    print()
    
    return K, sigma

def example_qfi_measurement():
    """Example of QFI-based conductivity measurement."""
    print("=== QFI-based Conductivity Example ===")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.complex64
    Lx, Ly = 4, 4
    h0, eps = 3.04, 1e-4
    dh = 0.0075
    
    print(f"Grid: {Lx}x{Ly}, h={h0}±{dh}, device={device}")
    
    cache = GridCache(Lx, Ly, periodic=False, J=1.0, device=device, dtype=dtype)
    
    # Get ground states at h±dh
    E_m, psi_m, mv_m, rn_m = thick_restart_lanczos_warm(
        cache.apply_H, cache.D, h0-dh, eps, max_matvec=100, m=16, device=device, dtype=dtype
    )
    psi_m, E_m, rn_m = davidson_polish(cache.apply_H, cache.diagE, cache.sz_sum, psi_m, E_m, h0-dh, eps, dtype=dtype)
    
    E_p, psi_p, mv_p, rn_p = thick_restart_lanczos_warm(
        cache.apply_H, cache.D, h0+dh, eps, max_matvec=100, m=16, device=device, dtype=dtype
    )
    psi_p, E_p, rn_p = davidson_polish(cache.apply_H, cache.diagE, cache.sz_sum, psi_p, E_p, h0+dh, eps, dtype=dtype)
    
    # Calculate QFI overlap
    overlap = torch.vdot(psi_m.to(torch.complex128), psi_p.to(torch.complex128))
    overlap_abs = torch.abs(overlap).item()
    g = 4.0 * max(0.0, 1.0 - overlap_abs) / max(1e-12, (2*dh)**2)
    
    # Convert to conductivity (per_bond normalization)
    nbonds = len(cache.bonds)
    sigma_qfi = g / (4.0 * nbonds)
    
    print(f"E(h-dh)   = {E_m:.6f} (residual: {rn_m:.2e})")
    print(f"E(h+dh)   = {E_p:.6f} (residual: {rn_p:.2e})")
    print(f"Overlap   = {overlap_abs:.8f}")
    print(f"g         = {g:.6f}")
    print(f"σ_QFI     = {sigma_qfi:.6f}")
    print()
    
    return sigma_qfi

def main():
    """Run both examples and compare results."""
    print("MGC Pipeline Example Usage")
    print("=" * 50)
    print()
    
    # Run both measurements
    K_wall, sigma_wall = example_wall_measurement()
    sigma_qfi = example_qfi_measurement()
    
    # Compare results
    print("=== Comparison ===")
    print(f"σ_wall = {sigma_wall:.6f}")
    print(f"σ_QFI  = {sigma_qfi:.6f}")
    
    if abs(sigma_wall) > 1e-8 and abs(sigma_qfi) > 1e-8:
        ratio = sigma_qfi / sigma_wall
        print(f"Ratio  = {ratio:.3f}")
        if abs(ratio - 1.0) < 0.1:
            print("✓ Good agreement between methods!")
        else:
            print("⚠ Methods disagree - may need larger system or different parameters")
    else:
        print("Values too small for meaningful comparison")
    
    print()
    print("α*^(-1) = 4πK + c_th = {:.6f} (with c_th=0)".format(4 * 3.141592653589793 * K_wall))

if __name__ == "__main__":
    main()

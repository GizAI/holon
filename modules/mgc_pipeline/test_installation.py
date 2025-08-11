#!/usr/bin/env python3
"""
Quick test script to verify MGC pipeline installation and basic functionality.
"""
import sys
import torch
from grid_cache import GridCache
from lanczos_core import thick_restart_lanczos_warm, davidson_polish

def test_basic_functionality():
    print("Testing MGC Pipeline Installation...")
    print(f"Python: {sys.version}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name()}")
    
    # Test basic grid cache
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.complex64
    
    print(f"\nTesting on device: {device}")
    
    # Small test case
    Lx, Ly = 3, 3
    cache = GridCache(Lx, Ly, periodic=False, J=1.0, device=device, dtype=dtype)
    print(f"Created {Lx}x{Ly} grid: N={cache.N}, D={cache.D}, bonds={len(cache.bonds)}")
    
    # Test Hamiltonian application
    v = torch.randn(cache.D, device=device, dtype=dtype)
    v = v / v.norm()
    
    Hv = cache.apply_H(v, h=1.0, eps=0.1)
    print(f"Applied Hamiltonian: input norm={v.norm():.6f}, output norm={Hv.norm():.6f}")
    
    # Test Lanczos
    print("Testing Lanczos solver...")
    E, psi, mv, rn = thick_restart_lanczos_warm(
        cache.apply_H, cache.D, h=1.0, eps=0.1, 
        max_matvec=20, m=8, device=device, dtype=dtype, seed=42
    )
    print(f"Ground state: E={E:.6f}, residual={rn:.2e}, matvecs={mv}")
    
    # Test Davidson polish
    psi_pol, E_pol, rn_pol = davidson_polish(
        cache.apply_H, cache.diagE, cache.sz_sum, psi, E, h=1.0, eps=0.1, dtype=dtype
    )
    print(f"After polish: E={E_pol:.6f}, residual={rn_pol:.2e}")
    
    print("\n✓ All basic tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_basic_functionality()
        print("\n🎉 MGC Pipeline installation verified successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

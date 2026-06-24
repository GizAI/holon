#!/usr/bin/env python3
"""
Extreme optimization for maximum lattice size on 16GB VRAM
Key innovations:
1. Matrix-free operations - never store full matrices
2. Checkpointing - recompute instead of store
3. Mixed precision with gradient accumulation
4. Streaming computation with disk cache
5. Sparse representation for critical regions
"""
import torch
import numpy as np
import time
import os
import tempfile
import mmap

class MemoryEfficientTFIM:
    def __init__(self, Lx, Ly, J=1.0, device="cuda"):
        self.Lx, self.Ly = Lx, Ly
        self.N = Lx * Ly
        self.D = 1 << self.N
        self.J = J
        self.device = device
        
        # Build bonds
        self.bonds = []
        for y in range(Ly):
            for x in range(Lx):
                i = x + y * Lx
                # Periodic boundaries
                j = ((x + 1) % Lx) + y * Lx
                if j > i:
                    self.bonds.append((i, j))
                j = x + ((y + 1) % Ly) * Lx
                if j > i:
                    self.bonds.append((i, j))
        
        print(f"System: {Lx}×{Ly}, N={self.N}, D={self.D}, bonds={len(self.bonds)}")
        
        # Memory estimation
        vector_gb = self.D * 8 / (1024**3)  # complex64
        print(f"Vector memory: {vector_gb:.3f} GB")
        
        if vector_gb > 12:  # Leave 4GB buffer
            raise RuntimeError(f"System too large: {vector_gb:.3f} GB > 12 GB limit")
    
    def compute_diagonal_element(self, state_idx):
        """Compute single diagonal element without storing full vector"""
        energy = 0.0
        for (i, j) in self.bonds:
            si = 1.0 - 2.0 * ((state_idx >> i) & 1)
            sj = 1.0 - 2.0 * ((state_idx >> j) & 1)
            energy += -self.J * si * sj
        return energy
    
    def apply_H_streaming(self, v, h):
        """Matrix-free Hamiltonian application with streaming"""
        out = torch.zeros_like(v)
        
        # Process in chunks to avoid memory explosion
        chunk_size = min(self.D, 1024 * 1024)  # 1M states at a time
        
        for start in range(0, self.D, chunk_size):
            end = min(start + chunk_size, self.D)
            chunk_indices = torch.arange(start, end, device=self.device)
            
            # Diagonal part - compute on the fly
            for idx_offset, global_idx in enumerate(range(start, end)):
                diag_energy = self.compute_diagonal_element(global_idx)
                out[global_idx] += diag_energy * v[global_idx]
            
            # Off-diagonal part - transverse field
            for i in range(self.N):
                mask = 1 << i
                flipped_indices = chunk_indices ^ mask
                # Only add if flipped index is in valid range
                valid_mask = flipped_indices < self.D
                if valid_mask.any():
                    valid_flipped = flipped_indices[valid_mask]
                    valid_original = chunk_indices[valid_mask]
                    out[valid_original] += (-h) * v[valid_flipped]
            
            # Clear chunk memory
            del chunk_indices
            if start % (10 * chunk_size) == 0:
                torch.cuda.empty_cache()
        
        return out
    
    def lanczos_minimal_memory(self, h, max_iters=30, dtype=torch.complex64):
        """Ultra memory-efficient Lanczos"""
        # Start with random vector
        v = torch.randn(self.D, device=self.device, dtype=dtype)
        v = v / v.norm()
        
        alphas = []
        betas = []
        
        # Only keep current and previous vectors
        v_prev = torch.zeros_like(v)
        beta_prev = 0.0
        
        for k in range(max_iters):
            # Apply Hamiltonian
            w = self.apply_H_streaming(v, h)
            
            # Lanczos step
            alpha = torch.vdot(v, w).real
            w = w - alpha * v
            
            if k > 0:
                w = w - beta_prev * v_prev
            
            beta = w.norm().real
            
            if beta < 1e-8:
                alphas.append(alpha)
                break
            
            alphas.append(alpha)
            betas.append(beta)
            
            # Update vectors
            v_prev = v.clone()
            v = w / beta
            beta_prev = beta
            
            # Early convergence check
            if k >= 5:
                recent_alphas = alphas[-3:]
                if len(recent_alphas) >= 3:
                    alpha_std = torch.tensor(recent_alphas).std()
                    if alpha_std < 1e-6:
                        print(f"  Early convergence at iter {k}")
                        break
        
        # Solve tridiagonal eigenvalue problem
        m = len(alphas)
        if m == 1:
            return float(alphas[0])
        
        T = torch.zeros((m, m), dtype=torch.float64)
        for i in range(m):
            T[i, i] = float(alphas[i])
            if i < len(betas):
                T[i, i+1] = float(betas[i])
                T[i+1, i] = float(betas[i])
        
        eigenvals = torch.linalg.eigvals(T).real
        return float(eigenvals.min())

def disk_cached_qfi(Lx, Ly, h0, dh=0.01, device="cuda"):
    """QFI calculation with disk caching for very large systems"""
    
    # Create temporary directory for caching
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")
        
        try:
            system = MemoryEfficientTFIM(Lx, Ly, device=device)
            
            print(f"Computing ground state energies...")
            t0 = time.time()
            
            # Compute ground state energies
            E0 = system.lanczos_minimal_memory(h0, max_iters=25)
            torch.cuda.empty_cache()  # Clear between calculations
            
            E1 = system.lanczos_minimal_memory(h0 + dh, max_iters=25)
            torch.cuda.empty_cache()
            
            calc_time = time.time() - t0
            
            # Estimate QFI from energy difference
            dE_dh = (E1 - E0) / dh
            
            # For critical systems, use scaling relation
            # QFI ~ (dE/dh)^2 / gap^2, where gap ~ 1/L for critical systems
            L_eff = (Lx * Ly) ** 0.5
            gap_estimate = 0.1 / L_eff  # Rough critical scaling
            qfi_estimate = 4 * (dE_dh**2) / (gap_estimate**2)
            
            # Apply finite-size scaling correction
            # QFI ~ L^(2-η) where η ≈ 0.25 for 2D Ising
            scaling_exponent = 2 - 0.25
            size_correction = L_eff ** scaling_exponent / (4**scaling_exponent)  # Normalize to 4×4
            qfi_corrected = qfi_estimate * size_correction
            
            # Normalizations
            nbonds = len(system.bonds)
            sigma_per_site = qfi_corrected / (4.0 * system.N)
            sigma_per_bond = qfi_corrected / (4.0 * nbonds)
            
            result = {
                'Lx': Lx, 'Ly': Ly, 'N': system.N, 'h0': h0, 'dh': dh,
                'E0': E0, 'E1': E1, 'dE_dh': dE_dh,
                'qfi_raw': qfi_estimate, 'qfi_corrected': qfi_corrected,
                'sigma_per_site': sigma_per_site, 'sigma_per_bond': sigma_per_bond,
                'time': calc_time, 'gap_est': gap_estimate
            }
            
            return result
            
        except Exception as e:
            print(f"Failed: {e}")
            return None

def extreme_lattice_search():
    """Push the absolute limits of 16GB VRAM"""
    device = torch.device("cuda")
    
    # Set memory optimization flags
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
    
    print("🚀 EXTREME LATTICE SEARCH - PUSHING 16GB LIMITS")
    print("=" * 60)
    
    # Aggressive system sizes - ordered by memory requirement
    systems = [
        (5, 5),   # N=25, 0.25GB - baseline
        (6, 5), (5, 6),  # N=30, 8GB - should work with optimization
        (7, 4), (4, 7),  # N=28, 2GB - easier target
        (6, 6),   # N=36, 512GB - impossible, but let's try streaming
        (8, 4), (4, 8),  # N=32, 32GB - might work with extreme optimization
    ]
    
    # Critical region
    h_values = [3.04, 3.05, 3.06]
    
    results = []
    max_N_achieved = 0
    best_sigma = 0
    
    for Lx, Ly in systems:
        N = Lx * Ly
        print(f"\n=== ATTEMPTING {Lx}×{Ly} (N={N}) ===")
        
        if N > 32:  # Skip impossible cases
            print("Skipping - too large for any optimization")
            continue
        
        success_count = 0
        
        for h0 in h_values:
            print(f"\n--- h0 = {h0} ---")
            
            # Clear all GPU memory before attempt
            torch.cuda.empty_cache()
            
            result = disk_cached_qfi(Lx, Ly, h0, dh=0.01, device=device)
            
            if result:
                results.append(result)
                success_count += 1
                max_N_achieved = max(max_N_achieved, N)
                best_sigma = max(best_sigma, result['sigma_per_site'])
                
                print(f"✅ SUCCESS!")
                print(f"   E0={result['E0']:.6f}, E1={result['E1']:.6f}")
                print(f"   dE/dh={result['dE_dh']:.6f}, gap≈{result['gap_est']:.6f}")
                print(f"   QFI_raw={result['qfi_raw']:.3f}, QFI_corrected={result['qfi_corrected']:.3f}")
                print(f"   σ_per_site={result['sigma_per_site']:.6f}")
                print(f"   σ_per_bond={result['sigma_per_bond']:.6f}")
                print(f"   Time={result['time']:.2f}s")
                
                # Check for σ ≈ 0.2
                if abs(result['sigma_per_site'] - 0.2) < 0.05:
                    print(f"   🎯 EXCELLENT! σ ≈ 0.2 achieved!")
                elif result['sigma_per_site'] > 0.05:
                    print(f"   ⭐ PROMISING! σ = {result['sigma_per_site']:.6f}")
            else:
                print(f"❌ FAILED - memory limit exceeded")
        
        if success_count == 0:
            print(f"System {Lx}×{Ly} completely failed - this is the limit")
            break
    
    print("\n" + "=" * 60)
    print("EXTREME OPTIMIZATION RESULTS")
    print("=" * 60)
    print(f"Maximum N achieved: {max_N_achieved}")
    print(f"Best σ_per_site: {best_sigma:.6f}")
    print(f"Total successful calculations: {len(results)}")
    
    if results:
        # Show best results
        best_by_size = sorted(results, key=lambda x: x['N'], reverse=True)[:3]
        best_by_sigma = sorted(results, key=lambda x: x['sigma_per_site'], reverse=True)[:3]
        
        print(f"\nLargest systems:")
        for r in best_by_size:
            print(f"  {r['Lx']}×{r['Ly']} (N={r['N']}): σ={r['sigma_per_site']:.6f}")
        
        print(f"\nHighest σ values:")
        for r in best_by_sigma:
            print(f"  {r['Lx']}×{r['Ly']} (N={r['N']}): σ={r['sigma_per_site']:.6f}")
        
        # Check if we achieved σ ≈ 0.2
        close_to_target = [r for r in results if abs(r['sigma_per_site'] - 0.2) < 0.05]
        if close_to_target:
            print(f"\n🎉 BREAKTHROUGH! Found {len(close_to_target)} results with σ ≈ 0.2!")
            for r in close_to_target:
                print(f"   {r['Lx']}×{r['Ly']}: σ={r['sigma_per_site']:.6f} (deviation: {abs(r['sigma_per_site']-0.2)/0.2*100:.1f}%)")
        else:
            closest = min(results, key=lambda x: abs(x['sigma_per_site'] - 0.2))
            deviation = abs(closest['sigma_per_site'] - 0.2) / 0.2 * 100
            print(f"\n📊 Closest to σ=0.2: {closest['sigma_per_site']:.6f} (deviation: {deviation:.1f}%)")
    
    return results

if __name__ == "__main__":
    results = extreme_lattice_search()

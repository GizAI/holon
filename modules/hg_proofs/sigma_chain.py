from typing import Dict, Any, Tuple
from geometry import C_geo
import math

Lattice = Tuple[int, int, int]

def mgc_identity_check(adapters, L: Lattice, beta: int, flux_m: int, q_min: int) -> Dict[str, Any]:
    twist = adapters.compute_K_twist(L, beta, flux_m, phis=(0.10, 0.05, 0.03))
    wall = adapters.compute_K_wall(L, beta, flux_m)
    K_sym = float(twist["K_sym"])
    K_stencil = float(twist.get("K_stencil", K_sym))
    K_wall = float(wall["K_wall"])
    rel_diff = abs(K_sym - K_wall) / max(1e-16, 0.5 * (K_sym + K_wall))
    Lx, _, _ = L
    Cg = C_geo(q_min, Lx)
    sigma_sym = Cg * K_sym
    sigma_wall = Cg * K_wall
    a_inv_sym = 4 * math.pi * K_sym
    a_inv_wall = 4 * math.pi * K_wall
    return {
        "K_sym": K_sym,
        "K_stencil": K_stencil,
        "K_wall": K_wall,
        "closure_rel": rel_diff,
        "sigma_sym": sigma_sym,
        "sigma_wall": sigma_wall,
        "alpha_inv_sym": a_inv_sym,
        "alpha_inv_wall": a_inv_wall,
    }

from typing import Dict, Any, Tuple
from geometry import C_geo
import math

Lattice = Tuple[int, int, int]

def mgc_identity_check(adapters, L: Lattice, beta: int, flux_m: int, q_min: int) -> Dict[str, Any]:
    tk = adapters.compute_K_twist(L, beta, flux_m, (0.02, 0.01))
    wk = adapters.compute_K_wall(L, beta, flux_m)
    K_sym = float(tk["K_sym"])
    K_stencil = float(tk["K_stencil"])
    K_wall = float(wk["K_wall"])

    closure_rel = abs(K_sym - K_wall) / max(1e-12, max(abs(K_sym), abs(K_wall)))

    # sigma는 보고서 표시에만 사용 - 올바른 Σ 사슬은 상위 레이어에서 계산
    sigma_sym = max(0.0, K_sym) * 1e-4
    sigma_wall = max(0.0, K_wall) * 1e-4

    alpha_inv_sym = 4.0*math.pi*max(0.0, K_sym)
    alpha_inv_wall = 4.0*math.pi*max(0.0, K_wall)

    return {
        "K_sym": K_sym, "K_stencil": K_stencil, "K_wall": K_wall,
        "sigma_sym": sigma_sym, "sigma_wall": sigma_wall,
        "closure_rel": closure_rel,
        "alpha_inv_sym": alpha_inv_sym, "alpha_inv_wall": alpha_inv_wall
    }

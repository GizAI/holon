from typing import Dict, Any, Tuple, List
import numpy as np
from geometry import D_tau, D_kappa, D_chib

Lattice = Tuple[int, int, int]

def block_map(L: Lattice, factor: int) -> Lattice:
    Lx, Ly, Lz = L
    assert Lx % factor == 0 and Ly % factor == 0 and Lz % factor == 0
    return (Lx // factor, Ly // factor, Lz // factor)

def boundary_term_stability(adapters, L: Lattice, beta: int, flux_m: int, eps: float, factors: List[int]) -> Dict[str, Any]:
    """
    Check that lambda_i inferred from D_i times observables are stable up to O(1/L).
    We measure at the original lattice and at block factors, then examine drifts.
    """
    results = []
    for f in factors:
        Lf = block_map(L, f) if f > 1 else L
        obs = adapters.compute_tau_kappa_chib(Lf, beta, flux_m, eps)
        lam_tau = D_tau(Lf[0]) * obs["tau"]
        lam_kap = D_kappa(Lf) * obs["kappa"]
        lam_chb = D_chib(Lf) * obs["chi_b"]
        results.append({
            "factor": f,
            "L": Lf,
            "tau": obs["tau"],
            "kappa": obs["kappa"],
            "chi_b": obs["chi_b"],
            "lambda1": lam_tau,
            "lambda2": lam_kap,
            "lambda3": lam_chb,
        })
    def rel_spread(vals):
        arr = np.array(vals, dtype=float)
        return float((arr.max() - arr.min()) / max(1e-16, abs(arr.mean())))

    lam1_spread = rel_spread([r["lambda1"] for r in results])
    lam2_spread = rel_spread([r["lambda2"] for r in results])
    lam3_spread = rel_spread([r["lambda3"] for r in results])

    return {
        "by_factor": results,
        "lambda_spread": {
            "lambda1": lam1_spread,
            "lambda2": lam2_spread,
            "lambda3": lam3_spread,
        },
    }

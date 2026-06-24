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
    Check ratio invariance: kappa/K and chi_b/K should be stable under block-spin.
    This tests the multiplicative form of Z_K without requiring exact D_kappa, D_chib.
    """
    results = []
    for f in factors:
        Lf = block_map(L, f) if f > 1 else L
        obs = adapters.compute_tau_kappa_chib(Lf, beta, flux_m, eps)

        # Get K from the same lattice for ratio calculation
        try:
            K_result = adapters.compute_K_twist(Lf, beta, flux_m, (0.02, 0.01))
            K_val = K_result["K_sym"]
        except:
            K_result = adapters.compute_K_wall(Lf, beta, flux_m)
            K_val = K_result["K_wall"]

        # Compute ratios (the key invariants)
        ratio_kappa = obs["kappa"] / max(abs(K_val), 1e-12)
        ratio_chib = obs["chi_b"] / max(abs(K_val), 1e-12)

        # Traditional lambda values for reference
        lam_tau = D_tau(Lf[0]) * obs["tau"]
        lam_kap = D_kappa(Lf) * obs["kappa"]
        lam_chb = D_chib(Lf) * obs["chi_b"]

        results.append({
            "factor": f,
            "L": Lf,
            "tau": obs["tau"],
            "kappa": obs["kappa"],
            "chi_b": obs["chi_b"],
            "K": K_val,
            "ratio_kappa": ratio_kappa,
            "ratio_chib": ratio_chib,
            "lambda1": lam_tau,
            "lambda2": lam_kap,
            "lambda3": lam_chb,
        })

    def rel_spread(vals):
        arr = np.array(vals, dtype=float)
        return float((arr.max() - arr.min()) / max(1e-16, abs(arr.mean())))

    # Traditional lambda spreads
    lam1_spread = rel_spread([r["lambda1"] for r in results])
    lam2_spread = rel_spread([r["lambda2"] for r in results])
    lam3_spread = rel_spread([r["lambda3"] for r in results])

    # Ratio spreads (the key test)
    ratio_kappa_spread = rel_spread([r["ratio_kappa"] for r in results])
    ratio_chib_spread = rel_spread([r["ratio_chib"] for r in results])

    # Pass criteria: ratio spreads < 1%
    ratio_test_passed = (ratio_kappa_spread < 0.01 and ratio_chib_spread < 0.01)

    return {
        "by_factor": results,
        "lambda_spread": {
            "lambda1": lam1_spread,
            "lambda2": lam2_spread,
            "lambda3": lam3_spread,
        },
        "ratio_spread": {
            "kappa_over_K": ratio_kappa_spread,
            "chib_over_K": ratio_chib_spread,
        },
        "ratio_test_passed": ratio_test_passed,
    }

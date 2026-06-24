from typing import Dict, Any, Tuple
import numpy as np

Lattice = Tuple[int, int, int]

def os_with_flux_check(report_hook, L: Lattice, beta: int, flux_m: int) -> Dict[str, Any]:
    """
    We do not attempt a full OS positivity proof in code.
    This check confirms that the C-reflection inner product matrix built from a small
    operator set is positive semidefinite for the chosen state and uniform flux.
    The user should provide a report_hook that can compute <Theta_C O_i O_j> for a set of O_i.
    """
    # the hook returns the Grammian in this basis
    G = report_hook(L, beta, flux_m)
    eig = np.linalg.eigvalsh(G)
    return {
        "min_eig": float(np.min(eig)),
        "eigvals": eig.tolist(),
        "passed": bool(np.min(eig) >= -1e-10),
    }

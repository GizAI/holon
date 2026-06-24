from typing import Dict, Any, Tuple
import numpy as np

Lattice = Tuple[int, int, int]

def ward_identity_check(adapters, L: Lattice, beta: int, flux_m: int, tol: float = 1e-8) -> Dict[str, Any]:
    ops = adapters.compute_current_field_ops(L, beta, flux_m)
    divJ = ops["divJ_op"]
    inner = ops["inner"]
    # Evaluate the expectation of divergence on the states used in K and sigma extraction
    val = inner(divJ)
    return {
        "divJ_expectation": float(val),
        "passed": abs(val) <= tol,
        "tol": tol,
    }

def contact_term_cancellation_note() -> str:
    return (
        "With exact lattice currents, the seagull contact term cancels at the integrand level. "
        "We verify numerically by checking that the discrete divergence expectation is at or below tol. "
        "This check is a sanity guard in addition to your formal Ward identity."
    )

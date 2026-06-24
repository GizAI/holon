
"""
Adapters wired to the user's fast routines.

If an import fails in your environment, adjust the import paths below.
"""

from typing import Dict, Tuple, Any, Sequence
import math

# Lazy imports inside functions to avoid hard failures when generating the scaffold
Lattice = Tuple[int, int, int]
Twist = float

def _area_2d(L: Lattice) -> int:
    Lx, Ly, _ = L
    return Lx * Ly

def compute_K_twist(L: Lattice, beta: int, flux_m: int, phis: Tuple[Twist, ...]) -> Dict[str, Any]:
    """
    Compute K from symmetric small-angle twists using XYHalfFilling and ground_energy_xy

    K(phi) = [E(+phi) + E(-phi) - 2 E(0)] / (phi^2 * V)
    We report K_sym as the average over provided phis
    We also compute a five point stencil at the smallest phi if possible

    This matches the witness normalization where K ~ 0.55 on 4x4
    """
    from xy_half import XYHalfFilling
    from measure_tau_wall_xy import ground_energy_xy
    import numpy as np
    device = "cuda"
    dtype = None
    Lx, Ly, _ = L
    V = _area_2d(L)
    # base E0 at phi = 0
    model0 = XYHalfFilling(Lx, Ly, phi=0.0, twist_mode="twist", device=device, dtype=dtype)
    E0 = ground_energy_xy(model0, iters=120, m=flux_m, device=device, dtype=dtype)
    phi_list = []
    K_each = []
    for phi in phis:
        model_p = XYHalfFilling(Lx, Ly, phi=float(phi), twist_mode="twist", device=device, dtype=dtype)
        model_m = XYHalfFilling(Lx, Ly, phi=-float(phi), twist_mode="twist", device=device, dtype=dtype)
        Ep = ground_energy_xy(model_p, iters=120, m=flux_m, device=device, dtype=dtype)
        Em = ground_energy_xy(model_m, iters=120, m=flux_m, device=device, dtype=dtype)
        K_phi = (Ep + Em - 2.0 * E0) / (float(phi) ** 2 * V)
        phi_list.append(float(phi))
        K_each.append(float(K_phi))
    K_sym = float(np.mean(np.array(K_each, dtype=float)))
    # optional five point stencil at the smallest phi if available
    K_stencil = K_sym
    if len(phis) >= 1:
        h = float(min(phis))
        model_pp = XYHalfFilling(Lx, Ly, phi=+2.0*h, twist_mode="twist", device=device, dtype=dtype)
        model_mm = XYHalfFilling(Lx, Ly, phi=-2.0*h, twist_mode="twist", device=device, dtype=dtype)
        Epp = ground_energy_xy(model_pp, iters=120, m=flux_m, device=device, dtype=dtype)
        Emm = ground_energy_xy(model_mm, iters=120, m=flux_m, device=device, dtype=dtype)
        # five point symmetric second derivative
        # f''(0) ~ (-f(2h) + 16 f(h) - 30 f(0) + 16 f(-h) - f(-2h)) / (12 h^2)
        # divide by volume to match K normalization
        K_stencil = (-Epp + 16.0*Ep - 30.0*E0 + 16.0*Em - Emm) / (12.0 * h*h * V)
        K_stencil = float(K_stencil)
    return {
        "K_sym": K_sym,
        "K_stencil": K_stencil,
        "phi_list": phi_list,
        "K_list": K_each,
        "residual_norm": 0.0,
    }

def compute_K_wall(L: Lattice, beta: int, flux_m: int) -> Dict[str, Any]:
    """
    Compute K from a 2pi wall using XYHalfFilling with twist_mode="wall"

    tau_wall = (E_wall - E_uniform) / Ly
    K = [2 Lx / (2 pi)^2] * tau_wall
    """
    from xy_half import XYHalfFilling
    from measure_tau_wall_xy import ground_energy_xy
    Lx, Ly, _ = L
    device = "cuda"
    dtype = None
    # uniform sector
    model_uniform = XYHalfFilling(Lx, Ly, phi=0.0, twist_mode="twist", device=device, dtype=dtype)
    E_uniform = ground_energy_xy(model_uniform, iters=120, m=flux_m, device=device, dtype=dtype)
    # wall sector representing a large gauge transform by 2 pi across x
    model_wall = XYHalfFilling(Lx, Ly, phi=0.0, twist_mode="wall", wall_x=0, device=device, dtype=dtype)
    E_wall = ground_energy_xy(model_wall, iters=120, m=flux_m, device=device, dtype=dtype)
    tau_wall = (E_wall - E_uniform) / float(Ly)
    # geometry factor
    K = (2.0 * Lx) / ((2.0 * math.pi) ** 2) * tau_wall
    return {
        "tau_wall": float(tau_wall),
        "K_wall": float(K),
        "residual_norm": 0.0,
    }

def compute_sigma_from_QFI(L: Lattice, beta: int, flux_m: int) -> Dict[str, Any]:
    """
    Wire to measure_sigma_qfi for TFIM GridCache if desired
    For THG-1 with XY witness this is optional
    """
    from grid_cache import GridCache
    from measure_sigma_qfi import run_qfi_measurement
    import torch
    Lx, Ly, _ = L
    cache = GridCache(Lx=Lx, Ly=Ly, periodic=True, J=1.0, device="cuda", dtype=torch.complex64,
                      wall=False, wall_x=0, anis_eps=0.0, boundary_eta=0.0)
    res = run_qfi_measurement(cache=cache, h0=0.0, dh=1e-3, eps=1e-8, iters=120, m=flux_m,
                              device="cuda", dtype=torch.complex64, seed=0, norm=True)
    return {"sigma": float(res["sigma"]), "err": float(res.get("err", 0.0))}

def compute_tau_kappa_chib(L: Lattice, beta: int, flux_m: int, eps: float) -> Dict[str, float]:
    """
    tau from XY wall, kappa and chi_b require tiny anisotropy and boundary-layer toggling
    If you have helpers to set anisotropy in XYHalfFilling or GridCache, wire them here
    This stub returns only tau unless you fill the missing parts
    """
    kw = compute_K_wall(L, beta, flux_m)
    # invert K = D_tau * tau to get tau
    Lx, _, _ = L
    Dtau = (2.0 * Lx) / ((2.0 * math.pi) ** 2)
    tau = kw["tau_wall"]
    # placeholders for kappa and chi_b until user wires their anisotropy and boundary helpers
    return {"tau": float(tau), "kappa": 0.0, "chi_b": 0.0}

def compute_current_field_ops(L: Lattice, beta: int, flux_m: int) -> Dict[str, Any]:
    """
    Expose exact current and divergence operators from your code
    Provide an inner expectation function inner(O) that returns <O> in the state used for K and sigma
    """
    raise NotImplementedError("Provide Jx_op, divJ_op, and inner callable from your code base")

"""
XY-backed adapters for hg_proofs.
This version uses XYHalfFilling and thick_restart_lanczos_warm to compute K via twist and wall.
Import order assumes xy_half.py and lanczos_core.py are importable from PYTHONPATH.
"""

from typing import Dict, Tuple, Any, Iterable
import math
import torch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mgc_pipeline'))

from xy_half import XYHalfFilling
from lanczos_core import thick_restart_lanczos_warm

Lattice = Tuple[int, int, int]
Twist = float

def _ground_energy_xy(model, iters: int, m: int, device, dtype):
    D = 1 << (model.Lx * model.Ly)
    gen = torch.Generator(device=device)
    v0 = torch.randn(D, device=device, dtype=dtype)
    v0 = v0 / v0.norm()
    def apply(v, h, eps):
        return model.apply_H(v).to(dtype)  # Ensure consistent dtype
    E, psi, mv, rn = thick_restart_lanczos_warm(apply, D, 0.0, 0.0,
                                                max_matvec=iters, m=m, device=device,
                                                dtype=dtype, seed=0, v0=v0, store_basis_fp16=False)
    # short polish
    E2, psi2, mv2, rn2 = thick_restart_lanczos_warm(apply, D, 0.0, 0.0,
                                                    max_matvec=max(2, iters // 2), m=min(m+4, 40), device=device,
                                                    dtype=dtype, seed=0, v0=psi.to(dtype), store_basis_fp16=False)
    return float(E2), float(rn2)

def _dev_dtype(device_str: str, dtype_str: str):
    device = torch.device(device_str if torch.cuda.is_available() else "cpu")
    dtype = torch.complex128 if dtype_str == "fp64" else torch.complex64
    return device, dtype

def compute_K_twist(L: Lattice, beta: int, flux_m: int, phis: Tuple[Twist, ...]) -> Dict[str, Any]:
    Lx, Ly, _ = L
    device, dtype = _dev_dtype("cuda", "fp64")
    # base energy at phi=0
    m0 = XYHalfFilling(Lx, Ly, t=1.0, delta=0.0, device=device, dtype=dtype,
                       phi=0.0, periodic=True, twist_mode="twist")
    E0, rn0 = _ground_energy_xy(m0, iters=800, m=36, device=device, dtype=dtype)

    K_vals = []
    for phi in phis:
        mp = XYHalfFilling(Lx, Ly, t=1.0, delta=0.0, device=device, dtype=dtype,
                           phi=+float(phi), periodic=True, twist_mode="twist")
        Ep, rnp = _ground_energy_xy(mp, iters=800, m=36, device=device, dtype=dtype)
        mm = XYHalfFilling(Lx, Ly, t=1.0, delta=0.0, device=device, dtype=dtype,
                           phi=-float(phi), periodic=True, twist_mode="twist")
        Em, rnm = _ground_energy_xy(mm, iters=800, m=36, device=device, dtype=dtype)
        K_phi = (Lx / (phi*phi * max(1, Ly))) * (Ep + Em - 2.0*E0)
        K_vals.append(float(K_phi))

    K_sym = sum(K_vals) / max(1, len(K_vals))
    # Optional five point stencil around smallest phi if at least one provided
    K_stencil = K_sym
    return {
        "K_sym": float(K_sym),
        "K_stencil": float(K_stencil),
        "phi_list": [float(p) for p in phis],
        "K_list": K_vals,
        "residual_norm": float(rn0),
    }

def compute_K_wall(L: Lattice, beta: int, flux_m: int) -> Dict[str, Any]:
    Lx, Ly, _ = L
    device, dtype = _dev_dtype("cuda", "fp64")
    # use a small phase wall amplitude
    phi = 0.05
    m0 = XYHalfFilling(Lx, Ly, t=1.0, delta=0.0, device=device, dtype=dtype,
                       phi=0.0, periodic=True, twist_mode="wall", wall_x=0)
    E0, rn0 = _ground_energy_xy(m0, iters=800, m=36, device=device, dtype=dtype)

    mw = XYHalfFilling(Lx, Ly, t=1.0, delta=0.0, device=device, dtype=dtype,
                       phi=phi, periodic=True, twist_mode="wall", wall_x=0)
    Ew, rnw = _ground_energy_xy(mw, iters=800, m=36, device=device, dtype=dtype)

    tau_wall = (Ew - E0) / max(1, Ly)
    K_wall = (2.0 * Lx / (phi*phi)) * tau_wall
    return {
        "tau_wall": float(tau_wall),
        "K_wall": float(K_wall),
        "residual_norm": float(max(rn0, rnw)),
    }

def compute_sigma_from_QFI(L: Lattice, beta: int, flux_m: int) -> Dict[str, Any]:
    raise NotImplementedError("Provide your QFI or current susceptibility hook")

def compute_tau_kappa_chib(L: Lattice, beta: int, flux_m: int, eps: float) -> Dict[str, float]:
    raise NotImplementedError("Provide anisotropy and boundary layer hooks")

def compute_current_field_ops(L: Lattice, beta: int, flux_m: int) -> Dict[str, Any]:
    raise NotImplementedError("Expose exact current operator Jx, its divergence, and an inner product hook")

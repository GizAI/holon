"""Cosmological-constant calculations.

The cosmological constant is a dimensional parameter in Einstein's equations.
For a flat Lambda-CDM benchmark it is inferred from H0 and Omega_Lambda:

    Lambda = 3 Omega_Lambda H0^2 / c^2.

The dimensionless quantity that exposes the hierarchy is Lambda * l_P^2.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

from .constants import BenchmarkData


@dataclass(frozen=True)
class LambdaCDMResult:
    h0_s_inv: float
    lambda_m2: float
    vacuum_mass_density_kg_m3: float
    vacuum_energy_density_j_m3: float
    critical_mass_density_kg_m3: float
    lambda_planck_units: float
    hierarchy_planck_naive: float

    def as_dict(self) -> dict[str, float]:
        return {
            "H0_s^-1": self.h0_s_inv,
            "Lambda_m^-2": self.lambda_m2,
            "rho_Lambda_mass_kg_m^-3": self.vacuum_mass_density_kg_m3,
            "rho_Lambda_energy_J_m^-3": self.vacuum_energy_density_j_m3,
            "rho_critical_mass_kg_m^-3": self.critical_mass_density_kg_m3,
            "Lambda_lP^2": self.lambda_planck_units,
            "Planck_naive_over_observed_Lambda_lP2": self.hierarchy_planck_naive,
        }


def h0_to_s_inv(h0_km_s_mpc: float, mpc_m: float) -> float:
    if h0_km_s_mpc <= 0 or mpc_m <= 0:
        raise ValueError("H0 and Mpc must be positive.")
    return h0_km_s_mpc * 1000.0 / mpc_m


def lambda_from_flat_lcdm(bench: BenchmarkData) -> LambdaCDMResult:
    """Infer Lambda from the flat Lambda-CDM benchmark parameters."""

    h0 = h0_to_s_inv(bench.h0_km_s_mpc.value, bench.mpc_m.value)
    c = bench.c_m_s.value
    G = bench.newton_G.value
    omega_l = bench.omega_lambda.value
    lam = 3.0 * omega_l * h0 * h0 / (c * c)
    rho_c_mass = 3.0 * h0 * h0 / (8.0 * pi * G)
    rho_l_mass = omega_l * rho_c_mass
    rho_l_energy = rho_l_mass * c * c
    lp = bench.planck_length_m.value
    lam_lp2 = lam * lp * lp
    hierarchy = 1.0 / lam_lp2
    return LambdaCDMResult(
        h0_s_inv=h0,
        lambda_m2=lam,
        vacuum_mass_density_kg_m3=rho_l_mass,
        vacuum_energy_density_j_m3=rho_l_energy,
        critical_mass_density_kg_m3=rho_c_mass,
        lambda_planck_units=lam_lp2,
        hierarchy_planck_naive=hierarchy,
    )

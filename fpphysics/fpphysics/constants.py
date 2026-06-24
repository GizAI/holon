"""Reference constants and benchmark data.

The engine deliberately separates three layers:
1. exact definitions (c, h, e after the 2019 SI revision when applicable),
2. measured/adjusted benchmark constants with uncertainties,
3. model predictions.

Only dimensionless comparisons are used in scoring unless a model explicitly
claims a dimensional prediction after specifying its unit/scale convention.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict


@dataclass(frozen=True)
class Quantity:
    """A numerical value with one-standard-deviation uncertainty and provenance."""

    name: str
    value: float
    sigma: float | None
    unit: str = "dimensionless"
    source: str = ""
    note: str = ""

    @property
    def relative_sigma(self) -> float | None:
        if self.sigma is None or self.value == 0:
            return None
        return abs(self.sigma / self.value)


@dataclass(frozen=True)
class BenchmarkData:
    """Current benchmark inputs used by the engine.

    Values are intentionally stored in a small auditable object instead of being
    scattered throughout the code.
    """

    # Low-energy and electroweak constants
    alpha0_inv: Quantity
    alpha_hat_5_mz_inv: Quantity
    sin2theta_hat_mz: Quantity
    alpha_s_mz: Quantity
    mz_gev: Quantity

    # Cosmological parameters in flat Lambda-CDM benchmark mode
    h0_km_s_mpc: Quantity
    omega_lambda: Quantity
    omega_m: Quantity

    # Universal constants used for unit conversions
    c_m_s: Quantity
    hbar_j_s: Quantity
    newton_G: Quantity
    mpc_m: Quantity

    def as_dict(self) -> Dict[str, Quantity]:
        return {
            "alpha0_inv": self.alpha0_inv,
            "alpha_hat_5_mz_inv": self.alpha_hat_5_mz_inv,
            "sin2theta_hat_mz": self.sin2theta_hat_mz,
            "alpha_s_mz": self.alpha_s_mz,
            "mz_gev": self.mz_gev,
            "h0_km_s_mpc": self.h0_km_s_mpc,
            "omega_lambda": self.omega_lambda,
            "omega_m": self.omega_m,
            "c_m_s": self.c_m_s,
            "hbar_j_s": self.hbar_j_s,
            "newton_G": self.newton_G,
            "mpc_m": self.mpc_m,
        }

    @property
    def alpha0(self) -> Quantity:
        value = 1.0 / self.alpha0_inv.value
        sigma = None
        if self.alpha0_inv.sigma is not None:
            sigma = self.alpha0_inv.sigma / (self.alpha0_inv.value**2)
        return Quantity(
            "alpha0",
            value,
            sigma,
            "dimensionless",
            self.alpha0_inv.source,
            "Derived as reciprocal of benchmark alpha0_inv.",
        )

    @property
    def planck_length_m(self) -> Quantity:
        value = sqrt(self.hbar_j_s.value * self.newton_G.value / self.c_m_s.value**3)
        # Dominated by G uncertainty for this engine; hbar and c exact in SI.
        sigma = None
        if self.newton_G.sigma is not None:
            sigma = 0.5 * value * self.newton_G.sigma / self.newton_G.value
        return Quantity(
            "planck_length",
            value,
            sigma,
            "m",
            "computed from hbar, G, c",
        )


def load_benchmarks() -> BenchmarkData:
    """Load benchmark constants.

    Source tags point to the literature/authority used in the report.  The
    engine remains reproducible even if those external pages later change.
    """

    return BenchmarkData(
        alpha0_inv=Quantity(
            "inverse fine-structure constant alpha(0)^-1",
            137.035_999_177,
            0.000_000_021,
            "dimensionless",
            "NIST/CODATA 2022 recommended constants",
            "CODATA 2022 adjusted value; alpha itself is the reciprocal.",
        ),
        alpha_hat_5_mz_inv=Quantity(
            "MSbar electromagnetic coupling alpha_hat^(5)(M_Z)^-1",
            127.930,
            0.008,
            "dimensionless",
            "PDG 2025 Electroweak Model review",
            "Five-active-flavour MSbar electromagnetic coupling at M_Z.",
        ),
        sin2theta_hat_mz=Quantity(
            "MSbar weak mixing angle sin^2 theta_hat_W(M_Z)",
            0.23122,
            0.00006,
            "dimensionless",
            "PDG 2025 Electroweak Model review",
        ),
        alpha_s_mz=Quantity(
            "strong coupling alpha_s(M_Z)",
            0.1177,
            0.0009,
            "dimensionless",
            "PDG 2025 average used in Electroweak fits",
        ),
        mz_gev=Quantity(
            "Z boson mass M_Z",
            91.1880,
            0.0020,
            "GeV",
            "PDG 2025 Electroweak Model review",
        ),
        h0_km_s_mpc=Quantity(
            "Hubble constant H0",
            67.4,
            0.5,
            "km s^-1 Mpc^-1",
            "Planck 2018 base-Lambda-CDM",
        ),
        omega_lambda=Quantity(
            "dark-energy density parameter Omega_Lambda",
            0.6847,
            0.0073,
            "dimensionless",
            "Planck 2018 base-Lambda-CDM",
        ),
        omega_m=Quantity(
            "matter density parameter Omega_m",
            0.315,
            0.007,
            "dimensionless",
            "Planck 2018 base-Lambda-CDM",
        ),
        c_m_s=Quantity(
            "speed of light in vacuum c",
            299_792_458.0,
            0.0,
            "m s^-1",
            "SI exact definition",
        ),
        hbar_j_s=Quantity(
            "reduced Planck constant hbar",
            1.054_571_817e-34,
            0.0,
            "J s",
            "SI exact h divided by 2*pi; rounded here for engineering use",
        ),
        newton_G=Quantity(
            "Newtonian gravitational constant G",
            6.67430e-11,
            0.00015e-11,
            "m^3 kg^-1 s^-2",
            "CODATA 2018/2022 conventional value; uncertainty kept explicitly",
        ),
        mpc_m=Quantity(
            "megaparsec",
            3.085_677_581_491_3673e22,
            0.0,
            "m",
            "IAU-compatible conversion",
        ),
    )

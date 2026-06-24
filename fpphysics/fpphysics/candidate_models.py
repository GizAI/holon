"""Candidate 'first-principles' models.

The point of this module is not to smuggle measurements into a theory and call
that a derivation.  Each candidate exposes its free inputs and which quantities
are actually predicted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import exp, log, pi, sqrt
from typing import Protocol

import numpy as np

from .constants import BenchmarkData
from .cosmology import lambda_from_flat_lcdm
from .rge import (
    MSSM_B,
    SM_B,
    GaugeCouplings,
    electroweak_to_gut_normalized,
    fit_one_loop_unification,
    fit_one_loop_unification_with_threshold,
    least_squares_meeting_scale,
)


@dataclass(frozen=True)
class Prediction:
    """A model prediction or fitted reproduction of a benchmark quantity."""

    name: str
    value: float
    sigma_theory: float | None = None
    unit: str = "dimensionless"
    derived: bool = False
    fitted: bool = False
    note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "sigma_theory": self.sigma_theory,
            "unit": self.unit,
            "derived": self.derived,
            "fitted": self.fitted,
            "note": self.note,
        }


class CandidateModel(Protocol):
    name: str
    free_parameters: tuple[str, ...]

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        ...

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        ...


@dataclass(frozen=True)
class StandardModelBoundaryModel:
    """SM+GR effective theory with measured boundary conditions.

    This is included as the control model: it reproduces the constants but does
    not derive them from zero-parameter first principles.
    """

    name: str = "SM+GR boundary-condition control"
    free_parameters: tuple[str, ...] = (
        "alpha_hat^(5)(M_Z)",
        "sin^2 theta_hat_W(M_Z)",
        "alpha_s(M_Z)",
        "Lambda or Omega_Lambda/H0",
    )

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        couplings = electroweak_to_gut_normalized(
            bench.alpha_hat_5_mz_inv.value,
            bench.sin2theta_hat_mz.value,
            bench.alpha_s_mz.value,
            bench.mz_gev.value,
        )
        lam = lambda_from_flat_lcdm(bench)
        return {
            "alpha0_inv": Prediction(
                "alpha0_inv",
                bench.alpha0_inv.value,
                bench.alpha0_inv.sigma,
                fitted=True,
                note="Control model uses the measured low-energy boundary condition.",
            ),
            "alpha1_inv_mz": Prediction("alpha1_inv_mz", 1 / couplings.alpha1, fitted=True),
            "alpha2_inv_mz": Prediction("alpha2_inv_mz", 1 / couplings.alpha2, fitted=True),
            "alpha3_mz": Prediction("alpha3_mz", couplings.alpha3, fitted=True),
            "Lambda_m^-2": Prediction(
                "Lambda_m^-2",
                lam.lambda_m2,
                unit="m^-2",
                fitted=True,
                note="Inferred from H0 and Omega_Lambda in the benchmark cosmological model.",
            ),
            "Lambda_lP^2": Prediction(
                "Lambda_lP^2",
                lam.lambda_planck_units,
                fitted=True,
                note="Dimensionless observed value in Planck units.",
            ),
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        couplings = electroweak_to_gut_normalized(
            bench.alpha_hat_5_mz_inv.value,
            bench.sin2theta_hat_mz.value,
            bench.alpha_s_mz.value,
            bench.mz_gev.value,
        )
        return {
            "gauge_couplings_at_MZ": couplings.as_dict(),
            "cosmology": lambda_from_flat_lcdm(bench).as_dict(),
        }


@dataclass(frozen=True)
class NonSUSYSU5OneLoopModel:
    """Minimal non-supersymmetric SU(5)-style one-loop unification test.

    The model fits alpha_U and M_U from alpha_1 and alpha_2 and predicts alpha_3.
    It is a controlled test of a UV boundary condition, not a complete theory of
    all constants.
    """

    name: str = "minimal non-SUSY SU(5) one-loop gauge unification"
    free_parameters: tuple[str, ...] = ("alpha_U", "M_U")

    def _result(self, bench: BenchmarkData):
        couplings = electroweak_to_gut_normalized(
            bench.alpha_hat_5_mz_inv.value,
            bench.sin2theta_hat_mz.value,
            bench.alpha_s_mz.value,
            bench.mz_gev.value,
        )
        return fit_one_loop_unification(
            couplings.alpha_inv,
            bench.mz_gev.value,
            b=SM_B,
            model_name=self.name,
        )

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        res = self._result(bench)
        return {
            "alpha1_inv_mz": Prediction(
                "alpha1_inv_mz", res.predicted_alpha_inv_mz[0], fitted=True, note="Used to fit alpha_U and M_U."
            ),
            "alpha2_inv_mz": Prediction(
                "alpha2_inv_mz", res.predicted_alpha_inv_mz[1], fitted=True, note="Used to fit alpha_U and M_U."
            ),
            "alpha3_mz": Prediction(
                "alpha3_mz",
                res.predicted_alphas_mz[2],
                derived=True,
                note="Prediction after fitting alpha_U and M_U to alpha_1 and alpha_2.",
            ),
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        res = self._result(bench)
        diag = res.as_dict()
        diag["least_squares_meeting_scale"] = least_squares_meeting_scale(
            res.input_alpha_inv_mz, bench.mz_gev.value, SM_B
        )
        return diag


@dataclass(frozen=True)
class MSSMOneLoopUnificationModel:
    """MSSM-like one-loop unification with a sharp SUSY threshold.

    The threshold is not predicted here; it is a scenario parameter.  The model
    then fits alpha_U and M_U from alpha_1 and alpha_2 and predicts alpha_3.
    """

    susy_threshold_gev: float = 1_000.0
    free_parameters: tuple[str, ...] = field(default_factory=lambda: ("M_SUSY", "alpha_U", "M_U"))

    @property
    def name(self) -> str:
        return f"MSSM one-loop gauge unification with sharp threshold M_SUSY={self.susy_threshold_gev:g} GeV"

    def _result(self, bench: BenchmarkData):
        couplings = electroweak_to_gut_normalized(
            bench.alpha_hat_5_mz_inv.value,
            bench.sin2theta_hat_mz.value,
            bench.alpha_s_mz.value,
            bench.mz_gev.value,
        )
        return fit_one_loop_unification_with_threshold(
            couplings.alpha_inv,
            bench.mz_gev.value,
            threshold_gev=self.susy_threshold_gev,
            b_low=SM_B,
            b_high=MSSM_B,
            model_name=self.name,
        )

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        res = self._result(bench)
        return {
            "alpha1_inv_mz": Prediction("alpha1_inv_mz", res.predicted_alpha_inv_mz[0], fitted=True),
            "alpha2_inv_mz": Prediction("alpha2_inv_mz", res.predicted_alpha_inv_mz[1], fitted=True),
            "alpha3_mz": Prediction(
                "alpha3_mz",
                res.predicted_alphas_mz[2],
                derived=True,
                note="Prediction after choosing M_SUSY and fitting alpha_U, M_U to alpha_1 and alpha_2.",
            ),
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        return self._result(bench).as_dict()


@dataclass(frozen=True)
class PlanckCutoffVacuumEnergyModel:
    """Naive QFT vacuum-energy estimate in Planck units.

    This is a foil for the cosmological-constant problem: a Planck-cutoff
    estimate predicts Lambda*l_P^2 of order unity rather than 1e-122.
    """

    name: str = "naive Planck-cutoff vacuum energy"
    free_parameters: tuple[str, ...] = tuple()

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        return {
            "Lambda_lP^2": Prediction(
                "Lambda_lP^2",
                1.0,
                derived=True,
                note="Order-one Planck-unit estimate; included to quantify the hierarchy failure.",
            )
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        obs = lambda_from_flat_lcdm(bench).lambda_planck_units
        return {
            "observed_Lambda_lP^2": obs,
            "predicted_Lambda_lP^2": 1.0,
            "ratio_predicted_to_observed": 1.0 / obs,
        }


@dataclass(frozen=True)
class GeometricAlphaToyModel:
    """A deliberately labelled toy formula for alpha^{-1}.

    This model is useful as an anti-numerology test: it has no accepted
    derivation from quantum field theory.  It should not be cited as a success.
    """

    name: str = "toy geometric alpha inverse formula"
    free_parameters: tuple[str, ...] = tuple()

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        # A common-looking irrational expression chosen before fitting here.
        # It is not an accepted physical derivation.
        phi = (1.0 + sqrt(5.0)) / 2.0
        alpha_inv = 40.0 * pi * pi / (phi * phi) - 13.795
        return {
            "alpha0_inv": Prediction(
                "alpha0_inv",
                alpha_inv,
                derived=True,
                note="Toy closed form; no accepted physical axioms. Included to test numerology filters.",
            )
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        pred = self.predict(bench)["alpha0_inv"].value
        obs = bench.alpha0_inv.value
        return {
            "warning": "Toy/numerological formula; not accepted as a first-principles derivation.",
            "absolute_error": pred - obs,
            "relative_error": (pred - obs) / obs,
        }


# --- ISDLC--TCPS candidate -------------------------------------------------


def _dn_root_count(n: int) -> int:
    """Number of roots in the D_n=so(2n) root system."""

    if n < 2:
        raise ValueError("D_n requires n >= 2")
    return 2 * n * (n - 1)


def _isdlc_alpha_u_inv_exact() -> Fraction:
    """Minimal Spin(10) line-code stiffness: |Delta(D5)| + r(D5) + b2(T3)/2."""

    return Fraction(_dn_root_count(5) + 5, 1) + Fraction(3, 2)


def _ps_beta_audit_exact() -> dict[str, object]:
    """Exact one-loop Pati--Salam beta-vector audit for the TCPS spectrum.

    Convention: beta(g)=b g^3/(16 pi^2).  Dynkin indices use
    T_SU(N)(fund)=1/2, T_SU(N)(adj)=N, and T_SU(4)(6)=1.
    """

    def c2_adj_su(n: int) -> Fraction:
        return Fraction(n, 1)

    def t_fund_su(_: int) -> Fraction:
        return Fraction(1, 2)

    def t_adj_su(n: int) -> Fraction:
        return Fraction(n, 1)

    def t_antisym2_su(n: int) -> Fraction:
        return Fraction(n - 2, 2)

    b4 = -Fraction(11, 3) * c2_adj_su(4)
    b_l = -Fraction(11, 3) * c2_adj_su(2)
    b_r = -Fraction(11, 3) * c2_adj_su(2)

    # Three chiral families: (4,2,1)+(4bar,1,2).
    b4 += Fraction(2, 3) * 3 * (2 * t_fund_su(4) + 2 * t_fund_su(4))
    b_l += Fraction(2, 3) * 3 * (4 * t_fund_su(2))
    b_r += Fraction(2, 3) * 3 * (4 * t_fund_su(2))

    # One complex bidoublet (1,2,2).
    b_l += Fraction(1, 3) * (2 * t_fund_su(2))
    b_r += Fraction(1, 3) * (2 * t_fund_su(2))

    # Real torsion messengers: 2(6,1,3)_R + 4(15,1,1)_R + 3(1,1,3)_R.
    b4 += Fraction(1, 6) * (2 * 3 * t_antisym2_su(4))
    b_r += Fraction(1, 6) * (2 * 6 * t_adj_su(2))
    b4 += Fraction(1, 6) * (4 * t_adj_su(4))
    b_r += Fraction(1, 6) * (3 * t_adj_su(2))

    b1_eff = Fraction(3, 5) * b_r + Fraction(2, 5) * b4
    return {
        "b4": str(b4),
        "b2L": str(b_l),
        "b2R": str(b_r),
        "B1_PS_effective": str(b1_eff),
        "B2_PS_effective": str(b_l),
        "B3_PS_effective": str(b4),
        "spectrum": "3[(4,2,1)+(4bar,1,2)]_Weyl + (1,2,2)_complex + 2(6,1,3)_real + 4(15,1,1)_real + 3(1,1,3)_real",
        "hypercharge_matching": "alpha1^{-1}=(3/5) alpha2R^{-1}+(2/5) alpha4^{-1}",
    }


@dataclass(frozen=True)
class ISDLCTCPSOneLoopGaugeModel:
    """ISDLC--TCPS one-loop gauge-coupling selection test.

    The model is deliberately scored only on M_Z-scale gauge quantities.  It
    does not claim a completed Thomson-limit alpha(0) derivation because that
    requires charged-fermion masses, hadronic vacuum polarization, and scheme
    thresholds.  It also keeps the cosmological ansatz out of the gauge score.
    """

    reduced_planck_mass_gev: float = 2.435e18
    clock_high: int = 6
    clock_low: int = 13
    name: str = "ISDLC--TCPS one-loop gauge-coupling selection"
    free_parameters: tuple[str, ...] = tuple()

    def _prediction_values(self, bench: BenchmarkData) -> dict[str, float]:
        if self.clock_high <= 0 or self.clock_low <= 0:
            raise ValueError("TCPS clock intervals must be positive integers.")
        alpha_u_inv = float(_isdlc_alpha_u_inv_exact())
        m_u = self.reduced_planck_mass_gev / _dn_root_count(5)
        log_total = log(m_u / bench.mz_gev.value)
        total_ticks = self.clock_high + self.clock_low
        ln_u_i = self.clock_high / total_ticks * log_total
        ln_i_z = self.clock_low / total_ticks * log_total
        m_i = bench.mz_gev.value * exp(ln_i_z)

        b_sm = (Fraction(41, 10), Fraction(-19, 6), Fraction(-7, 1))
        beta = _ps_beta_audit_exact()
        b_ps_eff = tuple(Fraction(str(beta[k])) for k in ("B1_PS_effective", "B2_PS_effective", "B3_PS_effective"))
        alpha_inv = [
            alpha_u_inv + float(b_sm[i]) / (2.0 * pi) * ln_i_z + float(b_ps_eff[i]) / (2.0 * pi) * ln_u_i
            for i in range(3)
        ]
        alpha1_inv, alpha2_inv, alpha3_inv = alpha_inv
        alpha_em_inv = (5.0 / 3.0) * alpha1_inv + alpha2_inv
        sin2 = alpha2_inv / alpha_em_inv
        alpha_s = 1.0 / alpha3_inv
        return {
            "alpha_u_inv": alpha_u_inv,
            "alpha_u": 1.0 / alpha_u_inv,
            "g_u": sqrt(4.0 * pi / alpha_u_inv),
            "m_u_gev": m_u,
            "m_i_gev": m_i,
            "ln_MU_MI": ln_u_i,
            "ln_MI_MZ": ln_i_z,
            "alpha1_inv_mz": alpha1_inv,
            "alpha2_inv_mz": alpha2_inv,
            "alpha3_inv_mz": alpha3_inv,
            "alpha_em_inv_mz": alpha_em_inv,
            "sin2theta_hat_mz": sin2,
            "alpha3_mz": alpha_s,
            "e_mz": sqrt(4.0 * pi / alpha_em_inv),
            "g1_mz": sqrt(4.0 * pi / alpha1_inv),
            "gY_mz": sqrt((3.0 / 5.0) * 4.0 * pi / alpha1_inv),
            "g2_mz": sqrt(4.0 * pi / alpha2_inv),
            "g3_mz": sqrt(4.0 * pi / alpha3_inv),
        }

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        v = self._prediction_values(bench)
        return {
            "alpha_em_inv_mz": Prediction(
                "alpha_em_inv_mz",
                v["alpha_em_inv_mz"],
                derived=True,
                note="TCPS one-loop prediction for the MSbar electromagnetic coupling at M_Z.",
            ),
            "sin2theta_hat_mz": Prediction(
                "sin2theta_hat_mz",
                v["sin2theta_hat_mz"],
                derived=True,
                note="TCPS one-loop prediction from alpha2^{-1}/alpha_em^{-1}.",
            ),
            "alpha3_mz": Prediction(
                "alpha3_mz",
                v["alpha3_mz"],
                derived=True,
                note="TCPS one-loop prediction for alpha_s(M_Z).",
            ),
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        v = self._prediction_values(bench)
        needed_ir_shift = bench.alpha0_inv.value - v["alpha_em_inv_mz"]
        return {
            "logical_status": "conditional on the ISDLC no-modulus/self-dual-line-code axioms and the TCPS discrete clock data; not an established consequence of known QFT or quantum gravity",
            "exact_counts": {
                "D5_root_count": _dn_root_count(5),
                "D5_rank": 5,
                "b2_T3": 3,
                "alpha_U_inv_exact": str(_isdlc_alpha_u_inv_exact()),
            },
            "transition_clock": {
                "M_U_formula": "reduced M_Pl / |Delta(D5)| = Mplbar/40",
                "M_U_GeV": v["m_u_gev"],
                "clock_ratio_ln_MU_MI_to_ln_MI_MZ": f"{self.clock_high}:{self.clock_low}",
                "M_I_GeV": v["m_i_gev"],
                "ln_MU_MI": v["ln_MU_MI"],
                "ln_MI_MZ": v["ln_MI_MZ"],
            },
            "beta_audit_exact": _ps_beta_audit_exact(),
            "unscored_internal_couplings": {
                "alpha1_inv_mz": v["alpha1_inv_mz"],
                "alpha2_inv_mz": v["alpha2_inv_mz"],
                "alpha3_inv_mz": v["alpha3_inv_mz"],
                "e_mz": v["e_mz"],
                "g1_mz": v["g1_mz"],
                "gY_mz": v["gY_mz"],
                "g2_mz": v["g2_mz"],
                "g3_mz": v["g3_mz"],
            },
            "alpha0_status": {
                "not_predicted_by_pure_TCPS": True,
                "required_inverse_coupling_IR_shift_alpha0_minus_alphaMZ": needed_ir_shift,
                "reason": "alpha(0) needs charged-lepton thresholds, hadronic vacuum polarization, and electroweak/scheme matching, which are not fixed by the one-loop TCPS gauge clock alone.",
            },
        }


@dataclass(frozen=True)
class ISDLCTCPSCosmologicalAnsatzModel:
    """ISDLC--TCPS torsion-instanton vacuum-energy ansatz stress test.

    This is intentionally marked as an ansatz stress test, not a completed
    determinant calculation.  It tests the commonly proposed prefactor
    (4*pi)^4 exp(-93*pi) against the engine's cosmological benchmarks.
    """

    name: str = "ISDLC--TCPS torsion-instanton vacuum-energy ansatz"
    free_parameters: tuple[str, ...] = ("normalization convention / zero-mode determinant",)

    def _rho_planck4_prediction(self) -> float:
        return (4.0 * pi) ** 4 * exp(-93.0 * pi)

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        # The ansatz is a dimensionless density in Planck units, not literally Lambda*l_P^2.
        # The engine target added below uses rho_Lambda/M_Pl^4 = Lambda*l_P^2/(8*pi).
        return {
            "rhoLambda_planck4": Prediction(
                "rhoLambda_planck4",
                self._rho_planck4_prediction(),
                derived=True,
                note="Stress test of (4*pi)^4 exp(-93*pi); determinant/prefactor is not derived from a specified microscopic Hamiltonian here.",
            )
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        obs_lambda_lp2 = lambda_from_flat_lcdm(bench).lambda_planck_units
        obs_rho = obs_lambda_lp2 / (8.0 * pi)
        pred = self._rho_planck4_prediction()
        return {
            "prediction_formula": "rho_Lambda/M_Pl^4 = (4*pi)^4 exp(-93*pi)",
            "predicted_rhoLambda_planck4": pred,
            "observed_Lambda_lP2": obs_lambda_lp2,
            "observed_rhoLambda_planck4_using_Lambda_lP2_over_8pi": obs_rho,
            "ratio_predicted_to_observed_rho": pred / obs_rho,
            "caveat": "order-of-magnitude interesting, but not a precision derivation until the zero-mode determinant and normalization are derived.",
        }


def default_models() -> list[CandidateModel]:
    return [
        StandardModelBoundaryModel(),
        ISDLCTCPSOneLoopGaugeModel(),
        ISDLCTCPSCosmologicalAnsatzModel(),
        NonSUSYSU5OneLoopModel(),
        MSSMOneLoopUnificationModel(1_000.0),
        MSSMOneLoopUnificationModel(10_000.0),
        PlanckCutoffVacuumEnergyModel(),
        GeometricAlphaToyModel(),
    ]

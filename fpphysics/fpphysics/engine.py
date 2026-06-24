"""Evaluation engine for candidate derivations."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, sqrt
from typing import Iterable

import numpy as np

from .candidate_models import CandidateModel, Prediction, default_models
from .constants import BenchmarkData, Quantity, load_benchmarks
from .cosmology import lambda_from_flat_lcdm
from .rge import electroweak_to_gut_normalized
from .sm import minimal_sm_free_parameter_count, standard_model_parameter_statuses


@dataclass(frozen=True)
class Target:
    name: str
    value: float
    sigma: float | None
    unit: str = "dimensionless"
    note: str = ""


@dataclass(frozen=True)
class ScoredPrediction:
    prediction: Prediction
    target: Target
    residual: float
    sigma_combined: float | None
    z: float | None
    counted_as_prediction: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.prediction.name,
            "prediction": self.prediction.as_dict(),
            "target": {
                "name": self.target.name,
                "value": self.target.value,
                "sigma": self.target.sigma,
                "unit": self.target.unit,
                "note": self.target.note,
            },
            "residual": self.residual,
            "sigma_combined": self.sigma_combined,
            "z": self.z,
            "counted_as_prediction": self.counted_as_prediction,
        }


@dataclass(frozen=True)
class EvaluationResult:
    model_name: str
    free_parameters: tuple[str, ...]
    scores: dict[str, ScoredPrediction]
    chi2_predictive: float | None
    dof_predictive: int
    diagnostics: dict[str, object] = field(default_factory=dict)

    @property
    def max_abs_z_predictive(self) -> float | None:
        z_values = [abs(s.z) for s in self.scores.values() if s.counted_as_prediction and s.z is not None]
        if not z_values:
            return None
        return max(z_values)

    @property
    def verdict(self) -> str:
        if self.dof_predictive == 0:
            return "control_or_no_genuine_predictions"
        max_z = self.max_abs_z_predictive
        if max_z is None:
            return "unscored_prediction"
        if max_z < 2:
            return "passes_current_scored_tests"
        if max_z < 5:
            return "tension"
        return "fails_current_scored_tests"

    def as_dict(self) -> dict[str, object]:
        return {
            "model_name": self.model_name,
            "free_parameters": self.free_parameters,
            "scores": {k: v.as_dict() for k, v in self.scores.items()},
            "chi2_predictive": self.chi2_predictive,
            "dof_predictive": self.dof_predictive,
            "max_abs_z_predictive": self.max_abs_z_predictive,
            "verdict": self.verdict,
            "diagnostics": self.diagnostics,
        }


class DerivationEngine:
    """Run and score candidate derivations against benchmark constants."""

    def __init__(self, bench: BenchmarkData | None = None):
        self.bench = bench or load_benchmarks()
        self.targets = self._make_targets(self.bench)

    @staticmethod
    def _make_targets(bench: BenchmarkData) -> dict[str, Target]:
        couplings = electroweak_to_gut_normalized(
            bench.alpha_hat_5_mz_inv.value,
            bench.sin2theta_hat_mz.value,
            bench.alpha_s_mz.value,
            bench.mz_gev.value,
        )
        alpha_inv_sigma = bench.alpha_hat_5_mz_inv.sigma or 0.0
        s2_sigma = bench.sin2theta_hat_mz.sigma or 0.0
        alpha1_inv = 1.0 / couplings.alpha1
        alpha2_inv = 1.0 / couplings.alpha2
        # alpha1_inv = (3/5)(1-s2) alpha_em_inv
        sigma_alpha1_inv = sqrt(((3.0 / 5.0) * (1.0 - bench.sin2theta_hat_mz.value) * alpha_inv_sigma) ** 2 + ((3.0 / 5.0) * bench.alpha_hat_5_mz_inv.value * s2_sigma) ** 2)
        # alpha2_inv = s2 alpha_em_inv
        sigma_alpha2_inv = sqrt((bench.sin2theta_hat_mz.value * alpha_inv_sigma) ** 2 + (bench.alpha_hat_5_mz_inv.value * s2_sigma) ** 2)
        lam = lambda_from_flat_lcdm(bench)
        rel_lam = 0.0
        if bench.omega_lambda.sigma is not None:
            rel_lam += (bench.omega_lambda.sigma / bench.omega_lambda.value) ** 2
        if bench.h0_km_s_mpc.sigma is not None:
            rel_lam += (2.0 * bench.h0_km_s_mpc.sigma / bench.h0_km_s_mpc.value) ** 2
        sigma_lam = lam.lambda_m2 * sqrt(rel_lam)
        rel_lam_lp2 = rel_lam
        if bench.newton_G.sigma is not None:
            # lP^2 proportional to G.
            rel_lam_lp2 += (bench.newton_G.sigma / bench.newton_G.value) ** 2
        sigma_lam_lp2 = lam.lambda_planck_units * sqrt(rel_lam_lp2)
        sigma_rho_planck4 = sigma_lam_lp2 / (8.0 * np.pi)
        return {
            "alpha0_inv": Target("alpha0_inv", bench.alpha0_inv.value, bench.alpha0_inv.sigma),
            "alpha_em_inv_mz": Target("alpha_em_inv_mz", bench.alpha_hat_5_mz_inv.value, bench.alpha_hat_5_mz_inv.sigma),
            "sin2theta_hat_mz": Target("sin2theta_hat_mz", bench.sin2theta_hat_mz.value, bench.sin2theta_hat_mz.sigma),
            "alpha1_inv_mz": Target("alpha1_inv_mz", alpha1_inv, sigma_alpha1_inv),
            "alpha2_inv_mz": Target("alpha2_inv_mz", alpha2_inv, sigma_alpha2_inv),
            "alpha3_mz": Target("alpha3_mz", bench.alpha_s_mz.value, bench.alpha_s_mz.sigma),
            "Lambda_m^-2": Target("Lambda_m^-2", lam.lambda_m2, sigma_lam, "m^-2"),
            "Lambda_lP^2": Target("Lambda_lP^2", lam.lambda_planck_units, sigma_lam_lp2),
            "rhoLambda_planck4": Target("rhoLambda_planck4", lam.lambda_planck_units / (8.0 * np.pi), sigma_rho_planck4),
        }

    def score_prediction(self, pred: Prediction) -> ScoredPrediction | None:
        target = self.targets.get(pred.name)
        if target is None:
            return None
        residual = pred.value - target.value
        sigma_sq = 0.0
        if target.sigma is not None:
            sigma_sq += target.sigma**2
        if pred.sigma_theory is not None:
            sigma_sq += pred.sigma_theory**2
        sigma = sqrt(sigma_sq) if sigma_sq > 0 else None
        z = residual / sigma if sigma is not None and sigma > 0 else None
        counted = bool(pred.derived and not pred.fitted)
        return ScoredPrediction(pred, target, residual, sigma, z, counted)

    def evaluate(self, model: CandidateModel) -> EvaluationResult:
        predictions = model.predict(self.bench)
        scores: dict[str, ScoredPrediction] = {}
        chi2 = 0.0
        dof = 0
        for key, pred in predictions.items():
            scored = self.score_prediction(pred)
            if scored is None:
                continue
            scores[key] = scored
            if scored.counted_as_prediction and scored.z is not None and isfinite(scored.z):
                chi2 += scored.z**2
                dof += 1
        return EvaluationResult(
            model_name=model.name,
            free_parameters=tuple(model.free_parameters),
            scores=scores,
            chi2_predictive=chi2 if dof else None,
            dof_predictive=dof,
            diagnostics=model.diagnostics(self.bench),
        )

    def evaluate_default_models(self) -> list[EvaluationResult]:
        return [self.evaluate(model) for model in default_models()]

    def audit_status(self) -> dict[str, object]:
        return {
            "sm_parameter_statuses": [
                {
                    "symbol": s.symbol,
                    "description": s.description,
                    "status": s.status.value,
                    "reason": s.reason,
                }
                for s in standard_model_parameter_statuses()
            ],
            "minimal_sm_parameter_count_without_neutrinos_plus_gravity": minimal_sm_free_parameter_count(
                include_neutrino_masses=False, include_gravity=True
            ),
            "minimal_sm_parameter_count_with_neutrinos_plus_gravity": minimal_sm_free_parameter_count(
                include_neutrino_masses=True, include_gravity=True
            ),
            "targets": {k: v.__dict__ for k, v in self.targets.items()},
        }

"""One-loop renormalization-group utilities.

Conventions
-----------
For gauge couplings alpha_i = g_i^2/(4*pi), the one-loop beta function is

    d alpha_i / d ln(mu) = (b_i / 2*pi) alpha_i^2

so

    d alpha_i^{-1} / d ln(mu) = - b_i / (2*pi).

Integrating from mu_low to mu_high gives

    alpha_i^{-1}(mu_low) = alpha_i^{-1}(mu_high)
                              + b_i/(2*pi) ln(mu_high/mu_low).

The U(1) coupling alpha_1 is GUT normalized: alpha_1=(5/3) alpha_Y.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, pi, sqrt
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class GaugeCouplings:
    """Gauge couplings in GUT normalization at a reference scale."""

    mu_gev: float
    alpha1: float
    alpha2: float
    alpha3: float

    @property
    def alpha_inv(self) -> np.ndarray:
        return np.array([1.0 / self.alpha1, 1.0 / self.alpha2, 1.0 / self.alpha3], dtype=float)

    @property
    def alphas(self) -> np.ndarray:
        return np.array([self.alpha1, self.alpha2, self.alpha3], dtype=float)

    @property
    def gs(self) -> np.ndarray:
        return np.sqrt(4.0 * pi * self.alphas)

    def as_dict(self) -> dict[str, float]:
        g1, g2, g3 = self.gs
        return {
            "mu_gev": self.mu_gev,
            "alpha1": self.alpha1,
            "alpha2": self.alpha2,
            "alpha3": self.alpha3,
            "alpha1_inv": 1 / self.alpha1,
            "alpha2_inv": 1 / self.alpha2,
            "alpha3_inv": 1 / self.alpha3,
            "g1": g1,
            "g2": g2,
            "g3": g3,
        }


def electroweak_to_gut_normalized(
    alpha_em_inv_mz: float,
    sin2theta_mz: float,
    alpha_s_mz: float,
    mz_gev: float,
) -> GaugeCouplings:
    """Convert MSbar electroweak inputs to GUT-normalized alpha_1, alpha_2, alpha_3.

    alpha_1 = (5/3) alpha_Y = (5/3) alpha_em / cos^2(theta_W)
    alpha_2 = alpha_em / sin^2(theta_W)
    alpha_3 = alpha_s
    """

    if not (0.0 < sin2theta_mz < 1.0):
        raise ValueError("sin2theta_mz must lie in (0, 1).")
    if alpha_em_inv_mz <= 0.0 or alpha_s_mz <= 0.0 or mz_gev <= 0.0:
        raise ValueError("Couplings and scale must be positive.")
    alpha_em = 1.0 / alpha_em_inv_mz
    cos2 = 1.0 - sin2theta_mz
    alpha1 = (5.0 / 3.0) * alpha_em / cos2
    alpha2 = alpha_em / sin2theta_mz
    return GaugeCouplings(mz_gev, alpha1, alpha2, alpha_s_mz)


def run_alpha_inv_1loop(alpha_inv_start: Sequence[float], b: Sequence[float], mu_start: float, mu_end: float) -> np.ndarray:
    """Run inverse gauge couplings from mu_start to mu_end at one loop."""

    if mu_start <= 0.0 or mu_end <= 0.0:
        raise ValueError("Scales must be positive.")
    alpha_inv = np.asarray(alpha_inv_start, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if alpha_inv.shape != b_arr.shape:
        raise ValueError("alpha_inv_start and b must have the same shape.")
    return alpha_inv - b_arr / (2.0 * pi) * log(mu_end / mu_start)


@dataclass(frozen=True)
class OneLoopUnificationResult:
    """Result of fitting a one-loop unification hypothesis."""

    model_name: str
    alpha_u_inv: float
    m_u_gev: float
    predicted_alpha_inv_mz: np.ndarray
    input_alpha_inv_mz: np.ndarray
    residual_alpha_inv: np.ndarray
    b_low: tuple[float, float, float]
    b_high: tuple[float, float, float] | None = None
    threshold_gev: float | None = None
    fit_pair: tuple[int, int] = (0, 1)

    @property
    def predicted_alphas_mz(self) -> np.ndarray:
        return 1.0 / self.predicted_alpha_inv_mz

    @property
    def alpha_u(self) -> float:
        return 1.0 / self.alpha_u_inv

    def as_dict(self) -> dict[str, object]:
        return {
            "model_name": self.model_name,
            "alpha_u_inv": self.alpha_u_inv,
            "alpha_u": self.alpha_u,
            "m_u_gev": self.m_u_gev,
            "predicted_alpha_inv_mz": self.predicted_alpha_inv_mz.tolist(),
            "predicted_alphas_mz": self.predicted_alphas_mz.tolist(),
            "input_alpha_inv_mz": self.input_alpha_inv_mz.tolist(),
            "residual_alpha_inv": self.residual_alpha_inv.tolist(),
            "b_low": self.b_low,
            "b_high": self.b_high,
            "threshold_gev": self.threshold_gev,
            "fit_pair": self.fit_pair,
        }


SM_B = (41.0 / 10.0, -19.0 / 6.0, -7.0)
MSSM_B = (33.0 / 5.0, 1.0, -3.0)


def fit_one_loop_unification(
    alpha_inv_mz: Sequence[float],
    mz_gev: float,
    b: Sequence[float] = SM_B,
    fit_pair: tuple[int, int] = (0, 1),
    model_name: str = "one-loop unification",
) -> OneLoopUnificationResult:
    """Fit alpha_U and M_U from two couplings and predict the third.

    This is not a zero-parameter derivation: alpha_U and M_U are inferred from
    two low-energy inputs.  The third coupling is then a genuine prediction of
    the one-loop unification ansatz.
    """

    alpha_inv = np.asarray(alpha_inv_mz, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    i, j = fit_pair
    denom = b_arr[i] - b_arr[j]
    if abs(denom) < 1e-15:
        raise ValueError("Chosen pair has degenerate beta-function coefficients.")
    log_mu = (alpha_inv[i] - alpha_inv[j]) * (2.0 * pi) / denom
    m_u = mz_gev * exp(log_mu)
    alpha_u_inv = alpha_inv[i] - b_arr[i] / (2.0 * pi) * log_mu
    predicted = alpha_u_inv + b_arr / (2.0 * pi) * log_mu
    return OneLoopUnificationResult(
        model_name=model_name,
        alpha_u_inv=float(alpha_u_inv),
        m_u_gev=float(m_u),
        predicted_alpha_inv_mz=predicted,
        input_alpha_inv_mz=alpha_inv,
        residual_alpha_inv=predicted - alpha_inv,
        b_low=tuple(float(x) for x in b_arr),
        fit_pair=fit_pair,
    )


def fit_one_loop_unification_with_threshold(
    alpha_inv_mz: Sequence[float],
    mz_gev: float,
    threshold_gev: float,
    b_low: Sequence[float] = SM_B,
    b_high: Sequence[float] = MSSM_B,
    fit_pair: tuple[int, int] = (0, 1),
    model_name: str = "one-loop threshold unification",
) -> OneLoopUnificationResult:
    """Fit unification with one sharp threshold between two beta-function regimes.

    The formula used is

      alpha_i^-1(M_Z) = alpha_U^-1
                      + b_high_i/(2*pi) ln(M_U/M_threshold)
                      + b_low_i /(2*pi) ln(M_threshold/M_Z).
    """

    if threshold_gev <= mz_gev:
        raise ValueError("threshold_gev must be above mz_gev.")
    alpha_inv = np.asarray(alpha_inv_mz, dtype=float)
    b_l = np.asarray(b_low, dtype=float)
    b_h = np.asarray(b_high, dtype=float)
    i, j = fit_pair
    threshold_log = log(threshold_gev / mz_gev)
    adjusted_diff = (
        alpha_inv[i]
        - alpha_inv[j]
        - (b_l[i] - b_l[j]) / (2.0 * pi) * threshold_log
    )
    denom = b_h[i] - b_h[j]
    if abs(denom) < 1e-15:
        raise ValueError("Chosen pair has degenerate high-energy beta coefficients.")
    log_high = adjusted_diff * (2.0 * pi) / denom
    m_u = threshold_gev * exp(log_high)
    alpha_u_inv = (
        alpha_inv[i]
        - b_h[i] / (2.0 * pi) * log_high
        - b_l[i] / (2.0 * pi) * threshold_log
    )
    predicted = alpha_u_inv + b_h / (2.0 * pi) * log_high + b_l / (2.0 * pi) * threshold_log
    return OneLoopUnificationResult(
        model_name=model_name,
        alpha_u_inv=float(alpha_u_inv),
        m_u_gev=float(m_u),
        predicted_alpha_inv_mz=predicted,
        input_alpha_inv_mz=alpha_inv,
        residual_alpha_inv=predicted - alpha_inv,
        b_low=tuple(float(x) for x in b_l),
        b_high=tuple(float(x) for x in b_h),
        threshold_gev=float(threshold_gev),
        fit_pair=fit_pair,
    )


def least_squares_meeting_scale(alpha_inv_mz: Sequence[float], mz_gev: float, b: Sequence[float] = SM_B) -> dict[str, float]:
    """Find the scale where the three one-loop inverse couplings are closest.

    This is diagnostic, not a physical fit with thresholds.  It minimizes the
    variance of alpha_i^-1(mu) across i in closed form.
    """

    y = np.asarray(alpha_inv_mz, dtype=float)
    beta = -np.asarray(b, dtype=float) / (2.0 * pi)  # y(mu)=y(MZ)+beta*t, t=ln(mu/MZ)
    beta_centered = beta - beta.mean()
    y_centered = y - y.mean()
    denom = float(np.dot(beta_centered, beta_centered))
    if denom <= 0:
        raise ValueError("Degenerate beta coefficients.")
    t = -float(np.dot(y_centered, beta_centered)) / denom
    y_at = y + beta * t
    return {
        "mu_gev": mz_gev * exp(t),
        "log_mu_over_mz": t,
        "mean_alpha_inv": float(y_at.mean()),
        "std_alpha_inv": float(y_at.std(ddof=0)),
        "alpha_inv_at_scale_1": float(y_at[0]),
        "alpha_inv_at_scale_2": float(y_at[1]),
        "alpha_inv_at_scale_3": float(y_at[2]),
    }

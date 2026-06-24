"""GPU-assisted search for frozen holdout-resistant formula candidates.

This module is deliberately not a proof engine.  It searches compact formula
families quickly, freezes the best packets, and immediately stress-tests them
against the strict academic external audit already bundled with the project.

If a candidate is selected using the bundled registry, it is not a final
external-blind success.  It becomes a new frozen candidate that needs a future
unseen tranche.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .academic_external_holdout import audit_packet
from .blind_protocol import BlindPredictionProtocol, PredictionPacket, default_observation_registry


REDUCED_PLANCK_MASS_GEV = 2.435e18
ALPHA_U_INV = 93.0 / 2.0
PLANCK_DIVISOR = 40
MU_GEV = REDUCED_PLANCK_MASS_GEV / PLANCK_DIVISOR
GEV_INV_TO_YEARS = 6.582119569e-25 / 31_557_600.0
PROTON_MASS_GEV = 0.9382720813


@dataclass(frozen=True)
class SearchConfig:
    candidates: int = 200_000
    seed: int = 613
    top_k: int = 12
    device: str = "auto"
    chunk_size: int = 250_000
    gpu_dtype: str = "float32"
    progress_every: int = 20

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchCandidate:
    rank: int
    objective: float
    bundled_blind_chi2: float
    academic_external_precision_chi2: float | None
    academic_external_max_abs_z: float | None
    academic_external_precision_failure_count: int
    academic_external_not_scoreable_count: int
    academic_external_verdict: str
    params: dict[str, Any]
    predictions: dict[str, float | str]
    packet_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def conservative_dim6_proton_lifetime_years(mx_gev: float = MU_GEV) -> float:
    alpha_u = 1.0 / ALPHA_U_INV
    gamma_gev = 10.0 * (alpha_u**2) * (PROTON_MASS_GEV**5) / (mx_gev**4)
    return (1.0 / gamma_gev) * GEV_INV_TO_YEARS


def _torch_backend(device: str):
    try:
        import torch  # type: ignore
    except Exception:
        return None, "numpy-cpu"
    if device == "cpu":
        return torch, "torch-cpu"
    if device in {"auto", "cuda"} and torch.cuda.is_available():
        return torch, "torch-cuda"
    if device == "cuda":
        raise RuntimeError("CUDA requested but torch.cuda.is_available() is false")
    return torch, "torch-cpu"


def _torch_dtype(torch: Any, name: str):
    if name == "float64":
        return torch.float64
    if name == "float32":
        return torch.float32
    raise ValueError(f"Unsupported torch dtype: {name}")


def _observed_registry() -> dict[str, tuple[float | str, float | None, str]]:
    obs = {}
    for item in default_observation_registry():
        if item.split == "blind" and item.required:
            obs[item.key] = (item.value, item.sigma, item.kind)
    return obs


def _external_targets() -> dict[str, tuple[float, float, str]]:
    return {
        "CKM_abs_Vtd": (0.00858, 0.00019, "gaussian"),
        "CKM_abs_Vts": (0.04111, 0.00077, "gaussian"),
        "CKM_abs_Vtb": (0.999118, 0.000034, "gaussian"),
        "CKM_gamma_deg": (65.7, 3.0, "gaussian"),
        "CKM_sin2beta": (0.709, 0.011, "gaussian"),
        "neutrino_sum_masses_eV": (0.12, 0.30, "upper_bound_log"),
        "beta_decay_mbeta_eV": (0.45, 0.30, "upper_bound_log"),
    }


def _score_bundle_np(pred: dict[str, np.ndarray]) -> np.ndarray:
    obs = _observed_registry()
    score = np.zeros_like(pred["Vus"], dtype=np.float64)
    for key, (target, sigma, kind) in obs.items():
        if key == "neutrino_ordering":
            continue
        if key in {"tau_p_to_e_pi0_years", "threshold_lightest_new_charged_gev", "threshold_lightest_new_colored_gev"}:
            p = pred[key]
            t = float(target)
            bad = p < t
            score += np.where(bad, (np.log10(np.maximum(t / np.maximum(p, 1e-300), 1.0)) / 0.30) ** 2, 0.0)
            continue
        p = pred.get(key)
        if p is None:
            score += 100.0
            continue
        t = float(target)
        sig = float(sigma or max(abs(t) * 0.01, 1e-12))
        if kind == "upper_bound":
            score += np.where(p <= t, 0.0, (np.log10(np.maximum(p / t, 1.0)) / (sigma or 0.30)) ** 2)
        elif kind == "lower_bound":
            score += np.where(p >= t, 0.0, (np.log10(np.maximum(t / np.maximum(p, 1e-300), 1.0)) / (sigma or 0.30)) ** 2)
        else:
            score += ((p - t) / sig) ** 2
    return score


def _score_external_np(pred: dict[str, np.ndarray]) -> np.ndarray:
    score = np.zeros_like(pred["Vus"], dtype=np.float64)
    for key, (target, sigma, kind) in _external_targets().items():
        p = pred[key]
        if kind == "upper_bound_log":
            score += np.where(p <= target, 0.0, (np.log10(np.maximum(p / target, 1.0)) / sigma) ** 2)
        else:
            score += ((p - target) / sigma) ** 2
    return score


def _score_bundle_torch(pred: dict[str, np.ndarray], torch: Any, dtype_name: str = "float32") -> np.ndarray:
    device = torch.device("cuda")
    dtype = _torch_dtype(torch, dtype_name)
    tensors = {k: torch.as_tensor(v, dtype=dtype, device=device) for k, v in pred.items()}
    return _score_bundle_torch_tensors(tensors, torch).detach().cpu().numpy()


def _score_bundle_torch_tensors(tensors: dict[str, Any], torch: Any):
    device = tensors["Vus"].device
    dtype = tensors["Vus"].dtype
    tiny = torch.finfo(dtype).tiny
    score = torch.zeros_like(tensors["Vus"], dtype=dtype, device=device)
    for key, (target, sigma, kind) in _observed_registry().items():
        if key == "neutrino_ordering":
            continue
        if key in {"tau_p_to_e_pi0_years", "threshold_lightest_new_charged_gev", "threshold_lightest_new_colored_gev"}:
            p = tensors[key]
            t = float(target)
            score = score + torch.where(
                p < t,
                (torch.log10(torch.clamp(torch.as_tensor(t, dtype=dtype, device=device) / torch.clamp(p, min=tiny), min=1.0)) / 0.30) ** 2,
                torch.zeros_like(score),
            )
            continue
        if key not in tensors:
            score = score + 100.0
            continue
        p = tensors[key]
        t = float(target)
        sig = float(sigma or max(abs(t) * 0.01, 1e-12))
        if kind == "upper_bound":
            score = score + torch.where(p <= t, torch.zeros_like(score), (torch.log10(torch.clamp(p / t, min=1.0)) / float(sigma or 0.30)) ** 2)
        elif kind == "lower_bound":
            score = score + torch.where(
                p >= t,
                torch.zeros_like(score),
                (torch.log10(torch.clamp(torch.as_tensor(t, dtype=dtype, device=device) / torch.clamp(p, min=tiny), min=1.0)) / float(sigma or 0.30)) ** 2,
            )
        else:
            score = score + ((p - t) / sig) ** 2
    return score


def _score_external_torch(pred: dict[str, np.ndarray], torch: Any, dtype_name: str = "float32") -> np.ndarray:
    device = torch.device("cuda")
    dtype = _torch_dtype(torch, dtype_name)
    tensors = {k: torch.as_tensor(v, dtype=dtype, device=device) for k, v in pred.items()}
    return _score_external_torch_tensors(tensors, torch).detach().cpu().numpy()


def _score_external_torch_tensors(tensors: dict[str, Any], torch: Any):
    device = tensors["Vus"].device
    dtype = tensors["Vus"].dtype
    score = torch.zeros_like(tensors["Vus"], dtype=dtype, device=device)
    for key, (target, sigma, kind) in _external_targets().items():
        p = tensors[key]
        if kind == "upper_bound_log":
            score = score + torch.where(p <= target, torch.zeros_like(score), (torch.log10(torch.clamp(p / target, min=1.0)) / sigma) ** 2)
        else:
            score = score + ((p - target) / sigma) ** 2
    return score


def _ckm_external(lam: np.ndarray, vcb: np.ndarray, vub: np.ndarray, j: np.ndarray) -> dict[str, np.ndarray]:
    a = vcb / np.maximum(lam**2, 1e-12)
    radius = vub / np.maximum(a * lam**3, 1e-12)
    eta = j / np.maximum((a**2) * (lam**6), 1e-18)
    eta = np.clip(eta, 1e-9, None)
    rho_sq = np.maximum(radius**2 - eta**2, 1e-12)
    rho = np.sqrt(rho_sq)
    beta = np.arctan2(eta, 1.0 - rho)
    gamma = np.arctan2(eta, rho)
    return {
        "CKM_abs_Vtd": a * lam**3 * np.sqrt((1.0 - rho) ** 2 + eta**2),
        "CKM_abs_Vts": a * lam**2,
        "CKM_abs_Vtb": 1.0 - 0.5 * (a**2) * (lam**4),
        "CKM_gamma_deg": gamma * 180.0 / math.pi,
        "CKM_sin2beta": np.sin(2.0 * beta),
    }


def _choice_torch(torch: Any, values: list[float], n: int, device: Any, generator: Any, dtype: Any):
    table = torch.tensor(values, dtype=dtype, device=device)
    idx = torch.randint(0, len(values), (n,), device=device, generator=generator)
    return table[idx]


def _ckm_external_torch(torch: Any, lam: Any, vcb: Any, vub: Any, j: Any) -> dict[str, Any]:
    a = vcb / torch.clamp(lam**2, min=1e-12)
    radius = vub / torch.clamp(a * lam**3, min=1e-12)
    eta = j / torch.clamp((a**2) * (lam**6), min=1e-18)
    eta = torch.clamp(eta, min=1e-9)
    rho = torch.sqrt(torch.clamp(radius**2 - eta**2, min=1e-12))
    beta = torch.atan2(eta, 1.0 - rho)
    gamma = torch.atan2(eta, rho)
    return {
        "CKM_abs_Vtd": a * lam**3 * torch.sqrt((1.0 - rho) ** 2 + eta**2),
        "CKM_abs_Vts": a * lam**2,
        "CKM_abs_Vtb": 1.0 - 0.5 * (a**2) * (lam**4),
        "CKM_gamma_deg": gamma * 180.0 / math.pi,
        "CKM_sin2beta": torch.sin(2.0 * beta),
    }


def _make_predictions_torch(torch: Any, generator: Any, n: int, device: Any, dtype: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    num = torch.randint(2, 16, (n,), dtype=torch.int64, device=device, generator=generator)
    den = torch.randint(7, 49, (n,), dtype=torch.int64, device=device, generator=generator)
    den = torch.where(num >= den, num + torch.randint(1, 25, (n,), dtype=torch.int64, device=device, generator=generator), den)
    c = torch.randint(2, 6, (n,), dtype=torch.int64, device=device, generator=generator)
    r = num.to(dtype) / den.to(dtype)
    lam = torch.sqrt(r) / c.to(dtype)

    vcb_coeff = _choice_torch(torch, [0.5, 2 / 3, 3 / 4, 5 / 6, math.sqrt(2 / 3), 1.0, 7 / 6], n, device, generator, dtype)
    vub_coeff = _choice_torch(torch, [1 / 4, 1 / 3, 2 / 5, 1 / 2, 2 / 3], n, device, generator, dtype)
    j_coeff = _choice_torch(torch, [1 / 6, 1 / 5, 1 / 4, 1 / 3, 1 / 2], n, device, generator, dtype)
    th12_base = _choice_torch(torch, [1 / 3, 0.30, 0.31, 0.32], n, device, generator, dtype)
    th12_coeff = _choice_torch(torch, [-1.0, -0.5, -1 / 3, 0.0, 1 / 3, 0.5], n, device, generator, dtype)
    th23_sign = _choice_torch(torch, [-1.5, -1.0, -0.5, 0.5, 1.0, 1.5], n, device, generator, dtype)
    th13_coeff = _choice_torch(torch, [1 / 3, 0.5, 2 / 3, 1.0], n, device, generator, dtype)
    solar_div = torch.randint(24, 56, (n,), dtype=torch.int64, device=device, generator=generator)
    m3 = 1.0 / torch.randint(16, 28, (n,), dtype=torch.int64, device=device, generator=generator).to(dtype)
    omega_coeff = _choice_torch(torch, [1 / 3, 1 / 4, 1 / 5, 2 / 7, 3 / 11], n, device, generator, dtype)
    quark_ms_coeff = _choice_torch(torch, [1 / 3, 0.5, 2 / 3], n, device, generator, dtype)
    quark_mc_coeff = _choice_torch(torch, [2.0, 2.5, 3.0, 3.5], n, device, generator, dtype)

    vcb = vcb_coeff * lam**2
    vub = vub_coeff * lam**3
    j = j_coeff * lam**6
    s13 = th13_coeff * lam**2
    s12 = th12_base + th12_coeff * lam**2
    s23 = 0.5 + th23_sign * lam**2
    dm3 = m3**2
    dm21 = dm3 / solar_div.to(dtype)
    m2 = torch.sqrt(dm21)
    m_beta = torch.sqrt(torch.clamp(s12 * (1.0 - s13) * m2**2 + s13 * m3**2, min=0.0))

    pred = {
        "ms_over_mb_2gev_working": quark_ms_coeff * lam**2,
        "mc_over_mt_working": quark_mc_coeff * lam**4,
        "Vus": lam,
        "Vcb": vcb,
        "Vub": vub,
        "Jarlskog_CKM": j,
        "pmns_sin2_theta12": s12,
        "pmns_sin2_theta23": s23,
        "pmns_sin2_theta13": s13,
        "delta_m21_sq_ev2": dm21,
        "abs_delta_m3l_sq_ev2": dm3,
        "rho_parameter": torch.ones(n, dtype=dtype, device=device),
        "tau_p_to_e_pi0_years": torch.full((n,), min(conservative_dim6_proton_lifetime_years(), 1.0e38), dtype=dtype, device=device),
        "threshold_lightest_new_charged_gev": torch.full((n,), MU_GEV, dtype=dtype, device=device),
        "threshold_lightest_new_colored_gev": torch.full((n,), MU_GEV, dtype=dtype, device=device),
        "N_eff": torch.full((n,), 3.044, dtype=dtype, device=device),
        "Omega_c_h2": omega_coeff * r,
        "neutrino_sum_masses_eV": m2 + m3,
        "beta_decay_mbeta_eV": m_beta,
        "proton_p_to_e_pi0_lifetime_years": torch.full((n,), min(conservative_dim6_proton_lifetime_years(), 1.0e38), dtype=dtype, device=device),
        "lightest_new_charged_threshold_GeV": torch.full((n,), MU_GEV, dtype=dtype, device=device),
        "lightest_new_colored_threshold_GeV": torch.full((n,), MU_GEV, dtype=dtype, device=device),
        "quark_ms_over_mb_external": quark_ms_coeff * lam**2,
        "quark_mc_over_mt_external": quark_mc_coeff * lam**4,
    }
    pred.update(_ckm_external_torch(torch, lam, vcb, vub, j))
    params = {
        "clock_num": num,
        "clock_den": den,
        "clock_divisor": c,
        "vcb_coeff": vcb_coeff,
        "vub_coeff": vub_coeff,
        "j_coeff": j_coeff,
        "theta12_base": th12_base,
        "theta12_coeff": th12_coeff,
        "theta23_coeff": th23_sign,
        "theta13_coeff": th13_coeff,
        "solar_divisor": solar_div,
        "m3_eV": m3,
        "omega_coeff": omega_coeff,
        "quark_ms_coeff": quark_ms_coeff,
        "quark_mc_coeff": quark_mc_coeff,
    }
    return pred, params


def _make_predictions_np(rng: np.random.Generator, n: int) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    # Compact integer/rational formula family.  This is a search space, not a
    # derivation claim.
    num = rng.integers(2, 16, size=n)
    den = rng.integers(7, 49, size=n)
    swap = num >= den
    den[swap] = num[swap] + rng.integers(1, 25, size=swap.sum())
    c = rng.integers(2, 6, size=n)
    r = num / den
    lam = np.sqrt(r) / c

    vcb_coeff = rng.choice(np.array([0.5, 2/3, 3/4, 5/6, math.sqrt(2/3), 1.0, 7/6]), size=n)
    vub_coeff = rng.choice(np.array([1/4, 1/3, 2/5, 1/2, 2/3]), size=n)
    j_coeff = rng.choice(np.array([1/6, 1/5, 1/4, 1/3, 1/2]), size=n)
    th12_base = rng.choice(np.array([1/3, 0.30, 0.31, 0.32]), size=n)
    th12_coeff = rng.choice(np.array([-1.0, -0.5, -1/3, 0.0, 1/3, 0.5]), size=n)
    th23_sign = rng.choice(np.array([-1.5, -1.0, -0.5, 0.5, 1.0, 1.5]), size=n)
    th13_coeff = rng.choice(np.array([r.mean() if n else 0.5, 1/3, 0.5, 2/3, 1.0]), size=n)
    solar_div = rng.integers(24, 56, size=n)
    m3 = 1.0 / rng.integers(16, 28, size=n)
    omega_coeff = rng.choice(np.array([1/3, 1/4, 1/5, 2/7, 3/11]), size=n)
    quark_ms_coeff = rng.choice(np.array([1/3, 0.5, 2/3]), size=n)
    quark_mc_coeff = rng.choice(np.array([2.0, 2.5, 3.0, 3.5]), size=n)

    vcb = vcb_coeff * lam**2
    vub = vub_coeff * lam**3
    j = j_coeff * lam**6
    s13 = th13_coeff * lam**2
    s12 = th12_base + th12_coeff * lam**2
    s23 = 0.5 + th23_sign * lam**2
    dm3 = m3**2
    dm21 = dm3 / solar_div
    m2 = np.sqrt(dm21)
    m_beta = np.sqrt(np.maximum((1.0 - s12) * (1.0 - s13) * 0.0 + s12 * (1.0 - s13) * m2**2 + s13 * m3**2, 0.0))

    pred = {
        "ms_over_mb_2gev_working": quark_ms_coeff * lam**2,
        "mc_over_mt_working": quark_mc_coeff * lam**4,
        "Vus": lam,
        "Vcb": vcb,
        "Vub": vub,
        "Jarlskog_CKM": j,
        "pmns_sin2_theta12": s12,
        "pmns_sin2_theta23": s23,
        "pmns_sin2_theta13": s13,
        "delta_m21_sq_ev2": dm21,
        "abs_delta_m3l_sq_ev2": dm3,
        "rho_parameter": np.ones(n),
        "tau_p_to_e_pi0_years": np.full(n, conservative_dim6_proton_lifetime_years()),
        "threshold_lightest_new_charged_gev": np.full(n, MU_GEV),
        "threshold_lightest_new_colored_gev": np.full(n, MU_GEV),
        "N_eff": np.full(n, 3.044),
        "Omega_c_h2": omega_coeff * r,
        "neutrino_sum_masses_eV": m2 + m3,
        "beta_decay_mbeta_eV": m_beta,
        "proton_p_to_e_pi0_lifetime_years": np.full(n, conservative_dim6_proton_lifetime_years()),
        "lightest_new_charged_threshold_GeV": np.full(n, MU_GEV),
        "lightest_new_colored_threshold_GeV": np.full(n, MU_GEV),
        "quark_ms_over_mb_external": quark_ms_coeff * lam**2,
        "quark_mc_over_mt_external": quark_mc_coeff * lam**4,
    }
    pred.update(_ckm_external(lam, vcb, vub, j))
    params = {
        "clock_num": num,
        "clock_den": den,
        "clock_divisor": c,
        "vcb_coeff": vcb_coeff,
        "vub_coeff": vub_coeff,
        "j_coeff": j_coeff,
        "theta12_base": th12_base,
        "theta12_coeff": th12_coeff,
        "theta23_coeff": th23_sign,
        "theta13_coeff": th13_coeff,
        "solar_divisor": solar_div,
        "m3_eV": m3,
        "omega_coeff": omega_coeff,
        "quark_ms_coeff": quark_ms_coeff,
        "quark_mc_coeff": quark_mc_coeff,
    }
    return pred, params


def _scalarize(pred: dict[str, np.ndarray], params: dict[str, np.ndarray], idx: int) -> tuple[dict[str, float | str], dict[str, Any]]:
    keys = [
        "ms_over_mb_2gev_working",
        "mc_over_mt_working",
        "Vus",
        "Vcb",
        "Vub",
        "Jarlskog_CKM",
        "pmns_sin2_theta12",
        "pmns_sin2_theta23",
        "pmns_sin2_theta13",
        "delta_m21_sq_ev2",
        "abs_delta_m3l_sq_ev2",
        "rho_parameter",
        "tau_p_to_e_pi0_years",
        "threshold_lightest_new_charged_gev",
        "threshold_lightest_new_colored_gev",
        "N_eff",
        "Omega_c_h2",
        "CKM_abs_Vtd",
        "CKM_abs_Vts",
        "CKM_abs_Vtb",
        "CKM_gamma_deg",
        "CKM_sin2beta",
        "neutrino_sum_masses_eV",
        "beta_decay_mbeta_eV",
        "proton_p_to_e_pi0_lifetime_years",
        "lightest_new_charged_threshold_GeV",
        "lightest_new_colored_threshold_GeV",
        "quark_ms_over_mb_external",
        "quark_mc_over_mt_external",
    ]
    out = {k: float(pred[k][idx]) for k in keys}
    out["neutrino_ordering"] = "normal"
    p = {k: (int(v[idx]) if np.issubdtype(v.dtype, np.integer) else float(v[idx])) for k, v in params.items()}
    return out, p


def _scalarize_torch(pred: dict[str, Any], params: dict[str, Any], idx: int) -> tuple[dict[str, float | str], dict[str, Any]]:
    keys = [
        "ms_over_mb_2gev_working",
        "mc_over_mt_working",
        "Vus",
        "Vcb",
        "Vub",
        "Jarlskog_CKM",
        "pmns_sin2_theta12",
        "pmns_sin2_theta23",
        "pmns_sin2_theta13",
        "delta_m21_sq_ev2",
        "abs_delta_m3l_sq_ev2",
        "rho_parameter",
        "tau_p_to_e_pi0_years",
        "threshold_lightest_new_charged_gev",
        "threshold_lightest_new_colored_gev",
        "N_eff",
        "Omega_c_h2",
        "CKM_abs_Vtd",
        "CKM_abs_Vts",
        "CKM_abs_Vtb",
        "CKM_gamma_deg",
        "CKM_sin2beta",
        "neutrino_sum_masses_eV",
        "beta_decay_mbeta_eV",
        "proton_p_to_e_pi0_lifetime_years",
        "lightest_new_charged_threshold_GeV",
        "lightest_new_colored_threshold_GeV",
        "quark_ms_over_mb_external",
        "quark_mc_over_mt_external",
    ]
    out = {k: float(pred[k][idx].detach().cpu()) for k in keys}
    out["neutrino_ordering"] = "normal"
    out["tau_p_to_e_pi0_years"] = conservative_dim6_proton_lifetime_years()
    out["threshold_lightest_new_charged_gev"] = MU_GEV
    out["threshold_lightest_new_colored_gev"] = MU_GEV
    out["proton_p_to_e_pi0_lifetime_years"] = conservative_dim6_proton_lifetime_years()
    out["lightest_new_charged_threshold_GeV"] = MU_GEV
    out["lightest_new_colored_threshold_GeV"] = MU_GEV
    p = {k: (int(v[idx].detach().cpu()) if str(v.dtype).endswith("int64") else float(v[idx].detach().cpu())) for k, v in params.items()}
    return out, p


def _packet(predictions: dict[str, float | str], params: dict[str, Any]) -> PredictionPacket:
    return PredictionPacket(
        model_name="GPU-searched ISDLC compact holdout candidate",
        predictions=predictions,
        provenance="GPU batch search over compact rational clock formula family; selected on bundled registry and external stress scores",
        trained_on=("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz", "rhoLambda_planck4"),
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=True,
        notes=(
            "This packet is a search result, not an external-blind success. "
            f"Search parameters: {json.dumps(params, sort_keys=True)}"
        ),
    )


def run_search(config: SearchConfig) -> dict[str, Any]:
    torch, backend = _torch_backend(config.device)
    started = time.perf_counter()
    rng = np.random.default_rng(config.seed)
    best: list[tuple[float, float, dict[str, float | str], dict[str, Any]]] = []
    remaining = config.candidates
    seen = 0
    generator = None
    device = None
    if backend == "torch-cuda" and torch is not None:
        device = torch.device("cuda")
        dtype = _torch_dtype(torch, config.gpu_dtype)
        generator = torch.Generator(device=device)
        generator.manual_seed(config.seed)
    else:
        dtype = None
    chunks = 0
    while remaining > 0:
        n = min(config.chunk_size, remaining)
        if backend == "torch-cuda" and torch is not None:
            pred_t, params_t = _make_predictions_torch(torch, generator, n, device, dtype)
            bundle_t = _score_bundle_torch_tensors(pred_t, torch)
            external_t = _score_external_torch_tensors(pred_t, torch)
            objective_t = bundle_t + 1.5 * external_t
            take = min(config.top_k * 4, n)
            values, idxs = torch.topk(objective_t, k=take, largest=False)
            bundle_values = bundle_t[idxs]
            for value, bundle_value, i in zip(values.detach().cpu().tolist(), bundle_values.detach().cpu().tolist(), idxs.detach().cpu().tolist(), strict=True):
                predictions, params = _scalarize_torch(pred_t, params_t, int(i))
                best.append((float(value), float(bundle_value), predictions, params))
        else:
            pred, params = _make_predictions_np(rng, n)
            bundle = _score_bundle_np(pred)
            external = _score_external_np(pred)
            objective = bundle + 1.5 * external
            take = min(config.top_k * 4, n)
            idxs = np.argpartition(objective, take - 1)[:take]
            for i in idxs:
                predictions, params_scalar = _scalarize(pred, params, int(i))
                best.append((float(objective[i]), float(bundle[i]), predictions, params_scalar))
        best.sort(key=lambda x: x[0])
        best = best[: config.top_k * 6]
        seen += n
        remaining -= n
        chunks += 1
        if config.progress_every > 0 and chunks % config.progress_every == 0:
            elapsed = time.perf_counter() - started
            rate = seen / max(elapsed, 1e-9)
            print(
                json.dumps(
                    {
                        "event": "progress",
                        "backend": backend,
                        "seen": seen,
                        "candidates_per_second": rate,
                        "best_objective": best[0][0] if best else None,
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
                flush=True,
            )

    proto = BlindPredictionProtocol(default_observation_registry())
    ranked: list[SearchCandidate] = []
    used_hashes: set[str] = set()
    for obj, bundle_score, predictions, params in best:
        packet = _packet(predictions, params)
        if packet.sha256 in used_hashes:
            continue
        used_hashes.add(packet.sha256)
        report = proto.score_packet(packet)
        with _temporary_packet(packet) as packet_path:
            external_audit = audit_packet(packet_path)
        summary = external_audit["summary"]
        ranked.append(
            SearchCandidate(
                rank=len(ranked) + 1,
                objective=float(obj),
                bundled_blind_chi2=float(report.split_scores["blind"].chi2),
                academic_external_precision_chi2=summary.get("external_precision_chi2"),
                academic_external_max_abs_z=summary.get("external_precision_max_abs_z"),
                academic_external_precision_failure_count=int(summary.get("precision_failure_count", 0)),
                academic_external_not_scoreable_count=int(summary.get("not_scoreable_count", 0)),
                academic_external_verdict=summary.get("strict_academic_external_tranche_verdict", "UNKNOWN"),
                params=params,
                predictions=predictions,
                packet_sha256=packet.sha256,
            )
        )
        if len(ranked) >= config.top_k:
            break

    strict_pass = [
        c
        for c in ranked
        if c.academic_external_verdict == "PASS"
        and c.academic_external_max_abs_z is not None
        and c.academic_external_max_abs_z <= 3.0
    ]
    precision_pass = [
        c
        for c in ranked
        if c.academic_external_precision_failure_count == 0
        and c.academic_external_max_abs_z is not None
        and c.academic_external_max_abs_z <= 3.0
    ]
    return {
        "config": config.as_dict(),
        "backend": backend,
        "elapsed_seconds": time.perf_counter() - started,
        "candidate_count": config.candidates,
        "summary": {
            "strict_academic_external_pass_candidates": len(strict_pass),
            "precision_external_stress_pass_candidates": len(precision_pass),
            "best_objective": ranked[0].objective if ranked else None,
            "best_academic_external_verdict": ranked[0].academic_external_verdict if ranked else None,
            "strict_warning": (
                "Candidates were selected by search against bundled/current registries. "
                "A future sealed tranche is required before calling any candidate an external-blind success."
            ),
        },
        "candidates": [c.as_dict() for c in ranked],
    }


class _temporary_packet:
    def __init__(self, packet: PredictionPacket):
        self.packet = packet
        self.path = Path("/tmp") / f"fpp_gpu_packet_{packet.sha256}.json"

    def __enter__(self) -> Path:
        self.path.write_text(json.dumps(self.packet.canonical_dict() | {"sha256": self.packet.sha256}, indent=2), encoding="utf-8")
        return self.path

    def __exit__(self, *_: object) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def write_search(run: dict[str, Any], outdir: str | Path) -> dict[str, str]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "gpu_holdout_search_results.json"
    md_path = out / "GPU_HOLDOUT_SEARCH_REPORT_ko.md"
    json_path.write_text(json.dumps(run, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_report_ko(run), encoding="utf-8")
    return {"json": str(json_path), "report": str(md_path)}


def render_report_ko(run: dict[str, Any]) -> str:
    lines = ["# GPU holdout search report", ""]
    lines.append("## 결론")
    lines.append("")
    s = run["summary"]
    lines.append(f"- backend: `{run['backend']}`")
    lines.append(f"- searched candidates: `{run['candidate_count']}`")
    lines.append(f"- elapsed seconds: `{run['elapsed_seconds']:.3f}`")
    lines.append(f"- candidates/sec: `{run['candidate_count'] / max(run['elapsed_seconds'], 1e-9):.3f}`")
    if "config" in run:
        cfg = run["config"]
        lines.append(f"- chunk size: `{cfg.get('chunk_size')}`")
        lines.append(f"- GPU dtype: `{cfg.get('gpu_dtype', 'n/a')}`")
    lines.append(f"- strict academic external pass candidates: `{s['strict_academic_external_pass_candidates']}`")
    lines.append(f"- precision external stress pass candidates: `{s['precision_external_stress_pass_candidates']}`")
    lines.append(f"- best external verdict: `{s['best_academic_external_verdict']}`")
    lines.append("")
    lines.append("이 실행은 후보 탐색이다. 탐색에 현재 registry가 들어갔으므로, 통과 후보가 나오더라도 새 sealed external tranche 전에는 최종 blind success가 아니다.")
    lines.append("")
    lines.append("## Top candidates")
    lines.append("")
    lines.append("| rank | objective | bundled chi2 | external verdict | precision fails | not scoreable | external max |z| | packet |")
    lines.append("|---:|---:|---:|---|---:|---:|---:|---|")
    for c in run["candidates"]:
        lines.append(
            f"| {c['rank']} | {c['objective']:.6g} | {c['bundled_blind_chi2']:.6g} | "
            f"`{c['academic_external_verdict']}` | {c['academic_external_precision_failure_count']} | "
            f"{c['academic_external_not_scoreable_count']} | {c['academic_external_max_abs_z']:.6g} | `{c['packet_sha256'][:12]}` |"
        )
    lines.append("")
    lines.append("## Best candidate parameters")
    lines.append("")
    if run["candidates"]:
        lines.append("```json")
        lines.append(json.dumps(run["candidates"][0]["params"], indent=2, ensure_ascii=False, sort_keys=True))
        lines.append("```")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="GPU-assisted compact formula search with external stress audit.")
    p.add_argument("--candidates", type=int, default=200_000)
    p.add_argument("--top-k", type=int, default=12)
    p.add_argument("--seed", type=int, default=613)
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--chunk-size", type=int, default=250_000)
    p.add_argument("--gpu-dtype", choices=["float32", "float64"], default="float32")
    p.add_argument("--progress-every", type=int, default=20)
    p.add_argument("--outdir", default="runs/gpu_holdout_search")
    args = p.parse_args(argv)
    run = run_search(
        SearchConfig(
            candidates=args.candidates,
            top_k=args.top_k,
            seed=args.seed,
            device=args.device,
            chunk_size=args.chunk_size,
            gpu_dtype=args.gpu_dtype,
            progress_every=args.progress_every,
        )
    )
    paths = write_search(run, args.outdir)
    print(json.dumps({"paths": paths, "summary": run["summary"], "backend": run["backend"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

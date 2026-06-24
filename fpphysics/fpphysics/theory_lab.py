"""High-level automatic theory-development lab.

This module is intentionally independent of the older discovery package so it
can provide a compact, auditable workflow:

1. seed physically motivated candidates already implemented in candidate_models,
2. generate discrete RGE clock hypotheses,
3. scan instanton-like vacuum-energy formulae,
4. perform closed-form/PSLQ numerology audits,
5. run optional global continuous fits and label them as fits.

A candidate is never certified as a first-principles derivation merely because it
matches numbers.  Provenance and leakage are part of every score.
"""

from __future__ import annotations

import csv
import heapq
import json
import math
import random
import time
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .candidate_models import ISDLCTCPSCosmologicalAnsatzModel, ISDLCTCPSOneLoopGaugeModel
from .constants import BenchmarkData, load_benchmarks
from .engine import DerivationEngine, Target
from .rge import SM_B, electroweak_to_gut_normalized

try:
    import mpmath as mp
except Exception:  # pragma: no cover
    mp = None  # type: ignore

try:
    from scipy.optimize import differential_evolution  # type: ignore
except Exception:  # pragma: no cover
    differential_evolution = None  # type: ignore


@dataclass(frozen=True)
class LabConfig:
    """Bounded search configuration."""

    mode: str = "local"
    top_k: int = 40
    random_seed: int = 137
    alpha_u_min: float = 35.0
    alpha_u_max: float = 60.0
    alpha_u_step: float = 0.5
    max_clock: int = 13
    planck_divisors: tuple[int, ...] = (20, 24, 30, 32, 36, 40, 45, 48, 54, 60)
    beta_denominators: tuple[int, ...] = (1, 2, 3, 4, 5, 6)
    beta_abs_max: float = 16.0
    instanton_n_min: int = 1
    instanton_n_max: int = 180
    instanton_power_min: int = -10
    instanton_power_max: int = 10
    symbolic_trials: int = 600
    run_global_fits: bool = True
    de_maxiter: int = 45
    de_popsize: int = 8

    @staticmethod
    def quick() -> "LabConfig":
        return LabConfig(mode="quick", top_k=25, max_clock=8, symbolic_trials=200, run_global_fits=True, de_maxiter=25)

    @staticmethod
    def deep() -> "LabConfig":
        return LabConfig(
            mode="deep",
            top_k=80,
            alpha_u_min=20.0,
            alpha_u_max=80.0,
            alpha_u_step=0.25,
            max_clock=24,
            planck_divisors=tuple(sorted(set(range(16, 101)) | {120, 160, 240})),
            beta_denominators=(1, 2, 3, 4, 5, 6, 8, 10, 12),
            instanton_n_max=260,
            instanton_power_min=-16,
            instanton_power_max=16,
            symbolic_trials=5000,
            de_maxiter=120,
            de_popsize=12,
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LabCandidate:
    family: str
    name: str
    formula: str
    predictions: dict[str, float]
    target_values: dict[str, float]
    residuals: dict[str, float]
    z_scores: dict[str, float | None]
    chi2: float | None
    max_abs_z: float | None
    log10_error: float | None
    complexity: float
    leakage_score: float
    provenance: str
    verdict: str
    parameters: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    @property
    def objective(self) -> float:
        fit = self.chi2 if self.chi2 is not None and math.isfinite(self.chi2) else 1e6 * (self.log10_error or 1e99)
        return fit + 0.20 * self.complexity + 25.0 * self.leakage_score

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["objective"] = self.objective
        return d


@dataclass(frozen=True)
class LabRun:
    config: dict[str, Any]
    hardware: dict[str, Any]
    elapsed_seconds: float
    targets: dict[str, dict[str, Any]]
    candidates: list[LabCandidate]
    summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "config": self.config,
            "hardware": self.hardware,
            "elapsed_seconds": self.elapsed_seconds,
            "targets": self.targets,
            "candidates": [c.as_dict() for c in self.candidates],
            "summary": self.summary,
        }


def _detect_hardware() -> dict[str, Any]:
    info: dict[str, Any] = {"selected_backend": "numpy-cpu"}
    try:
        import os
        import platform

        info.update({"cpu_count": os.cpu_count(), "platform": platform.platform(), "python": platform.python_version()})
    except Exception:
        pass
    try:
        import torch  # type: ignore

        info.update(
            {
                "torch_available": True,
                "torch_version": getattr(torch, "__version__", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
        )
        if info["cuda_available"]:
            info["selected_backend"] = "torch-cuda-detected; numpy path used for small scans"
    except Exception:
        info.update({"torch_available": False, "cuda_available": False, "cuda_device_count": 0})
    try:
        import scipy  # type: ignore

        info["scipy_version"] = getattr(scipy, "__version__", None)
    except Exception:
        info["scipy_version"] = None
    info["numpy_version"] = np.__version__
    return info


def _score(
    family: str,
    name: str,
    formula: str,
    predictions: Mapping[str, float],
    targets: Mapping[str, Target],
    complexity: float,
    leakage: float,
    provenance: str,
    parameters: dict[str, Any] | None = None,
    notes: str = "",
) -> LabCandidate:
    target_values: dict[str, float] = {}
    residuals: dict[str, float] = {}
    z_scores: dict[str, float | None] = {}
    chi2 = 0.0
    dof = 0
    logerr: list[float] = []
    for key, val in predictions.items():
        if key not in targets:
            continue
        t = targets[key]
        target_values[key] = float(t.value)
        residuals[key] = float(val - t.value)
        if val != 0 and t.value != 0 and val * t.value > 0:
            logerr.append(abs(math.log10(abs(val / t.value))))
        z = None
        if t.sigma is not None and t.sigma > 0:
            z = float((val - t.value) / t.sigma)
            if math.isfinite(z):
                chi2 += z * z
                dof += 1
        z_scores[key] = z
    chi2_value = float(chi2) if dof else None
    max_abs_z = max((abs(z) for z in z_scores.values() if z is not None and math.isfinite(z)), default=None)
    log10_error = float(sum(logerr) / len(logerr)) if logerr else None
    if leakage >= 0.8:
        verdict = "fit_or_posthoc_not_derivation"
    elif max_abs_z is None:
        verdict = "unscored"
    elif max_abs_z < 2:
        verdict = "passes_numeric_tests_needs_physics_audit"
    elif max_abs_z < 5:
        verdict = "tension"
    else:
        verdict = "fails_numeric_tests"
    return LabCandidate(
        family=family,
        name=name,
        formula=formula,
        predictions={k: float(v) for k, v in predictions.items()},
        target_values=target_values,
        residuals=residuals,
        z_scores=z_scores,
        chi2=chi2_value,
        max_abs_z=max_abs_z,
        log10_error=log10_error,
        complexity=float(complexity),
        leakage_score=float(leakage),
        provenance=provenance,
        verdict=verdict,
        parameters=parameters or {},
        notes=notes,
    )


def _push(heap: list[tuple[float, int, LabCandidate]], cand: LabCandidate, top_k: int, counter: int) -> int:
    item = (-cand.objective, counter, cand)
    if len(heap) < top_k:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)
    return counter + 1


def _nearest_fraction(x: float, denominators: Sequence[int], max_abs: float) -> Fraction:
    best = Fraction(0, 1)
    err = float("inf")
    for q in denominators:
        p = int(round(x * q))
        cand = Fraction(p, q)
        if abs(float(cand)) > max_abs:
            continue
        e = abs(float(cand) - x)
        if e < err:
            best, err = cand, e
    return best


def _gauge_from_inv(alpha_inv: Sequence[float]) -> dict[str, float]:
    a1, a2, a3inv = [float(x) for x in alpha_inv]
    alpha_em_inv = (5 / 3) * a1 + a2
    return {"alpha_em_inv_mz": alpha_em_inv, "sin2theta_hat_mz": a2 / alpha_em_inv, "alpha3_mz": 1 / a3inv}


class TheoryLab:
    def __init__(self, bench: BenchmarkData | None = None, config: LabConfig | None = None):
        self.bench = bench or load_benchmarks()
        self.config = config or LabConfig.quick()
        self.engine = DerivationEngine(self.bench)
        self.targets = self.engine.targets
        random.seed(self.config.random_seed)
        np.random.seed(self.config.random_seed)

    def run(self) -> LabRun:
        started = time.perf_counter()
        candidates: list[LabCandidate] = []
        candidates.extend(self._seed_candidates())
        candidates.extend(self._rg_clock_search())
        candidates.extend(self._cosmology_search())
        candidates.extend(self._symbolic_search())
        candidates.extend(self._pslq_audit())
        if self.config.run_global_fits:
            candidates.extend(self._global_fit_audit())
        candidates = sorted(candidates, key=lambda c: c.objective)
        # Keep a diverse top list: global top + best by family.
        selected: list[LabCandidate] = []
        seen: set[tuple[str, str]] = set()
        for cand in candidates:
            key = (cand.family, cand.name)
            if key not in seen:
                selected.append(cand)
                seen.add(key)
            if len(selected) >= self.config.top_k:
                break
        for fam in sorted({c.family for c in candidates}):
            fam_best = next(c for c in candidates if c.family == fam)
            key = (fam_best.family, fam_best.name)
            if key not in seen and len(selected) < self.config.top_k + 8:
                selected.append(fam_best)
                seen.add(key)
        family_counts: dict[str, int] = {}
        for cand in candidates:
            family_counts[cand.family] = family_counts.get(cand.family, 0) + 1
        low_leak_pass = [c for c in candidates if c.leakage_score < 0.4 and c.verdict == "passes_numeric_tests_needs_physics_audit"]
        summary = {
            "candidate_count": len(candidates),
            "reported_candidate_count": len(selected),
            "family_counts": family_counts,
            "low_leakage_numeric_pass_count": len(low_leak_pass),
            "complete_first_principles_derivation_found": False,
            "strict_conclusion": "automatic_generation_succeeded_but_no_complete_first_principles_derivation_certified",
        }
        return LabRun(
            config=self.config.as_dict(),
            hardware=_detect_hardware(),
            elapsed_seconds=time.perf_counter() - started,
            targets={k: asdict(v) for k, v in self.targets.items()},
            candidates=selected,
            summary=summary,
        )

    def _seed_candidates(self) -> list[LabCandidate]:
        out: list[LabCandidate] = []
        for model, provenance, leakage in [
            (ISDLCTCPSOneLoopGaugeModel(), "physically_audited_seed_ISDLC_TCPS_gauge", 0.08),
            (ISDLCTCPSCosmologicalAnsatzModel(), "ansatz_seed_ISDLC_TCPS_vacuum", 0.25),
        ]:
            ev = self.engine.evaluate(model)
            preds = {k: s.prediction.value for k, s in ev.scores.items() if s.counted_as_prediction}
            if preds:
                out.append(
                    _score(
                        "seeded_candidate",
                        ev.model_name,
                        model.name,
                        preds,
                        self.targets,
                        complexity=10 + 2 * len(ev.free_parameters),
                        leakage=leakage,
                        provenance=provenance,
                        parameters={"free_parameters": list(ev.free_parameters)},
                        notes="기존 엔진 후보를 자동 발견 랭킹에 seed로 보존했다.",
                    )
                )
        return out

    def _rg_clock_search(self) -> list[LabCandidate]:
        cfg = self.config
        target_inv = electroweak_to_gut_normalized(
            self.bench.alpha_hat_5_mz_inv.value,
            self.bench.sin2theta_hat_mz.value,
            self.bench.alpha_s_mz.value,
            self.bench.mz_gev.value,
        ).alpha_inv
        b_sm = np.array(SM_B, dtype=float)
        heap: list[tuple[float, int, LabCandidate]] = []
        counter = 0
        alphas = np.arange(cfg.alpha_u_min, cfg.alpha_u_max + 0.5 * cfg.alpha_u_step, cfg.alpha_u_step)
        clocks = [(h, l) for h in range(1, cfg.max_clock + 1) for l in range(1, cfg.max_clock + 1) if math.gcd(h, l) == 1]
        for alpha_u_inv in alphas:
            for divisor in cfg.planck_divisors:
                m_u = 2.435e18 / divisor
                log_total = math.log(m_u / self.bench.mz_gev.value)
                for h, l in clocks:
                    ln_hi = h / (h + l) * log_total
                    ln_lo = log_total - ln_hi
                    required = (target_inv - alpha_u_inv - b_sm * ln_lo / (2 * math.pi)) * (2 * math.pi) / ln_hi
                    if np.any(np.abs(required) > cfg.beta_abs_max):
                        continue
                    fracs = [_nearest_fraction(float(x), cfg.beta_denominators, cfg.beta_abs_max) for x in required]
                    b_high = np.array([float(f) for f in fracs])
                    pred_inv = alpha_u_inv + b_sm * ln_lo / (2 * math.pi) + b_high * ln_hi / (2 * math.pi)
                    if np.any(pred_inv <= 0) or not np.all(np.isfinite(pred_inv)):
                        continue
                    preds = _gauge_from_inv(pred_inv)
                    beta_label = ",".join(str(f) for f in fracs)
                    cand = _score(
                        "target_guided_rg_clock",
                        f"RG clock alphaU^-1={alpha_u_inv:g}, MbarPl/{divisor}, clock {h}:{l}, B=({beta_label})",
                        "alpha_i^-1(MZ)=alphaU^-1+bSM_i ln(MI/MZ)/(2π)+B_i ln(MU/MI)/(2π)",
                        preds,
                        self.targets,
                        complexity=18 + 0.1 * (h + l + divisor / 10) + sum(math.log(abs(f.numerator) + f.denominator + 1, 2) for f in fracs),
                        leakage=0.58,
                        provenance="target_guided_beta_quantization_not_derivation",
                        parameters={
                            "alpha_u_inv": float(alpha_u_inv),
                            "M_U_GeV": m_u,
                            "planck_divisor": divisor,
                            "clock": [h, l],
                            "B_high_fractional": [str(f) for f in fracs],
                            "required_continuous_B": [float(x) for x in required],
                            "alpha_inv_mz": [float(x) for x in pred_inv],
                        },
                    )
                    counter = _push(heap, cand, max(cfg.top_k * 4, 50), counter)
        return [x[2] for x in sorted(heap, key=lambda t: (-t[0], t[1]))]

    def _cosmology_search(self) -> list[LabCandidate]:
        cfg = self.config
        heap: list[tuple[float, int, LabCandidate]] = []
        counter = 0
        bases = [("1", 1.0), ("π", math.pi), ("2π", 2 * math.pi), ("4π", 4 * math.pi), ("8π", 8 * math.pi)]
        for n in range(cfg.instanton_n_min, cfg.instanton_n_max + 1):
            for label, base in bases:
                for p in range(cfg.instanton_power_min, cfg.instanton_power_max + 1):
                    try:
                        pred = (base**p) * math.exp(-n * math.pi)
                    except OverflowError:
                        continue
                    if pred <= 0 or not math.isfinite(pred):
                        continue
                    cand = _score(
                        "cosmological_instanton_scan",
                        f"rhoLambda={label}^{p} exp(-{n}π)",
                        f"rhoLambda_planck4=({label})^{p} exp(-{n}π)",
                        {"rhoLambda_planck4": pred},
                        self.targets,
                        complexity=5 + 0.4 * abs(p) + 0.02 * abs(n - 93),
                        leakage=0.18 if not (n == 93 and label == "4π" and p == 4) else 0.08,
                        provenance="integer_instanton_ansatz_scan",
                        parameters={"N": n, "base": label, "power": p},
                        notes="정밀 유도에는 prefactor/determinant의 독립 계산이 필요하다.",
                    )
                    counter = _push(heap, cand, max(cfg.top_k * 3, 60), counter)
        return [x[2] for x in sorted(heap, key=lambda t: (-t[0], t[1]))]

    def _symbolic_search(self) -> list[LabCandidate]:
        cfg = self.config
        rng = random.Random(cfg.random_seed)
        constants = {
            "π": math.pi,
            "π²": math.pi**2,
            "e": math.e,
            "φ": (1 + math.sqrt(5)) / 2,
            "ln2": math.log(2),
            "sqrt2": math.sqrt(2),
            "ln(4π)": math.log(4 * math.pi),
        }
        heap: list[tuple[float, int, LabCandidate]] = []
        counter = 0
        target = self.targets["alpha0_inv"].value
        names = list(constants)
        for _ in range(cfg.symbolic_trials):
            a, b = rng.sample(names, 2)
            ia = rng.randint(-40, 40)
            ib = rng.randint(-40, 40)
            if ia == 0 and ib == 0:
                continue
            # The intercept is intentionally target-centered and therefore high leakage.
            c0 = round(target - ia * constants[a] - ib * constants[b])
            for c in (c0 - 1, c0, c0 + 1):
                val = ia * constants[a] + ib * constants[b] + c
                cand = _score(
                    "symbolic_alpha_numerology_audit",
                    f"alpha0^-1≈{ia}{a}+{ib}{b}+{c}",
                    f"alpha0_inv={ia}*{a}+{ib}*{b}+{c}",
                    {"alpha0_inv": val},
                    self.targets,
                    complexity=8 + math.log(abs(ia) + abs(ib) + abs(c) + 2, 2),
                    leakage=0.88,
                    provenance="posthoc_symbolic_search",
                    parameters={"ia": ia, "ib": ib, "c": c, "atom_a": a, "atom_b": b},
                    notes="표적값을 사용한 절편 선택이므로 유도가 아니라 numerology 감시용이다.",
                )
                counter = _push(heap, cand, max(20, cfg.top_k), counter)
        return [x[2] for x in sorted(heap, key=lambda t: (-t[0], t[1]))]

    def _pslq_audit(self) -> list[LabCandidate]:
        if mp is None:
            return []
        mp.mp.dps = 80
        out: list[LabCandidate] = []
        basis = [("1", mp.mpf(1)), ("π", mp.pi), ("π²", mp.pi**2), ("e", mp.e), ("φ", (1 + mp.sqrt(5)) / 2), ("ln2", mp.log(2))]
        for target_name in ("alpha0_inv", "alpha_em_inv_mz"):
            y = mp.mpf(str(self.targets[target_name].value))
            try:
                rel = mp.pslq([y] + [v for _, v in basis], tol=mp.mpf("1e-18"), maxcoeff=200, maxsteps=1000)
            except Exception:
                rel = None
            if not rel or rel[0] == 0:
                continue
            coeffs = [int(x) for x in rel]
            pred = float(-sum(mp.mpf(c) * v for c, (_, v) in zip(coeffs[1:], basis)) / coeffs[0])
            formula = f"{target_name}=-Σ c_i basis_i/{coeffs[0]}, coeffs={coeffs}"
            out.append(
                _score(
                    "pslq_integer_relation_audit",
                    f"PSLQ relation for {target_name}",
                    formula,
                    {target_name: pred},
                    self.targets,
                    complexity=25 + sum(math.log(abs(c) + 2, 2) for c in coeffs),
                    leakage=0.97,
                    provenance="benchmark_included_in_pslq_vector",
                    parameters={"coefficients": coeffs, "basis": [n for n, _ in basis]},
                    notes="PSLQ는 표적값을 입력 벡터에 넣었으므로 물리 유도가 아니다.",
                )
            )
        return out

    def _global_fit_audit(self) -> list[LabCandidate]:
        if differential_evolution is None:
            return []
        out: list[LabCandidate] = []
        b_high = np.array([-8 / 5, -3, -7], dtype=float)
        b_sm = np.array(SM_B, dtype=float)
        mz = self.bench.mz_gev.value

        def obj(x: np.ndarray) -> float:
            alpha_u_inv, log_total, frac_hi = x
            frac_hi = float(np.clip(frac_hi, 0.01, 0.99))
            pred_inv = alpha_u_inv + b_sm * (1 - frac_hi) * log_total / (2 * math.pi) + b_high * frac_hi * log_total / (2 * math.pi)
            preds = _gauge_from_inv(pred_inv)
            s = 0.0
            for k in ("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz"):
                t = self.targets[k]
                s += ((preds[k] - t.value) / (t.sigma or 1)) ** 2
            return float(s)

        try:
            res = differential_evolution(obj, bounds=[(20, 80), (5, 45), (0.01, 0.99)], seed=self.config.random_seed, maxiter=self.config.de_maxiter, popsize=self.config.de_popsize, polish=True, workers=1)
            alpha_u_inv, log_total, frac_hi = [float(x) for x in res.x]
            pred_inv = alpha_u_inv + b_sm * (1 - frac_hi) * log_total / (2 * math.pi) + b_high * frac_hi * log_total / (2 * math.pi)
            preds = _gauge_from_inv(pred_inv)
            out.append(
                _score(
                    "continuous_global_fit_audit",
                    "DE fit of RG clock with fixed ISDLC effective beta",
                    "fit alphaU^-1, ln(MU/MZ), clock fraction; B=(-8/5,-3,-7)",
                    preds,
                    self.targets,
                    complexity=35,
                    leakage=0.94,
                    provenance="continuous_parameters_fitted_to_benchmark",
                    parameters={"alpha_u_inv": alpha_u_inv, "ln_MU_MZ": log_total, "clock_fraction_high": frac_hi, "optimizer_fun": float(res.fun), "success": bool(res.success)},
                    notes="연속 최적화가 수치를 맞추더라도 제1원리 유도가 아니다.",
                )
            )
        except Exception as exc:
            out.append(
                _score(
                    "continuous_global_fit_audit",
                    "DE fit failed",
                    "differential_evolution",
                    {},
                    self.targets,
                    complexity=0,
                    leakage=1.0,
                    provenance="optimizer_failure",
                    parameters={"exception": repr(exc)},
                )
            )
        return out

    def write(self, run: LabRun, outdir: str | Path) -> dict[str, str]:
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        json_path = out / "theory_lab_results.json"
        csv_path = out / "theory_lab_candidates.csv"
        md_path = out / "THEORY_LAB_REPORT_ko.md"
        json_path.write_text(json.dumps(run.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["rank", "family", "name", "verdict", "objective", "chi2", "max_abs_z", "log10_error", "leakage_score", "provenance", "formula"])
            writer.writeheader()
            for i, c in enumerate(run.candidates, 1):
                writer.writerow({"rank": i, "family": c.family, "name": c.name, "verdict": c.verdict, "objective": c.objective, "chi2": c.chi2, "max_abs_z": c.max_abs_z, "log10_error": c.log10_error, "leakage_score": c.leakage_score, "provenance": c.provenance, "formula": c.formula})
        md_path.write_text(render_lab_report_ko(run), encoding="utf-8")
        return {"json": str(json_path), "csv": str(csv_path), "report": str(md_path)}


def render_lab_report_ko(run: LabRun) -> str:
    def fmt(x: Any, d: int = 6) -> str:
        if x is None:
            return "—"
        try:
            v = float(x)
        except Exception:
            return str(x)
        if v == 0:
            return "0"
        if abs(v) < 1e-4 or abs(v) >= 1e6:
            return f"{v:.{d}e}"
        return f"{v:.{d}g}"

    lines = ["# Python 자동 이론 개발·발견 엔진 보고서", ""]
    lines += ["## 핵심 판정", ""]
    lines.append("자동 후보 생성, 정수/유리수 RG clock 탐색, 우주상수 instanton scan, symbolic/PSLQ 감사, 연속 전역최적화 fit 감사를 실행했다.")
    lines.append("이번 실행은 완전한 제1원리 이론을 인증하지 않았고, 후보 생성 및 반증/우선순위화 엔진을 구축·실행했다.")
    lines.append("")
    lines.append(f"- strict conclusion: `{run.summary['strict_conclusion']}`")
    lines.append(f"- candidates generated/reported: `{run.summary['candidate_count']}` / `{run.summary['reported_candidate_count']}`")
    lines.append(f"- low-leakage numeric pass count: `{run.summary['low_leakage_numeric_pass_count']}`")
    lines.append(f"- elapsed seconds: `{fmt(run.elapsed_seconds, 3)}`")
    lines.append("")
    lines += ["## 실행 환경", ""]
    hw = run.hardware
    for k in ("selected_backend", "cpu_count", "numpy_version", "scipy_version", "torch_available", "torch_version", "cuda_available", "cuda_device_count"):
        lines.append(f"- {k}: `{hw.get(k)}`")
    lines.append("")
    lines += ["## 방법론", ""]
    lines.append("- RG clock search: `alpha_i^-1(MZ)=alphaU^-1+bSM_i ln(MI/MZ)/(2π)+B_i ln(MU/MI)/(2π)`에서 `alphaU`, Planck divisor, clock ratio, rational beta-vector를 탐색한다.")
    lines.append("- Vacuum instanton scan: `rhoLambda_planck4 = base^p exp(-Nπ)` 정수 격자를 훑는다.")
    lines.append("- Symbolic/PSLQ audit: 닫힌형 수식이 얼마나 쉽게 생기는지 확인하되 benchmark 사용 후보는 high leakage로 격리한다.")
    lines.append("- Differential evolution audit: 연속 파라미터 fit의 수치 성능을 확인하되 유도로 인정하지 않는다.")
    lines.append("")
    lines += ["## 상위 후보", "", "| rank | family | verdict | objective | max |z| | leakage | formula |", "|---:|---|---|---:|---:|---:|---|"]
    for i, c in enumerate(run.candidates, 1):
        formula = c.formula.replace("|", "\\|")[:130]
        lines.append(f"| {i} | `{c.family}` | `{c.verdict}` | {fmt(c.objective,4)} | {fmt(c.max_abs_z,4)} | {fmt(c.leakage_score,3)} | `{formula}` |")
    lines.append("")
    lines += ["## 세부 예측", ""]
    for i, c in enumerate(run.candidates[:20], 1):
        lines.append(f"### {i}. {c.name}")
        lines.append(f"- provenance: `{c.provenance}`")
        lines.append(f"- formula: `{c.formula}`")
        lines.append(f"- notes: {c.notes or '—'}")
        lines.append("| quantity | prediction | target | residual | z |")
        lines.append("|---|---:|---:|---:|---:|")
        for k, v in c.predictions.items():
            lines.append(f"| `{k}` | {fmt(v,8)} | {fmt(c.target_values.get(k),8)} | {fmt(c.residuals.get(k),8)} | {fmt(c.z_scores.get(k),5)} |")
        lines.append("")
    return "\n".join(lines) + "\n"

"""Automated theory-discovery layer for the first-principles physics engine.

This module does *not* claim that a numerically good formula is a fundamental
law.  It gives a reproducible search procedure that can generate candidate
UV boundary conditions, run them through the existing scoring engine, and mark
which parts were post-selected from the benchmark data.

The design goal is to make data-mined structure auditable:

* enumerate simple exact/rational objects instead of opaque floating fits;
* score predictive accuracy and description length separately;
* quarantine post-selected formulas from certified first-principles claims;
* export enough metadata to reproduce every candidate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import exp, gcd, isfinite, log, pi, sqrt
import heapq
import json
import platform
import random
import time
from typing import Iterable, Mapping, Sequence

import numpy as np

from .candidate_models import Prediction
from .constants import BenchmarkData, load_benchmarks
from .cosmology import lambda_from_flat_lcdm
from .engine import DerivationEngine, EvaluationResult, Target
from .rge import SM_B, electroweak_to_gut_normalized


# ---------------------------------------------------------------------------
# Generic records


@dataclass(frozen=True)
class HardwareInfo:
    """Hardware/backend information detected at runtime."""

    python: str
    platform: str
    cpu_count: int | None
    numpy_version: str
    torch_available: bool = False
    cuda_available: bool = False
    cuda_device_count: int = 0
    cuda_device_names: tuple[str, ...] = tuple()

    def as_dict(self) -> dict[str, object]:
        return {
            "python": self.python,
            "platform": self.platform,
            "cpu_count": self.cpu_count,
            "numpy_version": self.numpy_version,
            "torch_available": self.torch_available,
            "cuda_available": self.cuda_available,
            "cuda_device_count": self.cuda_device_count,
            "cuda_device_names": list(self.cuda_device_names),
        }


def detect_hardware() -> HardwareInfo:
    """Detect CPU/GPU backends without requiring optional dependencies."""

    torch_available = False
    cuda_available = False
    cuda_count = 0
    cuda_names: list[str] = []
    try:  # pragma: no cover - depends on local machine
        import torch  # type: ignore

        torch_available = True
        cuda_available = bool(torch.cuda.is_available())
        cuda_count = int(torch.cuda.device_count()) if cuda_available else 0
        if cuda_available:
            cuda_names = [str(torch.cuda.get_device_name(i)) for i in range(cuda_count)]
    except Exception:
        pass
    try:
        import os

        cpu_count = os.cpu_count()
    except Exception:  # pragma: no cover
        cpu_count = None
    return HardwareInfo(
        python=platform.python_version(),
        platform=platform.platform(),
        cpu_count=cpu_count,
        numpy_version=np.__version__,
        torch_available=torch_available,
        cuda_available=cuda_available,
        cuda_device_count=cuda_count,
        cuda_device_names=tuple(cuda_names),
    )


@dataclass(frozen=True)
class DiscoveryScore:
    """Multi-objective score for a generated candidate."""

    chi2: float | None
    max_abs_z: float | None
    log10_error: float | None
    complexity: float
    post_selection_penalty: float
    objective: float
    dof: int

    def as_dict(self) -> dict[str, object]:
        return {
            "chi2": self.chi2,
            "max_abs_z": self.max_abs_z,
            "log10_error": self.log10_error,
            "complexity": self.complexity,
            "post_selection_penalty": self.post_selection_penalty,
            "objective": self.objective,
            "dof": self.dof,
        }


@dataclass(frozen=True)
class DiscoveryCandidate:
    """A candidate found by a searcher."""

    family: str
    name: str
    predictions: dict[str, Prediction]
    score: DiscoveryScore
    formulas: dict[str, str]
    metadata: dict[str, object] = field(default_factory=dict)
    free_parameters: tuple[str, ...] = tuple()
    post_selected: bool = True
    certified_first_principles: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "name": self.name,
            "predictions": {k: v.as_dict() for k, v in self.predictions.items()},
            "score": self.score.as_dict(),
            "formulas": self.formulas,
            "metadata": self.metadata,
            "free_parameters": list(self.free_parameters),
            "post_selected": self.post_selected,
            "certified_first_principles": self.certified_first_principles,
        }


class AutoCandidateModel:
    """Adapter that lets a discovery candidate be scored by DerivationEngine."""

    def __init__(self, candidate: DiscoveryCandidate):
        self._candidate = candidate
        self.name = candidate.name
        self.free_parameters = candidate.free_parameters

    def predict(self, bench: BenchmarkData) -> dict[str, Prediction]:
        # If the candidate was generated by fitting/post-selection, do not let
        # the strict engine count it as an independent derivation.
        if not self._candidate.post_selected and self._candidate.certified_first_principles:
            return self._candidate.predictions
        return {
            k: Prediction(
                name=v.name,
                value=v.value,
                sigma_theory=v.sigma_theory,
                unit=v.unit,
                derived=False,
                fitted=True,
                note=(v.note + " [auto-discovered/post-selected; quarantined from first-principles count]").strip(),
            )
            for k, v in self._candidate.predictions.items()
        }

    def diagnostics(self, bench: BenchmarkData) -> dict[str, object]:
        return {
            "family": self._candidate.family,
            "formulas": self._candidate.formulas,
            "metadata": self._candidate.metadata,
            "discovery_score": self._candidate.score.as_dict(),
            "post_selected": self._candidate.post_selected,
            "certified_first_principles": self._candidate.certified_first_principles,
        }


# ---------------------------------------------------------------------------
# Small exact-object library


@dataclass(frozen=True)
class ExactQuantity:
    value: float
    label: str
    complexity: float

    def as_dict(self) -> dict[str, object]:
        return {"value": self.value, "label": self.label, "complexity": self.complexity}


def _root_count(label: str, n: int | None = None) -> int:
    if label == "A" and n is not None:
        return n * (n + 1)
    if label in {"B", "C"} and n is not None:
        return 2 * n * n
    if label == "D" and n is not None:
        return 2 * n * (n - 1)
    exc = {"G2": 12, "F4": 48, "E6": 72, "E7": 126, "E8": 240}
    return exc[label]


def lie_root_denominators(max_integer: int = 160) -> list[ExactQuantity]:
    """Root counts and nearby simple geometric divisors for scale guesses."""

    out: dict[int, ExactQuantity] = {}
    for n in range(1, 13):
        for fam in ("A", "B", "C", "D"):
            if fam == "D" and n < 2:
                continue
            val = _root_count(fam, n)
            if 1 <= val <= max_integer and val not in out:
                out[val] = ExactQuantity(float(val), f"|Delta({fam}{n})|", 1.2 + 0.15 * n)
    for label in ("G2", "F4", "E6", "E7", "E8"):
        val = _root_count(label)
        if val <= max_integer and val not in out:
            out[val] = ExactQuantity(float(val), f"|Delta({label})|", 1.8)
    for val in range(1, max_integer + 1):
        out.setdefault(val, ExactQuantity(float(val), str(val), 2.5 + log(val + 1.0, 2.0) / 4.0))
    return [out[k] for k in sorted(out)]


def alpha_u_library(min_inv: float = 20.0, max_inv: float = 90.0) -> list[ExactQuantity]:
    """Simple half-integer and Lie-count-inspired inverse unified couplings."""

    out: dict[str, ExactQuantity] = {}
    # Half-integers are treated as a broad arithmetic search grammar, not a
    # derivation.  This lets the engine rediscover 93/2 without hard-coding it.
    m_min = int(np.ceil(2 * min_inv))
    m_max = int(np.floor(2 * max_inv))
    for m in range(m_min, m_max + 1):
        val = m / 2.0
        out[f"{m}/2"] = ExactQuantity(val, f"{m}/2", 2.4 + log(abs(m) + 1.0, 2.0) / 5.0)
    # Add recognizable compact-Lie formulas with lower complexity.
    for n in range(2, 13):
        roots = _root_count("D", n)
        rank = n
        val = roots + rank + 1.5
        if min_inv <= val <= max_inv:
            out[f"|Delta(D{n})|+rank(D{n})+b2(T3)/2"] = ExactQuantity(
                val,
                f"|Delta(D{n})|+rank(D{n})+b2(T3)/2",
                1.0 + 0.15 * n,
            )
    for fam in ("A", "B", "C", "D"):
        for n in range(2, 13):
            if fam == "D" and n < 2:
                continue
            roots = _root_count(fam, n)
            rank = n
            for label, val in (
                (f"|Delta({fam}{n})|+rank({fam}{n})", roots + rank),
                (f"(|Delta({fam}{n})|+rank({fam}{n}))/2", (roots + rank) / 2.0),
                (f"|Delta({fam}{n})|/2+rank({fam}{n})", roots / 2.0 + rank),
            ):
                if min_inv <= val <= max_inv and label not in out:
                    out[label] = ExactQuantity(float(val), label, 1.6 + 0.18 * n)
    return sorted(out.values(), key=lambda q: (q.value, q.complexity, q.label))


def clock_pairs(max_clock: int) -> list[tuple[int, int, float]]:
    """Coprime positive clock pairs and a small complexity cost.

    The ISDLC--TCPS 6:13 clock is always retained as an audited benchmark
    stress point, even in very small quick scans.
    """

    pairs = []
    seen: set[tuple[int, int]] = set()
    for hi in range(1, max_clock + 1):
        for lo in range(1, max_clock + 1):
            if gcd(hi, lo) == 1:
                cost = 1.0 + 0.2 * (log(hi + 1.0, 2.0) + log(lo + 1.0, 2.0))
                pairs.append((hi, lo, cost))
                seen.add((hi, lo))
    if (6, 13) not in seen:
        pairs.append((6, 13, 1.0 + 0.2 * (log(7.0, 2.0) + log(14.0, 2.0))))
    # Prefer compact clocks when scores tie.
    return sorted(pairs, key=lambda x: (x[0] + x[1], x[0], x[1]))


def nearest_rational(x: float, max_denominator: int = 6, max_abs_num: int = 80) -> tuple[Fraction, float, float]:
    """Nearest simple rational with a small exact-description cost."""

    best = Fraction(0, 1)
    best_err = float("inf")
    for q in range(1, max_denominator + 1):
        p = int(round(x * q))
        if abs(p) > max_abs_num:
            continue
        frac = Fraction(p, q)
        err = abs(float(frac) - x)
        if err < best_err:
            best = frac
            best_err = err
    p = abs(best.numerator)
    q = best.denominator
    complexity = 0.5 + log(p + 2.0, 2.0) / 3.0 + log(q + 1.0, 2.0) / 3.0
    return best, best_err, complexity


def _score_predictions(preds: Mapping[str, Prediction], targets: Mapping[str, Target], complexity: float, penalty: float) -> DiscoveryScore:
    chi2 = 0.0
    max_abs_z = 0.0
    dof = 0
    for name, pred in preds.items():
        target = targets.get(name)
        if target is None or target.sigma is None or target.sigma <= 0:
            continue
        sigma2 = target.sigma**2
        if pred.sigma_theory is not None:
            sigma2 += pred.sigma_theory**2
        z = (pred.value - target.value) / sqrt(sigma2)
        if isfinite(z):
            chi2 += z * z
            max_abs_z = max(max_abs_z, abs(z))
            dof += 1
    if dof == 0:
        chi2_value = None
        max_z_value = None
        objective = complexity + penalty
    else:
        chi2_value = chi2
        max_z_value = max_abs_z
        # The penalty is deliberately smaller than a formal Bayes factor because
        # the search output is a ranking, not a posterior probability.
        objective = chi2 + 0.05 * complexity + penalty
    return DiscoveryScore(
        chi2=chi2_value,
        max_abs_z=max_z_value,
        log10_error=None,
        complexity=complexity,
        post_selection_penalty=penalty,
        objective=objective,
        dof=dof,
    )


def _push_top(heap: list[tuple[float, int, DiscoveryCandidate]], candidate: DiscoveryCandidate, top_k: int, counter: int) -> None:
    item = (-candidate.score.objective, counter, candidate)
    if len(heap) < top_k:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


# ---------------------------------------------------------------------------
# RGE/gauge-clock discovery


@dataclass(frozen=True)
class GaugeSearchConfig:
    max_clock: int = 24
    max_scale_denominator: int = 120
    beta_denominator: int = 6
    beta_abs_max: float = 16.0
    top_k: int = 40
    min_alpha_u_inv: float = 25.0
    max_alpha_u_inv: float = 75.0
    reduced_planck_mass_gev: float = 2.435e18
    random_refine: int = 0
    seed: int = 12345


class GaugeClockSearcher:
    """Search simple one-loop UV boundary/clock theories.

    The search does not fit continuous beta coefficients.  For each exact
    alpha_U, UV scale divisor, and discrete clock pair, it computes the beta
    vector that would be required, snaps it to nearby simple rationals, and
    then scores the resulting one-loop prediction.
    """

    def __init__(self, bench: BenchmarkData, targets: Mapping[str, Target], config: GaugeSearchConfig | None = None):
        self.bench = bench
        self.targets = targets
        self.config = config or GaugeSearchConfig()
        self.couplings = electroweak_to_gut_normalized(
            bench.alpha_hat_5_mz_inv.value,
            bench.sin2theta_hat_mz.value,
            bench.alpha_s_mz.value,
            bench.mz_gev.value,
        )
        self.target_alpha_inv = self.couplings.alpha_inv

    def _make_candidate(
        self,
        alpha_u: ExactQuantity,
        denom: ExactQuantity,
        hi: int,
        lo: int,
        clock_cost: float,
        beta_fracs: Sequence[Fraction],
        required_beta: Sequence[float],
    ) -> DiscoveryCandidate | None:
        cfg = self.config
        m_u = cfg.reduced_planck_mass_gev / denom.value
        if m_u <= self.bench.mz_gev.value:
            return None
        log_total = log(m_u / self.bench.mz_gev.value)
        ln_hi = hi / (hi + lo) * log_total
        ln_low = lo / (hi + lo) * log_total
        b_high = np.array([float(b) for b in beta_fracs], dtype=float)
        alpha_inv = alpha_u.value + np.asarray(SM_B, dtype=float) / (2 * pi) * ln_low + b_high / (2 * pi) * ln_hi
        if np.any(alpha_inv <= 0) or not np.all(np.isfinite(alpha_inv)):
            return None
        alpha1_inv, alpha2_inv, alpha3_inv = [float(x) for x in alpha_inv]
        alpha_em_inv = (5.0 / 3.0) * alpha1_inv + alpha2_inv
        sin2 = alpha2_inv / alpha_em_inv
        alpha3 = 1.0 / alpha3_inv
        if not (0 < sin2 < 1 and alpha3 > 0):
            return None
        preds = {
            "alpha_em_inv_mz": Prediction(
                "alpha_em_inv_mz",
                alpha_em_inv,
                derived=True,
                note="Auto-generated one-loop clock/RGE prediction; beta vector was rationalized during data search.",
            ),
            "sin2theta_hat_mz": Prediction(
                "sin2theta_hat_mz",
                sin2,
                derived=True,
                note="Auto-generated one-loop clock/RGE prediction.",
            ),
            "alpha3_mz": Prediction(
                "alpha3_mz",
                alpha3,
                derived=True,
                note="Auto-generated one-loop clock/RGE prediction.",
            ),
        }
        beta_cost = 0.0
        beta_labels = []
        for b in beta_fracs:
            beta_labels.append(str(b))
            beta_cost += 0.5 + log(abs(b.numerator) + 2.0, 2.0) / 3.0 + log(b.denominator + 1.0, 2.0) / 3.0
        complexity = alpha_u.complexity + denom.complexity + clock_cost + beta_cost
        # Post-selection penalty grows slowly with searchable discrete choices.
        penalty = 0.5 * log(
            max(2.0, (cfg.max_clock**2) * cfg.max_scale_denominator * (cfg.max_alpha_u_inv - cfg.min_alpha_u_inv) * 2.0)
        )
        score = _score_predictions(preds, self.targets, complexity, penalty)
        name = (
            "auto gauge-clock: "
            f"alpha_U^-1={alpha_u.label}, M_U=Mbar_Pl/{denom.label}, "
            f"clock={hi}:{lo}, b_high=({', '.join(beta_labels)})"
        )
        is_isdlc_tcps = (
            "D5" in alpha_u.label
            and abs(alpha_u.value - 46.5) < 1e-12
            and abs(denom.value - 40.0) < 1e-12
            and hi == 6
            and lo == 13
            and [str(b) for b in beta_fracs] == ["-8/5", "-3", "-7"]
        )
        if is_isdlc_tcps:
            name = "audited seed: ISDLC--TCPS one-loop gauge clock"

        return DiscoveryCandidate(
            family="one_loop_gauge_clock",
            name=name,
            predictions=preds,
            score=score,
            formulas={
                "alpha_U_inv": alpha_u.label,
                "M_U": f"Mbar_Pl / ({denom.label})",
                "clock": f"ln(M_U/M_I):ln(M_I/M_Z) = {hi}:{lo}",
                "RGE": "alpha_i^-1(M_Z)=alpha_U^-1 + b_SM_i/(2*pi) ln(M_I/M_Z) + b_high_i/(2*pi) ln(M_U/M_I)",
                "b_SM": str(tuple(SM_B)),
                "b_high": f"({', '.join(beta_labels)})",
            },
            metadata={
                "alpha_U_inv_value": alpha_u.value,
                "scale_denominator_value": denom.value,
                "M_U_GeV": m_u,
                "M_I_GeV": self.bench.mz_gev.value * exp(ln_low),
                "ln_MU_MI": ln_hi,
                "ln_MI_MZ": ln_low,
                "required_continuous_b_high": [float(x) for x in required_beta],
                "rationalized_b_high": [str(b) for b in beta_fracs],
                "alpha1_inv_mz": alpha1_inv,
                "alpha2_inv_mz": alpha2_inv,
                "alpha3_inv_mz": alpha3_inv,
                "post_selection_warning": "This is a generated hypothesis, not a certified microscopic derivation of the spectrum." if not is_isdlc_tcps else "Audited ISDLC--TCPS seed preserved for comparison; still not a certified complete first-principles derivation.",
                "provenance": "audited_seed_ISDLC_TCPS" if is_isdlc_tcps else "posthoc_rationalized_rg_clock",
            },
            free_parameters=tuple() if is_isdlc_tcps else ("post-selected discrete grammar choices",),
            post_selected=not is_isdlc_tcps,
            certified_first_principles=False,
        )

    def search(self) -> list[DiscoveryCandidate]:
        cfg = self.config
        alphas = alpha_u_library(cfg.min_alpha_u_inv, cfg.max_alpha_u_inv)
        denoms = lie_root_denominators(cfg.max_scale_denominator)
        clocks = clock_pairs(cfg.max_clock)
        heap: list[tuple[float, int, DiscoveryCandidate]] = []
        counter = 0
        b_sm = np.asarray(SM_B, dtype=float)
        target = self.target_alpha_inv
        for alpha_u in alphas:
            a = alpha_u.value
            for denom in denoms:
                m_u = cfg.reduced_planck_mass_gev / denom.value
                if m_u <= self.bench.mz_gev.value:
                    continue
                log_total = log(m_u / self.bench.mz_gev.value)
                for hi, lo, clock_cost in clocks:
                    ln_hi = hi / (hi + lo) * log_total
                    if ln_hi <= 0:
                        continue
                    ln_low = lo / (hi + lo) * log_total
                    required = (target - a - b_sm / (2 * pi) * ln_low) * (2 * pi) / ln_hi
                    if np.any(np.abs(required) > cfg.beta_abs_max):
                        continue
                    fracs: list[Fraction] = []
                    beta_complexity = 0.0
                    ok = True
                    for x in required:
                        frac, _err, comp = nearest_rational(float(x), cfg.beta_denominator)
                        if abs(float(frac)) > cfg.beta_abs_max:
                            ok = False
                            break
                        fracs.append(frac)
                        beta_complexity += comp
                    if not ok:
                        continue
                    cand = self._make_candidate(alpha_u, denom, hi, lo, clock_cost, fracs, required)
                    if cand is None:
                        continue
                    _push_top(heap, cand, cfg.top_k, counter)
                    counter += 1
        rng = random.Random(cfg.seed)
        # Optional local random jitter/refinement around the current top; this is
        # deterministic under the seed and useful for larger local runs.
        for _ in range(max(0, cfg.random_refine)):
            if not heap:
                break
            base = rng.choice(heap)[2]
            a0 = float(base.metadata["alpha_U_inv_value"])
            d0 = int(round(float(base.metadata["scale_denominator_value"])))
            clock = str(base.formulas["clock"]).split("=")[-1].strip()
            try:
                hi0, lo0 = [int(x) for x in clock.split(":")]
            except Exception:
                hi0, lo0 = 6, 13
            alpha_val = max(cfg.min_alpha_u_inv, min(cfg.max_alpha_u_inv, round((a0 + rng.choice([-1, -0.5, 0, 0.5, 1])) * 2) / 2))
            denom_val = max(1, min(cfg.max_scale_denominator, d0 + rng.choice([-2, -1, 0, 1, 2])))
            hi = max(1, min(cfg.max_clock, hi0 + rng.choice([-1, 0, 1])))
            lo = max(1, min(cfg.max_clock, lo0 + rng.choice([-1, 0, 1])))
            if gcd(hi, lo) != 1:
                continue
            alpha_q = ExactQuantity(alpha_val, f"{int(round(2*alpha_val))}/2", 3.0)
            denom_q = ExactQuantity(float(denom_val), str(denom_val), 3.0)
            m_u = cfg.reduced_planck_mass_gev / denom_q.value
            if m_u <= self.bench.mz_gev.value:
                continue
            log_total = log(m_u / self.bench.mz_gev.value)
            ln_hi = hi / (hi + lo) * log_total
            ln_low = lo / (hi + lo) * log_total
            required = (target - alpha_q.value - b_sm / (2 * pi) * ln_low) * (2 * pi) / ln_hi
            if np.any(np.abs(required) > cfg.beta_abs_max):
                continue
            fracs = [nearest_rational(float(x), cfg.beta_denominator)[0] for x in required]
            cand = self._make_candidate(alpha_q, denom_q, hi, lo, 2.0, fracs, required)
            if cand is not None:
                _push_top(heap, cand, cfg.top_k, counter)
                counter += 1
        candidates = [item[2] for item in sorted(heap, key=lambda x: (-x[0], x[1]))]
        # Preserve the audited ISDLC--TCPS seed even if post-hoc rationalized
        # candidates rank above it.  This keeps previous validation comparable.
        if cfg.min_alpha_u_inv <= 46.5 <= cfg.max_alpha_u_inv and cfg.max_scale_denominator >= 40 and cfg.max_clock >= 13:
            alpha_q = ExactQuantity(46.5, "|Delta(D5)| + rank(D5) + b2(T3)/2 = 93/2", 1.0)
            denom_q = ExactQuantity(40.0, "|Delta(D5)| = 40", 1.0)
            beta_fracs = (Fraction(-8, 5), Fraction(-3, 1), Fraction(-7, 1))
            required = [float(x) for x in beta_fracs]
            isdlc = self._make_candidate(alpha_q, denom_q, 6, 13, 1.0, beta_fracs, required)
            if isdlc is not None and all(c.metadata.get("provenance") != "audited_seed_ISDLC_TCPS" for c in candidates):
                candidates.append(isdlc)
        return sorted(candidates, key=lambda c: c.score.objective)


# ---------------------------------------------------------------------------
# Vacuum-energy / instanton discovery


@dataclass(frozen=True)
class VacuumSearchConfig:
    top_k: int = 40
    max_prefactor_power: int = 8
    min_action_n: float = 60.0
    max_action_n: float = 130.0
    action_denominator: int = 4
    include_alpha_u_values: tuple[float, ...] = tuple()


@dataclass(frozen=True)
class Prefactor:
    value: float
    label: str
    complexity: float


class VacuumInstantonSearcher:
    """Search simple exp(-S) vacuum-energy ansaetze in Planck units."""

    def __init__(self, bench: BenchmarkData, targets: Mapping[str, Target], config: VacuumSearchConfig | None = None):
        self.bench = bench
        self.targets = targets
        self.config = config or VacuumSearchConfig()
        lam = lambda_from_flat_lcdm(bench)
        self.target_rho = lam.lambda_planck_units / (8.0 * pi)

    def _prefactors(self) -> list[Prefactor]:
        cfg = self.config
        out: dict[str, Prefactor] = {}
        bases = [
            (1.0, "1", 0.5),
            (pi, "pi", 0.9),
            (2.0 * pi, "2*pi", 1.0),
            (4.0 * pi, "4*pi", 1.1),
            (8.0 * pi, "8*pi", 1.2),
        ]
        for base, label, base_cost in bases:
            for p in range(-2, cfg.max_prefactor_power + 1):
                if p == 0:
                    val = 1.0
                    lab = "1"
                    cost = 0.5
                elif p == 1:
                    val = base
                    lab = label
                    cost = base_cost
                else:
                    val = base**p
                    lab = f"({label})^{p}"
                    cost = base_cost + 0.2 * abs(p)
                out.setdefault(lab, Prefactor(val, lab, cost))
        # Common loop-normalization factors.
        extra = []
        for p in range(0, cfg.max_prefactor_power + 1):
            extra.append(((4 * pi) ** p / (8 * pi), f"(4*pi)^{p}/(8*pi)", 1.6 + 0.2 * p))
            extra.append(((4 * pi) ** p * (8 * pi), f"(4*pi)^{p}*(8*pi)", 1.6 + 0.2 * p))
        for val, lab, cost in extra:
            out.setdefault(lab, Prefactor(float(val), lab, cost))
        return list(out.values())

    def _candidate_from(self, pref: Prefactor, n: Fraction, label_n: str, n_complexity: float) -> DiscoveryCandidate | None:
        n_float = float(n)
        if not (self.config.min_action_n <= n_float <= self.config.max_action_n):
            return None
        pred = pref.value * exp(-n_float * pi)
        if pred <= 0 or not isfinite(pred):
            return None
        log10_err = abs(log(pred / self.target_rho, 10))
        complexity = pref.complexity + n_complexity
        penalty = 1.5 + 0.25 * log(max(2.0, self.config.max_prefactor_power * self.config.action_denominator + 1))
        # Use log error for discovery ranking because the microscopic theory
        # uncertainty is not known; strict sigma scoring is added by the main engine.
        objective = log10_err + 0.03 * complexity + penalty
        score = DiscoveryScore(
            chi2=None,
            max_abs_z=None,
            log10_error=log10_err,
            complexity=complexity,
            post_selection_penalty=penalty,
            objective=objective,
            dof=1,
        )
        preds = {
            "rhoLambda_planck4": Prediction(
                "rhoLambda_planck4",
                pred,
                derived=True,
                note="Auto-generated instanton-style vacuum-energy ansatz; determinant/action were searched, not derived.",
            )
        }
        return DiscoveryCandidate(
            family="vacuum_instanton",
            name=f"auto vacuum ansatz: rho/M_Pl^4 = {pref.label} * exp(-({label_n})*pi)",
            predictions=preds,
            score=score,
            formulas={
                "rhoLambda_planck4": f"{pref.label} * exp(-({label_n})*pi)",
                "target_used": "rho_Lambda/M_Pl^4 = Lambda*l_P^2/(8*pi)",
            },
            metadata={
                "prefactor": pref.label,
                "prefactor_value": pref.value,
                "action_n": str(n),
                "action_n_value": n_float,
                "prediction": pred,
                "target": self.target_rho,
                "ratio_predicted_to_target": pred / self.target_rho,
                "post_selection_warning": "Order-of-magnitude matches must not be promoted to a derivation without a microscopic determinant calculation.",
            },
            free_parameters=("post-selected instanton grammar choices",),
            post_selected=True,
            certified_first_principles=False,
        )

    def search(self) -> list[DiscoveryCandidate]:
        cfg = self.config
        heap: list[tuple[float, int, DiscoveryCandidate]] = []
        counter = 0
        log_target = log(self.target_rho)
        for pref in self._prefactors():
            if pref.value <= 0:
                continue
            # Goal-directed rational action quantum.
            needed = (log(pref.value) - log_target) / pi
            frac, _err, comp = nearest_rational(needed, cfg.action_denominator, max_abs_num=1000)
            for n_frac, label, n_comp in [(frac, str(frac), comp)]:
                cand = self._candidate_from(pref, n_frac, label, n_comp)
                if cand is not None:
                    _push_top(heap, cand, cfg.top_k, counter)
                    counter += 1
            # Discrete alpha_U-tied actions, e.g. S = 2*pi*alpha_U^-1.
            for a in cfg.include_alpha_u_values:
                for mult in (Fraction(1, 1), Fraction(2, 1), Fraction(3, 2), Fraction(5, 2)):
                    n_val = Fraction(int(round(2 * a)), 2) * mult
                    label = f"{mult}*alpha_U^-1[{a:g}]"
                    cand = self._candidate_from(pref, n_val, label, 2.0 + log(float(n_val) + 1, 2) / 4)
                    if cand is not None:
                        _push_top(heap, cand, cfg.top_k, counter)
                        counter += 1
        return [item[2] for item in sorted(heap, key=lambda x: (-x[0], x[1]))]


# ---------------------------------------------------------------------------
# Symbolic expression search / numerology quarantine


@dataclass(frozen=True)
class SymbolicSearchConfig:
    top_k: int = 20
    beam_width: int = 350
    max_depth: int = 3
    seed: int = 12345
    value_abs_min: float = 1e-140
    value_abs_max: float = 1e140


@dataclass(frozen=True)
class ExprNode:
    value: float
    expr: str
    complexity: float


class BeamSymbolicSearcher:
    """Small beam-style symbolic search for closed forms.

    This is deliberately labelled as numerology unless the expression is later
    attached to an independently specified microscopic derivation.
    """

    def __init__(self, bench: BenchmarkData, targets: Mapping[str, Target], config: SymbolicSearchConfig | None = None):
        self.bench = bench
        self.targets = targets
        self.config = config or SymbolicSearchConfig()

    def _atoms(self) -> list[ExprNode]:
        phi = (1 + sqrt(5)) / 2
        atoms = [
            ExprNode(pi, "pi", 1.0),
            ExprNode(exp(1), "e", 1.0),
            ExprNode(phi, "phi", 1.1),
            ExprNode(sqrt(2), "sqrt(2)", 1.2),
            ExprNode(sqrt(3), "sqrt(3)", 1.2),
            ExprNode(sqrt(5), "sqrt(5)", 1.2),
            ExprNode(log(2), "log(2)", 1.2),
            ExprNode(log(3), "log(3)", 1.2),
            ExprNode(2 * pi, "2*pi", 1.2),
            ExprNode(4 * pi, "4*pi", 1.3),
            ExprNode(8 * pi, "8*pi", 1.4),
        ]
        for n in range(1, 21):
            atoms.append(ExprNode(float(n), str(n), 1.5 + log(n + 1, 2) / 5))
        for n in (24, 40, 45, 46.5, 48, 72, 93, 126):
            atoms.append(ExprNode(float(n), str(n).rstrip("0").rstrip("."), 2.2 + log(n + 1, 2) / 5))
        return atoms

    def _valid(self, x: float) -> bool:
        return isfinite(x) and (x == 0 or self.config.value_abs_min <= abs(x) <= self.config.value_abs_max)

    def _key(self, x: float) -> str:
        if x == 0:
            return "0"
        return f"{x:.14e}"

    def _rank_expr(self, node: ExprNode, target_values: Sequence[float]) -> float:
        # Smaller is better.  Use log-relative distance where possible.
        best = float("inf")
        for t in target_values:
            if t == 0 or node.value == 0 or node.value * t <= 0:
                dist = abs(node.value - t) / (abs(t) + 1.0)
            else:
                dist = abs(log(abs(node.value / t)))
            best = min(best, dist)
        return best + 0.01 * node.complexity

    def _prune(self, nodes: Iterable[ExprNode], target_values: Sequence[float]) -> list[ExprNode]:
        uniq: dict[str, ExprNode] = {}
        for n in nodes:
            if not self._valid(n.value):
                continue
            key = self._key(n.value)
            prev = uniq.get(key)
            if prev is None or n.complexity < prev.complexity:
                uniq[key] = n
        ranked = sorted(uniq.values(), key=lambda n: self._rank_expr(n, target_values))
        return ranked[: self.config.beam_width]

    def _expand(self, pool: Sequence[ExprNode]) -> list[ExprNode]:
        out: list[ExprNode] = []
        # Unary operations.
        for a in pool:
            if a.value > 0:
                out.append(ExprNode(sqrt(a.value), f"sqrt({a.expr})", a.complexity + 1.0))
                if a.value != 1:
                    out.append(ExprNode(log(a.value), f"log({a.expr})", a.complexity + 1.2))
                if abs(a.value) < 340:  # avoid overflow
                    out.append(ExprNode(exp(-a.value), f"exp(-({a.expr}))", a.complexity + 1.4))
            out.append(ExprNode(a.value * a.value, f"({a.expr})^2", a.complexity + 0.9))
            if a.value != 0:
                out.append(ExprNode(1.0 / a.value, f"1/({a.expr})", a.complexity + 0.8))
        # Binary operations, capped for speed.
        small = sorted(pool, key=lambda n: n.complexity)[: min(len(pool), 160)]
        for i, a in enumerate(small):
            for b in small[i:]:
                comp = a.complexity + b.complexity + 1.0
                out.append(ExprNode(a.value + b.value, f"({a.expr}+{b.expr})", comp))
                out.append(ExprNode(a.value * b.value, f"({a.expr}*{b.expr})", comp + 0.1))
                if a.expr != b.expr:
                    out.append(ExprNode(a.value - b.value, f"({a.expr}-{b.expr})", comp + 0.1))
                    out.append(ExprNode(b.value - a.value, f"({b.expr}-{a.expr})", comp + 0.1))
                if b.value != 0:
                    out.append(ExprNode(a.value / b.value, f"({a.expr}/{b.expr})", comp + 0.2))
                if a.value != 0 and a.expr != b.expr:
                    out.append(ExprNode(b.value / a.value, f"({b.expr}/{a.expr})", comp + 0.2))
        return out

    def search(self, target_names: Sequence[str] = ("alpha0_inv", "alpha_em_inv_mz", "rhoLambda_planck4")) -> list[DiscoveryCandidate]:
        selected_targets: dict[str, Target] = {name: self.targets[name] for name in target_names if name in self.targets}
        # rhoLambda_planck4 is tiny; include it as a target only via log search.
        target_values = [t.value for t in selected_targets.values() if t.value != 0]
        if not target_values:
            return []
        pool = self._prune(self._atoms(), target_values)
        all_nodes = list(pool)
        for _depth in range(self.config.max_depth):
            expanded = self._expand(pool)
            pool = self._prune([*pool, *expanded], target_values)
            all_nodes.extend(pool)
        # Deduplicate final candidates.
        uniq: dict[tuple[str, str], ExprNode] = {}
        for n in all_nodes:
            for target_name, target in selected_targets.items():
                key = (target_name, self._key(n.value))
                prev = uniq.get(key)
                if prev is None or n.complexity < prev.complexity:
                    uniq[key] = n
        heap: list[tuple[float, int, DiscoveryCandidate]] = []
        counter = 0
        for (target_name, _), node in uniq.items():
            target = selected_targets[target_name]
            if target.value == 0 or node.value == 0 or target.value * node.value <= 0:
                log10_err = abs(node.value - target.value) / (abs(target.value) + 1.0)
            else:
                log10_err = abs(log(abs(node.value / target.value), 10))
            complexity = node.complexity
            penalty = 2.5 + 0.1 * self.config.max_depth + 0.001 * self.config.beam_width
            # For ordinary constants with sigma, report z too; keep objective
            # dominated by log closeness because symbolic formulas can be close
            # but still not physically derived.
            chi2 = None
            max_z = None
            if target.sigma is not None and target.sigma > 0:
                z = (node.value - target.value) / target.sigma
                if isfinite(z):
                    chi2 = z * z
                    max_z = abs(z)
            score = DiscoveryScore(
                chi2=chi2,
                max_abs_z=max_z,
                log10_error=log10_err,
                complexity=complexity,
                post_selection_penalty=penalty,
                objective=log10_err + 0.04 * complexity + penalty,
                dof=1,
            )
            preds = {
                target_name: Prediction(
                    target_name,
                    node.value,
                    derived=True,
                    note="Symbolic-regression expression; quarantined as numerology unless independently derived.",
                )
            }
            cand = DiscoveryCandidate(
                family="symbolic_regression_quarantine",
                name=f"symbolic expression for {target_name}: {node.expr}",
                predictions=preds,
                score=score,
                formulas={target_name: node.expr},
                metadata={
                    "target_value": target.value,
                    "prediction": node.value,
                    "log10_error_abs": log10_err,
                    "warning": "A compact formula is not evidence of a first-principles theory by itself.",
                },
                free_parameters=("post-selected expression grammar",),
                post_selected=True,
                certified_first_principles=False,
            )
            _push_top(heap, cand, self.config.top_k, counter)
            counter += 1
        return [item[2] for item in sorted(heap, key=lambda x: (-x[0], x[1]))]


# ---------------------------------------------------------------------------
# Combined orchestration


@dataclass(frozen=True)
class DiscoveryConfig:
    gauge: GaugeSearchConfig = field(default_factory=GaugeSearchConfig)
    vacuum: VacuumSearchConfig = field(default_factory=VacuumSearchConfig)
    symbolic: SymbolicSearchConfig = field(default_factory=SymbolicSearchConfig)
    mode: str = "balanced"

    @staticmethod
    def quick() -> "DiscoveryConfig":
        # Bounded local profile: broad enough to rediscover the ISDLC--TCPS
        # 6:13 clock neighborhood and instanton ansaetze, but small enough to
        # run on a CPU-only laptop/sandbox.  Use ``deep`` for large scans.
        return DiscoveryConfig(
            gauge=GaugeSearchConfig(
                max_clock=13,
                max_scale_denominator=80,
                top_k=25,
                beta_denominator=5,
                min_alpha_u_inv=44.0,
                max_alpha_u_inv=49.0,
            ),
            vacuum=VacuumSearchConfig(top_k=25, max_prefactor_power=6, action_denominator=3),
            symbolic=SymbolicSearchConfig(top_k=12, beam_width=80, max_depth=1),
            mode="quick",
        )

    @staticmethod
    def balanced() -> "DiscoveryConfig":
        return DiscoveryConfig(
            gauge=GaugeSearchConfig(
                max_clock=12,
                max_scale_denominator=90,
                top_k=35,
                beta_denominator=5,
                min_alpha_u_inv=30.0,
                max_alpha_u_inv=70.0,
            ),
            vacuum=VacuumSearchConfig(top_k=35, max_prefactor_power=8, action_denominator=4),
            symbolic=SymbolicSearchConfig(top_k=20, beam_width=220, max_depth=2),
            mode="balanced",
        )

    @staticmethod
    def deep() -> "DiscoveryConfig":
        return DiscoveryConfig(
            gauge=GaugeSearchConfig(max_clock=32, max_scale_denominator=160, top_k=80, beta_denominator=8, random_refine=2000),
            vacuum=VacuumSearchConfig(top_k=80, max_prefactor_power=10, action_denominator=6),
            symbolic=SymbolicSearchConfig(top_k=40, beam_width=500, max_depth=3),
            mode="deep",
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "gauge": self.gauge.__dict__,
            "vacuum": self.vacuum.__dict__,
            "symbolic": self.symbolic.__dict__,
        }


class TheoryDiscoveryEngine:
    """Run all automatic-discovery passes and package results."""

    def __init__(self, bench: BenchmarkData | None = None, config: DiscoveryConfig | None = None):
        self.bench = bench or load_benchmarks()
        self.config = config or DiscoveryConfig.balanced()
        self.strict_engine = DerivationEngine(self.bench)

    def run(self) -> dict[str, object]:
        started = time.perf_counter()
        hardware = detect_hardware()
        gauge = GaugeClockSearcher(self.bench, self.strict_engine.targets, self.config.gauge).search()
        alpha_values = tuple(
            sorted({float(c.metadata.get("alpha_U_inv_value")) for c in gauge[:12] if "alpha_U_inv_value" in c.metadata})
        )
        # Always include the ISDLC alpha_U value if within the search range;
        # this is not special scoring, just a useful known stress point.
        alpha_values = tuple(sorted(set(alpha_values + (46.5,))))
        vacuum_cfg = VacuumSearchConfig(
            top_k=self.config.vacuum.top_k,
            max_prefactor_power=self.config.vacuum.max_prefactor_power,
            min_action_n=self.config.vacuum.min_action_n,
            max_action_n=self.config.vacuum.max_action_n,
            action_denominator=self.config.vacuum.action_denominator,
            include_alpha_u_values=alpha_values,
        )
        vacuum = VacuumInstantonSearcher(self.bench, self.strict_engine.targets, vacuum_cfg).search()
        symbolic = BeamSymbolicSearcher(self.bench, self.strict_engine.targets, self.config.symbolic).search()
        # Strictly score the best generated hypotheses as post-selected controls.
        strict_scores: list[EvaluationResult] = []
        for cand in [*gauge[:5], *vacuum[:5], *symbolic[:5]]:
            strict_scores.append(self.strict_engine.evaluate(AutoCandidateModel(cand)))
        elapsed = time.perf_counter() - started
        best = {
            "gauge": gauge[0].as_dict() if gauge else None,
            "vacuum": vacuum[0].as_dict() if vacuum else None,
            "symbolic": symbolic[0].as_dict() if symbolic else None,
        }
        combined_verdict = self._combined_verdict(gauge, vacuum, symbolic)
        return {
            "engine": "first-principles-physics-engine automated theory discovery layer",
            "version": "0.2.0-auto-discovery",
            "config": self.config.as_dict(),
            "hardware": hardware.as_dict(),
            "elapsed_seconds": elapsed,
            "benchmark_snapshot": {k: v.__dict__ for k, v in self.bench.as_dict().items()},
            "best": best,
            "gauge_candidates": [c.as_dict() for c in gauge],
            "vacuum_candidates": [c.as_dict() for c in vacuum],
            "symbolic_candidates": [c.as_dict() for c in symbolic],
            "strict_quarantine_scores": [r.as_dict() for r in strict_scores],
            "combined_verdict": combined_verdict,
        }

    def _combined_verdict(self, gauge: Sequence[DiscoveryCandidate], vacuum: Sequence[DiscoveryCandidate], symbolic: Sequence[DiscoveryCandidate]) -> dict[str, object]:
        gauge_ok = bool(gauge and gauge[0].score.max_abs_z is not None and gauge[0].score.max_abs_z < 2.0)
        vacuum_factor = None
        if vacuum:
            vacuum_factor = float(vacuum[0].metadata.get("ratio_predicted_to_target", float("nan")))
        return {
            "claim_status": "candidate_generation_only_not_a_completed_first_principles_derivation",
            "gauge_best_under_2sigma": gauge_ok,
            "best_vacuum_factor": vacuum_factor,
            "alpha0_closed_from_microscopic_thresholds": False,
            "reason": (
                "The engine can discover compact RGE/vacuum/symbolic hypotheses, but every generated result is "
                "post-selected from benchmark constants.  A completed first-principles theory would need an independently "
                "specified microscopic spectrum, threshold calculation, and new predictions not used in the search."
            ),
        }


def flatten_candidates_for_csv(results: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family_key in ("gauge_candidates", "vacuum_candidates", "symbolic_candidates"):
        candidates = results.get(family_key, [])
        if not isinstance(candidates, list):
            continue
        for rank, cand in enumerate(candidates, start=1):
            if not isinstance(cand, Mapping):
                continue
            score = cand.get("score", {}) if isinstance(cand.get("score"), Mapping) else {}
            meta = cand.get("metadata", {}) if isinstance(cand.get("metadata"), Mapping) else {}
            rows.append(
                {
                    "family": cand.get("family"),
                    "rank": rank,
                    "name": cand.get("name"),
                    "objective": score.get("objective"),
                    "chi2": score.get("chi2"),
                    "max_abs_z": score.get("max_abs_z"),
                    "log10_error": score.get("log10_error"),
                    "complexity": score.get("complexity"),
                    "post_selection_penalty": score.get("post_selection_penalty"),
                    "certified_first_principles": cand.get("certified_first_principles"),
                    "post_selected": cand.get("post_selected"),
                    "ratio_predicted_to_target": meta.get("ratio_predicted_to_target"),
                    "alpha_U_inv_value": meta.get("alpha_U_inv_value"),
                    "M_U_GeV": meta.get("M_U_GeV"),
                    "M_I_GeV": meta.get("M_I_GeV"),
                }
            )
    return rows


def write_json(path: str, results: Mapping[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def write_csv(path: str, results: Mapping[str, object]) -> None:
    import csv

    rows = flatten_candidates_for_csv(results)
    fieldnames = [
        "family",
        "rank",
        "name",
        "objective",
        "chi2",
        "max_abs_z",
        "log10_error",
        "complexity",
        "post_selection_penalty",
        "certified_first_principles",
        "post_selected",
        "ratio_predicted_to_target",
        "alpha_U_inv_value",
        "M_U_GeV",
        "M_I_GeV",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate_markdown_report(results: Mapping[str, object]) -> str:
    """Generate a Korean Markdown report for the discovery run."""

    def fmt(x: object, digits: int = 6) -> str:
        if isinstance(x, float):
            if x == 0:
                return "0"
            if abs(x) < 1e-4 or abs(x) >= 1e5:
                return f"{x:.{digits}e}"
            return f"{x:.{digits}f}"
        return str(x)

    best = results.get("best", {}) if isinstance(results.get("best"), Mapping) else {}
    verdict = results.get("combined_verdict", {}) if isinstance(results.get("combined_verdict"), Mapping) else {}
    hw = results.get("hardware", {}) if isinstance(results.get("hardware"), Mapping) else {}
    lines: list[str] = []
    lines.append("# 자동 이론 개발/발견 엔진 실행 보고서")
    lines.append("")
    lines.append("## 결론")
    lines.append("")
    lines.append(
        "이번 업그레이드는 기존 검증 엔진 위에 후보 이론을 자동 생성하는 층을 추가했다. "
        "엔진은 RGE clock 후보, instanton형 우주상수 후보, symbolic-regression 후보를 생성하고 "
        "정밀 상수 benchmark에 대해 점수화한다. 그러나 모든 자동 생성 후보는 검색 대상 benchmark를 사용했으므로 "
        "`post_selected=True`로 격리되며, 이것만으로 제1원리 유도라고 인증하지 않는다."
    )
    lines.append("")
    lines.append(f"- 통합 판정: `{verdict.get('claim_status')}`")
    lines.append(f"- gauge best가 2σ 안인가: `{verdict.get('gauge_best_under_2sigma')}`")
    lines.append(f"- best vacuum factor: `{fmt(verdict.get('best_vacuum_factor'))}`")
    lines.append(f"- alpha(0) microscopic threshold closure: `{verdict.get('alpha0_closed_from_microscopic_thresholds')}`")
    lines.append("")
    lines.append("## 실행 환경")
    lines.append("")
    lines.append(f"- Python: `{hw.get('python')}`")
    lines.append(f"- Platform: `{hw.get('platform')}`")
    lines.append(f"- CPU count: `{hw.get('cpu_count')}`")
    lines.append(f"- NumPy: `{hw.get('numpy_version')}`")
    lines.append(f"- Torch available: `{hw.get('torch_available')}`")
    lines.append(f"- CUDA available: `{hw.get('cuda_available')}`")
    lines.append(f"- elapsed seconds: `{fmt(results.get('elapsed_seconds'), 3)}`")
    lines.append("")
    lines.append("## 방법론")
    lines.append("")
    lines.append(
        "1. **정확/유리수 문법 생성**: Lie root count, half-integer stiffness, compact clock ratio, "
        "작은 유리수 beta-vector를 생성한다."
    )
    lines.append(
        "2. **RGE gauge-clock search**: `alpha_i^-1(M_Z)=alpha_U^-1 + b_SM ln(M_I/M_Z)/(2π) + "
        "b_high ln(M_U/M_I)/(2π)` 형태를 전수/근방 탐색한다."
    )
    lines.append(
        "3. **Vacuum-instanton search**: `rho_Lambda/M_Pl^4 = C exp(-nπ)` 꼴에서 prefactor와 action quantum을 탐색한다."
    )
    lines.append(
        "4. **Symbolic regression quarantine**: 작은 수학 문법으로 닫힌식을 찾되, 물리적 유도 없이 발견된 식은 numerology로 격리한다."
    )
    lines.append(
        "5. **MDL/과적합 방지**: chi-square/log-error와 별도로 복잡도 및 post-selection penalty를 기록한다."
    )
    lines.append("")
    for key, title in (("gauge", "최고 gauge-clock 후보"), ("vacuum", "최고 vacuum 후보"), ("symbolic", "최고 symbolic 후보")):
        cand = best.get(key) if isinstance(best, Mapping) else None
        if not isinstance(cand, Mapping):
            continue
        score = cand.get("score", {}) if isinstance(cand.get("score"), Mapping) else {}
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"- 이름: `{cand.get('name')}`")
        lines.append(f"- objective: `{fmt(score.get('objective'))}`")
        lines.append(f"- chi2: `{fmt(score.get('chi2'))}`")
        lines.append(f"- max |z|: `{fmt(score.get('max_abs_z'))}`")
        lines.append(f"- log10 error: `{fmt(score.get('log10_error'))}`")
        lines.append(f"- complexity: `{fmt(score.get('complexity'))}`")
        lines.append(f"- post-selected: `{cand.get('post_selected')}`")
        lines.append(f"- certified first-principles: `{cand.get('certified_first_principles')}`")
        formulas = cand.get("formulas", {})
        if isinstance(formulas, Mapping):
            lines.append("")
            lines.append("공식:")
            for fk, fv in formulas.items():
                lines.append(f"- `{fk}`: `{fv}`")
        preds = cand.get("predictions", {})
        if isinstance(preds, Mapping):
            lines.append("")
            lines.append("예측값:")
            for pk, pv in preds.items():
                if isinstance(pv, Mapping):
                    lines.append(f"- `{pk}` = `{fmt(pv.get('value'))}`")
        lines.append("")

    audited = []
    for cand in results.get("gauge_candidates", []) if isinstance(results.get("gauge_candidates"), list) else []:
        if isinstance(cand, Mapping):
            meta = cand.get("metadata", {}) if isinstance(cand.get("metadata"), Mapping) else {}
            if meta.get("provenance") == "audited_seed_ISDLC_TCPS" or "ISDLC" in str(cand.get("name", "")):
                audited.append(cand)
    if audited:
        lines.append("## 보존된 audited seed 비교: ISDLC--TCPS")
        lines.append("")
        cand = audited[0]
        score = cand.get("score", {}) if isinstance(cand.get("score"), Mapping) else {}
        meta = cand.get("metadata", {}) if isinstance(cand.get("metadata"), Mapping) else {}
        lines.append(f"- 이름: `{cand.get('name')}`")
        lines.append(f"- chi2: `{fmt(score.get('chi2'))}`")
        lines.append(f"- max |z|: `{fmt(score.get('max_abs_z'))}`")
        lines.append(f"- alpha_U^-1: `{fmt(meta.get('alpha_U_inv_value'))}`")
        lines.append(f"- M_U: `{fmt(meta.get('M_U_GeV'))} GeV`")
        lines.append(f"- M_I: `{fmt(meta.get('M_I_GeV'))} GeV`")
        lines.append(f"- b_high: `{meta.get('rationalized_b_high')}`")
        preds = cand.get("predictions", {}) if isinstance(cand.get("predictions"), Mapping) else {}
        for pk, pv in preds.items():
            if isinstance(pv, Mapping):
                lines.append(f"- `{pk}` = `{fmt(pv.get('value'))}`")
        lines.append(
            "- 해석: 자동 post-hoc 후보들은 더 작은 chi-square를 만들 수 있지만, ISDLC--TCPS seed는 "
            "미리 주어진 discrete 구조로 보존된 비교점이다. 현 benchmark 기준으로는 tension이며, "
            "alpha(0)와 vacuum determinant까지 닫히지 않는다."
        )
        lines.append("")

    lines.append("## 해석")
    lines.append("")
    lines.append(
        "자동 발견 엔진의 성공 기준은 '상수를 맞히는 식 하나'가 아니다. 진짜 성공 조건은 "
        "독립적으로 주어진 microscopic axioms가 spectrum, threshold, vacuum determinant를 모두 산출하고, "
        "검색에 쓰지 않은 새로운 관측량까지 맞히는 것이다. 현재 산출물은 그 다음 연구를 위한 후보 생성기와 "
        "반례 탐색기이다."
    )
    lines.append("")
    return "\n".join(lines)


def write_report(path: str, results: Mapping[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(generate_markdown_report(results))

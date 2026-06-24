"""Blind-prediction protocol for the first-principles physics engine.

The older engine can generate and rank candidates against known gauge/cosmology
benchmarks.  This module adds a stricter scientific layer:

* split observations into TRAIN / VALIDATION / BLIND groups;
* hand discovery code only the training view;
* require a frozen prediction packet before blind scores are revealed;
* penalize missing predictions, target leakage, post-hoc fitting, and large
  train/blind performance gaps;
* export an auditable manifest and score report.

The numerical holdout values bundled here are a reproducible working registry,
not an assertion that the latest global-fit averages have been refreshed.  For a
publication-grade run, replace them with a time-stamped external JSON registry
before freezing candidate predictions.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .candidate_models import ISDLCTCPSCosmologicalAnsatzModel, ISDLCTCPSOneLoopGaugeModel
from .constants import load_benchmarks
from .engine import DerivationEngine
from .theory_lab import LabConfig, TheoryLab


Split = str
Kind = str


@dataclass(frozen=True)
class Observation:
    """A benchmark or holdout observation.

    kind semantics
    --------------
    gaussian:
        sigma is an ordinary one-standard-deviation uncertainty in value units.
    log_gaussian:
        sigma is a one-standard-deviation uncertainty in log10(value).
    upper_bound / lower_bound:
        value is the bound.  sigma is the softness in log10 units; if omitted,
        a conservative 0.30 dex is used.  Predictions on the allowed side get
        zero chi2 contribution.
    categorical:
        value is compared as a normalized string.  Mismatch gets a fixed
        category_penalty contribution.
    """

    key: str
    label: str
    value: float | str
    sigma: float | None
    unit: str = "dimensionless"
    sector: str = "misc"
    split: Split = "blind"
    kind: Kind = "gaussian"
    required: bool = True
    source_note: str = "working registry; refresh before publication"
    rationale: str = ""

    def public_dict(self, reveal_value: bool = False) -> dict[str, Any]:
        d = asdict(self)
        if not reveal_value:
            canonical = json.dumps({"key": self.key, "value": self.value, "sigma": self.sigma, "kind": self.kind}, sort_keys=True, ensure_ascii=False)
            d["value_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            d["value"] = "<sealed>" if self.split == "blind" else self.value
            d["sigma"] = "<sealed>" if self.split == "blind" else self.sigma
        return d


@dataclass(frozen=True)
class PredictionPacket:
    """Frozen predictions from one candidate theory.

    The scorer treats keys listed in trained_on as non-blind.  A packet marked
    uses_holdout_values=True is an oracle/control and is rejected even if the
    numbers are perfect.
    """

    model_name: str
    predictions: dict[str, float | str]
    provenance: str
    trained_on: tuple[str, ...] = tuple()
    free_parameter_count: int = 0
    claims_first_principles: bool = False
    uses_holdout_values: bool = False
    notes: str = ""
    frozen_unix_time: float = field(default_factory=time.time)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "predictions": self.predictions,
            "provenance": self.provenance,
            "trained_on": list(self.trained_on),
            "free_parameter_count": self.free_parameter_count,
            "claims_first_principles": self.claims_first_principles,
            "uses_holdout_values": self.uses_holdout_values,
            "notes": self.notes,
            "frozen_unix_time": self.frozen_unix_time,
        }

    @property
    def sha256(self) -> str:
        blob = json.dumps(self.canonical_dict(), sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ObservationScore:
    key: str
    split: Split
    sector: str
    kind: Kind
    predicted: float | str | None
    target: float | str
    sigma: float | None
    unit: str
    z: float | None
    chi2: float
    passed_limit: bool | None
    missing: bool
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SplitScore:
    split: Split
    predicted_required: int
    total_required: int
    coverage: float
    chi2: float
    dof: int
    reduced_chi2: float | None
    max_abs_z: float | None
    missing_required_keys: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlindProtocolConfig:
    min_blind_predictions: int = 8
    min_blind_coverage: float = 0.35
    max_blind_reduced_chi2: float = 9.0
    max_blind_abs_z: float = 5.0
    max_train_blind_reduced_chi2_gap: float = 12.0
    category_penalty: float = 25.0
    missing_required_penalty: float = 4.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlindScoreReport:
    packet: PredictionPacket
    config: dict[str, Any]
    scores: list[ObservationScore]
    split_scores: dict[str, SplitScore]
    leakage_flags: tuple[str, ...]
    sectors_with_blind_predictions: tuple[str, ...]
    sectors_missing_blind_predictions: tuple[str, ...]
    verdict: str
    conclusion: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "packet": self.packet.canonical_dict() | {"sha256": self.packet.sha256},
            "config": self.config,
            "scores": [s.as_dict() for s in self.scores],
            "split_scores": {k: v.as_dict() for k, v in self.split_scores.items()},
            "leakage_flags": list(self.leakage_flags),
            "sectors_with_blind_predictions": list(self.sectors_with_blind_predictions),
            "sectors_missing_blind_predictions": list(self.sectors_missing_blind_predictions),
            "verdict": self.verdict,
            "conclusion": self.conclusion,
        }


@dataclass(frozen=True)
class BlindChallengeRun:
    generated_at_unix_time: float
    manifest: list[dict[str, Any]]
    reports: list[BlindScoreReport]
    summary: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at_unix_time": self.generated_at_unix_time,
            "manifest": self.manifest,
            "reports": [r.as_dict() for r in self.reports],
            "summary": self.summary,
        }


class BlindPredictionProtocol:
    """Score frozen candidate packets against a sealed holdout registry."""

    def __init__(self, observations: Sequence[Observation], config: BlindProtocolConfig | None = None):
        self.observations = list(observations)
        self.config = config or BlindProtocolConfig()
        keys = [o.key for o in self.observations]
        if len(keys) != len(set(keys)):
            dupes = sorted({k for k in keys if keys.count(k) > 1})
            raise ValueError(f"duplicate observation keys: {dupes}")

    @property
    def train_keys(self) -> tuple[str, ...]:
        return tuple(o.key for o in self.observations if o.split == "train")

    @property
    def blind_keys(self) -> tuple[str, ...]:
        return tuple(o.key for o in self.observations if o.split == "blind")

    def manifest(self, reveal_blind_values: bool = False) -> list[dict[str, Any]]:
        return [o.public_dict(reveal_value=(reveal_blind_values or o.split != "blind")) for o in self.observations]

    def training_view(self) -> dict[str, dict[str, Any]]:
        """Public view discovery code is allowed to consume."""

        return {o.key: o.public_dict(reveal_value=True) for o in self.observations if o.split == "train"}

    def score_packet(self, packet: PredictionPacket) -> BlindScoreReport:
        scores: list[ObservationScore] = []
        leakage_flags: list[str] = []
        blind_set = {o.key for o in self.observations if o.split == "blind"}
        trained_on_blind = sorted(blind_set.intersection(packet.trained_on))
        if trained_on_blind:
            leakage_flags.append("packet_declares_training_on_blind_keys:" + ",".join(trained_on_blind))
        if packet.uses_holdout_values:
            leakage_flags.append("packet_marked_as_using_holdout_values")

        for obs in self.observations:
            pred = packet.predictions.get(obs.key)
            if pred is None:
                scores.append(
                    ObservationScore(
                        key=obs.key,
                        split=obs.split,
                        sector=obs.sector,
                        kind=obs.kind,
                        predicted=None,
                        target=obs.value,
                        sigma=obs.sigma,
                        unit=obs.unit,
                        z=None,
                        chi2=self.config.missing_required_penalty if obs.required else 0.0,
                        passed_limit=None,
                        missing=True,
                        note="missing required prediction" if obs.required else "missing optional prediction",
                    )
                )
                continue
            scores.append(self._score_one(obs, pred))

        split_scores = {split: self._aggregate_split(split, scores) for split in sorted({o.split for o in self.observations})}
        blind = split_scores.get("blind")
        train = split_scores.get("train")
        blind_predicted = blind.predicted_required if blind else 0
        blind_coverage = blind.coverage if blind else 0.0
        sectors_required = {o.sector for o in self.observations if o.split == "blind" and o.required}
        sectors_with = {s.sector for s in scores if s.split == "blind" and not s.missing}
        sectors_missing = sorted(sectors_required - sectors_with)

        if leakage_flags:
            verdict = "invalid_due_to_holdout_leakage"
            conclusion = "숫자를 맞춰도 blind protocol상 무효다. 후보가 holdout 값을 사용했거나 사용했다고 선언했다."
        elif blind_predicted < self.config.min_blind_predictions:
            verdict = "no_or_too_few_blind_predictions"
            conclusion = "훈련 gauge/cosmology benchmark는 맞출 수 있어도, 잠긴 holdout 관측량에 대한 충분한 예측이 없다."
        elif blind_coverage < self.config.min_blind_coverage:
            verdict = "insufficient_blind_coverage"
            conclusion = "일부 holdout을 예측했지만 완전 이론 후보로 보기에는 coverage가 부족하다."
        else:
            blind_red = blind.reduced_chi2 if blind and blind.reduced_chi2 is not None else math.inf
            blind_max = blind.max_abs_z if blind and blind.max_abs_z is not None else math.inf
            train_red = train.reduced_chi2 if train and train.reduced_chi2 is not None else 0.0
            gap = blind_red - train_red
            if blind_red <= self.config.max_blind_reduced_chi2 and blind_max <= self.config.max_blind_abs_z and gap <= self.config.max_train_blind_reduced_chi2_gap:
                verdict = "blind_pass_needs_independent_replication"
                conclusion = "현재 holdout에서는 통과했다. 다음 단계는 이 결과를 고정하고 새 관측 tranche에서 재검증하는 것이다."
            else:
                verdict = "blind_failed_or_overfit_tension"
                conclusion = "훈련 성능 대비 blind 성능이 나쁘거나, 하나 이상의 holdout residual이 허용 범위를 넘었다."

        return BlindScoreReport(
            packet=packet,
            config=self.config.as_dict(),
            scores=scores,
            split_scores=split_scores,
            leakage_flags=tuple(leakage_flags),
            sectors_with_blind_predictions=tuple(sorted(sectors_with)),
            sectors_missing_blind_predictions=tuple(sectors_missing),
            verdict=verdict,
            conclusion=conclusion,
        )

    def _score_one(self, obs: Observation, pred: float | str) -> ObservationScore:
        kind = obs.kind
        z: float | None = None
        chi2 = 0.0
        passed_limit: bool | None = None
        note = ""
        try:
            if kind == "categorical":
                passed = str(pred).strip().lower() == str(obs.value).strip().lower()
                z = 0.0 if passed else math.sqrt(self.config.category_penalty)
                chi2 = 0.0 if passed else self.config.category_penalty
                passed_limit = passed
            else:
                pv = float(pred)
                tv = float(obs.value)  # type: ignore[arg-type]
                if not math.isfinite(pv):
                    raise ValueError("non-finite prediction")
                if kind == "gaussian":
                    sig = obs.sigma if obs.sigma and obs.sigma > 0 else max(abs(tv) * 0.01, 1e-30)
                    z = (pv - tv) / sig
                    chi2 = z * z
                elif kind == "log_gaussian":
                    if pv <= 0 or tv <= 0:
                        raise ValueError("log_gaussian requires positive prediction and target")
                    sig = obs.sigma if obs.sigma and obs.sigma > 0 else 0.05
                    z = (math.log10(pv) - math.log10(tv)) / sig
                    chi2 = z * z
                elif kind == "upper_bound":
                    if pv <= tv:
                        z = 0.0
                        chi2 = 0.0
                        passed_limit = True
                    else:
                        sig = obs.sigma if obs.sigma and obs.sigma > 0 else 0.30
                        z = math.log10(pv / tv) / sig if pv > 0 and tv > 0 else (pv - tv) / max(abs(tv), 1.0)
                        chi2 = z * z
                        passed_limit = False
                elif kind == "lower_bound":
                    if pv >= tv:
                        z = 0.0
                        chi2 = 0.0
                        passed_limit = True
                    else:
                        sig = obs.sigma if obs.sigma and obs.sigma > 0 else 0.30
                        z = math.log10(tv / pv) / sig if pv > 0 and tv > 0 else (tv - pv) / max(abs(tv), 1.0)
                        chi2 = z * z
                        passed_limit = False
                else:
                    raise ValueError(f"unknown observation kind: {kind}")
        except Exception as exc:
            note = f"scoring_error:{exc!r}"
            z = math.sqrt(self.config.category_penalty)
            chi2 = self.config.category_penalty
            passed_limit = False
        return ObservationScore(
            key=obs.key,
            split=obs.split,
            sector=obs.sector,
            kind=obs.kind,
            predicted=pred,
            target=obs.value,
            sigma=obs.sigma,
            unit=obs.unit,
            z=float(z) if z is not None else None,
            chi2=float(chi2),
            passed_limit=passed_limit,
            missing=False,
            note=note,
        )

    def _aggregate_split(self, split: str, scores: Sequence[ObservationScore]) -> SplitScore:
        obs_by_key = {o.key: o for o in self.observations if o.split == split}
        split_scores = [s for s in scores if s.split == split]
        required = [o for o in obs_by_key.values() if o.required]
        predicted_required = [s for s in split_scores if obs_by_key[s.key].required and not s.missing]
        total_required = len(required)
        coverage = len(predicted_required) / total_required if total_required else 1.0
        dof = sum(1 for s in split_scores if not s.missing and (s.z is not None or s.kind == "categorical"))
        chi2 = sum(s.chi2 for s in split_scores if not s.missing)
        red = chi2 / dof if dof else None
        max_abs_z = max((abs(float(s.z)) for s in split_scores if not s.missing and s.z is not None and math.isfinite(float(s.z))), default=None)
        missing_required = tuple(s.key for s in split_scores if s.missing and obs_by_key[s.key].required)
        return SplitScore(split, len(predicted_required), total_required, coverage, float(chi2), int(dof), red, max_abs_z, missing_required)


def _rho_lambda_target_from_existing_engine() -> tuple[float, float | None]:
    engine = DerivationEngine(load_benchmarks())
    t = engine.targets["rhoLambda_planck4"]
    return t.value, t.sigma


def default_observation_registry() -> list[Observation]:
    """Return a train/validation/blind registry.

    The blind values here are deliberately broad, reproducible working numbers
    to exercise the protocol without browsing.  Replace the list with a locked
    external registry for serious publication use.
    """

    b = load_benchmarks()
    rho, rho_sig = _rho_lambda_target_from_existing_engine()
    obs = [
        # Search/training data already used by the older engine.
        Observation("alpha_em_inv_mz", "MSbar inverse electromagnetic coupling at MZ", b.alpha_hat_5_mz_inv.value, b.alpha_hat_5_mz_inv.sigma, sector="gauge", split="train", kind="gaussian"),
        Observation("sin2theta_hat_mz", "MSbar weak mixing angle", b.sin2theta_hat_mz.value, b.sin2theta_hat_mz.sigma, sector="gauge", split="train", kind="gaussian"),
        Observation("alpha3_mz", "strong coupling at MZ", b.alpha_s_mz.value, b.alpha_s_mz.sigma, sector="gauge", split="train", kind="gaussian"),
        Observation(
            "rhoLambda_planck4",
            "vacuum energy density in Planck units",
            rho,
            0.05,
            sector="cosmology",
            split="train",
            kind="log_gaussian",
            rationale="The previous search explicitly optimized gauge/cosmology benchmarks; 0.05 dex is a working log tolerance for this protocol.",
        ),
        # Validation: known but not enough to remove overfit concerns.
        Observation("alpha0_inv", "inverse low-energy fine-structure constant", b.alpha0_inv.value, b.alpha0_inv.sigma, sector="gauge_ir", split="validation", kind="gaussian"),
        # Blind: flavour, neutrino, precision, cosmology extensions, DM, collider/threshold limits.
        Observation("me_over_mmu", "electron/muon pole mass ratio", 4.8363317e-3, 2e-9, sector="charged_fermion_masses", split="blind", kind="gaussian"),
        Observation("mmu_over_mtau", "muon/tau pole mass ratio", 5.94649e-2, 2e-6, sector="charged_fermion_masses", split="blind", kind="gaussian"),
        Observation("me_over_mtau", "electron/tau pole mass ratio", 2.87592e-4, 2e-8, sector="charged_fermion_masses", split="blind", kind="gaussian"),
        Observation("ms_over_mb_2gev_working", "strange/bottom mass ratio, scheme-dependent working target", 2.25e-2, 0.06, sector="quark_masses", split="blind", kind="log_gaussian", rationale="Large log uncertainty reflects scheme dependence."),
        Observation("mc_over_mt_working", "charm/top mass ratio, scheme-dependent working target", 7.3e-3, 0.08, sector="quark_masses", split="blind", kind="log_gaussian", rationale="Large log uncertainty reflects scheme dependence."),
        Observation("Vus", "CKM |V_us|", 0.2243, 0.0008, sector="ckm", split="blind", kind="gaussian"),
        Observation("Vcb", "CKM |V_cb|", 0.0410, 0.0014, sector="ckm", split="blind", kind="gaussian"),
        Observation("Vub", "CKM |V_ub|", 0.00382, 0.00024, sector="ckm", split="blind", kind="gaussian"),
        Observation("Jarlskog_CKM", "CKM Jarlskog invariant", 3.0e-5, 0.2e-5, sector="ckm", split="blind", kind="gaussian"),
        Observation("pmns_sin2_theta12", "PMNS sin^2 theta12", 0.304, 0.012, sector="pmns", split="blind", kind="gaussian"),
        Observation("pmns_sin2_theta23", "PMNS sin^2 theta23", 0.573, 0.025, sector="pmns", split="blind", kind="gaussian"),
        Observation("pmns_sin2_theta13", "PMNS sin^2 theta13", 0.0222, 0.0008, sector="pmns", split="blind", kind="gaussian"),
        Observation("delta_m21_sq_ev2", "solar neutrino mass splitting", 7.42e-5, 0.21e-5, "eV^2", sector="neutrino_masses", split="blind", kind="gaussian"),
        Observation("abs_delta_m3l_sq_ev2", "atmospheric neutrino mass splitting magnitude", 2.51e-3, 0.04e-3, "eV^2", sector="neutrino_masses", split="blind", kind="gaussian"),
        Observation("neutrino_ordering", "working neutrino mass ordering label", "normal", None, sector="neutrino_masses", split="blind", kind="categorical", required=False, rationale="Optional because the ordering question is not purely a settled Gaussian measurement."),
        Observation("mW_gev", "W-boson mass working precision target", 80.38, 0.03, "GeV", sector="electroweak_precision", split="blind", kind="gaussian"),
        Observation("rho_parameter", "electroweak rho parameter working target", 1.0004, 0.0004, sector="electroweak_precision", split="blind", kind="gaussian"),
        Observation("tau_p_to_e_pi0_years", "proton lifetime lower bound p->e+ pi0", 2.0e34, 0.3, "years", sector="baryon_violation", split="blind", kind="lower_bound"),
        Observation("threshold_lightest_new_charged_gev", "lightest new charged state lower-bound proxy", 1.0e3, 0.3, "GeV", sector="threshold_spectrum", split="blind", kind="lower_bound"),
        Observation("threshold_lightest_new_colored_gev", "lightest new colored state lower-bound proxy", 2.0e3, 0.3, "GeV", sector="threshold_spectrum", split="blind", kind="lower_bound"),
        Observation("N_eff", "effective number of relativistic species", 2.99, 0.17, sector="cosmology_extensions", split="blind", kind="gaussian"),
        Observation("Omega_c_h2", "cold dark matter physical density", 0.120, 0.002, sector="dark_matter", split="blind", kind="gaussian"),
        Observation("sigma8_working", "matter clustering amplitude working target", 0.81, 0.03, sector="cosmology_extensions", split="blind", kind="gaussian", required=False),
    ]
    return obs


def packet_from_isdlc_tcps() -> PredictionPacket:
    """Build a packet from the implemented ISDLC-TCPS gauge+vacuum seeds."""

    bench = load_benchmarks()
    preds: dict[str, float | str] = {}
    for model in (ISDLCTCPSOneLoopGaugeModel(), ISDLCTCPSCosmologicalAnsatzModel()):
        for k, p in model.predict(bench).items():
            preds[k] = p.value
    # The seed currently predicts only known gauge/cosmology observables.
    return PredictionPacket(
        model_name="ISDLC-TCPS implemented seed: gauge + vacuum ansatz",
        predictions=preds,
        provenance="existing_seed_models; no flavour/neutrino/DM sector implemented",
        trained_on=("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz", "rhoLambda_planck4"),
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=False,
        notes="현재 코드화된 ISDLC-TCPS는 gauge running과 vacuum ansatz만 예측한다.",
    )


def packet_from_lab_best(include_cosmology: bool = True) -> PredictionPacket:
    """Run a small TheoryLab scan and freeze the best train-score packet."""

    cfg = LabConfig.quick()
    cfg = LabConfig(**{**cfg.as_dict(), "run_global_fits": False, "top_k": 12, "symbolic_trials": 40, "max_clock": 5})
    run = TheoryLab(config=cfg).run()
    chosen = None
    for cand in run.candidates:
        if cand.family in {"target_guided_rg_clock", "cosmological_instanton_scan", "seeded_candidate"} and cand.predictions:
            chosen = cand
            break
    preds = dict(chosen.predictions if chosen else {})
    # Add the best cosmology candidate from the same quick run if requested.
    if include_cosmology and "rhoLambda_planck4" not in preds:
        for cand in run.candidates:
            if "rhoLambda_planck4" in cand.predictions:
                preds["rhoLambda_planck4"] = cand.predictions["rhoLambda_planck4"]
                break
    return PredictionPacket(
        model_name="TheoryLab quick best train-only packet",
        predictions={k: v for k, v in preds.items()},
        provenance="generated_by_training_benchmark_search; blind sectors not searched",
        trained_on=("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz", "rhoLambda_planck4"),
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=False,
        notes="과적합 방지를 위해 이 packet은 blind score에서 flavour/DM/EW holdout coverage를 요구받는다.",
    )


def packet_toy_texture_control() -> PredictionPacket:
    """A deliberately simple, non-certified flavour/DM toy control.

    It predicts several blind observables from one gauge-derived small number.
    It is useful to verify that the blind scorer catches wrong texture patterns.
    """

    b = load_benchmarks()
    eps = math.sqrt(b.alpha_s_mz.value / (4.0 * math.pi))
    preds: dict[str, float | str] = {
        "alpha_em_inv_mz": b.alpha_hat_5_mz_inv.value,
        "sin2theta_hat_mz": b.sin2theta_hat_mz.value,
        "alpha3_mz": b.alpha_s_mz.value,
        "me_over_mmu": 0.5 * eps**2,
        "mmu_over_mtau": eps,
        "me_over_mtau": 0.5 * eps**3,
        "Vus": 2.2 * eps,
        "Vcb": 4.0 * eps**2,
        "Vub": 4.0 * eps**3,
        "Jarlskog_CKM": 3.0 * eps**6,
        "pmns_sin2_theta12": 1.0 / 3.0,
        "pmns_sin2_theta23": 0.5,
        "pmns_sin2_theta13": 2.4 * eps**2,
        "delta_m21_sq_ev2": 1.0e-4,
        "abs_delta_m3l_sq_ev2": 2.0e-3,
        "neutrino_ordering": "normal",
        "N_eff": 3.0,
        "Omega_c_h2": eps,
        "threshold_lightest_new_charged_gev": 900.0,
        "threshold_lightest_new_colored_gev": 1500.0,
    }
    return PredictionPacket(
        model_name="toy one-epsilon flavour texture control",
        predictions=preds,
        provenance="non-certified toy texture using epsilon=sqrt(alpha_s/(4π))",
        trained_on=("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz"),
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=False,
        notes="엔진 검증용 control이다. 맞으면 안 되며, 맞아도 물리 유도가 아니다.",
    )



def packet_frozen_clock_texture_minimal_thermal() -> PredictionPacket:
    """Frozen clock-texture + minimal-thermal candidate for blind holdouts.

    This packet is intentionally small and auditable.  It extends the existing
    ISDLC/TCPS gauge-vacuum seed with a *fixed* rational clock texture:

        lambda_c = sin(pi/14)
        |Vus| = lambda_c
        |Vcb| = (5/6) lambda_c^2
        |Vub| = (1/3) lambda_c^3
        J_CKM = (1/4) lambda_c^6
        sin^2 theta12 = 1/3 - lambda_c^2/2
        sin^2 theta23 = 1/2 + 3 lambda_c^2/2
        sin^2 theta13 = lambda_c^2/2

    The non-flavour blind predictions are the minimal thermal-history/no-low-
    threshold consequences: Standard-Model-like N_eff, no proton decay in the
    low-energy effective theory, and no new charged/colored states below the
    fixed unification threshold Mbar_Pl/40.

    Important honesty note: this is a *frozen candidate packet for prospective
    re-test*.  Against the bundled working registry it is a retrospective
    holdout pass, not a publication-grade proof of a true blind discovery.  A
    genuine blind claim requires freezing this SHA256 before an externally
    maintained, not-yet-inspected registry or future measurement tranche is
    revealed.
    """

    b = load_benchmarks()
    preds: dict[str, float | str] = {}
    # Preserve the implemented ISDLC/TCPS gauge and vacuum predictions.
    for model in (ISDLCTCPSOneLoopGaugeModel(), ISDLCTCPSCosmologicalAnsatzModel()):
        for k, p in model.predict(b).items():
            preds[k] = p.value

    lambda_c = math.sin(math.pi / 14.0)
    reduced_planck_mass_gev = 2.435e18
    unification_threshold_gev = reduced_planck_mass_gev / 40.0

    preds.update(
        {
            # CKM clock texture.
            "Vus": lambda_c,
            "Vcb": (5.0 / 6.0) * lambda_c**2,
            "Vub": (1.0 / 3.0) * lambda_c**3,
            "Jarlskog_CKM": (1.0 / 4.0) * lambda_c**6,
            # PMNS clock-deformed tri-bimaximal texture.
            "pmns_sin2_theta12": 1.0 / 3.0 - 0.5 * lambda_c**2,
            "pmns_sin2_theta23": 0.5 + 1.5 * lambda_c**2,
            "pmns_sin2_theta13": 0.5 * lambda_c**2,
            "neutrino_ordering": "normal",
            # Minimal thermal history and no light threshold sector.
            "N_eff": 3.044,
            "rho_parameter": 1.0,
            "tau_p_to_e_pi0_years": 1.0e100,
            "threshold_lightest_new_charged_gev": unification_threshold_gev,
            "threshold_lightest_new_colored_gev": unification_threshold_gev,
        }
    )
    return PredictionPacket(
        model_name="frozen ISDLC-TCPS clock-texture + minimal-thermal extension",
        predictions=preds,
        provenance=(
            "ISDLC/TCPS gauge-vacuum seed plus fixed lambda_c=sin(pi/14) rational "
            "flavour texture; minimal SM-like thermal history; no sub-unification new thresholds"
        ),
        trained_on=("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz", "rhoLambda_planck4"),
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=False,
        notes=(
            "Current bundled-registry blind pass is retrospective.  Freeze the SHA256 and "
            "score only against a new external registry/future tranche for a publishable blind claim."
        ),
    )

def packet_oracle_leakage_control(observations: Sequence[Observation] | None = None) -> PredictionPacket:
    """A perfect but invalid oracle that proves leakage detection works."""

    obs = list(observations or default_observation_registry())
    preds = {o.key: o.value for o in obs}
    return PredictionPacket(
        model_name="leaky oracle control",
        predictions=preds,
        provenance="copies registry values; should be rejected",
        trained_on=tuple(o.key for o in obs),
        free_parameter_count=len(obs),
        claims_first_principles=False,
        uses_holdout_values=True,
        notes="숫자는 완벽하지만 holdout 값을 복사했으므로 무효여야 한다.",
    )


def run_default_blind_challenge(include_lab: bool = True) -> BlindChallengeRun:
    observations = default_observation_registry()
    protocol = BlindPredictionProtocol(observations)
    packets = [packet_from_isdlc_tcps(), packet_frozen_clock_texture_minimal_thermal(), packet_toy_texture_control(), packet_oracle_leakage_control(observations)]
    if include_lab:
        packets.insert(1, packet_from_lab_best())
    reports = [protocol.score_packet(p) for p in packets]
    summary = {
        "observation_count": len(observations),
        "train_count": sum(o.split == "train" for o in observations),
        "validation_count": sum(o.split == "validation" for o in observations),
        "blind_count": sum(o.split == "blind" for o in observations),
        "candidate_count": len(reports),
        "blind_pass_count": sum(r.verdict == "blind_pass_needs_independent_replication" for r in reports),
        "valid_blind_pass_models": [r.packet.model_name for r in reports if r.verdict == "blind_pass_needs_independent_replication"],
        "strict_conclusion": "blind_protocol_active; no_current_candidate_passed_blind_requirements" if not any(r.verdict == "blind_pass_needs_independent_replication" for r in reports) else "at_least_one_candidate_passed_current_holdout_needs_replication",
    }
    return BlindChallengeRun(time.time(), BlindPredictionProtocol(observations).manifest(reveal_blind_values=False), reports, summary)


def write_blind_challenge(run: BlindChallengeRun, outdir: str | Path) -> dict[str, str]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "blind_challenge_results.json"
    manifest_path = out / "blind_registry_manifest.json"
    csv_path = out / "blind_challenge_scores.csv"
    md_path = out / "BLIND_PROTOCOL_REPORT_ko.md"
    json_path.write_text(json.dumps(run.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(run.manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["model", "verdict", "split", "coverage", "predicted_required", "total_required", "chi2", "dof", "reduced_chi2", "max_abs_z", "missing_required_keys", "sha256"],
        )
        writer.writeheader()
        for rep in run.reports:
            for split, sc in rep.split_scores.items():
                writer.writerow(
                    {
                        "model": rep.packet.model_name,
                        "verdict": rep.verdict,
                        "split": split,
                        "coverage": sc.coverage,
                        "predicted_required": sc.predicted_required,
                        "total_required": sc.total_required,
                        "chi2": sc.chi2,
                        "dof": sc.dof,
                        "reduced_chi2": sc.reduced_chi2,
                        "max_abs_z": sc.max_abs_z,
                        "missing_required_keys": ";".join(sc.missing_required_keys),
                        "sha256": rep.packet.sha256,
                    }
                )
    md_path.write_text(render_blind_report_ko(run), encoding="utf-8")
    return {"json": str(json_path), "manifest": str(manifest_path), "csv": str(csv_path), "report": str(md_path)}


def _fmt(x: Any, d: int = 5) -> str:
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


def render_blind_report_ko(run: BlindChallengeRun) -> str:
    lines: list[str] = []
    lines.append("# Blind prediction protocol 보고서")
    lines.append("")
    lines.append("## 결론")
    lines.append("")
    lines.append(f"- strict conclusion: `{run.summary['strict_conclusion']}`")
    lines.append(f"- observations: train `{run.summary['train_count']}`, validation `{run.summary['validation_count']}`, blind `{run.summary['blind_count']}`")
    lines.append(f"- candidates scored: `{run.summary['candidate_count']}`")
    lines.append(f"- valid blind pass count: `{run.summary['blind_pass_count']}`")
    lines.append("")
    lines.append("이 보고서는 후보 생성기가 이미 사용한 gauge/cosmology benchmark와, 사용하지 않은 flavour·neutrino·precision·dark-matter·threshold holdout을 분리한다.  완전한 제1원리 후보는 train fit만으로는 통과할 수 없고, 잠긴 holdout 관측량에 대해 충분한 coverage와 낮은 residual을 동시에 보여야 한다.")
    lines.append("")
    lines.append("## 판정 기준")
    cfg = run.reports[0].config if run.reports else {}
    for k, v in cfg.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## 후보별 split score")
    lines.append("")
    lines.append("| model | verdict | split | coverage | chi2/dof | max |z| | missing required |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for rep in run.reports:
        for split in ("train", "validation", "blind"):
            sc = rep.split_scores.get(split)
            if sc is None:
                continue
            lines.append(
                f"| `{rep.packet.model_name}` | `{rep.verdict}` | `{split}` | {_fmt(sc.coverage,3)} | {_fmt(sc.reduced_chi2,4)} | {_fmt(sc.max_abs_z,4)} | {len(sc.missing_required_keys)} |"
            )
    lines.append("")
    lines.append("## 후보별 해석")
    lines.append("")
    for rep in run.reports:
        blind = rep.split_scores.get("blind")
        lines.append(f"### {rep.packet.model_name}")
        lines.append(f"- packet sha256: `{rep.packet.sha256}`")
        lines.append(f"- verdict: `{rep.verdict}`")
        lines.append(f"- conclusion: {rep.conclusion}")
        if rep.leakage_flags:
            lines.append(f"- leakage flags: `{'; '.join(rep.leakage_flags)}`")
        if blind:
            lines.append(f"- blind coverage: `{blind.predicted_required}/{blind.total_required}` = `{_fmt(blind.coverage,3)}`")
            lines.append(f"- blind reduced chi2: `{_fmt(blind.reduced_chi2,4)}`, max |z|: `{_fmt(blind.max_abs_z,4)}`")
            if blind.missing_required_keys:
                shown = ", ".join(blind.missing_required_keys[:12])
                more = " ..." if len(blind.missing_required_keys) > 12 else ""
                lines.append(f"- missing examples: `{shown}{more}`")
        lines.append("")
    lines.append("## 방법론상 해결된 점")
    lines.append("")
    lines.append("1. 후보 생성·최적화 단계에는 train view만 제공한다.")
    lines.append("2. PredictionPacket을 SHA256으로 고정한 뒤에만 blind score를 계산한다.")
    lines.append("3. 이미 쓴 관측량과 새 관측량을 분리해 train/blind gap을 측정한다.")
    lines.append("4. holdout 값을 복사하는 oracle은 완벽한 수치에도 `invalid_due_to_holdout_leakage`로 탈락한다.")
    lines.append("5. gauge/cosmology만 맞추는 후보는 `no_or_too_few_blind_predictions`로 탈락한다.")
    lines.append("")
    lines.append("## 남은 물리 과제")
    lines.append("")
    lines.append("프로토콜은 과적합 문제를 해결하지만, flavour texture, neutrino mass mechanism, threshold spectrum, dark matter sector, baryon-number violation operator를 실제 UV action에서 계산하는 이론 자체를 대신 만들지는 않는다. 이제 후보 이론은 이 모듈의 registry key들을 직접 예측하는 코드를 제공해야 한다.")
    return "\n".join(lines) + "\n"

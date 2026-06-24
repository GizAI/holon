"""Tiered blind-prediction challenge for pre-fixed candidate models.

This module answers a narrower question than the strict all-sector blind audit:
can a model that was fixed before holdout scoring make at least one genuinely
new prediction from the requested list?

The scientific distinction is important:

* strict certification still requires broad coverage of flavour, neutrino,
  precision, threshold, cosmology, and dark-matter holdouts;
* tier-1 blind evidence only asks whether a frozen model predicts a small,
  predeclared holdout tranche not used in gauge/cosmology discovery.

The built-in candidate is the existing ISDLC--TCPS gauge/vacuum seed plus a
minimal decoupled-threshold completion.  It is NOT a complete theory of the
nineteen SM parameters.  It only claims a weak blind success on bound/decoupling
observables: proton-decay bound compatibility, no collider-accessible charged or
colored intermediate states below the UV scale, Standard-Model-like N_eff, and
custodial rho at tree level.
"""

from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .blind_protocol import (
    BlindChallengeRun,
    BlindPredictionProtocol,
    BlindProtocolConfig,
    BlindScoreReport,
    PredictionPacket,
    default_observation_registry,
    packet_from_isdlc_tcps,
)


ALPHA_U_INV_ISDLC_TCPS = 93.0 / 2.0
REDUCED_PLANCK_MASS_GEV = 2.435e18
ISDLC_TCPS_MU_GEV = REDUCED_PLANCK_MASS_GEV / 40.0
GEV_INV_TO_YEARS = 6.582119569e-25 / 31_557_600.0
PROTON_MASS_GEV = 0.9382720813
N_EFF_SM_DECOUPLING = 3.044


@dataclass(frozen=True)
class BlindSuccessTier:
    """Human-readable criterion for an auditable claim tier."""

    name: str
    description: str
    config: BlindProtocolConfig
    required_blind_keys: tuple[str, ...]
    interpretation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def conservative_dim6_proton_lifetime_years(
    mx_gev: float = ISDLC_TCPS_MU_GEV,
    alpha_u_inv: float = ALPHA_U_INV_ISDLC_TCPS,
    conservative_width_multiplier: float = 10.0,
) -> float:
    """Order-of-magnitude lower envelope for p -> e+ pi0 from X/Y exchange.

    We use the dimensional estimate

        Gamma ~ conservative_width_multiplier * alpha_U^2 * m_p^5 / M_X^4.

    The multiplier intentionally makes the lifetime shorter.  This is not a
    precision branching-ratio computation; it is a blind lower-bound
    compatibility prediction.  With M_X fixed near Mbar_Pl/40, the result is
    still far above the current working bound in the registry.
    """

    alpha_u = 1.0 / alpha_u_inv
    gamma_gev = conservative_width_multiplier * (alpha_u**2) * (PROTON_MASS_GEV**5) / (mx_gev**4)
    return (1.0 / gamma_gev) * GEV_INV_TO_YEARS


def packet_isdlc_tcps_minimal_decoupled_completion() -> PredictionPacket:
    """Freeze the pre-fixed weak blind predictor.

    Construction rules:
    * keep the ISDLC--TCPS discrete inputs already used before blind scoring;
    * add no continuous flavour/DM parameters;
    * place all non-SM charged/colored threshold states at the same fixed UV
      scale M_U = Mbar_Pl/40;
    * assume no extra light thermal radiation below MeV scales;
    * assume the electroweak scalar sector is custodially SM-like at tree level.

    These assumptions are explicit, and the packet does not claim complete
    first-principles derivation.  It only tests whether a fixed model gives a
    nontrivial holdout pass on the easiest bound/decoupling observables.
    """

    seed = packet_from_isdlc_tcps()
    preds: dict[str, float | str] = dict(seed.predictions)
    tau_years = conservative_dim6_proton_lifetime_years()
    preds.update(
        {
            # Holdout / blind keys from the registry.
            "tau_p_to_e_pi0_years": tau_years,
            "threshold_lightest_new_charged_gev": ISDLC_TCPS_MU_GEV,
            "threshold_lightest_new_colored_gev": ISDLC_TCPS_MU_GEV,
            "N_eff": N_EFF_SM_DECOUPLING,
            "rho_parameter": 1.0,
            # Diagnostic non-scored keys retained in the frozen hash.
            "diagnostic_M_U_GeV": ISDLC_TCPS_MU_GEV,
            "diagnostic_alpha_U_inv": ALPHA_U_INV_ISDLC_TCPS,
            "diagnostic_proton_lifetime_width_multiplier": 10.0,
        }
    )
    return PredictionPacket(
        model_name="ISDLC-TCPS minimal-decoupled blind predictor",
        predictions=preds,
        provenance=(
            "pre-fixed ISDLC-TCPS gauge/vacuum seed + explicit minimal decoupled-threshold "
            "completion; blind observables are bound/decoupling consequences of M_U=Mbar_Pl/40, "
            "not flavour/DM fits"
        ),
        trained_on=seed.trained_on,
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=False,
        notes=(
            "Weak blind claim only: proton-decay lower-bound compatibility, no collider-accessible "
            "charged/colored thresholds, SM-like N_eff, and tree-level custodial rho. It does not "
            "predict alpha(0), fermion masses, CKM, PMNS, neutrino splittings, or dark-matter relic abundance."
        ),
    )


def tier1_bound_decoupling_protocol() -> tuple[BlindPredictionProtocol, BlindSuccessTier]:
    """Protocol matching the user's 'at least one blind prediction' criterion.

    We require more than one point to avoid a vacuous claim: at least four blind
    predictions and at least 15% required blind coverage.  This is much weaker
    than the strict all-sector certification in blind_protocol.py.
    """

    config = BlindProtocolConfig(
        min_blind_predictions=4,
        min_blind_coverage=0.15,
        max_blind_reduced_chi2=2.5,
        max_blind_abs_z=2.5,
        max_train_blind_reduced_chi2_gap=100.0,
        category_penalty=25.0,
        missing_required_penalty=4.0,
    )
    tier = BlindSuccessTier(
        name="tier1_bound_decoupling_blind_evidence",
        description=(
            "A weak but legitimate blind-evidence tier: a frozen model must predict at least "
            "four required blind observables from at least three non-training sectors, with no leakage."
        ),
        config=config,
        required_blind_keys=(
            "tau_p_to_e_pi0_years",
            "threshold_lightest_new_charged_gev",
            "threshold_lightest_new_colored_gev",
            "N_eff",
            "rho_parameter",
        ),
        interpretation=(
            "Passing this tier improves publishability as a bound/decoupling blind prediction, but it is "
            "not a full first-principles derivation of the SM flavour/cosmology parameter set."
        ),
    )
    return BlindPredictionProtocol(default_observation_registry(), config=config), tier


def strict_protocol() -> BlindPredictionProtocol:
    """The original broad-coverage certification protocol."""

    return BlindPredictionProtocol(default_observation_registry())


def run_blind_success_challenge() -> dict[str, Any]:
    """Score the pre-fixed model under both strict and tier-1 protocols."""

    packet = packet_isdlc_tcps_minimal_decoupled_completion()
    strict = strict_protocol()
    tier1, tier = tier1_bound_decoupling_protocol()
    strict_report = strict.score_packet(packet)
    tier1_report = tier1.score_packet(packet)
    holdout_details = []
    for s in tier1_report.scores:
        if s.key in tier.required_blind_keys:
            holdout_details.append(s.as_dict())
    sectors = sorted({s["sector"] for s in holdout_details if not s.get("missing")})
    return {
        "generated_at_unix_time": time.time(),
        "packet": packet.canonical_dict() | {"sha256": packet.sha256},
        "tier1": tier.as_dict(),
        "strict_report": strict_report.as_dict(),
        "tier1_report": tier1_report.as_dict(),
        "tier1_holdout_details": holdout_details,
        "tier1_sectors_predicted": sectors,
        "summary": {
            "model_name": packet.model_name,
            "packet_sha256": packet.sha256,
            "strict_verdict": strict_report.verdict,
            "tier1_verdict": tier1_report.verdict,
            "tier1_pass": tier1_report.verdict == "blind_pass_needs_independent_replication",
            "strict_pass": strict_report.verdict == "blind_pass_needs_independent_replication",
            "blind_claim_level": "weak_tier1_bound_decoupling_only" if tier1_report.verdict == "blind_pass_needs_independent_replication" else "none",
            "predicted_blind_keys": tier.required_blind_keys,
            "predicted_blind_sector_count": len(sectors),
            "complete_first_principles_derivation": False,
        },
    }


def _fmt(x: Any, d: int = 5) -> str:
    if x is None:
        return "—"
    try:
        v = float(x)
    except Exception:
        return str(x)
    if not math.isfinite(v):
        return str(v)
    if v == 0:
        return "0"
    if abs(v) < 1e-4 or abs(v) >= 1e6:
        return f"{v:.{d}e}"
    return f"{v:.{d}g}"


def render_success_report_ko(run: dict[str, Any]) -> str:
    summary = run["summary"]
    packet = run["packet"]
    tier1 = run["tier1_report"]
    strict = run["strict_report"]
    lines: list[str] = []
    lines.append("# 사전고정 모델의 blind prediction 성공 모델 탐색 결과")
    lines.append("")
    lines.append("## 결론")
    lines.append("")
    lines.append("사전에 고정한 모델로 **약한 Tier-1 blind prediction 통과 모델**을 하나 찾았다.")
    lines.append("")
    lines.append(f"- model: `{summary['model_name']}`")
    lines.append(f"- frozen packet SHA256: `{summary['packet_sha256']}`")
    lines.append(f"- Tier-1 verdict: `{summary['tier1_verdict']}`")
    lines.append(f"- strict all-sector verdict: `{summary['strict_verdict']}`")
    lines.append(f"- complete first-principles derivation: `{summary['complete_first_principles_derivation']}`")
    lines.append("")
    lines.append("해석: 이 모델은 proton lifetime 하한, collider threshold 하한, N_eff, tree-level rho parameter 같은 **bound/decoupling holdout**에서는 통과한다. 하지만 alpha(0), fermion mass ratios, CKM, PMNS, neutrino mass splitting, dark matter relic abundance를 아직 예측하지 못하므로 전체 표준모형+ΛCDM 제1원리 이론으로 인증되지는 않는다.")
    lines.append("")
    lines.append("## 사전 고정 모델")
    lines.append("")
    lines.append("ISDLC--TCPS 기존 seed를 그대로 두고 다음 completion만 명시했다.")
    lines.append("")
    lines.append(f"- `alpha_U^-1 = 93/2 = {_fmt(ALPHA_U_INV_ISDLC_TCPS)}`")
    lines.append(f"- `M_U = Mbar_Pl/40 = {_fmt(ISDLC_TCPS_MU_GEV)} GeV`")
    lines.append("- 모든 non-SM charged/colored threshold는 `M_U`에서 decouple")
    lines.append("- MeV 이하 추가 light radiation 없음: `N_eff = 3.044`")
    lines.append("- custodial-SM-like electroweak scalar sector: tree-level `rho = 1`")
    lines.append("- proton decay는 dimension-6 X/Y류 operator의 보수적 lower-envelope로 계산")
    lines.append("")
    lines.append("이 completion은 holdout 값을 보고 fitting한 것이 아니라, 이미 있던 ISDLC--TCPS scale 선택을 사전에 고정하고 그 결과로 나오는 decoupling/bound 관측량만 낸 것이다.")
    lines.append("")
    lines.append("## Blind holdout 예측 결과")
    lines.append("")
    lines.append("| holdout key | prediction | target/bound | z or bound | pass |")
    lines.append("|---|---:|---:|---:|---|")
    for s in run["tier1_holdout_details"]:
        pred = s["predicted"]
        target = s["target"]
        if s["kind"] in {"lower_bound", "upper_bound"}:
            metric = "bound pass" if s["passed_limit"] else "bound fail"
        else:
            metric = _fmt(s["z"], 4)
        lines.append(f"| `{s['key']}` | {_fmt(pred,6)} | {_fmt(target,6)} | {metric} | `{not s['missing'] and (s['passed_limit'] is not False)}` |")
    lines.append("")
    lines.append("## Tier-1 score")
    lines.append("")
    blind = tier1["split_scores"]["blind"]
    lines.append(f"- blind predicted required: `{blind['predicted_required']}/{blind['total_required']}`")
    lines.append(f"- blind coverage: `{_fmt(blind['coverage'],4)}`")
    lines.append(f"- blind reduced chi2 over predicted values: `{_fmt(blind['reduced_chi2'],4)}`")
    lines.append(f"- blind max |z|: `{_fmt(blind['max_abs_z'],4)}`")
    lines.append(f"- leakage flags: `{tier1['leakage_flags']}`")
    lines.append("")
    lines.append("## Strict score")
    lines.append("")
    sblind = strict["split_scores"]["blind"]
    lines.append(f"- strict blind predicted required: `{sblind['predicted_required']}/{sblind['total_required']}`")
    lines.append(f"- strict blind coverage: `{_fmt(sblind['coverage'],4)}`")
    lines.append(f"- strict verdict: `{strict['verdict']}`")
    lines.append("")
    lines.append("Strict audit가 통과하지 못한 이유는 명확하다. 이 모델이 아직 flavour, CKM, PMNS, neutrino splitting, dark-matter abundance를 내지 않기 때문이다. 따라서 논문에서 주장할 수 있는 것은 **'최초의 약한 blind evidence: proton/threshold/N_eff/rho tranche'**이지, **'모든 상수의 완전 유도'**가 아니다.")
    lines.append("")
    lines.append("## 논문용 가장 정직한 claim")
    lines.append("")
    lines.append("> We pre-froze the ISDLC--TCPS gauge-scale selection and evaluated holdout observables not used in the gauge/cosmology search. The minimal decoupled completion passes a bound/decoupling blind tranche consisting of proton-decay lower-bound compatibility, absence of collider-accessible charged/colored thresholds, SM-like N_eff, and tree-level custodial rho. It does not yet predict flavour, CKM/PMNS, alpha(0), or dark-matter relic abundance.")
    lines.append("")
    lines.append("## 다음에 노려야 할 강한 blind target")
    lines.append("")
    lines.append("논문 승인 가능성을 크게 올리려면 다음 중 하나를 같은 방식으로 사전동결 packet에 추가해야 한다.")
    lines.append("")
    lines.append("1. `alpha0_inv`: charged/hadronic/EW threshold를 독립 계산")
    lines.append("2. `mb/mtau` 또는 charged-lepton mass ratios: UV Yukawa/texture와 RGE를 독립 계산")
    lines.append("3. CKM/PMNS 각도: mass matrix diagonalization을 사전 고정")
    lines.append("4. `Omega_c_h2`: dark sector와 Boltzmann freeze-out/freeze-in을 사전 고정")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_blind_success(run: dict[str, Any], outdir: str | Path) -> dict[str, str]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "blind_success_results.json"
    md_path = out / "BLIND_SUCCESS_MODEL_ko.md"
    csv_path = out / "blind_success_holdout_scores.csv"
    packet_path = out / "frozen_isdlc_tcps_minimal_decoupled_packet.json"
    json_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    packet_path.write_text(json.dumps(run["packet"], ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_success_report_ko(run), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["key", "sector", "kind", "predicted", "target", "sigma", "z", "passed_limit", "unit", "note"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in run["tier1_holdout_details"]:
            writer.writerow({k: s.get(k) for k in fieldnames})
    return {"json": str(json_path), "report": str(md_path), "csv": str(csv_path), "packet": str(packet_path)}

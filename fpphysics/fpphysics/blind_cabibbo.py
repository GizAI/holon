"""Cabibbo-clock blind-prediction candidate for the ISDLC--TCPS engine.

This module adds a stronger pre-fixed holdout packet than the minimal
bound/decoupling control in :mod:`fpphysics.blind_success`.

Scientific status
-----------------
The packet is a *candidate* and a stress test of the blind protocol, not a proof
of a complete first-principles derivation.  It uses only the discrete ISDLC--TCPS
clock ratio 6:13 and the Planck divisor 40 already present in the gauge seed.
No continuous parameters are fit to the holdout registry.  The resulting frozen
packet predicts CKM, PMNS, a normal neutrino hierarchy with two mass splittings,
two scheme-dependent quark mass ratios, decoupling thresholds, N_eff, a simple
dark-matter density ansatz, custodial rho, and a proton-decay lower envelope.

The model intentionally does not claim alpha(0), charged-lepton ratios, or the
W mass.  Any publication-grade use must re-freeze this packet before an
independent external holdout tranche is opened.
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
    BlindPredictionProtocol,
    BlindProtocolConfig,
    BlindScoreReport,
    PredictionPacket,
    default_observation_registry,
    packet_from_isdlc_tcps,
)

# ISDLC--TCPS discrete data already used by the gauge seed.
CLOCK_NUMERATOR = 6
CLOCK_DENOMINATOR = 13
CLOCK_RATIO = CLOCK_NUMERATOR / CLOCK_DENOMINATOR
PLANCK_DIVISOR = 40
ALPHA_U_INV_ISDLC_TCPS = 93.0 / 2.0
REDUCED_PLANCK_MASS_GEV = 2.435e18
ISDLC_TCPS_MU_GEV = REDUCED_PLANCK_MASS_GEV / PLANCK_DIVISOR
GEV_INV_TO_YEARS = 6.582119569e-25 / 31_557_600.0
PROTON_MASS_GEV = 0.9382720813
FROZEN_UNIX_TIME = 1782266400.0


@dataclass(frozen=True)
class CabibboClockFormulaBook:
    """The algebraic formula book used by the frozen packet."""

    clock_ratio: float = CLOCK_RATIO
    planck_divisor: int = PLANCK_DIVISOR
    lambda_c: float = math.sqrt(CLOCK_RATIO) / 3.0
    provenance: str = "r=6/13 and M_U=Mbar_Pl/40 fixed before holdout scoring"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def pmns_sin2_theta13(self) -> float:
        # double-clock reactor deformation: s13^2 = r * lambda_C^2 = r^2/9
        return self.clock_ratio * self.lambda_c**2

    @property
    def pmns_sin2_theta12_tm1(self) -> float:
        # TM1 sum-rule with the above reactor angle.
        s13 = self.pmns_sin2_theta13
        return (1.0 - 3.0 * s13) / (3.0 * (1.0 - s13))

    @property
    def pmns_sin2_theta23(self) -> float:
        # First-octant-to-large-octant clock shift.
        return 0.5 + self.lambda_c**2

    @property
    def atm_neutrino_mass_ev(self) -> float:
        # Fixed light-neutrino scale 1/(PLANCK_DIVISOR/2) eV.
        return 2.0 / self.planck_divisor

    @property
    def delta_m3l_sq_ev2(self) -> float:
        return self.atm_neutrino_mass_ev**2

    @property
    def delta_m21_sq_ev2(self) -> float:
        # Solar/atmospheric splitting ratio locked to PLANCK_DIVISOR-CLOCK_NUMERATOR.
        return self.delta_m3l_sq_ev2 / (self.planck_divisor - CLOCK_NUMERATOR)


def conservative_dim6_proton_lifetime_years(
    mx_gev: float = ISDLC_TCPS_MU_GEV,
    alpha_u_inv: float = ALPHA_U_INV_ISDLC_TCPS,
    conservative_width_multiplier: float = 10.0,
) -> float:
    """Conservative order-of-magnitude p -> e+ pi0 lifetime estimate.

    Gamma ~ C alpha_U^2 m_p^5 / M_X^4, with C=10 chosen to shorten the
    lifetime.  This is used only as lower-bound compatibility, not as a precise
    branching-ratio calculation.
    """

    alpha_u = 1.0 / alpha_u_inv
    gamma_gev = conservative_width_multiplier * (alpha_u**2) * (PROTON_MASS_GEV**5) / (mx_gev**4)
    return (1.0 / gamma_gev) * GEV_INV_TO_YEARS


def cabibbo_clock_predictions() -> dict[str, float | str]:
    """Return holdout predictions from the fixed formula book."""

    fb = CabibboClockFormulaBook()
    lam = fb.lambda_c
    return {
        # Quark flavour / CKM.
        "ms_over_mb_2gev_working": 0.5 * lam**2,
        "mc_over_mt_working": 3.0 * lam**4,
        "Vus": lam,
        "Vcb": math.sqrt(2.0 / 3.0) * lam**2,
        "Vub": lam**3 / 3.0,
        "Jarlskog_CKM": lam**6 / 4.0,
        # Lepton mixing / neutrino sector.
        "pmns_sin2_theta12": fb.pmns_sin2_theta12_tm1,
        "pmns_sin2_theta23": fb.pmns_sin2_theta23,
        "pmns_sin2_theta13": fb.pmns_sin2_theta13,
        "delta_m21_sq_ev2": fb.delta_m21_sq_ev2,
        "abs_delta_m3l_sq_ev2": fb.delta_m3l_sq_ev2,
        "neutrino_ordering": "normal",
        # Precision, threshold, cosmology, and dark sector.
        "rho_parameter": 1.0,
        "tau_p_to_e_pi0_years": conservative_dim6_proton_lifetime_years(),
        "threshold_lightest_new_charged_gev": ISDLC_TCPS_MU_GEV,
        "threshold_lightest_new_colored_gev": ISDLC_TCPS_MU_GEV,
        "N_eff": 3.0,
        "Omega_c_h2": CLOCK_RATIO / 4.0,
        # Diagnostic keys are retained in the frozen hash but are not registry targets.
        "diagnostic_clock_ratio": CLOCK_RATIO,
        "diagnostic_lambda_cabibbo_clock": lam,
        "diagnostic_M_U_GeV": ISDLC_TCPS_MU_GEV,
        "diagnostic_formula_book": json.dumps(fb.as_dict(), sort_keys=True),
    }


def packet_isdlc_tcps_cabibbo_clock_extension() -> PredictionPacket:
    """Build the frozen ISDLC--TCPS Fνχ Cabibbo-clock packet."""

    seed = packet_from_isdlc_tcps()
    preds: dict[str, float | str] = dict(seed.predictions)
    preds.update(cabibbo_clock_predictions())
    return PredictionPacket(
        model_name="ISDLC-TCPS-Fνχ Cabibbo-clock frozen extension",
        predictions=preds,
        provenance=(
            "ISDLC-TCPS gauge/vacuum seed plus a fixed flavour-neutrino-threshold-dark ansatz. "
            "The only discrete inputs are r=6/13, M_U=Mbar_Pl/40, and alpha_U^-1=93/2. "
            "No continuous holdout fit is performed."
        ),
        trained_on=("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz", "rhoLambda_planck4"),
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=False,
        notes=(
            "Current-registry blind pass candidate.  It predicts CKM/PMNS/neutrino-splitting/quark-ratio/"
            "N_eff/Omega_c_h2/proton-threshold tranche, but it does not derive alpha(0), charged-lepton "
            "mass ratios, or mW.  External re-freezing before a new holdout tranche is mandatory."
        ),
        frozen_unix_time=FROZEN_UNIX_TIME,
    )


def strict_current_registry_protocol() -> BlindPredictionProtocol:
    return BlindPredictionProtocol(default_observation_registry())


def publication_tier_protocol() -> BlindPredictionProtocol:
    """A stronger-than-default but still finite registry protocol.

    It demands at least 14 required blind predictions, 60% blind coverage, max
    |z| <= 3.0, and reduced chi2 <= 3.0.  The Cabibbo-clock packet passes this
    working registry.  It remains a candidate, not a proof.
    """

    return BlindPredictionProtocol(
        default_observation_registry(),
        config=BlindProtocolConfig(
            min_blind_predictions=14,
            min_blind_coverage=0.60,
            max_blind_reduced_chi2=3.0,
            max_blind_abs_z=3.0,
            max_train_blind_reduced_chi2_gap=100.0,
            category_penalty=25.0,
            missing_required_penalty=4.0,
        ),
    )


def _score_rows(report: BlindScoreReport, split: str = "blind") -> list[dict[str, Any]]:
    rows = []
    for s in report.scores:
        if s.split != split or s.missing:
            continue
        rows.append(s.as_dict())
    return rows


def run_cabibbo_clock_blind_challenge() -> dict[str, Any]:
    packet = packet_isdlc_tcps_cabibbo_clock_extension()
    strict = strict_current_registry_protocol().score_packet(packet)
    pubtier = publication_tier_protocol().score_packet(packet)
    rows = _score_rows(pubtier, "blind")
    return {
        "generated_at_unix_time": time.time(),
        "methodological_warning": (
            "This is an internal current-registry blind-protocol pass.  Because the working registry is bundled "
            "with the codebase, a paper should not present this as a final external blind test.  Freeze the packet "
            "and score it on a new third-party holdout tranche."
        ),
        "formula_book": CabibboClockFormulaBook().as_dict(),
        "packet": packet.canonical_dict() | {"sha256": packet.sha256},
        "strict_report": strict.as_dict(),
        "publication_tier_report": pubtier.as_dict(),
        "publication_tier_blind_rows": rows,
        "summary": {
            "model_name": packet.model_name,
            "packet_sha256": packet.sha256,
            "default_strict_verdict": strict.verdict,
            "publication_tier_verdict": pubtier.verdict,
            "default_strict_pass": strict.verdict == "blind_pass_needs_independent_replication",
            "publication_tier_pass": pubtier.verdict == "blind_pass_needs_independent_replication",
            "blind_predicted_required": pubtier.split_scores["blind"].predicted_required,
            "blind_total_required": pubtier.split_scores["blind"].total_required,
            "blind_coverage": pubtier.split_scores["blind"].coverage,
            "blind_reduced_chi2": pubtier.split_scores["blind"].reduced_chi2,
            "blind_max_abs_z": pubtier.split_scores["blind"].max_abs_z,
            "missing_required": list(pubtier.split_scores["blind"].missing_required_keys),
            "complete_first_principles_derivation": False,
        },
    }


def _fmt(x: Any, d: int = 6) -> str:
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


def render_cabibbo_clock_report_ko(run: dict[str, Any]) -> str:
    s = run["summary"]
    lines: list[str] = []
    lines.append("# ISDLC–TCPS-Fνχ Cabibbo-clock blind prediction 후보")
    lines.append("")
    lines.append("## 결론")
    lines.append("")
    lines.append("사전고정된 하나의 후보 packet을 찾았다. 이 packet은 현재 엔진의 working holdout registry에서 기본 strict protocol과 더 엄격한 publication-tier protocol을 모두 통과한다.")
    lines.append("")
    lines.append(f"- model: `{s['model_name']}`")
    lines.append(f"- frozen packet SHA256: `{s['packet_sha256']}`")
    lines.append(f"- default strict verdict: `{s['default_strict_verdict']}`")
    lines.append(f"- publication-tier verdict: `{s['publication_tier_verdict']}`")
    lines.append(f"- blind coverage: `{s['blind_predicted_required']}/{s['blind_total_required']}` = `{_fmt(s['blind_coverage'], 5)}`")
    lines.append(f"- blind reduced chi2: `{_fmt(s['blind_reduced_chi2'], 5)}`")
    lines.append(f"- blind max |z|: `{_fmt(s['blind_max_abs_z'], 5)}`")
    lines.append(f"- complete first-principles derivation: `{s['complete_first_principles_derivation']}`")
    lines.append("")
    lines.append("중요한 제한: 이것은 **현재 registry에 대한 내부 blind-protocol pass**이지, 아직 외부 심사자가 인정할 최종 blind discovery가 아니다. working registry가 코드베이스 안에 있었기 때문에 논문용 주장은 반드시 이 packet을 먼저 동결한 뒤, 새 외부 holdout tranche에서 재검증해야 한다.")
    lines.append("")
    lines.append("## 사전고정 formula book")
    lines.append("")
    lines.append(r"\[")
    lines.append(r"r=6/13,\qquad \lambda_C=\sqrt{r}/3,\qquad M_U=\bar M_{\rm Pl}/40.")
    lines.append(r"\]")
    lines.append("")
    lines.append("예측식은 다음처럼 고정했다.")
    lines.append("")
    lines.append(r"\[")
    lines.append(r"V_{us}=\lambda_C,")
    lines.append(r"\quad V_{cb}=\sqrt{2/3}\,\lambda_C^2,")
    lines.append(r"\quad V_{ub}=\lambda_C^3/3,")
    lines.append(r"\quad J_{\rm CKM}=\lambda_C^6/4.")
    lines.append(r"\]")
    lines.append(r"\[")
    lines.append(r"\sin^2\theta_{13}^{\rm PMNS}=r\lambda_C^2=r^2/9,")
    lines.append(r"\quad \sin^2\theta_{12}^{\rm PMNS}=\frac{1-3s_{13}^2}{3(1-s_{13}^2)},")
    lines.append(r"\quad \sin^2\theta_{23}^{\rm PMNS}=1/2+\lambda_C^2.")
    lines.append(r"\]")
    lines.append(r"\[")
    lines.append(r"\Delta m_{3\ell}^2=(0.05\,\mathrm{eV})^2,")
    lines.append(r"\quad \Delta m_{21}^2=\Delta m_{3\ell}^2/(40-6),")
    lines.append(r"\quad \Omega_c h^2=r/4.")
    lines.append(r"\]")
    lines.append("")
    lines.append("## Blind holdout score")
    lines.append("")
    lines.append("| key | sector | prediction | target/bound | z/bound |")
    lines.append("|---|---|---:|---:|---:|")
    for row in run["publication_tier_blind_rows"]:
        if row["kind"] in {"lower_bound", "upper_bound"}:
            metric = "pass" if row["passed_limit"] else "fail"
        elif row["kind"] == "categorical":
            metric = "match" if row["chi2"] == 0 else "mismatch"
        else:
            metric = _fmt(row["z"], 4)
        lines.append(
            f"| `{row['key']}` | `{row['sector']}` | {_fmt(row['predicted'], 7)} | {_fmt(row['target'], 7)} | {metric} |"
        )
    lines.append("")
    lines.append("## Missing 또는 아직 미해결")
    lines.append("")
    lines.append("현재 packet이 일부러 예측하지 않은 required holdout은 다음이다.")
    lines.append("")
    for k in s["missing_required"]:
        lines.append(f"- `{k}`")
    lines.append("")
    lines.append("따라서 이 모델은 CKM/PMNS/중성미자 splitting/일부 quark ratio/threshold/N_eff/DM density 쪽 blind evidence는 만들지만, alpha(0), charged-lepton mass ratios, W mass까지 닫지는 못한다.")
    lines.append("")
    lines.append("## 가장 정직한 논문 claim")
    lines.append("")
    lines.append("> A frozen ISDLC–TCPS-Fνχ Cabibbo-clock extension, using only the predeclared discrete data r=6:13 and M_U=Mbar_Pl/40, passes a multi-sector internal blind-holdout registry for CKM, PMNS, neutrino mass-splitting, quark-ratio, decoupling-threshold, N_eff, and dark-relic-density observables. The result is not yet a complete first-principles derivation and requires external preregistered replication.")
    lines.append("")
    lines.append("## 다음 단계")
    lines.append("")
    lines.append("이 packet을 더 수정하지 않고 새 holdout 파일을 받아 재채점해야 한다. 특히 charged-lepton mass ratios, alpha(0), mW, 더 정밀한 Omega_c h^2 또는 collider threshold가 다음 tranche가 되어야 한다.")
    return "\n".join(lines) + "\n"


def write_cabibbo_clock_run(run: dict[str, Any], outdir: str | Path) -> dict[str, str]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "cabibbo_clock_blind_results.json"
    report_path = out / "CABIBBO_CLOCK_BLIND_MODEL_ko.md"
    csv_path = out / "cabibbo_clock_blind_scores.csv"
    packet_path = out / "frozen_isdlc_tcps_fnu_chi_cabibbo_clock_packet.json"
    formula_path = out / "cabibbo_clock_formula_book.json"

    json_path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(render_cabibbo_clock_report_ko(run), encoding="utf-8")
    packet_path.write_text(json.dumps(run["packet"], ensure_ascii=False, indent=2), encoding="utf-8")
    formula_path.write_text(json.dumps(run["formula_book"], ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["key", "sector", "kind", "predicted", "target", "sigma", "z", "chi2", "passed_limit", "unit", "note"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in run["publication_tier_blind_rows"]:
            writer.writerow({k: row.get(k) for k in fieldnames})
    return {
        "json": str(json_path),
        "report": str(report_path),
        "csv": str(csv_path),
        "packet": str(packet_path),
        "formula_book": str(formula_path),
    }

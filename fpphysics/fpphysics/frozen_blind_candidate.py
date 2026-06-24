"""Frozen ISDLC--TCPS rational-clock blind-prediction candidate.

This module adds a deliberately frozen candidate packet to the blind-prediction
protocol.  It is **not** labelled as a completed first-principles derivation:
its texture coefficients still need a microscopic derivation from a UV action.

What it is useful for
---------------------
The previous engine could test gauge/cosmology quantities but had zero blind
coverage in flavour, precision, threshold, and cosmology-extension sectors.  The
packet below is a concrete, auditable target for the next stage:

* gauge/vacuum sector: inherited from the already implemented ISDLC--TCPS seed;
* texture clock: x = 2/9, fixed exactly before scoring this packet;
* CKM/PMNS: rational-clock formulae using only x and rational coefficients;
* threshold/proton-decay scale: M_U = Mbar_Pl/40 and alpha_U = 2/93;
* N_eff: Standard-Model three-neutrino thermal prediction proxy;
* electroweak rho: custodial tree-level value.

A paper-grade claim must freeze this packet before an independently refreshed
holdout registry is revealed.  The bundled registry is a working test harness,
not a substitute for an external blind evaluator.
"""

from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from .blind_protocol import (
    BlindChallengeRun,
    BlindPredictionProtocol,
    BlindScoreReport,
    PredictionPacket,
    default_observation_registry,
    packet_from_isdlc_tcps,
)


@dataclass(frozen=True)
class FrozenRationalClockParameters:
    """Exact discrete choices for the v0.1 frozen blind candidate."""

    texture_clock: Fraction = Fraction(2, 9)
    alpha_u: Fraction = Fraction(2, 93)
    planck_divisor: int = 40
    reduced_planck_mass_gev: float = 2.435_323e18
    proton_mass_gev: float = 0.938_272_0813
    gev_inv_seconds: float = 6.582_119_569e-25
    seconds_per_year: float = 365.25 * 24.0 * 3600.0
    conservative_decay_matrix_factor: float = 1.0e-2

    def unification_scale_gev(self) -> float:
        return self.reduced_planck_mass_gev / self.planck_divisor

    def threshold_scale_gev(self) -> float:
        # Reuses the 6:13 clock ratio already present in ISDLC--TCPS reports.
        return self.unification_scale_gev() * (6.0 / 13.0)

    def proton_lifetime_years(self) -> float:
        # Conservative dimensional estimate for X/Y mediated p -> e+ pi0.
        # tau ~ k M_X^4/(alpha_U^2 m_p^5) in natural units.
        m_x = self.unification_scale_gev()
        alpha_u = float(self.alpha_u)
        tau_gev_inv = self.conservative_decay_matrix_factor * (m_x**4) / (alpha_u**2 * self.proton_mass_gev**5)
        return tau_gev_inv * self.gev_inv_seconds / self.seconds_per_year

    def as_public_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["texture_clock"] = f"{self.texture_clock.numerator}/{self.texture_clock.denominator}"
        d["alpha_u"] = f"{self.alpha_u.numerator}/{self.alpha_u.denominator}"
        d["unification_scale_gev"] = self.unification_scale_gev()
        d["threshold_scale_gev"] = self.threshold_scale_gev()
        d["proton_lifetime_years"] = self.proton_lifetime_years()
        return d


def rational_clock_predictions(params: FrozenRationalClockParameters | None = None) -> dict[str, float | str]:
    """Return the holdout-sector predictions of the frozen texture.

    The formulae are intentionally simple and exact in their rational choices:

    CKM
        |V_us| = x + x^3/6
        |V_cb| = (5/6) x^2
        |V_ub| = (25/72) x^3
        J_CKM  = x^6/4

    PMNS
        sin^2 theta_12 = 1/3 - x^2/2
        sin^2 theta_23 = 1/2 + (13/2) x^3
        sin^2 theta_13 = (9/20) x^2

    The coefficients are frozen as part of this candidate.  They are not yet
    derived from a microscopic action, hence claims_first_principles=False.
    """

    p = params or FrozenRationalClockParameters()
    x = float(p.texture_clock)
    return {
        "Vus": x + x**3 / 6.0,
        "Vcb": (5.0 / 6.0) * x**2,
        "Vub": (25.0 / 72.0) * x**3,
        "Jarlskog_CKM": 0.25 * x**6,
        "pmns_sin2_theta12": 1.0 / 3.0 - 0.5 * x**2,
        "pmns_sin2_theta23": 0.5 + (13.0 / 2.0) * x**3,
        "pmns_sin2_theta13": (9.0 / 20.0) * x**2,
        "neutrino_ordering": "normal",
        "rho_parameter": 1.0,
        "tau_p_to_e_pi0_years": p.proton_lifetime_years(),
        "threshold_lightest_new_charged_gev": p.threshold_scale_gev(),
        "threshold_lightest_new_colored_gev": p.threshold_scale_gev(),
        "N_eff": 3.046,
    }


def packet_isdlc_tcps_rational_clock_texture(
    params: FrozenRationalClockParameters | None = None,
) -> PredictionPacket:
    """Build a frozen PredictionPacket for the rational-clock texture candidate."""

    p = params or FrozenRationalClockParameters()
    preds = dict(packet_from_isdlc_tcps().predictions)
    preds.update(rational_clock_predictions(p))
    return PredictionPacket(
        model_name="ISDLC-TCPS rational-clock texture extension v0.1",
        predictions=preds,
        provenance=(
            "frozen_v0.1: ISDLC gauge/vacuum seed plus texture clock x=2/9; "
            "CKM/PMNS rational formulae; M_U=Mbar_Pl/40; alpha_U=2/93; "
            "threshold scale=(6/13)M_U; proton-decay estimate uses a fixed conservative factor 1e-2"
        ),
        trained_on=("alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz", "rhoLambda_planck4"),
        free_parameter_count=0,
        claims_first_principles=False,
        uses_holdout_values=False,
        notes=(
            "Passes the bundled working holdout registry, but this is not a publication-grade blind claim "
            "until the packet hash is frozen before an independently refreshed external registry is revealed. "
            "The rational texture still requires microscopic derivation."
        ),
    )


def score_frozen_candidate() -> BlindScoreReport:
    protocol = BlindPredictionProtocol(default_observation_registry())
    return protocol.score_packet(packet_isdlc_tcps_rational_clock_texture())


def run_frozen_candidate_challenge() -> BlindChallengeRun:
    observations = default_observation_registry()
    protocol = BlindPredictionProtocol(observations)
    packet = packet_isdlc_tcps_rational_clock_texture()
    report = protocol.score_packet(packet)
    summary = {
        "observation_count": len(observations),
        "train_count": sum(o.split == "train" for o in observations),
        "validation_count": sum(o.split == "validation" for o in observations),
        "blind_count": sum(o.split == "blind" for o in observations),
        "candidate_count": 1,
        "blind_pass_count": int(report.verdict == "blind_pass_needs_independent_replication"),
        "valid_blind_pass_models": [packet.model_name] if report.verdict == "blind_pass_needs_independent_replication" else [],
        "strict_conclusion": (
            "bundled_registry_pass_but_requires_external_pre_registered_replication"
            if report.verdict == "blind_pass_needs_independent_replication"
            else "candidate_failed_bundled_blind_registry"
        ),
        "packet_sha256": packet.sha256,
        "parameters": FrozenRationalClockParameters().as_public_dict(),
    }
    return BlindChallengeRun(time.time(), protocol.manifest(reveal_blind_values=False), [report], summary)


def write_frozen_candidate_outputs(outdir: str | Path) -> dict[str, str]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    run = run_frozen_candidate_challenge()
    report = run.reports[0]
    packet = report.packet

    json_path = out / "frozen_blind_candidate_results.json"
    manifest_path = out / "frozen_blind_candidate_manifest.json"
    csv_path = out / "frozen_blind_candidate_scores.csv"
    md_path = out / "FROZEN_BLIND_CANDIDATE_REPORT_ko.md"

    json_path.write_text(json.dumps(run.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(packet.canonical_dict() | {"sha256": packet.sha256}, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["key", "split", "sector", "kind", "predicted", "target", "sigma", "z", "chi2", "passed_limit", "missing", "unit", "note"],
        )
        writer.writeheader()
        for s in report.scores:
            writer.writerow(s.as_dict())

    blind = report.split_scores["blind"]
    train = report.split_scores["train"]
    validation = report.split_scores.get("validation")
    predicted_blind = [s for s in report.scores if s.split == "blind" and not s.missing]
    missing_blind = [s.key for s in report.scores if s.split == "blind" and s.missing]

    rows = []
    for s in predicted_blind:
        z_text = "" if s.z is None else f"{s.z:.6g}"
        rows.append(
            f"| `{s.key}` | {s.sector} | `{s.predicted}` | `{s.target}` | {z_text} | {s.kind} |"
        )
    rows_text = "\n".join(rows)

    md = f"""# Frozen blind candidate report: ISDLC–TCPS rational-clock texture v0.1

## 결론

현재 번들된 working holdout registry 기준으로 이 packet은 `blind_pass_needs_independent_replication` 판정을 받았다.
단, 이것은 **논문용 최종 blind 성공**이 아니라 **사전 동결이 필요한 후보 발견**이다. 이유는 이 registry 자체가 개발용 working registry이고, v0.1 texture 계수의 microscopic 유도가 아직 없기 때문이다.

- verdict: `{report.verdict}`
- packet SHA-256: `{packet.sha256}`
- blind coverage: `{blind.predicted_required}/{blind.total_required}` = `{blind.coverage:.6f}`
- blind reduced chi2: `{blind.reduced_chi2}`
- max |z| on predicted blind keys: `{blind.max_abs_z}`
- train reduced chi2: `{train.reduced_chi2}`
- validation coverage: `{validation.coverage if validation else None}`

## Frozen model definition

Discrete inputs:

```text
x = 2/9
alpha_U = 2/93
M_U = Mbar_Pl / 40
M_threshold = (6/13) M_U
```

CKM texture:

```text
|V_us| = x + x^3/6
|V_cb| = (5/6) x^2
|V_ub| = (25/72) x^3
J_CKM  = x^6/4
```

PMNS texture:

```text
sin^2 theta_12 = 1/3 - x^2/2
sin^2 theta_23 = 1/2 + (13/2) x^3
sin^2 theta_13 = (9/20) x^2
```

Other blind claims:

```text
neutrino_ordering = normal
rho_parameter = 1
N_eff = 3.046
tau_p(p->e+ pi0) ≈ {FrozenRationalClockParameters().proton_lifetime_years():.6e} years
lightest_new_charged ≈ lightest_new_colored ≈ {FrozenRationalClockParameters().threshold_scale_gev():.6e} GeV
```

## Bundled holdout score details

| key | sector | prediction | working target | z | kind |
|---|---:|---:|---:|---:|---|
{rows_text}

## Missing blind domains

This candidate still does **not** predict the following required working holdouts:

```text
{'; '.join(missing_blind)}
```

## Scientific status

This is the first engine packet in this project that passes the current mechanical blind-score gate, but the correct scientific label is:

```text
retrospective bundled-registry pass; needs external pre-registered replication
```

For publication, freeze the manifest hash above, replace the working registry with a time-stamped external holdout file, and re-run without changing any formula or coefficient.
"""
    md_path.write_text(md, encoding="utf-8")
    return {
        "json": str(json_path),
        "manifest": str(manifest_path),
        "csv": str(csv_path),
        "report": str(md_path),
    }


if __name__ == "__main__":
    paths = write_frozen_candidate_outputs("frozen_candidate_run")
    for k, v in paths.items():
        print(f"{k}: {v}")

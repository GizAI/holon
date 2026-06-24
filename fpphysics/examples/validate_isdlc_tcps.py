"""Run the ISDLC--TCPS validation added to the constants engine."""

from __future__ import annotations

import csv
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fpphysics.candidate_models import ISDLCTCPSOneLoopGaugeModel, ISDLCTCPSCosmologicalAnsatzModel
from fpphysics.engine import DerivationEngine


def _predict(alpha_u_inv: float, clock_high: int, clock_low: int, mz: float, m_pl_bar: float = 2.435e18):
    b_sm = (Fraction(41, 10), Fraction(-19, 6), Fraction(-7, 1))
    b_ps = (Fraction(-8, 5), Fraction(-3, 1), Fraction(-7, 1))
    m_u = m_pl_bar / 40.0
    log_total = math.log(m_u / mz)
    ln_ui = clock_high / (clock_high + clock_low) * log_total
    ln_iz = clock_low / (clock_high + clock_low) * log_total
    a_inv = [
        alpha_u_inv + float(b_sm[i]) / (2.0 * math.pi) * ln_iz + float(b_ps[i]) / (2.0 * math.pi) * ln_ui
        for i in range(3)
    ]
    aem_inv = (5.0 / 3.0) * a_inv[0] + a_inv[1]
    return {
        "alpha_U_inv": alpha_u_inv,
        "clock_high": clock_high,
        "clock_low": clock_low,
        "alpha1_inv_mz": a_inv[0],
        "alpha2_inv_mz": a_inv[1],
        "alpha3_inv_mz": a_inv[2],
        "alpha_em_inv_mz": aem_inv,
        "sin2theta_hat_mz": a_inv[1] / aem_inv,
        "alpha3_mz": 1.0 / a_inv[2],
    }


def write_stress_scan(path: Path) -> None:
    engine = DerivationEngine()
    targets = engine.targets
    rows = []
    for delta in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        for high, low in [(5, 14), (6, 13), (7, 12), (6, 12), (6, 14), (5, 13), (7, 13)]:
            row = _predict(46.5 + delta, high, low, engine.bench.mz_gev.value)
            loss = 0.0
            for key in ["alpha_em_inv_mz", "sin2theta_hat_mz", "alpha3_mz"]:
                z = (row[key] - targets[key].value) / targets[key].sigma
                row[f"z_{key}"] = z
                loss += z * z
            row["chi2_3obs"] = loss
            rows.append(row)
    rows.sort(key=lambda r: r["chi2_3obs"])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    outdir = Path(".")
    engine = DerivationEngine()
    models = [ISDLCTCPSOneLoopGaugeModel(), ISDLCTCPSCosmologicalAnsatzModel()]
    payload = {"results": [engine.evaluate(m).as_dict() for m in models]}
    (outdir / "isdlc_tcps_only_results.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_stress_scan(outdir / "isdlc_tcps_stress_scan.csv")
    for r in payload["results"]:
        print(r["model_name"], r["verdict"], r["max_abs_z_predictive"])


if __name__ == "__main__":
    main()

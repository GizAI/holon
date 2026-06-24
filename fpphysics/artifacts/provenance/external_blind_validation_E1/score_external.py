#!/usr/bin/env python3
"""Verify the frozen packet and score the external holdout tranche.

This script is intentionally standalone so that a referee can run it without
installing the whole fpphysics engine.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def canonical_sha256(packet: dict[str, Any]) -> str:
    tmp = dict(packet)
    tmp.pop("packet_sha256", None)
    payload = json.dumps(tmp, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    packet_path = ROOT / "FROZEN_EXTERNAL_PACKET_E1.json"
    obs_path = ROOT / "external_observations_E1.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    expected = packet["packet_sha256"]
    actual = canonical_sha256(packet)
    if actual != expected:
        raise SystemExit(f"packet hash mismatch: expected {expected}, actual {actual}")

    obs = json.loads(obs_path.read_text(encoding="utf-8"))
    preds = packet["predictions"]
    scores: list[dict[str, Any]] = []
    chi2 = 0.0
    ndof = 0

    for name, o in obs.items():
        pred_key = o["pred_key"]
        p = preds.get(pred_key)
        row: dict[str, Any] = {
            "name": name,
            "pred_key": pred_key,
            "prediction": p,
            "kind": o["kind"],
            "source_key": o["source_key"],
        }
        if p is None:
            row["status"] = "missing_prediction"
            scores.append(row)
            continue

        kind = o["kind"]
        if kind in ("point", "scheme_diagnostic_point"):
            z = (p - o["value"]) / o["sigma"]
            row.update({"observed": o["value"], "sigma": o["sigma"], "z": z, "chi2": z * z})
            if kind == "scheme_diagnostic_point":
                row["scheme_note"] = o.get("scheme_note", "")
                row["status"] = "diagnostic_pass_but_not_certified" if abs(z) <= 3 else "diagnostic_fail_scheme_or_value"
            else:
                chi2 += z * z
                ndof += 1
                row["status"] = "pass_3sigma" if abs(z) <= 3 else "fail_gt_3sigma"
        elif kind == "point_with_3sigma_interval":
            z = (p - o["value"]) / o["sigma"]
            chi2 += z * z
            ndof += 1
            interval_pass = o["lo3"] <= p <= o["hi3"]
            if interval_pass and abs(z) > 3:
                status = "inside_3sigma_interval_but_fails_local_bestfit_z"
            elif abs(z) <= 3:
                status = "pass_3sigma"
            else:
                status = "fail_gt_3sigma"
            row.update({
                "observed": o["value"], "sigma": o["sigma"], "z": z,
                "chi2": z * z, "lo3": o["lo3"], "hi3": o["hi3"], "status": status,
            })
        elif kind == "category":
            row.update({"observed": o["value"], "status": "pass_category" if p == o["value"] else "fail_category"})
        elif kind == "lower_bound":
            row.update({"observed_lower_bound": o["value"], "status": "pass_lower_bound" if p >= o["value"] else "fail_lower_bound"})
        else:
            raise ValueError(f"unknown observation kind: {kind}")
        scores.append(row)

    failed = [s["name"] for s in scores if s["status"].startswith("fail") or s["status"].startswith("diagnostic_fail") or s["status"] == "inside_3sigma_interval_but_fails_local_bestfit_z"]
    result = {
        "packet_sha256": expected,
        "verified_packet_hash": actual,
        "strict_gaussian_chi2_excluding_scheme_diagnostics": chi2,
        "strict_gaussian_ndof_excluding_scheme_diagnostics": ndof,
        "strict_gaussian_reduced_chi2_excluding_scheme_diagnostics": chi2 / ndof if ndof else None,
        "publication_tier_verdict": "not_certified" if failed else "certified_on_this_tranche",
        "strict_failed_names": failed,
        "scores": scores,
    }
    (ROOT / "external_score_E1_recomputed.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    with (ROOT / "external_blind_scores_E1_recomputed.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["name", "pred_key", "prediction", "observed", "sigma", "z", "status", "kind", "source_key", "observed_lower_bound", "lo3", "hi3", "scheme_note"]
        writer = csv.DictWriter(f, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(scores)
    print(json.dumps({k: result[k] for k in ["packet_sha256", "publication_tier_verdict", "strict_failed_names", "strict_gaussian_reduced_chi2_excluding_scheme_diagnostics"]}, indent=2))


if __name__ == "__main__":
    main()

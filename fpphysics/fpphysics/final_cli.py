"""Unified final command-line entry point for the consolidated FPP engine.

This module intentionally exposes one top-level workflow while preserving the
specialized modules underneath.  It is meant for reproducibility and research
orientation, not for declaring a completed first-principles theory.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .engine import DerivationEngine
from .report import write_report
from .theory_lab import LabConfig, TheoryLab
from .academic_external_holdout import audit_packet


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = PACKAGE_ROOT / "artifacts" / "packets" / "external_holdout_frozen_packet.json"


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _status_payload() -> dict[str, Any]:
    return {
        "engine": "first_principles_physics_engine_final",
        "version": "1.0.0",
        "scientific_verdict": "no complete first-principles derivation certified",
        "best_positive_signal": "ISDLC-TCPS/Cabibbo-clock packets show partial gauge, CKM, neutrino-bound structure",
        "blocking_failures": [
            "alpha(0) not independently derived from microscopic threshold/HVP/electroweak matching",
            "full Yukawa sector and charged-lepton mass ratios not derived",
            "external holdout has >3σ failures in at least one CKM/PMNS/dark-sector diagnostic depending on tranche",
            "resolved threshold spectrum and collider phenomenology are not specified",
            "all six ΛCDM parameters plus extensions are not derived from a microscopic action",
        ],
        "proper_claim": "auditable research engine plus falsified/partial candidate ledger, not a successful theory of all constants",
    }


def cmd_status(args: argparse.Namespace) -> int:
    payload = _status_payload()
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("FPP final engine v1.0.0")
        print("Verdict:", payload["scientific_verdict"])
        print("Best signal:", payload["best_positive_signal"])
        print("Blocking failures:")
        for item in payload["blocking_failures"]:
            print(" -", item)
    return 0


def cmd_baseline(args: argparse.Namespace) -> int:
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    engine = DerivationEngine()
    results = engine.evaluate_default_models()
    payload = {"audit": engine.audit_status(), "results": [r.as_dict() for r in results]}
    _write_json(out / "baseline_strict_results.json", payload)
    write_report(out / "baseline_report.md")
    print(json.dumps({"outdir": str(out), "models": len(results)}, ensure_ascii=False))
    return 0


def cmd_theory_lab(args: argparse.Namespace) -> int:
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    cfg = LabConfig.deep() if args.deep else LabConfig.quick()
    if args.no_global_fits:
        cfg = LabConfig(**{**cfg.as_dict(), "run_global_fits": False})
    lab = TheoryLab(config=cfg)
    run = lab.run()
    paths = lab.write(run, out)
    print(json.dumps({"outdir": str(out), "paths": paths, "summary": run.summary}, ensure_ascii=False, indent=2))
    return 0


def cmd_academic_holdout(args: argparse.Namespace) -> int:
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    packet = Path(args.packet) if args.packet else DEFAULT_PACKET
    if not packet.exists():
        raise SystemExit(f"Frozen packet not found: {packet}")
    result = audit_packet(str(packet))
    _write_json(out / "academic_external_holdout_results.json", result)
    rows = result["external_tranche_rows"] + result["diagnostic_rows_not_part_of_strict_external_tranche"]
    if rows:
        import csv
        fields: list[str] = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
        with (out / "academic_external_holdout_scores.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    cmd_baseline(argparse.Namespace(outdir=str(out / "baseline")))
    cmd_theory_lab(argparse.Namespace(outdir=str(out / "theory_lab"), deep=False, no_global_fits=args.no_global_fits))
    cmd_academic_holdout(argparse.Namespace(outdir=str(out / "academic_external_holdout"), packet=args.packet))
    _write_json(out / "FINAL_STATUS.json", _status_payload())
    print(json.dumps({"outdir": str(out), "status": "completed", "verdict": _status_payload()["scientific_verdict"]}, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Unified final workflow for the consolidated FPP engine.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="Print final scientific status.")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    b = sub.add_parser("baseline", help="Run strict baseline candidate scoring.")
    b.add_argument("--outdir", default="final_run/baseline")
    b.set_defaults(func=cmd_baseline)

    t = sub.add_parser("theory-lab", help="Run quick/deep automatic theory lab.")
    t.add_argument("--outdir", default="final_run/theory_lab")
    t.add_argument("--deep", action="store_true")
    t.add_argument("--no-global-fits", action="store_true")
    t.set_defaults(func=cmd_theory_lab)

    h = sub.add_parser("academic-holdout", help="Score a frozen packet on strict external academic holdout.")
    h.add_argument("--packet", default=None)
    h.add_argument("--outdir", default="final_run/academic_external_holdout")
    h.set_defaults(func=cmd_academic_holdout)

    a = sub.add_parser("run-all", help="Run the final reproducibility pipeline.")
    a.add_argument("--outdir", default="final_run")
    a.add_argument("--packet", default=None)
    a.add_argument("--no-global-fits", action="store_true")
    a.set_defaults(func=cmd_run_all)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

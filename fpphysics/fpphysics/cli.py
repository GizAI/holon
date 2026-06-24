"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import DerivationEngine
from .report import write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate candidate first-principles derivations of constants.")
    parser.add_argument("--json", dest="json_path", default=None, help="Write machine-readable results to this JSON file.")
    parser.add_argument("--report", dest="report_path", default=None, help="Write a Markdown report to this file.")
    args = parser.parse_args(argv)

    engine = DerivationEngine()
    results = engine.evaluate_default_models()

    if args.json_path:
        payload = {
            "audit": engine.audit_status(),
            "results": [r.as_dict() for r in results],
        }
        Path(args.json_path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_path:
        write_report(args.report_path)
    if not args.json_path and not args.report_path:
        for r in results:
            print(f"{r.model_name}: {r.verdict}; predictive dof={r.dof_predictive}; max|z|={r.max_abs_z_predictive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line interface for the automatic theory-discovery engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .autodiscovery import DiscoveryConfig, TheoryDiscoveryEngine, write_csv, write_json, write_report


def _config_from_args(args: argparse.Namespace) -> DiscoveryConfig:
    if args.deep:
        cfg = DiscoveryConfig.deep()
    elif args.quick:
        cfg = DiscoveryConfig.quick()
    else:
        cfg = DiscoveryConfig.balanced()
    if args.top_k is not None:
        cfg = DiscoveryConfig(
            gauge=type(cfg.gauge)(**{**cfg.gauge.__dict__, "top_k": args.top_k}),
            vacuum=type(cfg.vacuum)(**{**cfg.vacuum.__dict__, "top_k": args.top_k}),
            symbolic=type(cfg.symbolic)(**{**cfg.symbolic.__dict__, "top_k": max(5, args.top_k // 2)}),
            mode=cfg.mode,
        )
    return cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run automatic candidate-theory discovery.")
    parser.add_argument("--outdir", default=".", help="Directory for discovery JSON, report, and CSV.")
    parser.add_argument("--quick", action="store_true", help="Use a bounded quick profile.")
    parser.add_argument("--deep", action="store_true", help="Use wider search bounds.")
    parser.add_argument("--top-k", type=int, default=None, help="Candidates retained per search family.")
    parser.add_argument("--device", default="auto", help="Accepted for compatibility; backend is auto-detected.")
    parser.add_argument("--no-global-optimizers", action="store_true", help="Accepted for compatibility; current engine uses discrete searches.")
    args = parser.parse_args(argv)

    cfg = _config_from_args(args)
    result = TheoryDiscoveryEngine(config=cfg).run()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "discovery_results.json"
    csv_path = outdir / "discovery_top_candidates.csv"
    md_path = outdir / "DISCOVERY_REPORT_ko.md"
    write_json(str(json_path), result)
    write_csv(str(csv_path), result)
    write_report(str(md_path), result)
    print(json.dumps({"json": str(json_path), "csv": str(csv_path), "report": str(md_path), "combined_verdict": result.get("combined_verdict")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

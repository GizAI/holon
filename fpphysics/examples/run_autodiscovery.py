"""Backward-compatible example for the autodiscovery API."""

from __future__ import annotations


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fpphysics.autodiscovery import DiscoveryConfig, TheoryDiscoveryEngine, write_csv, write_json, write_report


if __name__ == "__main__":
    outdir = Path("autodiscovery_run")
    outdir.mkdir(exist_ok=True)
    results = TheoryDiscoveryEngine(config=DiscoveryConfig.quick()).run()
    write_json(str(outdir / "autodiscovery_results.json"), results)
    write_csv(str(outdir / "autodiscovery_top_candidates.csv"), results)
    write_report(str(outdir / "AUTODISCOVERY_REPORT_ko.md"), results)
    for name in ["autodiscovery_results.json", "autodiscovery_top_candidates.csv", "AUTODISCOVERY_REPORT_ko.md"]:
        print(outdir / name)

"""Run the automatic theory-discovery engine from a source checkout."""

from __future__ import annotations


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fpphysics.autodiscovery import DiscoveryConfig, TheoryDiscoveryEngine, write_csv, write_json, write_report


if __name__ == "__main__":
    outdir = Path("discovery_outputs")
    outdir.mkdir(exist_ok=True)
    results = TheoryDiscoveryEngine(config=DiscoveryConfig.quick()).run()
    write_json(str(outdir / "discovery_results.json"), results)
    write_csv(str(outdir / "discovery_top_candidates.csv"), results)
    write_report(str(outdir / "DISCOVERY_REPORT_ko.md"), results)
    print(results["combined_verdict"])
    print("best gauge:", results["best"]["gauge"]["name"])

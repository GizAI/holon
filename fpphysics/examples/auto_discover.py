"""Run a quick automated discovery pass from a source checkout."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fpphysics.discovery import DiscoveryConfig, TheoryDiscoveryEngine, write_csv, write_json, write_report


if __name__ == "__main__":
    engine = TheoryDiscoveryEngine(config=DiscoveryConfig.quick())
    results = engine.run()
    write_json("auto_discovery_results.json", results)
    write_csv("auto_discovery_candidates.csv", results)
    write_report("AUTO_DISCOVERY_REPORT_ko.md", results)
    print(results["combined_verdict"])
    print(results["best"]["gauge"]["name"])

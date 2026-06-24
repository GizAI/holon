"""CLI for the frozen ISDLC--TCPS rational-clock blind candidate."""

from __future__ import annotations

import argparse
import json

from .frozen_blind_candidate import score_frozen_candidate, write_frozen_candidate_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score the frozen ISDLC--TCPS rational-clock blind candidate.")
    parser.add_argument("--outdir", default="frozen_candidate_run", help="Directory for JSON/CSV/Markdown outputs")
    args = parser.parse_args(argv)
    paths = write_frozen_candidate_outputs(args.outdir)
    report = score_frozen_candidate()
    print(json.dumps({"verdict": report.verdict, "sha256": report.packet.sha256, "outputs": paths}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

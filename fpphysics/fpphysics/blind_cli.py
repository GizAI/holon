from __future__ import annotations

import argparse
import json

from .blind_protocol import run_default_blind_challenge, write_blind_challenge


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run the blind-prediction holdout protocol.")
    p.add_argument("--outdir", default="blind_challenge_run")
    p.add_argument("--no-lab", action="store_true", help="Skip the quick TheoryLab-generated train-only packet.")
    args = p.parse_args(argv)
    run = run_default_blind_challenge(include_lab=not args.no_lab)
    paths = write_blind_challenge(run, args.outdir)
    print(json.dumps({"paths": paths, "summary": run.summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

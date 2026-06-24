from __future__ import annotations

import argparse
import json

from .blind_success import run_blind_success_challenge, write_blind_success


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run tiered blind-success challenge for pre-fixed models.")
    parser.add_argument("--outdir", default="blind_success_run")
    args = parser.parse_args(argv)
    run = run_blind_success_challenge()
    paths = write_blind_success(run, args.outdir)
    print(json.dumps({"summary": run["summary"], "paths": paths}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

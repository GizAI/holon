from __future__ import annotations

import argparse
import json

from .blind_cabibbo import run_cabibbo_clock_blind_challenge, write_cabibbo_clock_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ISDLC-TCPS-Fνχ Cabibbo-clock blind candidate challenge.")
    parser.add_argument("--outdir", default="cabibbo_clock_blind_run")
    args = parser.parse_args(argv)
    run = run_cabibbo_clock_blind_challenge()
    paths = write_cabibbo_clock_run(run, args.outdir)
    print(json.dumps({"summary": run["summary"], "paths": paths}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

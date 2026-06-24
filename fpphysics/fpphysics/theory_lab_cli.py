from __future__ import annotations

import argparse
import json

from .theory_lab import LabConfig, TheoryLab


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run the high-level automatic theory lab.")
    p.add_argument("--outdir", default=".")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--deep", action="store_true")
    p.add_argument("--no-global-fits", action="store_true")
    args = p.parse_args(argv)
    cfg = LabConfig.deep() if args.deep else LabConfig.quick() if args.quick else LabConfig()
    if args.no_global_fits:
        cfg = LabConfig(**{**cfg.as_dict(), "run_global_fits": False})
    lab = TheoryLab(config=cfg)
    run = lab.run()
    paths = lab.write(run, args.outdir)
    print(json.dumps({"paths": paths, "summary": run.summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

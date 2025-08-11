#!/usr/bin/env python3
"""
MGC validation script - compares K_twist vs K_wall measurements
"""
import json, math, os, argparse

def load(p):
    return json.load(open(p)) if os.path.exists(p) else []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sym",   type=str, default="results/xy_sym/tau_wall_xy_results.json")
    ap.add_argument("--st5",   type=str, default="results/xy_stencil/tau_wall_xy_results.json")
    ap.add_argument("--wall",  type=str, default="results/xy_wall/tau_wall_xy_results.json")
    ap.add_argument("--Lx",    type=int, default=4)
    ap.add_argument("--Ly",    type=int, default=4)
    ap.add_argument("--tol",   type=float, default=0.01)  # 1 percent
    ap.add_argument("--label", type=str, default="4x4")
    args = ap.parse_args()

    sym = load(args.sym)
    st5 = load(args.st5)
    wal = load(args.wall)
    rows = sym + st5 + wal

    ks = [r["K"] for r in rows if r.get("Lx")==args.Lx and r.get("Ly")==args.Ly and r.get("mode") in ("sym","stencil5")]
    kw = [r["K"] for r in rows if r.get("Lx")==args.Lx and r.get("Ly")==args.Ly and r.get("mode")=="wall"]

    def avg(v): 
        return sum(v)/len(v) if v else float("nan")

    Ks, Kw = avg(ks), avg(kw)
    rel = abs(Ks-Kw)/max(1e-16, abs(Ks)) if ks and kw else float("nan")

    print(f"=== MGC Validation {args.label} ===")
    for r in rows:
        if r.get("Lx")==args.Lx and r.get("Ly")==args.Ly:
            print(f"  {r['mode']:<8} phi={r['phi']:.3f}  K={r['K']:.6f}  alpha_inv={4*math.pi*r['K']:.6f}")
    print()
    print(f"K_sym avg = {Ks:.6f}   K_wall avg = {Kw:.6f}   rel diff = {100*rel:.3f}%")

    ok = (rel <= args.tol)
    print("✅ PASS" if ok else "❌ FAIL")
    return ok

if __name__ == "__main__":
    main()

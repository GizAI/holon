import argparse, json, os, math, time, subprocess, sys

def run(cmd):
    print(">>", " ".join(cmd)); sys.stdout.flush()
    t0 = time.time()
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(p.stdout)
    return time.time() - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", type=str, default="both", choices=["wall","qfi","both"])
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--dtype", type=str, default="fp32", choices=["fp32","fp64"])
    ap.add_argument("--grids", type=str, default="4x4,5x4,6x4,5x5")
    ap.add_argument("--h", type=float, default=3.04)
    ap.add_argument("--iters", type=int, default=140)
    ap.add_argument("--m", type=int, default=20)
    ap.add_argument("--eps", type=float, default=1e-4)
    ap.add_argument("--phi_wall", type=float, default=6.283185307179586)
    ap.add_argument("--qmin", type=float, default=1.0)
    ap.add_argument("--norm", type=str, default="per_bond", choices=["per_bond","per_site","none"])
    ap.add_argument("--cth", type=float, default=0.0)
    ap.add_argument("--outdir", type=str, default="results")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    if args.mode in ["wall","both"]:
        elapsed = run([sys.executable, "measure_tau_wall.py",
                       "--device", args.device, "--dtype", args.dtype,
                       "--iters", str(args.iters), "--m", str(args.m),
                       "--eps", str(args.eps), "--grids", args.grids,
                       "--phi_wall", str(args.phi_wall), "--qmin", str(args.qmin),
                       "--h", str(args.h), "--outdir", args.outdir])
        print(f"[wall] elapsed {elapsed:.1f}s")

    if args.mode in ["qfi","both"]:
        elapsed = run([sys.executable, "measure_sigma_qfi.py",
                       "--device", args.device, "--dtype", args.dtype,
                       "--iters", str(args.iters), "--m", str(args.m),
                       "--eps", str(args.eps), "--grids", args.grids,
                       "--h", str(args.h), "--norm", args.norm])
        print(f"[qfi] elapsed {elapsed:.1f}s")

    # Generate summary if both modes were run
    if args.mode == "both":
        try:
            wall_file = os.path.join(args.outdir, "tau_wall_results.json")
            if os.path.exists(wall_file):
                with open(wall_file, "r") as f:
                    wall_data = json.load(f)
                
                summary = []
                for row in wall_data:
                    alpha_inv = 4.0 * math.pi * row["K"] + args.cth
                    summary_row = {
                        "grid": f"{row['Lx']}x{row['Ly']}",
                        "h": row["h"],
                        "tau_wall": row["tau_wall"],
                        "K": row["K"],
                        "sigma_wall": row["sigma"],
                        "alpha_inv": alpha_inv,
                        "elapsed": row["elapsed"]
                    }
                    summary.append(summary_row)
                
                summary_file = os.path.join(args.outdir, "mgc_summary.json")
                with open(summary_file, "w") as f:
                    json.dump(summary, f, indent=2)
                
                print(f"\nMGC Summary:")
                print(f"{'Grid':<8} {'K':<10} {'σ_wall':<10} {'α*^-1':<10}")
                print("-" * 40)
                for row in summary:
                    print(f"{row['grid']:<8} {row['K']:<10.6f} {row['sigma_wall']:<10.6f} {row['alpha_inv']:<10.6f}")
                print(f"\nSaved {summary_file}")
        except Exception as e:
            print(f"Warning: Could not generate summary: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Plot extrapolation results from QFI sigma calculations
"""
import matplotlib.pyplot as plt
import numpy as np
import argparse
import subprocess
import re

def run_qfi_calculation(args_dict):
    """Run the QFI calculation and parse results"""
    cmd = ["python", "qfi_sigma.py"]
    for key, value in args_dict.items():
        if isinstance(value, bool) and value:
            cmd.append(f"--{key}")
        elif not isinstance(value, bool):
            cmd.extend([f"--{key}", str(value)])
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
    if result.returncode != 0:
        print(f"Error running calculation: {result.stderr}")
        return None, None, None
    
    # Parse output
    lines = result.stdout.split('\n')
    sizes = []
    sigma_values = []
    
    # Find the results table
    in_table = False
    for line in lines:
        if "Lx  Ly   N  σ_finite" in line:
            in_table = True
            continue
        if in_table and line.startswith("--"):
            continue
        if in_table and line.strip() and not line.startswith("Final"):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    N = int(parts[2])
                    sigma = float(parts[3])
                    sizes.append(N)
                    sigma_values.append(sigma)
                except:
                    break
        if "Final linear extrapolation" in line:
            break
    
    # Extract extrapolation results
    linear_extrap = None
    quad_extrap = None
    
    for line in lines:
        if "Final linear extrapolation" in line:
            match = re.search(r'σ_∞ ≈ ([-+]?\d*\.?\d+)', line)
            if match:
                linear_extrap = float(match.group(1))
        if "Final quadratic extrapolation" in line and "failed" not in line:
            match = re.search(r'σ_∞ ≈ ([-+]?\d*\.?\d+)', line)
            if match:
                quad_extrap = float(match.group(1))
    
    return sizes, sigma_values, (linear_extrap, quad_extrap)

def plot_extrapolation(sizes_list, sigma_list, extrap_list, labels, title="QFI σ Extrapolation"):
    """Plot extrapolation results"""
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, (sizes, sigmas, (linear, quad)) in enumerate(zip(sizes_list, sigma_list, extrap_list)):
        if not sizes:
            continue
            
        color = colors[i % len(colors)]
        label = labels[i] if i < len(labels) else f"Series {i+1}"
        
        # Plot finite size data
        inv_N = [1.0/N for N in sizes]
        plt.scatter(inv_N, sigmas, color=color, s=50, alpha=0.7, label=f"{label} (finite)")
        
        # Plot extrapolation lines
        if len(sizes) >= 2 and linear is not None:
            x_extrap = np.linspace(0, max(inv_N), 100)
            # Linear fit through data points
            if len(sizes) >= 2:
                x_data = np.array(inv_N)
                y_data = np.array(sigmas)
                # Linear regression
                A = np.vstack([x_data, np.ones(len(x_data))]).T
                slope, intercept = np.linalg.lstsq(A, y_data, rcond=None)[0]
                y_extrap = slope * x_extrap + intercept
                plt.plot(x_extrap, y_extrap, '--', color=color, alpha=0.7, 
                        label=f"{label} linear → {linear:.4f}")
        
        # Mark extrapolated value
        if linear is not None:
            plt.scatter([0], [linear], color=color, s=100, marker='*', 
                       edgecolor='black', linewidth=1, zorder=5)
    
    plt.xlabel('1/N (inverse system size)', fontsize=12)
    plt.ylabel('σ (normalized QFI)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xlim(-0.01, max([max([1.0/N for N in sizes]) for sizes in sizes_list if sizes]) * 1.1)
    
    # Add vertical line at 1/N = 0 (infinite size limit)
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
    plt.text(0.005, plt.ylim()[1]*0.9, 'Infinite size\nlimit', fontsize=10, alpha=0.7)
    
    plt.tight_layout()
    return plt.gcf()

def main():
    parser = argparse.ArgumentParser(description="Plot QFI extrapolation results")
    parser.add_argument("--output", type=str, default="qfi_extrapolation.png", help="Output plot filename")
    parser.add_argument("--dh_values", type=float, nargs='+', default=[0.01, 0.005], 
                       help="Different dh values to compare")
    parser.add_argument("--h0_values", type=float, nargs='+', default=[3.0], 
                       help="Different h0 values to compare")
    parser.add_argument("--max_N", type=int, default=16, help="Maximum system size")
    args = parser.parse_args()
    
    sizes_list = []
    sigma_list = []
    extrap_list = []
    labels = []
    
    print("Running QFI calculations...")
    
    for h0 in args.h0_values:
        for dh in args.dh_values:
            print(f"Computing h0={h0}, dh={dh}...")
            
            calc_args = {
                'square_only': True,
                'Lx_start': 3,
                'Lx_max': 4,
                'max_N': args.max_N,
                'h0': h0,
                'dh': dh,
                'iters': 60
            }
            
            sizes, sigmas, extraps = run_qfi_calculation(calc_args)
            
            if sizes and sigmas:
                sizes_list.append(sizes)
                sigma_list.append(sigmas)
                extrap_list.append(extraps)
                labels.append(f"h₀={h0}, δh={dh}")
                print(f"  Found {len(sizes)} data points, linear extrap: {extraps[0]:.6f}")
            else:
                print(f"  Failed to get results")
    
    if not sizes_list:
        print("No successful calculations!")
        return
    
    # Create plot
    fig = plot_extrapolation(sizes_list, sigma_list, extrap_list, labels)
    fig.savefig(args.output, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {args.output}")
    
    # Print summary
    print("\nSummary of extrapolated values:")
    for label, (linear, quad) in zip(labels, extrap_list):
        print(f"{label}: σ_∞ ≈ {linear:.6f}" + (f" (quad: {quad:.6f})" if quad else ""))

if __name__ == "__main__":
    main()

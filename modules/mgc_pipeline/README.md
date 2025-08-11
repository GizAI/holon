# MGC Pipeline - Modular Geometric Conductivity

Complete implementation of the MGC (Modular Geometric Conductivity) pipeline for 2D TFIM systems with wall-based and QFI-based conductivity measurements.

## Overview

This pipeline implements two complementary approaches to measure geometric conductivity:

1. **Wall-based MGC**: Uses domain wall energy differences to compute τ_wall and derive K
2. **QFI-based surrogate**: Uses quantum Fisher information overlap method for direct σ measurement

## Key Formulas

- **Wall tension**: `τ_wall = (E_wall - E_uniform) / L_y`
- **MGC parameter**: `K = (2*L_x / φ_wall²) * τ_wall`
- **Geometric factor**: `C_geo = q_min² / ((2π)² * L_x²)`
- **Conductivity**: `σ = C_geo * K`
- **Universal relation**: `α*^(-1) = 4π*K + c_th`

## Quick Start

1. **Setup environment**:
```bash
pip install -r requirements.txt
```

2. **Run wall-based MGC only**:
```bash
python mgc_pipeline.py --mode wall --grids 4x4,5x4,6x4 --phi_wall 6.283185307179586 --qmin 1.0
```

3. **Run QFI surrogate only**:
```bash
python measure_sigma_qfi.py --device cuda --dtype fp32 --grids 4x4,5x4,6x4 --norm per_bond
```

4. **Run complete pipeline**:
```bash
python mgc_pipeline.py --mode both --grids 4x4,5x4,6x4 --phi_wall 6.283185307179586 --qmin 1.0 --cth 0.0
```

## Components

- **`grid_cache.py`**: 2D lattice TFIM Hamiltonian with domain wall implementation
- **`lanczos_core.py`**: Thick-restart Lanczos with Davidson polishing for RTX 4080
- **`measure_tau_wall.py`**: Wall tension measurement (uniform vs wall sectors)
- **`measure_sigma_qfi.py`**: QFI-based conductivity with warm start and refinement
- **`mgc_pipeline.py`**: Orchestration script with summary generation

## Key Options

- **`--phi_wall`**: Phase difference implemented by wall (default: 2π)
- **`--qmin`**: Charge normalization factor (default: 1.0)
- **`--dtype fp64`**: Higher precision mode
- **`--iters`, `--m`**: Lanczos iteration control (20-24 safe for RTX 4080)
- **`--norm`**: QFI normalization (per_bond, per_site, none)

## Validation

Compare wall-based K with QFI-based σ using σ = C_geo * K. Agreement within ~1% validates MGC consistency.

## Output Files

- **`results/tau_wall_results.json`**: Detailed wall measurements
- **`results/mgc_summary.json`**: Final K, σ, and α*^(-1) values

## Performance Notes

- Optimized for RTX 4080 with fp32 precision
- Uses fp16 basis storage and torch.compile when available
- Warm start caching for QFI measurements
- Automatic refinement with overlap/residual quality control

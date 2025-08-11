# MGC Pipeline v2 - Enhanced with XY Model

## What's New in v2

### 🔧 **TFIM Domain Wall Fix**
- **Fixed cut definition**: Cut now properly between `(wall_x-1)` and `wall_x`
- **Wrap bond handling**: Periodic boundary conditions correctly handle wall cuts
- **Improved accuracy**: More reliable wall tension measurements

### 🆕 **XY Half-Filling Model**
- **True U(1) twist**: Peierls phase `e^(iφ/Lx)` on x-bonds
- **Hardcore bosons**: Half-filling constraint with proper particle conservation
- **Clean MGC**: Direct correspondence between twist and wall measurements

### 📊 **Enhanced Measurements**
- **XY-specific script**: `measure_tau_wall_xy.py` for U(1) twist measurements
- **Improved validation**: Better parameter ranges for meaningful results
- **Extended documentation**: Clear usage examples for both models

## Quick Start Guide

### 1. TFIM with Corrected Wall (Low h for visible wall cost)
```bash
python measure_tau_wall.py --device cuda --dtype fp32 --grids 4x4,5x4 --h 0.2 --phi_wall 6.283185307179586 --qmin 1.0
```
**Expected**: Positive τ_wall, non-zero K values

### 2. XY Model U(1) Twist (Recommended for MGC validation)
```bash
python measure_tau_wall_xy.py --device cuda --dtype fp32 --grids 4x4,5x4 --t 1.0 --delta 0.0 --phi_wall 6.283185307179586 --qmin 1.0
```
**Expected**: Clear τ_wall signal, consistent K and σ values

### 3. Full Pipeline with XY
```bash
# Run XY measurement
python measure_tau_wall_xy.py --grids 4x4,5x4,6x4 --t 1.0 --delta 0.0 --phi_wall 6.283185307179586 --qmin 1.0

# Then analyze results
python -c "
import json, math
with open('results/tau_wall_xy_results.json', 'r') as f:
    data = json.load(f)
print('Grid     K          σ          α*^-1')
print('-' * 35)
for row in data:
    alpha_inv = 4.0 * math.pi * row['K']
    print(f'{row[\"Lx\"]}x{row[\"Ly\"]}     {row[\"K\"]:.6f}  {row[\"sigma\"]:.6f}  {alpha_inv:.6f}')
"
```

## Key Formulas

### Wall Tension Method
- **τ_wall = [E(φ) - E(0)] / L_y**
- **K = (2×L_x / φ²) × τ_wall**
- **σ = C_geo × K** where **C_geo = q_min² / [(2π)² × L_x²]**
- **α*^(-1) = 4π×K + c_th**

### Model Differences
- **TFIM**: Z₂ symmetry, domain wall implementation, best at small h
- **XY**: U(1) symmetry, Peierls twist, natural MGC correspondence

## Parameter Guidelines

### TFIM Parameters
- **h < 1.0**: Ferromagnetic region with significant wall cost
- **h = 0.2-0.5**: Optimal range for wall measurements
- **h > 2.0**: Paramagnetic region, τ_wall ≈ 0

### XY Parameters  
- **t = 1.0**: Standard hopping amplitude
- **delta = 0.0**: Pure XY model
- **delta > 0**: Enhanced curvature, clearer K signal
- **φ_wall = 2π**: Standard twist for MGC

### Computational Settings
- **dtype = fp64**: Higher precision for small signals
- **iters = 140-200**: More iterations for convergence
- **m = 20-24**: Larger Krylov space for RTX 4080

## Validation Strategy

1. **TFIM consistency**: Compare h=0.2 vs h=3.04 results
2. **XY verification**: Check τ_wall scaling with φ_wall
3. **Cross-validation**: Compare K values between methods
4. **MGC relation**: Verify α*^(-1) = 4πK relationship

## File Structure
```
mgc_pipeline/
├── grid_cache.py          # TFIM with fixed wall cuts
├── xy_half.py             # XY half-filling model  
├── measure_tau_wall.py    # TFIM wall measurements
├── measure_tau_wall_xy.py # XY twist measurements
├── measure_sigma_qfi.py   # QFI-based conductivity
├── mgc_pipeline.py        # Full orchestration
└── README_v2.md           # This file
```

## Expected Results

### TFIM at h=0.2
- τ_wall > 0 (positive wall cost)
- K ~ O(10^-3) (measurable geometric response)
- Clear system size dependence

### XY Model
- τ_wall ~ O(10^-2) (strong twist response)  
- K ~ O(10^-3) (consistent with TFIM)
- Linear scaling with φ_wall

The XY model provides the cleanest validation of MGC theory due to its natural U(1) structure.

## Important Notes

**XY Periodicity**: XY는 φ=2π가 주기점이라 E(2π)=E(0) 가능. 작은 φ에서 대칭차분으로 K를 추정하는 것이 표준.

**TFIM Parameter Range**: TFIM은 큰 h에서 벽 비용이 거의 0. 이방성 응답과 경계 민감도로 λ_2, λ_3를 보정하면 H 계수 물리 기반이 닫힘.

**Enhanced Measurements**: v2 includes anisotropy response (κ) and boundary susceptibility (χ_b) for complete characterization of geometric response coefficients.

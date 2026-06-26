# A finite boundary-code closure theorem for Standard Model constants

## Abstract

The Standard Model contains a finite set of empirical inputs: three gauge couplings, Yukawa matrices and flavor mixing parameters, Higgs-sector scale data, and infrared quantities controlled by non-perturbative QCD. Attempts to derive these constants often fail because they introduce continuous moduli, select small integers after comparison with data, or conflate postdiction with prediction. We present BHF-OCEAN, a finite boundary-code program combining an Occam enumeration and null-test framework with a BC4-Hamming-Fano boundary Hamiltonian. The gauge-boundary sector uniquely selects, under stated finite-code assumptions, a BC4 root class, a seven-sector Fano flux code, a 3:14 clock, and a minimal Pati-Salam threshold hierarchy. The resulting one-loop benchmark compactly reproduces the broad weak-scale gauge-coupling pattern. We then prove a no-modulus closure theorem: once gauge kinetic data are fixed by the boundary code, any irreducible completion of the Standard Model constants requires exactly three additional spectral modules - flavor, QCD-infrared, and electroweak-scale modules. The paper does not claim to derive the Thomson-limit fine-structure constant, fermion masses, CKM/PMNS data, or the Higgs scale. It defines the finite Hamiltonian framework and the open spectral targets required for such derivations.

## 1. Motivation

Gauge symmetry fixes interaction form but not the numerical coefficients of gauge kinetic terms. The Standard Model also leaves Yukawa matrices, the Higgs relevant operator, the Higgs quartic, and low-energy hadronic vacuum-polarization data as empirical inputs. A credible theory of constants must therefore separate three tasks: finite selection of gauge data, avoidance of hidden continuous moduli, and computation of the remaining spectra without importing measured constants.

BHF-OCEAN is designed around this separation. OCEAN supplies the audit principle: enumerate finite-code alternatives and penalize post-hoc selection. BHF supplies the current best finite boundary-code benchmark found in this program.

## 2. Source lineage and canonical status

The research lineage contains four major stages. D5/ISDLC produced a numerically strong reference candidate with a D5 root system and a finite determinant correction. MCC introduced claim labels separating prediction, standard bridge, and open target. OCEAN supplied a zero-base enumeration and showed that D5 is not unique among compact finite-code candidates. COVE-BC4, then BHF, promoted the best OCEAN-passing BC4 candidate to a finite boundary Hamiltonian with threshold uniqueness under dimension minimality.

The canonical status is therefore:

- D5/ISDLC: reference baseline.
- OCEAN: validation framework.
- BHF/COVE-BC4: final gauge-boundary benchmark.
- flavor, QCD-IR, and EW spectral modules: required but open completion sectors.

## 3. BHF state space

The finite microscopic state space is

$$
H_BHF = H_root \otimes H_Fano \otimes H_clock \otimes H_th \otimes H_cl.
$$

The closure factor decomposes as

$$
H_cl = H_flavor \otimes H_QCD \otimes H_EW.
$$

This is not an arbitrary triplication. It follows from the no-modulus closure theorem below.

## 4. Root, flux and clock selection

The admissible rank-four irreducible crystallographic root classes are `A4, B4, C4, D4, F4`. Non-simply-laced electric/magnetic boundary completeness removes `A4` and `D4`. Langlands-dual closure identifies `B4 ~ C4` as `BC4`. The remaining non-simply-laced classes are `BC4` and `F4`, with root counts 32 and 48. Minimal root count selects `BC4`.

The Fano boundary is `F_2^3 \ {0}`, giving seven nonzero flux sectors. The open clock counts three generators, and the closed oriented return clock counts twice the seven nonzero sectors. Therefore the clock is `3:14`.

## 5. Threshold hierarchy certificate

The Pati-Salam threshold occupation vector is `n=(n_SR,n_hL,n_hR,n_qC,n_QCL,n_XLR,n_G4,n_GL,n_GR)`. The charge matrix in units of `1/6` is

```text
C = [[0,0,0,1,2,0,32,0,0],
     [0,1,0,0,4,8,0,16,0],
     [2,0,1,0,0,8,0,0,16]]
```

The BHF target charge is `T=(67,45,27)`. The threshold Hamiltonian is

```text
H_th = Lambda || C n - T ||^2 + epsilon d.n + delta n.n
```

where `Lambda >> epsilon >> delta > 0` and `d=(3,2,2,4,8,4,15,3,3)`.

An exhaustive enumeration gives 1792 nonnegative integer solutions. The unique minimizer of dimension is `[1, 1, 1, 1, 1, 1, 2, 2, 1]`, with dimension 62. Thus the BHF threshold hierarchy is unique under beta-charge closure and microscopic dimension minimality.

## 6. Gauge-coupling benchmark

The BHF stiffness is `alpha_U^-1 = 32 + 4 + 7/2 = 39.5`. The unification scale is `M_U = Mbar_Pl/32`. The Pati-Salam beta vector is `(1/2,9/2,3/2)`. One-loop running gives

```text
alpha_em^-1(MZ)  = 127.956742827056
sin2_MSbar(MZ)   = 0.231188712312
alpha_s(MZ)      = 0.118205763021
```

These are formal benchmark values, not nine-digit physical predictions.

## 7. D5 reference baseline

For comparison, the D5 reference candidate gives

```text
alpha_em^-1(MZ)  = 127.928418368491
sin2_MSbar(MZ)   = 0.231223633775
alpha_s(MZ)      = 0.118000699956
```

OCEAN retains D5 as an important reference but does not treat it as a unique derivation because compact rival candidates exist.

## 8. No-modulus closure theorem

Assume the BHF gauge-boundary sector fixes gauge kinetic data and the infrared theory is required to contain no independent continuous Standard Model moduli. Then exactly three closure modules are required: flavor, QCD-infrared, and electroweak-scale modules.

Proof. After gauge kinetic coefficients are fixed, the remaining Standard Model inputs fall into three mutually independent operator classes. Yukawa matrices and flavor mixing require a finite flavor spectral module. The bridge from the running electromagnetic coupling at `M_Z` to `alpha(0)` requires charged thresholds and hadronic vacuum polarization, so it requires a QCD-infrared spectral module. The Higgs vacuum scale and quartic require an electroweak-scale spectral module. No two of these operator classes determine the third. Conversely, the gauge sector plus these three modules covers the Standard Model constant classes. Therefore a no-modulus completion requires exactly these three modules.

## 9. Fine-structure constant status

The low-energy fine-structure constant is not claimed as a prediction. In BHF form,

```text
alpha^-1(0) = alpha_em^-1(MZ) + Delta_lepton + Delta_QCD+EW
```

For the BHF benchmark, `Delta_QCD+EW = 4.773458085764`. This is an open target for the QCD-infrared spectral module.

## 10. Falsifiability

The program can fail if two-loop and threshold-corrected running invalidates the gauge benchmark, if an expanded primitive threshold block space produces a lower-complexity rival, if the closure modules cannot be constructed as BHF-compatible finite operators, or if blind holdout predictions fail.

## 11. Conclusion

BHF-OCEAN v0.2 is not a completed derivation of all constants. It is a consolidated finite-code research program. Its strongest present result is the combination of OCEAN null-testing, a BC4-Fano gauge-boundary benchmark, a threshold uniqueness certificate, and a no-modulus closure theorem specifying the three spectral modules required for future derivation of the remaining constants.

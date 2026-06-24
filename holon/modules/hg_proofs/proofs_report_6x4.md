# THG-1 proofs report
Generated at 2025-08-11T05:53:26.691739Z

## Model and geometry
Lattice L = (6, 4, 4), beta = 8, flux m = 1, q_min = 1
C_geo = 7.036193e-04, K_geom = 1.785962e+04

## 1. Ward identity - exact current
Not run: Expose exact current operator Jx, its divergence, and an inner product hook

## 2. OS positivity with uniform flux
min eigenvalue of C-reflection Grammian: 1.000e+00, passed = True

## 3. Boundary-term stability under block-spin
Not run: Provide anisotropy and boundary layer hooks

## 4. Sigma chain and MGC identity
K_sym = 0.541852, K_stencil = 0.541852, K_wall = 0.540093
MGC closure relative diff = 0.325 percent
sigma_sym = 3.812575e-04, sigma_wall = 3.800201e-04
alpha_*^-1 from sym = 6.809112, from wall = 6.787013

## 5. D_can - H duality notes
This report is paired with a formal note that states:
- A1 to A5 for D_can on THG-1
- Legendre dual from max entropy with D_can produces H with lambda_i fixed by measured observables
- Stability under local graph moves up to boundary terms
Measured lambda spreads above act as the numerical sanity check for boundary-term stability.

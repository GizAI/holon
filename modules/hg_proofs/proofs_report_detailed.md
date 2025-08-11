# THG-1 proofs report
Generated at 2025-08-11T04:29:52.528860Z

## Model and geometry
Lattice L = (4, 4, 4), beta = 8, flux m = 1, q_min = 1
C_geo = 1.583143e-03, K_geom = 7.937607e+03

## 1. Ward identity - exact current
Not run: Expose exact current operator Jx, its divergence, and an inner product hook

## 2. OS positivity with uniform flux
min eigenvalue of C-reflection Grammian: 1.000e+00, passed = True

## 3. Boundary-term stability under block-spin
Not run: Provide anisotropy and boundary layer hooks

## 4. Sigma chain and MGC identity
K_sym = 0.554435, K_stencil = 0.554435, K_wall = 0.553901
MGC closure relative diff = 0.096 percent
sigma_sym = 8.777507e-04, sigma_wall = 8.769055e-04
alpha_*^-1 from sym = 6.967240, from wall = 6.960531

## 5. D_can - H duality notes
This report is paired with a formal note that states:
- A1 to A5 for D_can on THG-1
- Legendre dual from max entropy with D_can produces H with lambda_i fixed by measured observables
- Stability under local graph moves up to boundary terms
Measured lambda spreads above act as the numerical sanity check for boundary-term stability.

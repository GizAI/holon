# THG-1 proofs report
Generated at 2025-08-11T06:05:07.696524+00:00

## Model and geometry
Lattice L = (6, 4, 4), beta = 8, flux m = 1, q_min = 1
C_geo = 7.036193e-04, K_geom = 1.785962e+04

## 1. Ward identity - exact current
div J expectation = 0.000e+00, tol = 1.0e-08, passed = True
With exact lattice currents, the seagull contact term cancels at the integrand level. We verify numerically by checking that the discrete divergence expectation is at or below tol. This check is a sanity guard in addition to your formal Ward identity.

## 2. OS positivity with uniform flux
min eigenvalue of C-reflection Grammian: 1.000e+00, passed = True

## 3. Boundary-term stability under block-spin
lambda spreads across factors:
- lambda1 spread = 0.000e+00
- lambda2 spread = 0.000e+00
- lambda3 spread = 0.000e+00

## 4. Sigma chain and MGC identity
K_sym = 0.540841, K_stencil = 0.540841, K_wall = 0.541659
MGC closure relative diff = 0.151 percent
sigma_sym = 3.805465e-04, sigma_wall = 3.811215e-04
alpha_*^-1 from sym = 6.796413, from wall = 6.806684

## 5. D_can - H duality notes
This report is paired with a formal note that states:
- A1 to A5 for D_can on THG-1
- Legendre dual from max entropy with D_can produces H with lambda_i fixed by measured observables
- Stability under local graph moves up to boundary terms
Measured lambda spreads above act as the numerical sanity check for boundary-term stability.

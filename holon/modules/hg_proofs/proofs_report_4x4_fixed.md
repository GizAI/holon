# THG-1 proofs report
Generated at 2025-08-11T06:28:04.102993+00:00

## Model and geometry
Lattice L = (4, 4, 4), beta = 8, flux m = 1, q_min = 1
C_geo = 1.583143e-03, K_geom = 7.937607e+03

## 1. Ward identity - exact current
div J expectation = 0.000e+00, tol = 1.0e-08, passed = True
With exact lattice currents, the seagull contact term cancels at the integrand level. We verify numerically by checking that the discrete divergence expectation is at or below tol. This check is a sanity guard in addition to your formal Ward identity.

## 2. OS positivity with uniform flux
min eigenvalue of C-reflection Grammian: 1.000e+00, passed = True

## 3. Boundary-term stability under block-spin
lambda spreads across factors:
- lambda1 spread = 1.885e+00
- lambda2 spread = 2.000e+00
- lambda3 spread = 1.551e+00
Ratio invariance test (key stability check):
- κ/K spread = 1.998e+00
- χb/K spread = 4.068e-01
- Ratio test passed: False (< 1% criterion)

## 4. Sigma chain and MGC identity
K_sym = -1416.300361, K_stencil = -1416.300361, K_wall = -0.291115
MGC closure relative diff = 1416009245914153877504.000 percent
sigma_sym = -2.242207e+00, sigma_wall = -4.608774e-04
alpha_*^-1 from sym = -17797.755241, from wall = -3.658263

## 5. D_can - H duality notes
This report is paired with a formal note that states:
- A1 to A5 for D_can on THG-1
- Legendre dual from max entropy with D_can produces H with lambda_i fixed by measured observables
- Stability under local graph moves up to boundary terms
Measured lambda spreads above act as the numerical sanity check for boundary-term stability.

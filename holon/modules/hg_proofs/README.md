# HG proofs scaffold

This package is a thin scaffold that plugs into your existing fast code to generate a compact proofs report.
It targets one microscopic Holon Graph: THG-1 (stabilizer + compact U(1) rotor) on a 3d torus with uniform flux.

Focus items:
1) D_can - H duality: we provide the statement templates and show boundary-term stability by direct checks on tau, kappa, chi_b.
   The duality proof text lives in the report and references measured D_i multipliers. You should include or link your formal writeup.
2) Boundary-term stability: block-spin map with area law control. We test that inferred lambda_i = D_i * observable are stable up to O(1/L).
3) Sigma-chain preservation: exact-current Ward checks, OS positivity with flux via C-reflection, and MGC identity closure.

Wire these adapters to your existing modules:
- mgc_pipeline for computing K with twists and flux normalization
- measure_tau_wall.py and measure_tau_wall_xy.py for wall tension
- measure_sigma_qfi.py for sigma from QFI or current susceptibility
- lanczos_core.py for eigenpairs when needed
- grid_cache.py for lattice bookkeeping

See hg_proofs/adapters.py for the required function signatures.
Run the proofs report:
    python -m hg_proofs.proofs_report --out proofs_report.md

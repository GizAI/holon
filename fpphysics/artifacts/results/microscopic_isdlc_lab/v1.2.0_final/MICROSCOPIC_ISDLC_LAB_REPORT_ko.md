# Microscopic ISDLC Laboratory

## 결론

이 실행은 상수 검색이 아니라 ISDLC--TCPS--LCI--DFC theorem 후보의 finite audit이다.
현재 결과는 `conditional_theorem`이며, 완성된 물리 증명이 아니다.
classification: `B_plus`
finite complex audits pass and a constructed non-diagonal Hamiltonian response reproduces the sector stiffness; still not C because the microscopic Hamiltonian is engineered rather than uniquely derived.

- `finite_holonomy_stiffness`: `conditional_theorem`, pass=`True`
- `tcps_clock_ratio`: `conditional_theorem`, pass=`True`
- `lci_jacobian_supertrace`: `conditional_theorem`, pass=`True`
- `dfc_chain_supertrace`: `conditional_theorem`, pass=`True`

## Null scan

- backend: `torch-cuda`
- candidates: `5000000000`
- elapsed seconds: `6.812`
- candidates/sec: `733986902.624`
- p_null upper: `2e-10`
- best null score: `0.099283`

## Non-diagonal Hamiltonian

- constructed stiffness: `46.5`
- largest table size: `64`
- curvature: `46.4999106443`
- abs error: `8.94e-05`

## LCI/DFC

- LCI regulator verdict: `topological_regulator_trace_passes; ordinary_ungraded_control_fails`
- DFC Q^2=0: `True`
- DFC cohomology dimensions: `{'H0': 1, 'H1': 0, 'H2': 0}`
- ordinary messenger control: `fail_generates_ordinary_threshold_and_two_loop_messenger_interpretation`

## Frozen flavor extension

- packet: `63d9ed215a92`
- lambda: `sqrt(13/29)/3`
- status: `frozen_for_later_origin_search`

## Blockers

- finite_holonomy_stiffness: Needs a non-tautological microscopic ISDLC Hamiltonian whose primitive sectors force these weights.
- finite_holonomy_stiffness: Needs finite-size flow or tensor-network evidence that the same stiffness survives non-diagonal perturbations.
- tcps_clock_ratio: Needs construction of the clock as a spectrum of the same Hamiltonian, not an external discrete input.
- lci_jacobian_supertrace: Needs a concrete blocking operator K_A and heat-kernel regulator on the same finite Hilbert space.
- lci_jacobian_supertrace: Needs gauge covariance tests for non-constant background links.
- lci_jacobian_supertrace: Needs proof that these modes are Jacobian index modes, not propagating messenger matter.
- dfc_chain_supertrace: Needs derivation of the protected charges from the ISDLC differential Q rather than assigning them.
- dfc_chain_supertrace: Needs a locality/no-propagator audit against ordinary threshold matter.

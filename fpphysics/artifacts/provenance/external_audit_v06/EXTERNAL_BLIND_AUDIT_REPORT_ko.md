# 외부 holdout tranche freeze-before-reveal 감사 보고서 v0.6
## 결론
사전에 고정된 `ISDLC–TCPS-Fνχ Cabibbo-clock frozen extension` packet을 외부 tranche에 재채점했다. 모델은 CKM의 일부와 N_eff, proton lifetime lower bound는 통과하지만, **NuFIT 6.0 IC24+SK의 PMNS θ23와 Planck Ωc h²에서 3σ 초과 실패**가 발생한다. 또한 α(0), charged lepton mass ratios, resolved threshold spectrum, 전체 SM+ΛCDM 파라미터가 빠져 있으므로 학계 기준의 완전 제1원리 유도 성공으로 주장할 수 없다.
## Frozen packet
- embedded canonical SHA256: `e0855d9ba75a7b58a66cadf60dcbcdedae18bf8e3bdd9eff63b8afe73af8aaaa`
- file-bytes SHA256: `1746dbf32813800fb4bcdf424d474058f910d4928f291f8afab7ec073c546cc1`
- frozen UTC from packet: `2026-06-24T02:00:00+00:00`
- claims_first_principles: `False`
## External-tranche scoring summary
- numeric_count: `11`
- chi2: `63.745989097470975`
- reduced_chi2_independent_diag_approx: `5.795089917951906`
- pass_count_including_bounds_and_categorical: `11`
- fail_count: `2`
- missing_count: `3`
- incomplete_count: `0`
- external_tranche_pass: `False`
- complete_SM_LambdaCDM_first_principles_derivation_success: `False`
- reason: `External tranche has >3σ failures in PMNS theta23 and Omega_c h^2, and required alpha(0), charged-lepton mass ratios, resolved threshold spectrum, and many SM/LambdaCDM parameters remain unpredicted.`

## Scores
| quantity | pred | external | z/status |
|---|---:|---:|---:|
| Vus | 0.22645541 | 0.22501 | 2.126 / pass_3sigma |
| Vcb | 0.04187162 | 0.04183 | 0.053 / pass_3sigma |
| Vub | 0.0038710326 | 0.003732 | 1.545 / pass_3sigma |
| Jarlskog_CKM | 3.371601e-05 | 3.12e-05 | 1.935 / pass_3sigma |
| pmns_sin2_theta12 | 0.31717172 | 0.308 | 0.764 / pass_3sigma |
| pmns_sin2_theta23 | 0.55128205 | 0.47 | 4.781 / fail_gt_3sigma |
| pmns_sin2_theta13 | 0.023668639 | 0.02215 | 2.712 / pass_3sigma |
| delta_m21_sq_ev2 | 7.3529412e-05 | 7.49e-05 | -0.721 / pass_3sigma |
| abs_delta_m3l_sq_ev2 | 0.0025 | 0.002513 | -0.684 / pass_3sigma |
| neutrino_ordering | normal | — | categorical_pass / categorical_pass |
| Omega_c_h2 | 0.11538462 | 0.12 | -4.615 / fail_gt_3sigma |
| N_eff | 3 | 2.99 | 0.059 / pass_3sigma |
| tau_p_to_e_pi0_years | 8.5168625e+37 | 2.4e+34 | one_sided_bound_pass / one_sided_bound_pass |
| alpha0_inv | None | 137.036 | missing_prediction / missing_prediction |
| charged_lepton_mass_ratios | None | — | incomplete_target_definition_or_missing_prediction / incomplete_target_definition_or_missing_prediction |
| threshold_spectrum_resolved | None | — | incomplete_target_definition_or_missing_prediction / incomplete_target_definition_or_missing_prediction |

## Methodological note
이 감사는 기존 packet을 변형하지 않고 외부값을 대입해 채점한 것이다. 그러나 packet 자체가 과거 공개 물리값을 전혀 몰랐다는 역사적 blind는 아니다. 논문에서는 “external-tranche audit” 또는 “pre-registered replication candidate” 정도로 표현해야 하며, true blind claim은 향후 새 실험/새 global-fit release를 packet 수정 없이 기다려야 가능하다.

## All pre-existing frozen-packet sweep
현재 작업 전에 존재하던 frozen packet들을 중복 SHA 기준으로 모아 같은 외부 tranche에 채점했다. **external_pass=True인 후보는 없었다.**

| model | numeric | fail | missing | red chi2 | hard fails |
|---|---:|---:|---:|---:|---|
| ISDLC-TCPS minimal-decoupled blind predictor | 1 | 0 | 14 | 0.101 |  |
| ISDLC-TCPS minimal-decoupled blind predictor | 1 | 0 | 14 | 0.101 |  |
| ISDLC-TCPS minimal-decoupled blind predictor | 1 | 0 | 14 | 0.101 |  |
| ISDLC-TCPS minimal-decoupled blind predictor | 1 | 0 | 14 | 0.101 |  |
| ISDLC-TCPS-Fnu-chi Cabibbo-clock frozen extension, external-holdout packet | 0 | 0 | 16 | — |  |
| ISDLC-TCPS-Fνχ Cabibbo-clock frozen extension | 11 | 2 | 3 | 5.8 | pmns_sin2_theta23:4.78; Omega_c_h2:-4.62 |
| frozen ISDLC-TCPS clock-texture + minimal-thermal extension | 8 | 3 | 6 | 9.31 | Vus:-3.66; pmns_sin2_theta23:6.13; pmns_sin2_theta13:4.66 |
| FROZEN-RGCICT-1: RG-clock + instanton + clock-texture minimal thermal model | 8 | 3 | 6 | 9.31 | Vus:-3.66; pmns_sin2_theta23:6.13; pmns_sin2_theta13:4.66 |

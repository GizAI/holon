# Freeze-before-reveal 외부 holdout 검증 E1
## 결론
요청한 방식대로 이 세션 안에서 **모델 packet을 먼저 동결하고**, 그 다음에 외부 공개 holdout 값을 조회하여 채점했다. 결과는 다음과 같다.
- Frozen packet SHA-256: `590c1a3a3b3c4fe8287dee99200e689f831cbbd6da015d44baccb3820c5540a9`
- 후보명: `ISDLC-TCPS-Fnu-chi Cabibbo-clock external-holdout packet E1`
- publication-tier verdict: `not_certified`
- limited verdict: `partial_blind_predictive_candidate_CKM_neutrino_splittings_Neff_threshold_bounds_only`
- strict reduced chi^2, scheme diagnostics excluded: `5.14417`
- complete first-principles SM+LCDM derivation: `not_achieved`

따라서 **학계가 인정할 수 있는 수준의 완전 성공은 아니다.** 부분 성공은 있다: CKM 4개, PMNS 일부, neutrino mass splitting, N_eff, proton/threshold null bound는 동결 packet이 맞혔다. 그러나 theta23 local best-fit, dark matter relic abundance, scheme-defined mass ratio가 실패 또는 미인증이다.
## 동결 공식
동결된 discrete inputs는 다음뿐이다.
```text
r = 6/13
alpha_U^-1 = 93/2
M_U = Mbar_Pl/40
lambda_C = sqrt(6/13)/3
```
주요 예측식은 `FROZEN_EXTERNAL_PACKET_E1.json` 안에 canonical JSON으로 저장되어 있다. 이 파일에서 `packet_sha256` 필드를 제거한 canonical JSON의 SHA-256이 위 hash와 같아야 한다.
## 외부 holdout 채점표
| target | frozen prediction | external observation/bound | z | status |
|---|---:|---:|---:|---|
| `Vus` | 0.226455 | 0.22501 | 2.126 | `pass_3sigma` |
| `Vcb` | 0.041872 | 0.04182 | 0.063 | `pass_3sigma` |
| `Vub` | 0.003871 | 0.003637 | 2.239 | `pass_3sigma` |
| `J_CKM` | 3.3716e-05 | 3.11949e-05 | 1.741 | `pass_3sigma` |
| `pmns_sin2_theta12` | 0.317172 | 0.308 | 0.798 | `pass_3sigma` |
| `pmns_sin2_theta13` | 0.023669 | 0.02215 | 2.664 | `pass_3sigma` |
| `pmns_sin2_theta23_IC24_SK_NO_local` | 0.551282 | 0.47 | 5.419 | `inside_3sigma_interval_but_fails_local_bestfit_z` |
| `delta_m21_sq_ev2` | 7.35294e-05 | 7.49e-05 | -0.721 | `pass_3sigma` |
| `abs_delta_m3l_sq_ev2` | 0.0025 | 0.002513 | -0.650 | `pass_3sigma` |
| `neutrino_ordering` | normal | normal |  | `pass_category` |
| `ms_over_mb_PDG2025_mixed_scale_diagnostic` | 0.025641 | 0.022352 | 16.876 | `diagnostic_fail_scheme_or_value` |
| `mc_over_mt_direct_PDG2025_diagnostic` | 0.00789 | 0.007377 | 17.212 | `diagnostic_fail_scheme_or_value` |
| `mc_over_mt_crosssection_MSbar_like_diagnostic` | 0.00789 | 0.007834 | 0.610 | `diagnostic_pass_but_not_certified` |
| `N_eff` | 3 | 2.99 | 0.059 | `pass_3sigma` |
| `Delta_N_eff` | 0 | -0.056 | 0.329 | `pass_3sigma` |
| `omega_cdm_h2` | 0.115385 | 0.12 | -4.615 | `fail_gt_3sigma` |
| `tau_p_to_e_pi0_years` | 4.75096e+38 | 2.4e+34 |  | `pass_lower_bound` |
| `M_intermediate_lightest_GeV` | 6.3389e+08 | 2600 |  | `pass_lower_bound` |
| `collider_lightest_new_state_GeV` | 6.3389e+08 | 2600 |  | `pass_lower_bound` |
| `S_new` | 0 | 0 | 0.000 | `pass_3sigma` |
| `T_new` | 0 | 0 | 0.000 | `pass_3sigma` |

## 실패 원인
1. `pmns_sin2_theta23`: NuFIT 6.0 IC24+SK normal-ordering local best-fit 중앙값 기준으로 약 5.42 sigma 떨어져 있다. 다만 3σ interval 안에는 있으므로 “octant/multimodal ambiguity 안에서 생존”이지, 정밀 blind hit는 아니다.
2. `omega_cdm_h2`: Planck base-LCDM의 cold dark matter density에 대해 약 -4.62 sigma로 낮다. 따라서 이 packet은 dark matter relic abundance를 해결하지 못한다.
3. `ms_over_mb`, `mc_over_mt`: packet이 renormalization scheme과 scale, threshold matching을 사전에 명시하지 않았다. 현재 채점에서는 diagnostic으로만 표시했고, scheme이 맞지 않는 경우 실패한다.
4. `alpha(0)`, charged lepton ratios, full Yukawa spectrum, full six-parameter LCDM vector는 예측하지 못했다.
## 엄밀한 학술 판정
이 결과는 “blind-predictive partial candidate”로는 가치가 있지만, **모든 SM+LCDM 파라미터의 완전 제1원리 유도**라고 쓸 수 없다. 논문 claim은 다음 수준이 정직하다.
> A frozen ISDLC-TCPS-Fnu-chi Cabibbo-clock packet gives nontrivial post-freeze agreement for CKM, several neutrino observables, N_eff, and high-scale threshold/proton-decay null bounds, but it fails publication-tier external validation because of theta23, dark matter relic abundance, and undefined mass-ratio scheme matching.
## 재현 명령
```bash
cd external_blind_validation_v1
python score_external.py
```
## 파일
- `FROZEN_EXTERNAL_PACKET_E1.json`: reveal 전 동결 packet
- `external_observations_E1.json`: reveal 후 외부 holdout tranche
- `external_score_E1.json`: 채점 결과
- `external_blind_scores_E1.csv`: 개별 score table
- `score_external.py`: hash 검증 + 재채점 스크립트

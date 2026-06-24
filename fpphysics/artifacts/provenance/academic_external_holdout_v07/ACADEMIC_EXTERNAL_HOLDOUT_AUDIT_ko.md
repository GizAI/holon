# Academic external freeze-before-reveal audit v0.7

## Bottom line
이 감사는 frozen packet을 수정하지 않고 새 외부 holdout tranche에 대입했다. 학계 방어 기준으로는 **부분 양성 신호는 있지만 엄격 성공은 아니다**.

- strict academic external verdict: `FAIL`
- complete SM+ΛCDM first-principles derivation: `False`
- precision numeric count: `5`
- reduced chi2 over precision external tranche: `2.3566`
- max |z|: `3.2997`

## Frozen packet integrity
- embedded packet hash: `74e16bedd02799dab4fb3322516dc3a4648233df5742f20b9ad4056cf06e32ad`
- canonical-without-embedded-sha hash: `74e16bedd02799dab4fb3322516dc3a4648233df5742f20b9ad4056cf06e32ad`
- raw file SHA256: `08cb6fcc767d547e9b5b7d8e19fcd6e499f9cce8e6d8766b911ba2b4e376b60f`
- source packet SHA256: `e0855d9ba75a7b58a66cadf60dcbcdedae18bf8e3bdd9eff63b8afe73af8aaaa`

## Strict external tranche results
| target | prediction | target / bound | z or ratio | status |
|---|---:|---:|---:|---|
| `CKM_abs_Vtd` | 0.00871069 | 0.00858 | z=0.687846 | `pass_3sigma` |
| `CKM_abs_Vts` | 0.0415329 | 0.04111 | z=0.549238 | `pass_3sigma` |
| `CKM_abs_Vtb` | 0.999116 | 0.999118 | z=-0.0735258 | `pass_3sigma` |
| `CKM_gamma_deg` | 66.7163 | 65.7 | z=0.338756 | `pass_3sigma` |
| `CKM_sin2beta` | 0.745297 | 0.709 | z=3.29969 | `fail_gt_3sigma` |
| `neutrino_sum_masses_eV` | 0.0585749 | < 0.12 | ratio=0.488124 | `pass_upper_bound` |
| `beta_decay_mbeta_eV` | 0.00905213 | < 0.45 | ratio=0.0201158 | `pass_upper_bound` |
| `proton_p_to_e_pi0_lifetime_years` | 8.516862e+37 | > 2.400000e+34 | ratio=3548.69 | `pass_lower_bound` |
| `lightest_new_charged_threshold_GeV` | 6.087500e+16 | not well-defined | not scored | `not_scoreable_academic` |
| `lightest_new_colored_threshold_GeV` | 6.087500e+16 | not well-defined | not scored | `not_scoreable_academic` |
| `quark_ms_over_mb_external` | 0.025641 | not well-defined | not scored | `not_scoreable_academic` |
| `quark_mc_over_mt_external` | 0.00788955 | not well-defined | not scored | `not_scoreable_academic` |

## Diagnostic rows, not counted as strict external tranche
| diagnostic | prediction | target | z | status |
|---|---:|---:|---:|---|
| `PMNS_sin2_theta12_diagnostic` | 0.317172 | 0.308 | 0.76431 | `diagnostic_pass_3sigma` |
| `PMNS_sin2_theta23_diagnostic` | 0.551282 | 0.47 | 4.7813 | `diagnostic_fail_gt_3sigma` |
| `PMNS_sin2_theta13_diagnostic` | 0.0236686 | 0.02215 | 2.71186 | `diagnostic_pass_3sigma` |
| `Omega_c_h2_formula_diagnostic` | 0.115385 | 0.12 | -4.61538 | `diagnostic_fail_gt_3sigma` |

## Interpretation
- CKM 외부 tranche에서 `Vtd`, `Vts`, `Vtb`, `gamma`는 3σ 안에 들어간다.
- `sin2beta`는 3σ를 넘는 실패다. CKM 전체의 publication-grade blind success라고 쓰면 안 된다.
- neutrino sum mass, beta-decay effective mass, proton lifetime은 lower/upper bound 통과지만 precision prediction 성공은 아니다.
- threshold spectrum은 표현/결합/붕괴모드가 지정되지 않아 collider bound와 학술적으로 채점할 수 없다.
- quark mass ratios는 common MSbar scale 및 threshold/RGE matching이 없어 채점에서 제외했다.
- 따라서 현재 얻은 것은 “동결된 후보의 부분 외부 검증”이지, 모든 SM+ΛCDM 파라미터의 완전 제1원리 유도 성공이 아니다.
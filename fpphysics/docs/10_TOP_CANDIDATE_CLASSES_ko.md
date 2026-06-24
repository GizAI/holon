# 10. Top Candidate Classes — 최종 후보군 3분류

이 문서는 최종 엔진 v1.0.1에서 가장 중요하게 보존해야 하는 세 후보군을 중복 없이 정리한 것이다. 세 후보군은 서로 다른 물리 영역을 담당하므로 MECE하게 분리한다.

## 요약 표

| rank | 후보군 | 수치 신호 | 학술 리스크 | 최종 판정 |
|---:|---|---:|---:|---|
| 1 | Cabibbo-clock flavor core | 높음 | 중간 | 가장 물리적 냄새가 남. CKM/PMNS 일부와 neutrino splitting에서 compact relation을 보이나, external holdout에서 \(\theta_{23}\), \(\Omega_c h^2\) 실패 및 charged-lepton/Yukawa full closure 미완성. |
| 2 | one-loop gauge-clock RGE 후보 | 높음 | 낮음~중간 | gauge coupling 쪽은 가장 구조화되어 있음. UV representation/spectrum과 threshold determinant가 실제로 나오면 강해짐. 현재는 one-loop/post-selected 후보와 ISDLC–TCPS tension을 구분해 보존. |
| 3 | 우주상수 exponential / instanton 후보 | 매우 높음 | 낮음 | \(\rho_\Lambda/M_{Pl}^4\) 크기를 놀랍게 맞추는 식이 있으나 action·prefactor·measure determinant 유도가 없으면 numerology 위험이 큼. |

## 1. Cabibbo-clock flavor core

### 포함 위치

- 코드: `fpphysics/blind_cabibbo.py`, `fpphysics/blind_cabibbo_cli.py`
- 예제: `examples/run_blind_cabibbo_clock.py`
- packet: `artifacts/packets/frozen_isdlc_tcps_fnu_chi_cabibbo_clock_packet.json`
- formula book: `artifacts/packets/cabibbo_clock_formula_book.json`
- 내부 blind 결과: `artifacts/results/internal_blind_cabibbo_results.json`
- 외부 holdout 결과: `artifacts/results/external_holdout_audit_v06_results.json`, `artifacts/results/academic_external_holdout_audit_v07_results.json`
- 점수표: `artifacts/tables/cabibbo_clock_blind_scores.csv`, `artifacts/tables/external_blind_holdout_scores.csv`, `artifacts/tables/academic_external_holdout_scores.csv`
- 설명 문서: `docs/04_RESULTS_MATRIX_ko.md`, `docs/06_EXTERNAL_HOLDOUT_AUDIT_ko.md`

### 왜 남길 가치가 있는가

Cabibbo-clock core는 단일 clock ratio에서 CKM/PMNS/neutrino splitting 일부를 산출하므로 단순 숫자놀음보다 물리적 구조의 냄새가 강하다. 특히 CKM의 \(|V_{cb}|, |V_{ub}|, J\)와 neutrino mass splitting은 compact formula로 꽤 좋은 신호를 보인다.

### 왜 아직 성공이 아닌가

외부 holdout에서 PMNS \(\theta_{23}\)와 \(\Omega_c h^2\)가 실패했고, \(\alpha(0)\), charged lepton mass ratios, full Yukawa texture, CP phases, resolved threshold spectrum은 닫히지 않았다. 따라서 논문에서는 "promising frozen flavor-core candidate"로만 써야 한다.

## 2. one-loop gauge-clock RGE 후보

### 포함 위치

- 코드: `fpphysics/rge.py`, `fpphysics/candidate_models.py`, `fpphysics/autodiscovery.py`, `fpphysics/theory_lab.py`
- 예제: `examples/validate_isdlc_tcps.py`, `examples/run_autodiscovery.py`, `examples/run_autodiscovery_focused.py`
- ISDLC–TCPS 결과: `artifacts/results/isdlc_tcps_validation_results.json`
- 자동발견 결과: `artifacts/results/autodiscovery_results.json`, `artifacts/results/theory_lab_results.json`
- 표: `artifacts/tables/isdlc_tcps_stress_scan.csv`, `artifacts/tables/autodiscovery_top_candidates.csv`, `artifacts/tables/theory_lab_candidates.csv`
- 설명 문서: `docs/03_MODEL_REGISTRY_ko.md`, `docs/04_RESULTS_MATRIX_ko.md`

### 왜 남길 가치가 있는가

Gauge sector는 RGE라는 표준 계산 구조가 확실하고, ISDLC–TCPS의 discrete clock + PS beta vector는 \(\alpha_s\)와 \(\sin^2\theta_W\)에 강한 신호를 보인다. 자동 discovery의 top one-loop gauge-clock 후보들도 수치적으로 매우 높다.

### 왜 아직 성공이 아닌가

자동 discovery의 최고 후보는 target-guided/post-selected 가능성이 크고, ISDLC–TCPS 자체도 \(\hat\alpha_{em}^{-1}(M_Z)\)에서 약 \(-2.8\sigma\) tension이 남는다. 학술적으로 강해지려면 high-scale beta vector와 threshold correction이 실제 UV spectrum, representation, determinant 계산에서 독립적으로 나와야 한다.

## 3. 우주상수 exponential / instanton 후보

### 포함 위치

- 코드: `fpphysics/cosmology.py`, `fpphysics/autodiscovery.py`, `fpphysics/theory_lab.py`
- 결과: `artifacts/results/baseline_strict_results.json`, `artifacts/results/autodiscovery_results.json`, `artifacts/results/theory_lab_results.json`, `artifacts/results/consolidated_summary.json`
- 설명 문서: `docs/00_EXECUTIVE_SUMMARY_ko.md`, `docs/03_MODEL_REGISTRY_ko.md`, `docs/04_RESULTS_MATRIX_ko.md`

### 왜 남길 가치가 있는가

Exponential/instanton ansatz는 \(\rho_\Lambda/M_{Pl}^4\sim 10^{-123}\)라는 극단적 스케일을 compact expression으로 근접하게 만든다. 이 점은 탐색 가치가 있다.

### 왜 아직 성공이 아닌가

현재는 action, prefactor, path-integral measure, zero-mode determinant가 microscopic theory에서 계산되지 않았다. 따라서 "예쁘지만 numerology 위험이 큰 후보"로 quarantine한다.

## 최종 사용 원칙

- 세 후보군은 모두 최종 엔진에 포함되어 있다.
- 논문 주장 강도는 `complete derivation`이 아니라 `auditable candidate ledger + falsification engine`으로 제한한다.
- 향후 연구 우선순위는 Cabibbo-clock flavor core와 gauge-clock UV spectrum closure다.
- 우주상수 exponential 후보는 determinant 유도 전까지 보조/부록 후보로 둔다.

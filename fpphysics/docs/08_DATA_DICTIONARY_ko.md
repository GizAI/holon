# 08. Data Dictionary

## `artifacts/results/`

| file | 의미 |
|---|---|
| `consolidated_summary.json` | 최종 기계판독 요약 |
| `baseline_strict_results.json` | 기본 후보 scoring 결과 |
| `isdlc_tcps_validation_results.json` | ISDLC–TCPS gauge/vacuum 검증 |
| `autodiscovery_results.json` | 자동 후보 생성 결과 |
| `theory_lab_results.json` | 고수준 theory lab 결과 |
| `blind_protocol_audit_results.json` | train/blind split 감사 |
| `internal_blind_cabibbo_results.json` | internal Cabibbo-clock blind 결과 |
| `external_holdout_audit_v06_results.json` | revealed external holdout 결과 |
| `academic_external_holdout_audit_v07_results.json` | strict academic external audit 결과 |

## `artifacts/tables/`

CSV score table과 candidate ranking을 저장한다. 논문 표 작성은 여기서 시작하면 된다.

## `artifacts/packets/`

frozen prediction packet과 formula book을 저장한다. 이 파일은 수정하면 hash가 바뀌므로 외부 검증에서 새 후보로 취급해야 한다.

## `artifacts/provenance/`

이전 파편화 파일들이 최종 구조 어디로 흡수되었는지와 SHA256 source hash를 저장한다.

| path | 의미 |
|---|---|
| `academic_external_holdout_v07/` | strict academic external audit의 pre-reveal freeze manifest, full report, original scorer |
| `external_audit_v06/` | v0.6 external audit의 all-frozen-packet sweep, revealed tranche, original scorer |
| `external_blind_validation_E1/` | earlier E1 freeze-before-reveal validation bundle; final verdict에는 직접 사용하지 않음 |

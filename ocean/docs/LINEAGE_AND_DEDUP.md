# Lineage and deduplication map

이 문서는 `/mnt/data`의 산출물을 중복 없이 최종 구조에 매핑한다.

| Source | 역할 | 최종 처리 |
|---|---|---|
| `isdlc-line-code-gauge-couplings-v0.2(1).md` | D5/ISDLC 원고 | D5 reference baseline으로 보존 |
| `붙여넣은 마크다운(1)(44).md` | microscopic realization 메모 | BHF closure/theorem 배경으로 흡수, 원문은 source inventory에 보존 |
| `holon-main (1).zip` | 외부 코드/검증 참고자료 | raw archive로 보존, 최종 canonical engine에는 직접 병합하지 않음 |
| `mcc_candidate_v0/` 및 zip | 첫 zero-base MCC | claim-labeling 원칙만 보존, 후보는 superseded |
| `ocean_zero_base_v1/` 및 zip | OCEAN validation | 최종 검증 코어로 보존 |
| `octu_v0_1/` 및 zip | OCTU field-content branch | 일부 beta/claim hygiene 보존, final gauge benchmark에서는 superseded |
| `cove_bc4_v0_1/` 및 zip | COVE-BC4 | 최종 BHF gauge benchmark로 승격 |
| `user-x.../_renders` | PDF preview images | source inventory에만 기록 |
| `bhf_ocean_final_v0_2/` | 현재 최종본 | canonical package |

## 중복 제거 원칙

- 기존 ZIP과 풀린 디렉터리는 둘 다 원천 자료로 기록하지만, 최종 패키지 안에 다시 복사하지 않는다.
- 최종 패키지는 새 canonical docs/code/output만 포함한다.
- 모든 legacy material은 `archive_index/source_inventory.*`에서 path, role, SHA-256으로 추적한다.
- 최종 논문은 여러 후보를 하나로 섞지 않고, D5를 reference, OCEAN을 검증 도구, BHF/COVE-BC4를 최종 후보로 역할 분리한다.

# 00. Executive Summary

## 최종 결론

\[
oxed{	ext{완전한 SM+}\Lambda	ext{CDM 제1원리 유도는 아직 인증되지 않았다.}}
\]

하지만 다음은 달성되었다.

- 미세구조상수, 표준모형 gauge coupling, 우주상수 후보를 엄격히 채점하는 파이썬 엔진 구축
- ISDLC–TCPS gauge-sector 예측의 재현 가능한 수치 검증
- 자동 후보 생성/탐색 엔진 구축
- train/validation/blind 관측량 분리와 prediction-packet SHA256 freeze 구현
- internal blind registry에서 강한 후보를 찾은 뒤, 외부 holdout으로 재검증하여 실패를 정직하게 기록
- 모든 산출물을 중복 없는 단일 저장소 구조로 정리

## 핵심 수치 상태

| 항목 | 최종 상태 |
|---|---|
| \(lpha(0)\) 독립 유도 | 실패 / 미완성 |
| ISDLC–TCPS gauge coupling | 부분 성공 + \(\hatlpha_{em}(M_Z)\) tension |
| 우주상수 instanton ansatz | 크기 근접, determinant 유도 없음 |
| 자동 발견 후보 | 생성 성공, post-selection quarantine |
| internal blind Cabibbo-clock | 내부 registry 통과 |
| 외부 holdout | 실패 |
| 모든 SM+ΛCDM 파라미터 | 미완성 |

## 논문에서 쓸 수 있는 정직한 claim

> We present an auditable Python framework for testing claimed first-principles derivations of Standard-Model and cosmological parameters. It finds compact candidate structures and falsifies overfitted claims through freeze-before-reveal holdout audits. No complete SM+ΛCDM first-principles derivation is certified.

## 논문에서 쓰면 안 되는 claim

- “미세구조상수를 완전히 제1원리에서 유도했다.”
- “모든 표준모형 파라미터를 유도했다.”
- “ISDLC–TCPS가 외부 blind prediction을 최종 통과했다.”
- “우주상수 문제를 해결했다.”

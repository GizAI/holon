# 최종 연구 저장소 인덱스

이 저장소는 지금까지의 모든 실험을 **하나의 최종 엔진**으로 정리한 버전이다. 이전 v0.3–v0.7 산출물은 다음 구조로 흡수되었다.

## 구조

```text
README.md
FINAL_VERDICT_ko.md
pyproject.toml
fpphysics/                 # 단일 엔진 코드
tests/                     # 회귀 테스트
examples/                  # 실행 예제
docs/                      # 연구 문서
papers/                    # 논문 초안
artifacts/results/         # canonical JSON 결과
artifacts/tables/          # canonical CSV 표
artifacts/packets/         # frozen prediction packets
artifacts/manifests/       # templates and manifests
artifacts/provenance/      # source hashes, legacy map, selected evidence
```

1. `00_EXECUTIVE_SUMMARY_ko.md` — 한눈에 보는 결론
2. `01_SCIENTIFIC_SCOPE_AND_STATUS_ko.md` — 무엇을 증명했고 무엇을 증명하지 못했는가
3. `02_ENGINE_ARCHITECTURE_ko.md` — 엔진 구조
4. `03_MODEL_REGISTRY_ko.md` — 후보 이론 목록과 상태
5. `04_RESULTS_MATRIX_ko.md` — 핵심 수치 결과
6. `05_BLIND_PROTOCOL_ko.md` — 과적합 차단/봉인 프로토콜
7. `06_EXTERNAL_HOLDOUT_AUDIT_ko.md` — 외부 holdout 재검증
8. `07_REPRODUCIBILITY_ko.md` — 재현 실행법
9. `08_DATA_DICTIONARY_ko.md` — 파일/데이터 사전
10. `09_RESEARCH_ROADMAP_ko.md` — 다음 연구 과제

최종 판정은 `artifacts/results/consolidated_summary.json`에 기계판독 형태로도 저장되어 있다.

- [10. Top Candidate Classes](10_TOP_CANDIDATE_CLASSES_ko.md) — Cabibbo-clock flavor core, one-loop gauge-clock RGE, 우주상수 exponential 후보 3분류 정리

- [11. 가장 놀라운 후보 이론 해설](11_SURPRISING_CANDIDATES_EXPLAINED_ko.md) — ISDLC–TCPS core, Cabibbo-clock, vacuum exponential, D7 자동 후보의 의미와 한계.

선별 provenance는 `artifacts/provenance/`에 둔다. full dump 전체가 아니라 pre-reveal manifest, external audit sweep, standalone scorer처럼 재현성과 증거성에 필요한 파일만 보존한다.

# BHF-OCEAN Final v0.2 정리본

생성 시각: 2026-06-26T02:09:55

이 폴더는 `/mnt/data`에 흩어진 ISDLC, MCC, OCEAN, OCTU, COVE-BC4, BHF closure 논의와 코드/출력물을 **중복 없이 하나의 최종 연구 패키지로 정리한 것**입니다.

## 최종 채택 구조

- **방법론 코어:** OCEAN - finite-code 후보를 사전 정의된 null-test와 enumeration으로 검증하는 감사 프레임워크.
- **최종 gauge benchmark:** BHF/COVE-BC4 - BC4 root/Fano flux/3:14 clock/최소 threshold hierarchy.
- **현상론 기준선:** D5/ISDLC/OCTU - 높은 수치 적중력을 가진 D5 reference이지만 DFC 미세보정과 선택규칙 문제가 있어 최종 이론이 아니라 비교 기준선으로 보존.
- **최종 논문 claim:** gauge-boundary selection + no-modulus closure theorem. `alpha(0)`, flavor, QCD-IR, EW scale은 아직 예측이 아니라 필수 closure module의 open target.

## 바로 볼 파일

1. `docs/FINAL_KO_COMPACT.md` - 전체 연구 압축본.
2. `manuscript/bhf_ocean_manuscript_v0_2.md` - 최초 투고용 논문 초안.
3. `docs/CLAIMS_LEDGER.md` - 증명/조건부/미해결 claim 분리.
4. `outputs/final_report.md` - 엔진 실행 리포트.
5. `outputs/final_predictions.csv` - D5 reference와 BHF final 수치 비교.
6. `archive_index/source_inventory.csv` - `/mnt/data` 전체 소스 인벤토리와 해시.

## 실행

```bash
python src/bhf_ocean_final_engine.py --outdir outputs
python -m pytest -q tests
```

현재 테스트 상태:

```text
...                                                                      [100%]
3 passed in 2.39s
```

## 가장 중요한 정직한 결론

BHF-OCEAN v0.2는 완성된 제1원리 TOE가 아닙니다. 현재 가장 강한 claim은 다음입니다.

> BHF-OCEAN은 OCEAN 검증 철학 아래, BC4-Fano gauge boundary와 최소 Pati-Salam threshold hierarchy를 하나의 finite Hamiltonian 선택 문제로 묶고, no-modulus 완성을 위해 flavor, QCD-IR, electroweak-scale 세 spectral module이 필연적으로 필요함을 보이는 연구 프로그램이다.

하지 않는 claim:

> `alpha(0)^-1 = 137.035999177`, fermion masses, CKM/PMNS, Higgs scale, cosmological constant를 이미 제1원리에서 유도했다.

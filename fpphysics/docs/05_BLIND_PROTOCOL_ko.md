# 05. Blind Prediction Protocol

## 목적

이미 알려진 gauge/cosmology benchmark를 보고 만든 수식은 논문 심사에서 후험선택 의심을 받는다. 이를 막기 위해 엔진은 관측량을 다음으로 분리한다.

- `train`: 후보 생성에 사용 가능
- `validation`: 개발 중 sanity check
- `blind`: 후보 freeze 전에는 값 사용 금지
- `external`: packet freeze 후 독립 공개 tranche

## 절차

1. 후보 이론 formula book 작성
2. prediction packet 생성
3. canonical JSON 직렬화
4. SHA256 hash 고정
5. holdout 값 reveal
6. frozen packet만 채점
7. 실패/누락/불완전 판정까지 기록

## abuse 방지

- packet이 holdout key를 training source로 선언하면 자동 무효
- `derived=False` 또는 `fitted=True`는 blind success에서 제외
- coverage가 낮으면 탈락
- post-hoc 수정은 새 모델명과 새 hash가 필요

## 현재 결과

internal registry를 통과한 후보는 있었지만, 외부 holdout에서 살아남은 후보는 없다.

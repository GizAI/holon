# 02. Engine Architecture

## 단일 패키지

모든 코드는 `fpphysics` 하나의 패키지 아래에 있다.

```text
fpphysics/
  constants.py                  # benchmark data and uncertainties
  sm.py                         # SM parameter-status audit
  rge.py                        # one-loop RGE utilities
  cosmology.py                  # Lambda-CDM inference
  candidate_models.py           # baseline and ISDLC-TCPS candidates
  engine.py                     # strict scoring and chi-square audit
  autodiscovery.py              # post-selected candidate generator
  theory_lab.py                 # high-level automatic theory lab
  blind_protocol.py             # train/blind split, leakage checks, packet freeze
  blind_cabibbo.py              # frozen Cabibbo-clock internal candidate
  academic_external_holdout.py  # strict external holdout scorer
  final_cli.py                  # single final workflow entrypoint
```

## 데이터 흐름

```text
benchmark constants
   ↓
strict scoring engine
   ↓
seeded candidates / autodiscovery / theory lab
   ↓
prediction packet freeze + SHA256
   ↓
blind registry scoring
   ↓
external holdout audit
   ↓
final verdict ledger
```

## 왜 여러 모듈이 있어도 “단일 엔진”인가

물리 기능별로 파일은 분리했지만, 실행·판정·산출물 구조는 하나다. 최상위 실행은 `python -m fpphysics.final_cli ...` 또는 `fpp-final ...`로 통일했다.

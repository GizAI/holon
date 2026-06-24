# 07. Reproducibility

## 설치

```bash
cd first_principles_physics_engine_final
python -m pip install -e '.[test]'
```

## 전체 테스트

```bash
python -m pytest -q
```

최종 패키지 생성 시점의 테스트 결과:

```text
26 passed
```

## 단일 final CLI

```bash
python -m fpphysics.final_cli status
python -m fpphysics.final_cli baseline --outdir run/baseline
python -m fpphysics.final_cli theory-lab --outdir run/theory_lab
python -m fpphysics.final_cli academic-holdout --outdir run/academic_holdout
python -m fpphysics.final_cli run-all --outdir run/final
```

설치 후 console script도 사용할 수 있다.

```bash
fpp-final status
fpp-final run-all --outdir run/final
```

## 주요 결과 파일

- `artifacts/results/consolidated_summary.json`
- `artifacts/results/isdlc_tcps_validation_results.json`
- `artifacts/results/internal_blind_cabibbo_results.json`
- `artifacts/results/external_holdout_audit_v06_results.json`
- `artifacts/results/academic_external_holdout_audit_v07_results.json`

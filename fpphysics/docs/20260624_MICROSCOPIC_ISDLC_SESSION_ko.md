# 2026-06-24 Microscopic ISDLC 세션 기록

## 목적

이번 세션의 목표는 ISDLC gauge-sector 연구를 단순 수치 맞춤에서 한 단계 올리는 것이었다. 핵심 요구는 다음이었다.

- \(40\), \(5\), \(3/2\), \(93/2\)를 Hamiltonian sector weight로 직접 넣지 않는다.
- D5 root count 공식을 직접 쓰지 않는다.
- local incidence rule과 constraint algebra에서 Hilbert space, cohomology, stiffness가 자동 산출되게 한다.
- 결과는 과장하지 않고 theorem-audit 상태로 분류한다.

## 이전 상태

`microscopic_lab.py`는 v1.2.0 audit lab으로서 유용했지만, \(\alpha_U^{-1}\) 경로에는 직접 count 성격이 남아 있었다.

```text
spin10_root_count() = 2 * 5 * (5 - 1)
D5_rank = 5
T3_second_betti_half = 3/2
stiffness = 40 + 5 + 3/2 = 93/2
```

이 구조는 내부 일관성 검증으로는 충분하지만, reviewer 관점에서는 “target에 맞는 group/topology count를 고른 것”이라는 공격을 피하기 어렵다.

## 변경한 구조

새 경로는 다음 순서로 계산된다.

```text
local incidence rule
  -> Cartan matrix
  -> integer vectors satisfying v^T C v = 2
  -> norm-two root enumeration
  -> Cartan rank
  -> one-cell torus cohomology
  -> stiffness = root_count + rank + dim H2 / 2
```

구현 위치:

- `fpphysics/microscopic_lab.py::local_incidence_rule`
- `fpphysics/microscopic_lab.py::cartan_from_incidence`
- `fpphysics/microscopic_lab.py::enumerate_norm_two_roots`
- `fpphysics/microscopic_lab.py::one_cell_torus_cohomology_dimension`
- `fpphysics/microscopic_lab.py::local_incidence_stiffness_components`

## 산출값

현재 local incidence rule은 “minimal trivalent simply-laced fork with one extended arm”이다. 이 rule에서 생성된 Cartan matrix에 대해 \(v^T C v = 2\)를 만족하는 integer vector를 열거하면 다음이 나온다.

```text
root_count = 40
rank = 5
betti_numbers = {H0: 1, H1: 3, H2: 3, H3: 1}
stiffness = 40 + 5 + 3/2 = 93/2
```

중요한 점은 `40`, `5`, `3/2`가 Hamiltonian 입력으로 들어가지 않고, incidence-derived Cartan/root enumeration/cohomology 결과로 들어간다는 것이다.

## Hamiltonian audit

finite non-diagonal Hamiltonian table도 같은 provenance를 사용하게 바꿨다. 즉 sector weight 이름은 D5 literal이 아니라 다음으로 바뀌었다.

```text
incidence_root_sector
cartan_rank_sector
torus_H2_half_sector
```

검증 실행에서 마지막 finite-size row는 다음 수준으로 수렴했다.

```text
curvature_last = 46.49992483382157
abs_error_last = 7.52e-05
```

이는 non-diagonal response가 incidence-derived stiffness와 일치함을 보여준다. 다만 아직 C 등급 theorem이라고 부르지는 않는다. Hamiltonian의 local incidence rule 자체가 더 깊은 microscopic action에서 유일하게 나와야 한다.

## dependency graph / leakage 판정

변경 후 dependency graph는 다음을 명시한다.

- \(\alpha_U^{-1}\) observed value는 `local_incidence_rule -> cartan_matrix -> norm_two_root_enumeration / rank / torus_cohomology`에서 나온다.
- \(\alpha_U^{-1}=93/2\) target literal은 pass/fail comparison으로만 남는다.
- 남은 leakage risk는 “minimal trivalent fork rule” 선택이다.

따라서 현재 판정은 다음이다.

```text
이전: A/B 사이, count-derived conditional audit
현재: 더 명확한 B, finite complex / incidence theorem-audit
아직 아님: C, uniquely derived non-diagonal microscopic Hamiltonian theorem
아직 아님: D, scheme-complete physical prediction
```

## 테스트

추가된 테스트:

- `test_local_incidence_rule_forces_stiffness_components`
  - root count, rank, H2, stiffness가 local incidence path에서 산출되는지 확인한다.
- 기존 tiny CPU lab run 테스트에 `incidence_provenance.root_count` 검증을 추가했다.

검증 결과:

```text
PYTHONPATH=. python -m pytest -q
31 passed

git diff --check
pass
```

## 보존한 것

`artifacts/results/microscopic_isdlc_lab/v1.2.0_final`의 기존 5B GPU null-scan artifact는 덮어쓰지 않았다. 중간에 128-candidate smoke run으로 artifact가 갱신될 뻔했지만, 이는 릴리스 품질을 낮추는 변경이므로 복구했다.

## 남은 과제

1. local incidence rule을 더 근본적인 microscopic line-code action에서 유일하게 도출해야 한다.
2. TCPS \(6:13\)은 아직 clock input이다. 같은 Hamiltonian의 eigenvalue/spectral theorem으로 올려야 한다.
3. LCI/DFC는 regulator/cohomology audit은 강화됐지만, protected labels와 block entries의 origin theorem이 필요하다.
4. physical prediction 등급으로 가려면 two-loop, threshold, scheme/covariance matching이 필요하다.

## 결론

이번 세션의 실제 진전은 “숫자를 더 맞춘 것”이 아니다. \(40\), \(5\), \(3/2\), \(93/2\)를 직접 sector weight로 넣던 경로를 제거하고, local incidence와 constraint algebra의 계산 산물로 바꾼 것이다.

이것은 학계 인정 수준의 완성 증명은 아니지만, target leakage audit 관점에서는 의미 있는 구조 개선이다.

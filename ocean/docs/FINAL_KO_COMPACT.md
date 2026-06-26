# 최종 압축 정리: BHF-OCEAN v0.2

## 0. 정리 원칙

이번 최종본은 지금까지의 모든 산출물을 하나의 계층으로 정리한다. 중복된 후보는 제거하고, 역할이 다른 것은 분리한다. 최종 형태는 **OCEAN 검증 프레임워크 + BHF/COVE-BC4 gauge benchmark + no-modulus closure theorem**이다.

- **ISDLC/D5 v0.2:** 원래의 정밀 gauge-coupling 후보. 수치 적중력은 높지만 DFC 미세보정과 microscopic 선택규칙이 약하다. 최종본에서는 reference baseline으로 보존한다.
- **MCC:** claim hygiene와 `prediction/target/open` 라벨링을 도입한 첫 zero-base 패키지. 개념은 보존하되 후보 자체는 superseded.
- **OCEAN:** 가장 중요한 방법론 산출물. 작은 정수 후보들을 열거하고 null-test를 수행해, D5가 유일하지 않음을 보였다. 최종본의 검증 코어다.
- **OCTU:** field-content와 threshold 구현을 명시하려는 중간 버전. 일부 산술과 claim hygiene는 보존하되 최종 구조는 COVE/BHF로 통합한다.
- **COVE-BC4:** OCEAN에서 D5 reference보다 더 좋은 arithmetic score를 얻은 BC4 후보. 최종 gauge benchmark로 채택한다.
- **BHF closure theorem:** BC4, flux 7, clock 3:14, threshold hierarchy를 하나의 finite Hamiltonian 선택 문제로 묶고, 남은 상수에는 flavor/QCD-IR/EW 세 closure module이 필연적으로 필요함을 정리한다.

## 1. 최종 이론 이름과 핵심 claim

최종 명칭은 **BHF-OCEAN v0.2**이다.

- BHF = BC4-Hamming-Fano finite boundary Hamiltonian.
- OCEAN = Occam Enumeration and Null-test framework.

핵심 claim은 낮고 단단하게 잡는다.

> BHF-OCEAN은 표준모형 gauge-coupling pattern을 finite boundary-code 선택 문제로 압축하고, no-modulus 완성을 위해 flavor, QCD-infrared, electroweak-scale 세 spectral module이 필연적으로 필요함을 보이는 조건부 연구 프로그램이다.

## 2. 최종 canonical gauge benchmark: BHF/COVE-BC4

```text
root class        = BC4
root count        = 32
rank              = 4
Fano flux count   = 7
alpha_U^-1        = 32 + 4 + 7/2 = 39.5
M_U               = Mbar_Pl / 32
clock             = 3:14
Pati-Salam beta   = (1/2, 9/2, 3/2)
DFC               = none
```

엔진 출력:

```text
M_U                         = 7.609375000000e+16 GeV
M_I                         = 1.770754777584e+14 GeV
alpha_em^-1(MZ)             = 127.956742827056
sin2_MSbar(MZ)              = 0.231188712312
alpha_s(MZ)                 = 0.118205763021
alpha0 residual QCD+EW      = 4.773458085764
K_IR target                 = 43.270062333201
```

이 수치는 formal one-loop benchmark다. 12자리 숫자는 엔진 산술 정밀도이지 물리 예측 오차가 아니다.

## 3. D5/ISDLC reference의 위치

D5 reference는 폐기하지 않는다. 최종본에서는 비교 기준선으로 둔다.

```text
alpha_em^-1(MZ)   = 127.928418368491
sin2_MSbar(MZ)    = 0.231223633775
alpha_s(MZ)       = 0.118000699956
```

D5는 electroweak/strong coupling 수치가 매우 좋지만, OCEAN scan에서 BC4라는 rival이 나왔기 때문에 “유일한 제1원리 유도”라고 주장하면 안 된다.

## 4. BHF 선택 정리

1. rank-4 irreducible crystallographic root class 중 electric/magnetic boundary completeness를 요구하면 simply-laced `A4,D4`가 제거된다.
2. Langlands-dual closure로 `B4~C4`를 하나의 `BC4` class로 본다.
3. 남은 non-simply-laced 후보 `BC4,F4` 중 root count가 최소인 것은 `BC4`다.
4. boundary flux는 `F_2^3`의 nonzero sector이므로 `2^3-1=7`이다.
5. clock은 generator/return pair이므로 `3:2*7=3:14`다.
6. threshold occupation vector는 beta-charge closure와 microscopic dimension minimality로 선택된다.

Threshold certificate:

```text
target charge6                       = [67, 45, 27]
number of nonnegative integer sols   = 1792
minimal dimension                    = 62
number of minimizers                 = 1
unique minimizer                     = [1, 1, 1, 1, 1, 1, 2, 2, 1]
```

따라서 threshold hierarchy는 BHF 내부에서는 유일한 ground state다.

## 5. 미세구조상수 137.035999의 상태

`alpha(0)^-1 = 137.035999177`은 아직 예측값이 아니다. 최종본에서 이것은 QCD+EW infrared spectral closure가 유도해야 할 target이다.

```text
alpha(0)^-1 = alpha_em^-1(MZ) + Delta_lepton + Delta_QCD+EW
```

BHF/COVE-BC4 기준:

```text
alpha_em^-1(MZ)      = 127.956742827056
Delta_lepton bridge  = 4.305798264180
Delta_QCD+EW target  = 4.773458085764
```

이 target을 실제 QCD/hadronic spectral operator에서 계산하기 전까지는 alpha(0)를 유도했다고 쓰면 안 된다.

## 6. 최종 논문 claim 구조

최초 투고용 논문 제목은 다음이 안전하다.

**A finite boundary-code closure theorem for Standard Model constants**

논문에서 말할 수 있는 것:

- BC4-Fano gauge boundary와 최소 threshold hierarchy의 finite selection theorem.
- formal one-loop gauge benchmark.
- no-modulus 완성 조건에서 flavor, QCD-IR, EW-scale 세 spectral module의 필연성.
- 기존 상수 numerology를 피하기 위한 OCEAN null-test와 source inventory.

논문에서 말하면 안 되는 것:

- fine-structure constant를 이미 제1원리에서 유도했다.
- fermion masses, CKM/PMNS, Higgs scale, cosmological constant를 이미 유도했다.
- BHF Hamiltonian이 자연의 최종 Hamiltonian임을 증명했다.

## 7. 최종 상태판

| 항목 | 최종 상태 |
|---|---|
| D5/ISDLC | reference baseline, not final |
| MCC | superseded hygiene prototype |
| OCEAN | final validation core |
| OCTU | superseded field-content branch |
| COVE-BC4 | final gauge benchmark |
| BHF | final microscopic selection architecture |
| alpha(0) | target, not prediction |
| Flavor masses/mixings | required closure module, open |
| QCD-IR bridge | required closure module, open |
| EW scale | required closure module, open |
| 최종 주장 강도 | conditional finite-code research program |

## 8. 다음 단계

1. BHF primitive threshold block space를 더 넓혀도 dimension-minimal uniqueness가 유지되는지 OCEAN v2로 검증한다.
2. two-loop RGE, heavy threshold, scheme conversion을 넣어 gauge benchmark의 실제 오차예산을 계산한다.
3. flavor spectral module의 operator를 사전등록하고 charged-lepton/quark/CKM/PMNS를 holdout 방식으로 예측한다.
4. QCD-IR spectral module로 `Delta_QCD+EW` target을 계산한다.
5. EW module로 `v`, `m_H`, Higgs quartic을 유도한다.

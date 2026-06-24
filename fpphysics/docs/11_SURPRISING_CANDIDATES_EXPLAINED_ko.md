# 11. 가장 놀라운 후보 이론 해설

이 문서는 최종 엔진에 남긴 후보들 중 “버릴 수 없는 이상한 신호”를 보인 후보들을 해설한다. 목적은 성공 선언이 아니라, 새 연구자가 어디에 집중해야 하는지 빠르게 파악하게 하는 것이다.

## 결론 요약

현재까지의 후보 중 **학술적으로 가장 진지한 후보**는 `ISDLC–TCPS gauge-sector core`이고, **숫자적으로 가장 섬뜩한 후보**는 `ISDLC–TCPS-Fνχ Cabibbo-clock extension`이다. 그러나 둘 다 아직 완전한 제1원리 이론으로 인증되지는 않았다.

| 순위 | 후보 | 놀라운 점 | 실패/리스크 | 보존 이유 |
|---:|---|---|---|---|
| 1 | ISDLC–TCPS gauge-sector core | Spin(10)/Pati–Salam/SM clock 구조에서 \(\alpha_s\), \(\sin^2\theta_W\)가 자연스럽게 가까워짐 | \(\hat\alpha_{em}^{-1}(M_Z)\) 약 \(-2.8\sigma\) tension, threshold 미완성 | 가장 “물리 이론”처럼 보이는 구조 |
| 2 | Cabibbo-clock flavor extension | 동일한 \(6:13\) clock에서 CKM scale과 PMNS 일부가 나옴 | 외부 holdout에서 \(\theta_{23}\), \(\Omega_c h^2\) 실패 | 우연으로 치부하기엔 compact relation이 강함 |
| 3 | Vacuum exponential / instanton ansatz | \(10^{-123}\) 우주상수 스케일을 짧은 식으로 근접 재현 | action/prefactor/determinant 미유도 | QFT/path-integral closure 과제로 가치 있음 |
| 4 | 자동 발견 D7 one-loop 후보 | gauge coupling 세 개를 매우 잘 맞춤 | target-guided/post-hoc 가능성 큼 | “어떤 UV beta vector가 필요한가”를 알려주는 역문제 단서 |

---

## 1. ISDLC–TCPS gauge-sector core

### 핵심 아이디어

ISDLC–TCPS core는 다음 네 개의 구조적 입력을 사용한다.

\[
\alpha_U^{-1}=\frac{93}{2},
\qquad
M_U=\frac{\bar M_{Pl}}{40},
\qquad
\ln(M_U/M_I):\ln(M_I/M_Z)=6:13,
\qquad
b^{PS}=(-7,-3,+2).
\]

여기서 중요한 점은 단순히 숫자를 넣은 것이 아니라, 각각이 다음 해석을 가진다는 것이다.

- \(40\): \(D_5\) root/discriminant 또는 Spin(10) 계열 discrete index로 해석되는 수.
- \(93/2\): \(40+5+3/2\) 형태의 half-clock unified inverse coupling.
- \(6\): Standard Model \(\mathbb Z_6\) quotient와 연결되는 clock order.
- \(13\): Pati–Salam breaking clock으로 쓰인 폐곡선/line-operator count.
- \((-7,-3,+2)\): intermediate Pati–Salam 구간의 beta-vector.

### 왜 놀라운가

이 구조에서 1-loop RGE를 돌리면 대략 다음 값이 나온다.

\[
\hat\alpha_{em}^{-1}(M_Z)\approx127.9077,
\qquad
\sin^2\hat\theta_W(M_Z)\approx0.231279,
\qquad
\alpha_s(M_Z)\approx0.11805.
\]

특히 \(\alpha_s\)와 \(\sin^2\theta_W\)는 매우 가까운 편이다. Gauge sector는 표준적인 RGE 계산 구조가 있으므로, 후보 이론 중 가장 “학계가 검산할 수 있는 형태”에 가깝다.

### 왜 아직 성공이 아닌가

- \(\hat\alpha_{em}^{-1}(M_Z)\)가 기준값 대비 약 \(-2.8\sigma\) 낮다.
- \(b^{PS}=(-7,-3,+2)\)가 실제 UV spectrum에서 유일하게 나오는지 아직 완전히 보이지 않았다.
- 2-loop, threshold determinant, electroweak matching, scheme conversion이 닫히지 않았다.
- \(\alpha(0)\)까지 독립 유도하지 못한다.

### 다음 연구 질문

1. \((-7,-3,+2)\)를 실제 Pati–Salam representation content의 finite determinant에서 유도할 수 있는가?
2. \(-2.8\sigma\) electromagnetic tension을 threshold correction으로 자연스럽게 해소할 수 있는가?
3. 같은 discrete data가 flavor sector에도 독립적으로 나타나는가?

---

## 2. ISDLC–TCPS-Fνχ Cabibbo-clock extension

### 핵심 아이디어

이 후보는 gauge-sector의 clock ratio를 flavor sector에 재사용한다.

\[
r=\frac{6}{13},
\qquad
\lambda_C=\frac{\sqrt r}{3}.
\]

그러면

\[
\lambda_C\approx0.226455
\]

가 되어 Cabibbo angle scale 근처에 놓인다. 여기서 다음 compact formula를 둔다.

\[
V_{us}=\lambda_C,
\qquad
V_{cb}=\sqrt{\frac{2}{3}}\lambda_C^2,
\qquad
V_{ub}=\frac{\lambda_C^3}{3},
\qquad
J_{CKM}=\frac{\lambda_C^6}{4}.
\]

PMNS 쪽도 같은 \(r\)과 \(\lambda_C\)에서 일부가 생성된다.

\[
\sin^2\theta_{13}=r\lambda_C^2=\frac{r^2}{9},
\]

\[
\sin^2\theta_{12}=\frac{1-3\sin^2\theta_{13}}{3(1-\sin^2\theta_{13})},
\qquad
\sin^2\theta_{23}=\frac12+\lambda_C^2.
\]

### 왜 놀라운가

가장 섬뜩한 점은 \(6:13\)이 원래 gauge running clock에서 등장했는데, 같은 ratio가 flavor mixing의 작은 parameter로도 작동한다는 것이다. 특히 \(\lambda_C=\sqrt{6/13}/3\)는 손으로 끼워 맞춘 복잡한 식이 아니라 매우 짧은 식이다.

엔진 내부 blind registry에서는 CKM, PMNS 일부, 중성미자 질량차, threshold bound, \(N_{eff}\) 등 여러 항목을 동시에 맞히는 것처럼 보였다. 그래서 이 후보는 “완전 성공”은 아니어도 가장 주목할 만한 flavor-core 신호로 남겨야 한다.

### 외부 holdout에서 왜 실패했나

외부 holdout에서는 다음이 문제였다.

- PMNS \(\sin^2\theta_{23}\)가 NuFIT comprehensive branch 기준에서 크게 어긋났다.
- \(\Omega_c h^2=r/4\)가 Planck 기준보다 약 \(-4.6\sigma\) 낮았다.
- \(\alpha(0)\), charged-lepton mass ratios, full Yukawa texture, CP phases가 없다.

따라서 이 후보를 “blind prediction 성공 이론”이라고 쓰면 안 된다. 정확한 표현은 다음이다.

> A compact frozen flavor-core candidate with nontrivial CKM/PMNS/neutrino-splitting signals, but externally falsified in the \(\theta_{23}\) and dark-matter-density channels.

### 다음 연구 질문

1. \(\theta_{23}\)의 octant 구조가 별도 discrete choice에서 나와야 하는가?
2. \(\Omega_c h^2=r/4\)는 버려야 하는가, 아니면 dark-sector freeze-out 계산으로 교체해야 하는가?
3. charged lepton mass ratios가 같은 clock algebra에서 독립적으로 나올 수 있는가?

중요: 기존 frozen packet은 수정하면 안 된다. 새 해석은 반드시 새 모델명과 새 hash로 시작해야 한다.

---

## 3. Vacuum exponential / instanton ansatz

### 핵심 아이디어

우주상수 후보들은 대체로 다음 꼴이다.

\[
\rho_\Lambda/M_{Pl}^4=C\exp(-S).
\]

ISDLC 계열에서는 예를 들어

\[
\rho_\Lambda/M_{Pl}^4=(4\pi)^4 e^{-93\pi}
\]

같은 식이 등장했다. 자동 탐색에서는 유사한 exponential ansatz들이 \(10^{-123}\) 스케일에 매우 가까이 접근했다.

### 왜 놀라운가

우주상수 문제는 약 \(10^{-123}\)라는 극단적인 hierarchy를 요구한다. 이 정도 스케일을 짧은 exponential 식으로 근접하게 만드는 것은 연구 단서로는 가치가 있다.

특히 \(93\)이 gauge-sector의 \(\alpha_U^{-1}=93/2\)와 연결될 가능성이 있다는 점이 흥미롭다. 즉,

\[
2\alpha_U^{-1}=93
\]

이 vacuum action의 coefficient처럼 나타나는 구조는 그냥 버리기 아깝다.

### 왜 아직 성공이 아닌가

- \(S=93\pi\)가 실제 Euclidean action인지 유도되지 않았다.
- \((4\pi)^4\) prefactor가 zero-mode/determinant/measure에서 계산되지 않았다.
- vacuum energy normalization이 모형마다 달라질 수 있다.
- DESI/Planck 계열 관측에서 dark energy가 정확한 constant인지도 계속 검증 중이다.

따라서 이 후보는 “numerology 위험이 큰 quarantine 후보”로 남긴다.

---

## 4. 자동 발견 D7 one-loop gauge 후보

### 핵심 아이디어

자동 탐색기는 gauge benchmark를 매우 잘 맞히는 후보를 찾았다. 대표적으로 \(D_7\) 계열 root data, Planck divisor, clock ratio, rational beta-vector를 조합한 one-loop RGE 후보가 있었다.

### 왜 놀라운가

세 gauge coupling을 동시에 매우 작은 residual로 맞힐 수 있었다. 이 후보는 “어떤 beta-vector와 scale 구조가 있으면 관측값에 도달하는가”라는 역문제 관점에서 유용하다.

### 왜 가장 위험한가

이 후보는 target-guided/post-hoc 가능성이 가장 크다. 즉, 수치적으로는 압도적이어도 학술적으로는 가장 취약할 수 있다.

이 후보의 올바른 사용법은 다음이다.

- 성공 이론으로 제시하지 않는다.
- UV model builder에게 필요한 beta-vector/spectrum 힌트로만 제공한다.
- 동일 구조가 blind observable을 추가로 맞히기 전까지 quarantine한다.

---

## 비교 판정

| 평가축 | ISDLC–TCPS gauge core | Cabibbo-clock flavor | Vacuum exponential | D7 auto-discovery |
|---|---:|---:|---:|---:|
| 구조적 단순성 | 높음 | 높음 | 높음 | 중간 |
| 표준 계산 가능성 | 높음 | 중간 | 낮음 | 높음 |
| blind/external 상태 | tension | external fail | 미검증/미유도 | post-hoc quarantine |
| 논문 본문 가치 | 높음 | 중간~높음 | 낮음~중간 | 낮음 |
| 부록/탐색 ledger 가치 | 높음 | 높음 | 높음 | 높음 |

## 최종 해설

가장 놀라운 신호는 다음 한 줄로 요약된다.

\[
\boxed{6:13\ \text{clock이 gauge running과 flavor mixing 양쪽에서 반복적으로 나타난다.}}
\]

그러나 “절대 우연일 수 없다”라고 주장하려면 아직 부족하다. 다중 후보 탐색을 했기 때문에 look-elsewhere effect가 존재한다. 정직한 논문 전략은 다음이다.

1. ISDLC–TCPS gauge core를 본문 핵심 후보로 둔다.
2. Cabibbo-clock은 frozen flavor-core signal로 별도 섹션 또는 companion note에 둔다.
3. Vacuum exponential은 부록의 speculative clue로 둔다.
4. D7 자동 후보는 model-building hint로만 둔다.
5. 다음 외부 tranche에서 새 hash로 다시 freeze-before-reveal 검증한다.

현재 상태의 가장 안전한 논문 문장은 다음이다.

> The study identifies a nontrivial recurrent \(6:13\) clock pattern appearing in both one-loop gauge running and compact flavor-mixing ansätze. While no candidate is certified as a complete first-principles derivation, the recurrence is sufficiently structured to motivate a preregistered next-round blind test.

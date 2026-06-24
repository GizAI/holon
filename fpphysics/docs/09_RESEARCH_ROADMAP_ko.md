# 09. Research Roadmap

## 우선순위 1: true blind 가능한 새 예측

기존 packet을 고치지 말고, 새 모델은 별도 hash로 freeze해야 한다. 가장 가치 있는 target은 다음이다.

1. \(lpha(0)\) — charged thresholds + hadronic vacuum polarization + EW matching 독립 계산
2. charged lepton mass ratios — \(m_e/m_\mu\), \(m_\mu/m_	au\)
3. CKM CP sector — \(\sin 2eta\), \(\gamma\), Jarlskog 동시 예측
4. PMNS octant/CP — \(	heta_{23}\), \(\delta_{CP}\)
5. resolved threshold spectrum — representation, mass, coupling, decay mode까지 지정
6. dark sector — \(\Omega_c h^2\)를 Boltzmann equation으로 계산

## 우선순위 2: microscopic action

현재 가장 큰 결손은 formula가 아니라 action이다. 필요한 것은 다음이다.

- UV gauge group and representation generator
- anomaly cancellation checker
- Yukawa/flavour texture generator
- seesaw/neutrino mass module
- threshold/matching calculator
- proton-decay operator estimator
- dark-matter relic solver
- collider likelihood interface

## 우선순위 3: 외부 holdout 반복

새 packet은 다음 공개 데이터 release 전 freeze해야 한다. 이후 PDG/NuFIT/Planck-DESI 등 새 tranche가 공개되면 수정 없이 채점한다.

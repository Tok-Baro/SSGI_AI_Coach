# QA Round 2 — Part A: 6명 페르소나 7~28일 여정 시뮬레이션

검증일: 2026-05-07. 정적 코드 매칭 + ADR 정책 비교

## 핵심 코드 사실 (검증)
- 알림 우선순위 (`notification_service.py`): kakao `send_to_me` (talk/memo/default/send, **본인에게만**) → FCM → log only
- **알림톡(친구톡) 채널 발송 코드 부재** — ADR 004의 "Kakao" 사실상 "카카오 메모(나에게)"
- 결제 UI: `types/index.ts`에 `plan_tier: "free" | "pro"` 타입만. **결제 페이지·페이월·CTA 전부 부재**

## 1. 6명 페르소나 7-day journey 요약

### P001 종로 백반집 60세 카톡만 7y+ 매출감소 (C01-1)
- Day 0 가입 50% (사업자등록증 찾기 + 10자리 입력 부담)
- Day 1 푸시 클릭 8% — "나에게" 채널 미인지
- Day 3 SurvivalMatrix "패턴 유사도 47%"를 "내 폐업 확률 47%"로 오해 → 분노/공포 → 앱 삭제 30% 가능성
- D7 8%, D28 2%, NPS -40 (Detractor "어려워서 못 써")
- **핵심 막힘**: 카카오 "나에게 보내기" 채널 미인지 (코드 vs 사용자 멘탈 모델 충돌)

### P002 마포 카페 32세 SNS 1년차 마케팅 (C03-1)
- Day 0 가입 88%, 첫 가치 80초
- Day 1 FCM 권한 허용, 푸시 클릭 60%
- Day 3 /insights/marketing fit_score=87, ROI=240% 처음엔 흥분 → 출처 안 보여 의심 증폭
- D7 55%, D28 28% (PDF fatigue), NPS +10
- **핵심 막힘**: /marketing GPT 환각 — 마케팅 직군 ROAS 검증 일상

### P008 마포 치킨 38세 배달앱 2년차 (C02-1)
- Day 0 82%, 첫 가치 100초
- Day 1 안드로이드 FCM 즉시 클릭 55%. 그러나 today_action "배달 광고비 12%"가 loss_counter `/365` 환산일 뿐 → 배민 어드민 실제와 불일치
- Day 3 /insights/competition 만족 (95% REAL Seoul)
- Day 7 budget_scenarios 30만원 → "매출 X원 추가" 환각, 1회 시도 후 무시
- D28 22%, NPS 0
- **핵심 막힘**: 배민 어드민과 본 앱 데이터 단절

### P020 관악 문구점 58세 카톡만 폐업위험 (C08-3) — **🔴 도덕적 위험**
- Day 0 가입 38% — 빨간 카피 3연속에 "사기 의심"
- Day 1 푸시 클릭 12% — P001과 같은 채널 도달 문제
- **Day 3 SurvivalMatrixCard "위험: critical, 패턴 유사도 80%"** 보면 **자살 관련 우려까지 갈 수 있음**. 회피 행동 (앱 삭제) 유발
- D7 5%, D28 1%, NPS -60
- **핵심 막힘**: ADR 001 손실 프레이밍을 시니어·폐업위험 세그먼트에 무차별 적용한 부메랑

### P022 강남 카페 35세 데이터분석 (C16) 
- Day 0 92%, 평가관 마인드로 가입
- Day 1 FactorBar description prose만 보고 "블랙박스" 평가
- Day 3 peer_percentile k=10 정직, 그러나 /marketing fit_score 87/ROI 240% **3분 만에 GPT 환각 간파**
- Day 7 PDF는 노션에 첨부. SWOT/TOWS "수준 낮음" 평가
- D7 50%, D28 18% (CSV/API export 부재가 결정타), NPS -10
- **핵심 막힘**: /marketing GPT 환각 + 데이터 export 부재

### P024 연남 미용실 30대 SNS 마케팅 (C09-3)
- Day 0 90%, 60초 가입
- Day 1 푸시 클릭 70% — UpliftCard 시각화 호감
- Day 3 budget_scenarios 3종 다 시도 → 결과 반영 루프 없음. CopyVariantsCard는 인스타 캡션 즉시 복붙 가치
- Day 7 60%, QR 쿠폰 인스타 스토리 1회 → REAL DB 기반 스캔 카운터 = **유일하게 검증된 가치**
- D28 35%, NPS +20
- **핵심 막힘**: GPT 카피 다양성 부족 (Few-shot 부재) → fatigue

## 2. 종합 retention 표

| 페르소나 | D0 가입 | D1 푸시 클릭 | D3 재방문 | D7 retention | D28 retention | 프로 전환 | NPS |
|---|---|---|---|---|---|---|---|
| P001 60세 백반 | 50% | 8% | 18% | 8% | 2% | 0% | -40 |
| P002 32세 카페 | 88% | 60% | 70% | 55% | 28% | 0% | +10 |
| P008 38세 치킨 | 82% | 55% | 65% | 50% | 22% | 0% | 0 |
| P020 58세 폐업위험 | 38% | 12% | 22% | 5% | 1% | 0% | -60 |
| P022 35세 데이터족 | 92% | 80% | 75% | 50% | 18% | 0% | -10 |
| P024 30대 미용 | 90% | 70% | 75% | 60% | 35% | 0% | +20 |
| **평균** | **73%** | **48%** | **54%** | **38%** | **18%** | **0%** | **-13** |

**INV1 김도윤 합격 기준**: D30 ≥ 25% → **FAIL** (평균 18%)
**INV1 액션 완수율 ≥ 40%**: 추정 25-30% → FAIL

## 3. 핵심 막힘 6건

| # | 페르소나 | 페이지/컴포넌트 | 막힘 원인 |
|---|---|---|---|
| 1 | P001 60세 | `/onboarding` Step1 input maxLength=10 | 시니어 폰트·OCR 미적용 |
| 2 | P002 32세 마케팅 | `/insights` marketing fit_score/ROI | GPT 환각 즉시 간파 |
| 3 | P008 38세 배달 | dashboard `loss_counter` ÷365 | 배민 실데이터 미연동 |
| 4 | **P020 58세 폐업위험** | **`SurvivalMatrixCard` critical + 빨간 카피** | **공포 자극 3연속, 폐업/재기 의사결정 트리 부재** |
| 5 | P022 35세 데이터 | `FactorBar` description prose | 가중치/공식/원시값 미공개, CSV export 없음 |
| 6 | P024 30대 마케팅 | `CopyVariantsCard` 3개 톤 | Few-shot 부족, fatigue |

## 4. 손실 프레이밍 효과 검증 (ADR 001)

행동경제학 (Kahneman prospect theory): 손실 프레이밍은 얻을 것 대비 약 2배 행동 동기. **단, 조건**:
1. 손실 수치 **검증 가능**해야 함 — 본 앱 total_potential_amount는 매칭 SEED max_amount 합계 (이론 최대치). 사장님 실제 수령 가능성 30% 이하 (지원사업 경쟁률)
2. **귀속**이 사장 본인 → 책임 가능 행동 — `/coupons` 만들기는 OK, **SurvivalMatrixCard 폐업 패턴**은 사장 책임 행동 막연
3. **시니어에게 부메랑** — P001·P020에서 신뢰 붕괴. 강유나 "정중한 알림" 톤 다운 부재

| 페르소나 | 손실 프레이밍 효과 |
|---|---|
| P001 60세 | **부정** — 사기 의심 |
| P002 32세 | 긍정 — "지금 신청해야겠다" |
| P008 38세 | 중립 — 환각이 신뢰 균열 |
| P020 58세 폐업위험 | **위험** — 회피 행동, 잠재 정신건강 우려 |
| P022 35세 | 중립 — 검증 불가 판단 |
| P024 30대 | 긍정 — 한번 시도 |

**6명 중 2명 긍정, 2명 중립, 2명 부정/위험**. ADR 001은 30-40대 마케팅 직군에만 효과적, 시니어·데이터족·폐업위험에는 역효과 또는 무효. **세그먼트별 톤 분기 필수**.

## 5. 카카오 알림 도달성 분석 (ADR 004)

`kakao_service.py:18` `SEND_TO_ME_URL = https://kapi.kakao.com/v2/api/talk/memo/default/send` — **본인 메모 API**:
- 사장님 채팅창 노출 X. "나에게 보내기" 채널 활성·모니터링 안 하면 미수신
- 카카오 알림톡(AlimTalk, 사업자 인증 필요) 코드 부재
- 카카오 친구톡·플러스친구·비즈메시지 코드 부재

**INV5 한지원 합격 기준** "카카오 비즈메시지로 일 액션 발송 가능" → **FAIL**

| 페르소나 | 채널 | 도달률 |
|---|---|---|
| P001 60세 | "나에게" 미인지 | 5% |
| P002 32세 | iOS FCM | 50% |
| P008 38세 | 안드 FCM | 70% |
| P020 58세 | "나에게" + iOS 권한 거부 | 3% |
| P022 35세 | FCM | 65% |
| P024 30대 | FCM | 75% |

**평균 알림 도달률 약 45%**

## 6. 무료 → 프로 funnel 분석

**코드 사실**: `types/index.ts`에 `plan_tier: "free" | "pro"` 인터페이스만. 결제 페이지·페이월·CTA·webhook·iamport/toss/kakaopay SDK·dashboard 페이월 트리거 — **전부 부재**.

| 항목 | 결과 |
|---|---|
| 프로 권유 노출 페이지 | 없음 |
| 결제 모듈 | 없음 |
| 9,900원 결제 가능 페르소나 | 0명 |
| 잠재 의향 (UI 구축 시) | P002 25%, P024 30%, 기타 5-10% |

**LTV/CAC 추정 (가설)**:
- CAC: 카카오+인스타 광고 ≈ 12,000원
- LTV: D28 18% × 6개월 잔존 × 9,900 ≈ 10,690원
- **LTV/CAC ≈ 0.89** → INV1 ≥ 3 기준 **FAIL**
- INV4 CAC < 2만원 marginally pass, K > 0.3 미증명

**우선순위 액션**: 결제 모듈 구축 + 페이월 트리거 시점 설계 (PDF 다운, deep 탭 진입, /marketing 4번째 카드 클릭)

## 7. 가장 위험한 시나리오 (한 줄)

> **P020 (관악 문구점 58세 폐업위험)이 가입 후 SurvivalMatrixCard "패턴 유사도 80% critical"을 본 순간, 손실 프레이밍 카피와 결합해 회피 행동(앱 삭제·신뢰 붕괴)을 유발하며, 잠재적으로는 정신건강 측면 우려까지 도달 — ADR 001 손실 프레이밍을 시니어·폐업위험 세그먼트에 무차별 적용한 결과로, 도덕적·법적 책임 노출까지 가능.**

## Top 5 fix 권고

1. **결제 모듈 부재** — INV1·INV4·INV5 통과 위해 iamport/toss 통합 + 프로 페이월 신규 구현
2. **카카오 "나에게 보내기" 한계** — 카카오 비즈메시지/알림톡 SDK 도입, 그 전엔 ADR 004를 "FCM 우선"으로 재정의
3. **SurvivalMatrixCard critical 시니어/폐업위험 톤 다운** — 세그먼트별 카피 분기 + 정신건강 자원(자살예방상담 1393) 안내 의무화
4. **/marketing GPT 환각 숫자** — fit_score/ROI/uplift/attach_rate 공식화 또는 "AI 추정치(검증 필요)" 라벨 강제
5. **/onboarding Step1 시니어 친화화** — OCR 카메라 입력 + 18px 폰트 + stepper + 가족 도움 호출 (QR 가족 공유)

## 추가 발견 (코드 검증)

- **kakao OAuth scope `talk_message`** onboarding 시 강제 옵션 미확인. send_to_me 401 가능
- **kakao_access_token DB**는 `crypto.encrypt_token` 적용 OK (TECH4 합격)
- 일부 페르소나가 진위 의심 발생 시점:
  - P002: Day 3 marketing 탭 진입 직후
  - P022: Day 1 즉시 (가입 시 평가관 마인드)
  - P024: Day 4-5 budget_scenarios 결과 차이 발견 시

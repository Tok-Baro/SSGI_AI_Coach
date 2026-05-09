# QA Round 1 — Part B: Dashboard

검증 대상: `frontend/src/app/dashboard/page.tsx` (749줄, 정직 버전) + 백엔드 `dashboard.py` phased pattern

## 1. 페르소나 통과 매트릭스 (Lens A)

| 페르소나 | 1분 동선 | 멈추는 카드 | 이탈 사유 | 진위 인지 |
|---|---|---|---|---|
| **C01-1 P001** 종로 백반 50대+ 카톡만 | 헤더 → 큰 노란 숫자 → 멈춤 | PotentialSubsidyBadge | "원" 6자리 거부감, "47%" 의심, 위험도 그래프 의미 모름 | 낮음 |
| **C01-3 P017** 노원 김밥 50대+ | 헤더 → 큰 숫자 → 위험도 막대 | 위험도 67점 같은 숫자 | "67점이 나쁜 건가요?" 답 없음. 색이 빨강이라 불안. peer_percentile null로 "데이터 부족" | 낮음 |
| **C02-1 P008** 마포 치킨 30대 배달앱 | PotentialSubsidyBadge 스킵 → 매칭 지원사업 → 요인 분석 | 매칭 지원사업 D-14 | "이 지원금 진짜 마감인가" 검증 못함 | 중간 — 외부 검색 시 SEED 발각 |
| **C02-4 P027** 망원 떡볶이 40대 배달앱 | 위험도 → "경쟁 압력" factor 펼침 | 매출 트렌드 description | "전분기 대비 -3.4%"가 본인 매출인 듯 오해 (실제는 행정동 평균) | 매우 낮음 |
| **C04-1 P009** 강남 의원 5500만원 | 헤더 → 위험도 30점(녹색) → 끝 | 거의 안 멈춤 | risk_score 낮으면 카드 useful X. 매칭 0건일 가능성 → 빈 상태 | 낮음 |
| **C04-3 P022** 강남 카페 6200만원 30대 데이터분석 | 모든 카드 훑음 → "요인 분석" 펼침 | risk_factors[] description | 출처 표기 없음, peer_sample 작음 | **높음** — quarterly_change_percent 의심 |
| **C05-2 P005** 노원 편의점 50대+ 매출감소 | 큰 숫자 → 위험도 → SurvivalMatrix critical | SurvivalMatrix gradient | survival_action hardcoded dict 미스매치 시 "그래서 뭐 어쩌라고" 이탈 | 낮음 |
| **C05-4 P021** 상계 갈비 40대 매출감소 | 위험도 → SurvivalMatrix → D-14 | 매칭사유 칩 | 칩 4개 모두 "사장님 일치"만 — 너무 일반적 | 중간 |
| **C08-1 P007** 관악 떡볶이 폐업위험 | SurvivalMatrix critical → 빨간 그라데이션 | Survival score 막대 | 충격 받지만 행동변화 단일 액션이 일반적. 폐업/재기 의사결정 트리 부재 | 낮음 |
| **C08-3 P020** 관악 문구점 50대+ | SurvivalMatrix → 충격 → 이탈 | "폐업 평균 53개월" | **자극적 빨간색으로 신뢰감 붕괴**, "내 가게 폐업 임박이라고? 너네가 어떻게 알아" — 시니어 위협감 | 매우 낮음 (감정 반응 큼) |
| **C09-1 P002** 마포 카페 30대 SNS | 위험도 → 매칭 → PDF 리포트 | PDF 리포트 카드 | PDF 내용은 GPT prose. "구체적 행동 없음" 인상 | **높음** — GPT 환각 detect |
| **C09-3 P024** 연남 미용실 30대 마케팅 | 위험도 → 매칭 → "왜 다 100%?" | 매칭 칩 | 모든 항목 "✓ 업종 일치" → 의심 | **매우 높음** |
| **C16** 데이터 능숙 사장 | 모든 카드 훑음 → 콘솔 열기 | 개발자 도구 분석 | API 출처 표기 부족, source field 없음 | **매우 높음** — 8개 RED FLAG 중 6-7개 detect |

**핵심**: C01·C05 시니어는 위험도 의미 이해 실패. C04 안정 케이스는 빈 상태로 재방문 유인 부족. C08 폐업 임박은 충격받지만 행동 막힘. C09·C16 마케팅·데이터 능숙은 출처 표기 미흡 즉시 detect.

## 2. 투자자 Verdict (Lens B)

| 투자자 | 판정 | 사유 |
|---|---|---|
| **INV1 김도윤** | **탈락** | D7/D30 retention, 알림 클릭률, MAU 그래프 0개. 코호트 비교 불가 |
| **INV2 박순자** | **조건부** | "위험도 67점"이 50-60대에게 의미 전달 실패 — 한국어 평어로 바꿔야 통과 |
| **INV3 정희경** | **탈락** | 대시보드 카드에 **"서울시 출처" 라벨 0건**. UpcomingEvents만 출처 명시. ADR-002 k-anonymity UI 비활성화 안내만 |
| **INV4 이재훈** | **조건부** | 첫 가치 30초 내 OK. 그러나 **공유 가능한 한 줄 카피 부재** — loss_message 백엔드 생성하나 UI 미노출 |
| **INV5 한지원** | **탈락** | 대시보드에 카카오 알림톡 통합 흔적 0건. 카카오맵 가게 위치 시각화 없음 |

**합격 0 / 조건부 2 / 탈락 3** — 데모 통과 불가. 핵심 결손: ① 코호트/리텐션, ② 데이터 출처 라벨, ③ 카카오 시너지, ④ 공유 카피.

## 3. 기술전문가 8×5 매트릭스 (Lens C)

40개 셀 합계: **P=6, F=29, N=4, N/A=1**. 합격률 **15%**.

| Checkpoint | TECH1 백엔드 | TECH2 프론트 | TECH3 AI/ML | TECH4 보안 | TECH5 UI/UX |
|---|---|---|---|---|---|
| CP1 | F: Phase A에 RAG·SocialProof gather. ChromaDB I/O가 PG 점유 | P: Server/Client 경계 정확 | F: today_action GPT silent fallback. is_fallback 미전달 | F: 응답에 nickname/business_name 평문 (PII 마스킹 없음) | F: "Dashboard"·"홈" 영문/한글 혼재 |
| CP2 | F: social_proof N+1 (10× count) | F: useEffect 의존성 `[user]` reference 변경 시 매 렌더 | F: GPT 응답 fallback에 "추천합니다" 톤 (ADR 001 위반) | N | F: 위험도 차트 **색상만으로 의미** → 색맹 위반 |
| CP3 | P: `_safe()` retry+timeout. 단 **silent failure** | P: api.ts ApiClient | F: ChromaDB top_k=3, vector similarity 자체는 SQL 필터만 — **진짜 RAG 아님** | N/A | F: 손실 빨강 4곳 사용 — **빨강 남발** 시각적 피로 |
| CP4 | P: Alembic 006 추가 | F: `sw 2.js`/`sw 3.js` 중복 | F: golden set 회귀 테스트 부재 | F: kakao access_token 평문 DB 가능성 | F: 시니어 폰트 미적용. 본문 14px. **Pretendard 미적용 (Inter)** |
| CP5 | P: Pydantic v2. 응답 모델 분리 X | F: any 타입, 응답 dict가 frontend·backend drift 위험 | F: prompt에 사장님 PII 평문 주입 → OpenAI logs 누출 | F: 응답 본문 PII. cache header `private, no-store` 강제 필요 | F: 액션 카드 정보 위계 약함 — chip 먼저 보임 |
| CP6 | F: peer_row JOIN에 인덱스 미확인 | N | F: 청킹 CHUNK_SIZE=500 — 한국어 보조금 의미 단위 미정렬 | F: rate limit /dashboard 부재 | F: 액션 빈 상태 스켈레톤 부재 |
| CP7 | F: peer_row count distinct 비싸짐 | F: setData race condition (unmount 후 setState 경고) | F: 평가 0건 | F: JWT 무효화 경로 미확인 | F: 로그아웃 버튼 `text-xs` `py-1.5` → **44pt 미달** |
| CP8 | F: `_safe()` 모든 예외 swallow. 모니터링 어려움 | F: useEffect 의존성 eslint 경고 가능 | F: 회귀 테스트 0건 | F: PII 로그 (action_generator → OpenAI) | F: aria-label 부재. 위험도 막대 div, 스크린리더 미인식 |

## 4. 데이터 진위 결함 노출 위험 (Lens D)

| # | 결함 | 대시보드 노출 | UI 텍스트 | 인지 가능 페르소나 |
|---|---|---|---|---|
| 1 | 47% 하드코딩 | PotentialSubsidyBadge socialProof | "2025년 ○○동 ○○ 47%가..." | C09·C16, INV3 — 시니어는 detect 못함 |
| 2 | 모든 보조금 SEED | "매칭 지원사업" 카드 max_amount, deadline | 권위 정보로 읽음 | C09·C16 |
| 3 | survival_action hardcoded | SurvivalMatrixCard 하단 | "지금 해야 할 단 1가지" + 5개 if-else | C08 — 본인 상황 미일치 시 detect |
| 4 | quarterly_change_percent 명칭 오류 | 위험도 요인 분석 매출 트렌드 | "전분기 대비 +/-X%" (실제는 분산) | C16. C02·C05는 본인 매출로 오해 |
| 5 | /marketing GPT 환각 | PDF 리포트 다운로드 후 내부 fit_score/ROI | GPT 자유생성 숫자 | C09 — 일관성 없음 detect |
| 6 | today_action silent fallback | "오늘의 액션" 동일 UI | is_fallback flag 미전달 | **거의 detect 불가 — 가장 잘 숨겨짐** |
| 7 | loss_counter `/365` | UI 미노출 | (미사용) | N/A |
| 8 | relevance_score=1.0 literal | UI 미노출 | (미사용) | C09·C16 응답 본문 |

**핵심**: 결함 1·2·3·4·5는 UI 직접 노출, 데이터 능숙 사장과 INV3에게 즉시 발각. 결함 6이 가장 위험 — 사용자가 fallback 인지 못함.

## 5. 발견 이슈 우선순위

### P0 (즉시 수정)

| ID | 위치 | 이슈 |
|---|---|---|
| **P0-1** | `social_proof_service.py:48,54` | "47%" 하드코딩 출처 0. 메시지 제거 또는 실수치 교체 |
| **P0-2** | `action_generator.py:148-150` | GPT silent fallback. 응답에 `is_fallback: bool` + UI chip 구분 |
| **P0-3** | `risk_score_engine.py:108-118` + `seoul_api_service.py:148-150` | quarterly_change_percent가 intra-period dispersion. 위험도 핵심 factor가 misnamed metric 위. 필드명 변경 + UI description |
| **P0-4** | `dashboard/page.tsx:166` | "67점" 의미 불명 (시니어). "100점에 가까울수록 위험" 한 줄 또는 4단계 등급 |

### P1 (다음 스프린트)

| ID | 위치 | 이슈 |
|---|---|---|
| P1-1 | `dashboard/page.tsx:509-513` | socialProof 출처 라벨 없음. "출처: 서울 열린데이터" 추가 |
| P1-2 | `dashboard/page.tsx:140` | loss_counter UI 미노출. 공유 카피 카드 추가 |
| P1-3 | `dashboard.py:124-133` | RAG가 Phase A 내 PG 점유. RAG를 Phase B로 |
| P1-4 | `insights.py:1414-1426` | survival_action hardcoded. "기본 가이드" 라벨 또는 LLM 산출 |
| P1-5 | `dashboard/page.tsx:23,40` | useEffect 의존성 `[user]` → `[user?.id, user?.onboarding_completed]` |
| P1-6 | `dashboard/page.tsx:194-204` | 위험도 차트 color-only 접근성 위반. 점수 숫자 또는 패턴 |
| P1-7 | `action_generator.py:114-117` | OpenAI prompt에 PII. 추상화 또는 ZDR 워크스페이스 |
| P1-8 | `public/sw 2.js`, `sw 3.js` | 중복 파일 즉시 삭제 + .gitignore 패턴 |

### P2 (백로그) — 8건 추가
- 6+ 카드 길이 collapsible
- 시니어 모드 토글
- _safe() logger 추가
- blob URL race
- 손실 빨강 4곳 분리
- SurvivalMatrix `left: 53%` 하드코딩
- risk_trend slice(-14) 하드코딩
- business_start_date fallback 명시

## 6. 한 줄 정리

대시보드는 phased pattern으로 백엔드 병목 1개 해소했지만, **데이터 신뢰(P0-1·P0-2·P0-3) + 시니어 가독성(P0-4) + 출처 라벨(P1-1) 5가지가 막혀 있어** 데모 통과 가능성은 INV2·INV4 조건부, 나머지 3명 탈락. 기술 매트릭스 합격률 15%. 시급한 fix는 47% 하드코딩 제거 + today_action fallback flag + risk score factor 명칭 정정.

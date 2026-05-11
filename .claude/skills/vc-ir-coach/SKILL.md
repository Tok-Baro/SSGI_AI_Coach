---
name: vc-ir-coach
description: Use this skill when reviewing, scoring, or rewriting investor/IR decks (PPT/Keynote/PDF) — especially Korean Pre-Seed/Seed/Pre-A/Series A pitch decks, demo day decks, 데모데이 자료, 정부 경진대회 사업화 트랙, 사업계획서 PPT. Triggers when user says "VC가 어떻게 볼까", "투자자 눈으로", "IR 덱 평가/리뷰", "이 슬라이드 더 IR답게", "발표 멘트 써줘", "Pre-A 자료 다듬어", "TAM 산식 검증", "LTV/CAC 정직하게", "Q&A 대비". Loads five reference files (VC mental models, 15-slide rubric, numerical hygiene, Korean VC landscape, talk-track patterns) so output reads like it was written by a senior IR consultant rather than an AI.
version: 0.1.0
---

# VC IR Coach — 투자자 IR 덱 전문 스킬

## 언제 호출되는가

- "VC가 어떻게 볼까" / "투자자 눈으로 평가해"
- "IR 덱 평가/리뷰" / "데모데이 자료 채점해"
- "이 슬라이드 IR답게" / "더 VC답게 다듬어"
- "발표 멘트 써줘" / "5분/10분 스크립트"
- "Q&A 대비 / 받을 질문 30개"
- "TAM/SAM/SOM 산식 검증" / "환각 숫자 잡아내"
- "LTV·CAC 정직하게 표기"
- "Pre-A·Series A 자료 점검"
- 사업계획서 PPT 리뷰/리라이트

## 핵심 철학

> VC는 **30초 안에 NO를 결정한다**. 5초 안에 "YES일 수도 있다"는 신호를 줘야 한다.
>
> 그 5초는 **표지 한 줄 + 큰 숫자 한 개**다. 나머지 슬라이드는 "왜 NO 안 할 건지"를 만들어 가는 과정.
>
> AI가 자동 생성한 IR 덱은 **버즈워드·일반론·top-down TAM·트랙션 부풀리기**가 특징.
> 사람이 잘 쓴 IR 덱은 **숫자 출처·bottom-up·약점 선제 인정·구체 다음 단계**가 특징.

## 작업 순서

### Step 1 — Triage (5초 테스트)

표지 + 첫 3장만 보고 **6 질문**에 답할 수 있나:

1. **무엇** (What is it?) — 한 줄로 설명 가능한가
2. **누구** (For whom?) — 페르소나 1명이 떠오르는가
3. **왜 지금** (Why now?) — 5년 전엔 안 됐는데 지금 되는 이유
4. **얼마짜리** (How big?) — TAM bottom-up 한 줄
5. **어떻게 돈 버나** (How monetize?) — 단가 × 빈도
6. **누가** (Why this team?) — 이 문제를 풀 자격

→ 답 못 하는 질문 ≥ 2개 = 즉시 표지·첫 3장 리라이트

### Step 2 — Score (15 essential slides 채점)

`references/slide-rubric.md`의 0-10 체크리스트로 슬라이드별 점수.
총점 100점. **70점 미만 = 1차 서류·데모데이 통과 어려움**.

### Step 3 — Numerical Hygiene (숫자 검증)

`references/numerical-hygiene.md` 체크리스트로 환각·과장·top-down 전부 적발:
- TAM이 top-down ("XX조 시장")이면 즉시 bottom-up으로 강제 변환
- LTV/CAC, ARR, churn rate 등은 결제 데이터 없으면 "가설" 라벨
- 모든 숫자에 출처 + 추출일 의무

### Step 4 — Rewrite (한 슬라이드 한 메시지)

`references/slide-rubric.md`의 슬라이드별 must-answer 패턴으로:
- 헤드라인 = 슬라이드의 한 줄 요약 (50자 이내, 동사 포함)
- 본문 = 그 헤드라인의 근거 1개 + 숫자 1개
- 푸터 = 출처 + 페이지

### Step 5 — Talk Track (구두 스크립트)

`references/ir-talk-track.md`의 슬라이드 ↔ 멘트 매핑:
- 슬라이드당 30~45초
- 첫 문장은 헤드라인 그대로 읽지 말고 **재해석** (예: "이 4.5년이 무슨 의미냐면…")
- 마지막 문장은 다음 슬라이드로 넘어가는 다리

### Step 6 — Q&A 시뮬

`references/ir-talk-track.md`의 "VC가 던지는 30 질문"으로 셀프 시뮬:
- 답 못 하는 질문 = 그 슬라이드 백업 강화
- 약점 질문 (트랙션·결제·팀)은 **선제 인정 → 다음 단계** 패턴

## 빠른 참조 — 슬라이드별 must-answer 매트릭스

| # | 슬라이드 | 한 줄 답해야 할 질문 | 환각 신호 |
|---|---|---|---|
| 1 | Cover | "한 줄로 뭐 하는 회사인가" | 추상적 비전/슬로건만 |
| 2 | Problem | "누가, 얼마짜리 손해 보고 있나" | "X 시장은 비효율적" 일반론 |
| 3 | Solution | "그래서 우리가 어떻게 푸나 (1문장)" | 기능 나열 |
| 4 | Why Now | "5년 전엔 안 됐는데 지금 되는 이유" | "AI/블록체인이 발전" |
| 5 | Product | "데모 화면 1장 + 핵심 인터랙션" | 설계도/구조도만 |
| 6 | Market (TAM/SAM/SOM) | "bottom-up 산식 한 줄" | "X조 시장" top-down |
| 7 | Business Model | "단가 × 빈도 = ARPU" | 무료 + Pro만 나열 |
| 8 | Traction | "지난 N개월 추세 + 핵심 1지표" | 누적 가입 자랑 |
| 9 | Competition | "우리만 가진 1가지" | 4-quadrant 우상단 자뻑 |
| 10 | GTM | "첫 100명을 어떻게 잡나" | "마케팅 강화" |
| 11 | Team | "이 문제 풀 자격" | LinkedIn 나열 |
| 12 | Roadmap | "다음 6개월 마일스톤 3개" | 5년 비전 |
| 13 | Financials | "burn / runway / 다음 라운드 트리거" | EBITDA만 |
| 14 | Ask | "얼마, 무엇에 쓸지" | "투자해 주세요" |
| 15 | Why Us | "VC가 다음 미팅 잡는 이유" | 다 빠짐 |

→ 백업 슬라이드: cohort retention / unit economics / regulatory / hiring plan / dilution 등

## 정직성 — pre-revenue 표기 룰

결제 데이터 0건일 때:
- ❌ "LTV/CAC 3.96, Payback 4.8개월"
- ✅ "베타 인터뷰 N=8 중 5명 9,900원 결제 의향. 결제 모듈 Q3 출시 예정 — LTV/CAC는 코호트 측정 후 갱신"

상상 트랙션 표기:
- ❌ "월 매출 1,200만원 예상"
- ✅ "Year 2 목표 (가설) — N=8 의향 데이터 기반 추정"

→ "가설" 라벨 + amber chip 일관 적용. VC는 **거짓말을 가장 싫어한다**. 모르는 건 모른다고 적는 게 점수 더 받는다.

## 한국 VC 화법

`references/korean-vc-landscape.md` 참조. 핵심:
- **카카오벤처스**: 카카오 시너지 명시, B2C 사장님·소비자 중심
- **본엔젤스**: 첫 투자 + 멘토링, 트랙션 작아도 OK
- **알토스**: 기술 차별화 + 글로벌 가능성
- **매쉬업엔젤스**: 한국 시장 기반 + 빠른 BEP
- **스트롱벤처스**: 미국 LP 대상 → 영문 IR 동시 준비
- **TIPS / K-Startup / 카카오벤처스 데모데이**: 정부 평가표 매칭 의무

## 안티패턴 — 이렇게 쓰면 즉시 다시 써라

### 안티패턴 1 — Top-down TAM
> "한국 자영업 시장은 100조 규모입니다"

→ bottom-up 강제: "730만 사업자 × 30% 디지털 수용 × 9,900원 × 12 = 2,604억"

### 안티패턴 2 — 버즈워드 폭격
> "AI 기반 데이터 드리븐 솔루션으로 비즈니스 임팩트를 극대화"

→ 다 빼고: "사장님이 매일 받는 1줄 액션 — '오늘 단골 카톡 보내세요'"

### 안티패턴 3 — 가짜 트랙션
> "베타 사용자 1만명 돌파!"

→ 정직: "Free 가입 1만 / Active 7-day 600 / 결제 0 / 인터뷰 N=8"

### 안티패턴 4 — 5년 비전
> "5년 안에 동남아 진출, 핀테크 확장, IPO"

→ "다음 6개월: ① 결제 모듈 출시 ② D7 retention 25%+ ③ 1,000 MAU"

### 안티패턴 5 — Team 슬라이드 LinkedIn
> "John Doe — Stanford CS, ex-Google, ex-Facebook"

→ "**이 문제와의 연결**: 김OO은 본가가 13년 운영한 한식집 폐업을 겪고 SSGI 시작."

### 안티패턴 6 — Ask 슬라이드 누락
> (Ask 슬라이드 없음)

→ 마지막 슬라이드 의무: "5억원 모집 · 18개월 runway · 2건 채용 + GTM"

### 안티패턴 7 — 4-quadrant 자뻑
> 경쟁 매트릭스 우상단에 우리만 노란색 별 ⭐

→ 7개 차원 표 + 각 차원 정직 표기. 우리가 약한 1개도 보여줘야 신뢰.

### 안티패턴 8 — 풍선 스토리
> "이 모든 것이 합쳐져 거대한 시너지를…"

→ 한 슬라이드 한 메시지. 시너지 슬라이드는 만들지 말라.

## 이 프로젝트(SSGI_AI_Coach) 활용 가이드

방금 만든 `SSGI_AI경영코치_상세기획서.pptx`는:
- 1차 서류 (서울시 빅데이터 경진대회 창업부문) **통과 목적**
- 동시에 데모데이 / Pre-A 라운드 **재활용 가능 구조**
- 평가표 매칭 (공공25·AI20·독창15·완성15·발전20·ESG5)

이 스킬로 검증할 때 우선순위:
1. 표지·문제 슬라이드 — 5초 테스트 통과 여부
2. 솔루션 슬라이드 — 한 줄 요약 + 데모 화면
3. TAM 슬라이드 — bottom-up 정직성 (현재 2,604억 확인 OK)
4. 트랙션 슬라이드 — N=8 정직 표기 (현재 OK)
5. Ask 누락 — **현재 덱은 경진대회용이라 Ask 슬라이드 없음**. Pre-A 모드로 재활용 시 추가 필수.

## 다른 스킬과의 결합

| 스킬 | 언제 같이 쓰나 |
|------|---|
| `human-tone` | 모든 슬라이드 헤드라인·캡션 한국어 다듬기 (필수 결합) |
| `sme-coach` | 소상공인·B2C 도메인 IR 덱일 때 (산업 KPI·상권 데이터 인용) |
| `frontend-design` | IR 덱 시각 디자인이 약하다는 피드백 받았을 때만 (메모리 룰: 약함) |

## 레퍼런스 인덱스

| 파일 | 내용 | 언제 |
|------|------|------|
| `references/vc-mental-models.md` | 5/30/3분 테스트 · 스테이지별 기대치 · 의사결정 트리 | Step 1 |
| `references/slide-rubric.md` | 15 essential 슬라이드 0-10 채점 + 패턴 | Step 2, 4 |
| `references/numerical-hygiene.md` | TAM bottom-up · LTV/CAC pre-rev · 환각 적발 | Step 3 |
| `references/korean-vc-landscape.md` | 한국 VC/AC 50선 · 화법 차이 · 데모데이 평가 | 한국 VC 미팅 직전 |
| `references/ir-talk-track.md` | 5/10/15분 스크립트 · Q&A Top 30 · 클로징 | Step 5, 6 |

---

> **유지보수**: 새 VC 미팅 후 받은 질문은 `ir-talk-track.md`의 Q&A 섹션에 추가.
> 새로운 한국 VC/AC 정보는 `korean-vc-landscape.md`에 추가.

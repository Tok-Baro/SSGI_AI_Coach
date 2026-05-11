---
name: sme-coach
description: Use this skill when generating analysis, advice, or copy for Korean small-business owners (소상공인) — especially when the project involves industry-specific recommendations, Seoul commercial district analysis, marketing channel ROI, unit economics, or government subsidy matching. Triggers when user asks to "improve the analysis", "더 정확한 진단", "업종별 다른 추천", "상권 분석", "지원사업 매칭" or when working on the SSGI_AI_Coach deep-report/marketing-strategy/menu-strategy endpoints. Loads four reference files (industry playbooks, Seoul zone analysis, marketing channels, unit economics, subsidy landscape) so the AI can give grounded, industry-aware diagnoses instead of generic "쿠폰 발행" advice for every store.
version: 0.1.0
---

# SME Coach — 소상공인 도메인 지식 스킬

## 언제 호출되는가

- 한국 소상공인 가게 분석/조언 작성
- 업종별로 다른 추천을 만들어야 할 때 (치킨집 vs 카페 vs 미용실)
- 서울 상권 데이터(HHI/직주비율/생활인구) 해석
- 마케팅 채널 ROI 추천 (배민/네이버/인스타/카카오)
- 손익 구조 진단 (임대료 비중·객단가·재방문율 등)
- 정부 지원사업 매칭 가이드

## 핵심 철학

> 같은 데이터에서도 **업종이 다르면 다른 진단**이 나와야 한다.
> 치킨집 사장님에게 "인스타 사진 톤 통일"은 불필요한 조언.
> 카페 사장님에게 "배민 광고비 늘리세요"는 잘못된 조언.

## 작업 순서 (deep-report / marketing-strategy / menu-strategy 같은 분석 생성 시)

### Step 1 — 업종 식별
사장님 `business_type`(치킨/한식/카페/미용/의류 등) 확인.
`industry-playbooks.md`의 6대 업종군 분류로 매핑.

### Step 2 — 상권 컨텍스트 파악
사장님 `gu_name` + `dong_name` + `직주비율` + `상권변화지표`로:
- 서울 5대 상권 유형 매핑 (CBD / 부도심 / 주거 / 학군 / 관광)
- HHI · 집객력 · 생애주기 해석 (`seoul-commercial-zones.md`)

### Step 3 — KPI 임계값 확인
업종별 안전/주의/위험 임계값으로 사장님 데이터 평가 (`unit-economics.md`):
- 외식업 객단가 < 1.2만 = 위험
- 카페 일 손님 < 30 = 위험
- 미용 재방문율 < 50% = 위험

### Step 4 — 마케팅 채널 추천
업종 + 예산 + 현재 활동 기반으로 1~3개 채널 추천 (`marketing-channels.md`).
**원칙**: 모든 채널 동시 시작 X, 1개부터 단단하게.

### Step 5 — 지원사업 매칭
사장님 자격(매출/사업기간/업종)에 맞는 정부 사업 1~3개 (`subsidy-landscape.md`).

### Step 6 — 카피 톤 적용
human-tone 스킬 + 업종별 어휘로 사람 말투 변환:
- 치킨집: "야간 단골 카톡 한 번에"
- 카페: "단골 락인 시스템"
- 미용실: "재방문 5회 시 VIP 등급"

## 빠른 참조 — 업종 분기 매트릭스

| 업종 | Hero KPI | Top 채널 | 핵심 손실 프레임 |
|---|---|---|---|
| 치킨/분식/배달 | 객단가 + 배달 비중 | 배민 | "배달앱 노출 점수" |
| 카페/베이커리 | 재방문율 + 평일 매출 | 인스타 | "단골 락인 부재" |
| 한식/양식 일반 | 점심 회전율 + 객단가 | 네이버 플레이스 | "직장인 점심 동선" |
| 편의점/슈퍼 | 평당 매출 + 단골 비율 | 카카오 단골방 | "동네 인지도" |
| 의류/뷰티 | 재구매율 + 인스타 팔로워 | 인스타 + 무신사 | "온라인 노출" |
| 미용/네일/세탁 | 재방문율 + 예약 비율 | 네이버 + 예약시스템 | "워크인 손실" |

## 레퍼런스 인덱스

| 파일 | 내용 | 언제 |
|---|---|---|
| `references/industry-playbooks.md` | 6대 업종군 KPI/전략/카피 톤 | Step 1, 6 |
| `references/seoul-commercial-zones.md` | 서울 상권 유형 + 데이터 해석법 | Step 2 |
| `references/marketing-channels.md` | 채널별 ROI/적합 업종/예산 가이드 | Step 4 |
| `references/unit-economics.md` | 업종별 손익 구조 + KPI 임계값 | Step 3 |
| `references/subsidy-landscape.md` | 지원사업 카테고리 + 매칭 로직 | Step 5 |

## 이 프로젝트(SSGI_AI_Coach) 활용 가이드

다음 GPT 시스템 프롬프트들에서 sme-coach 자료 인용:
- `backend/app/routers/insights.py` line 457 (deep-report 시스템 프롬프트)
- `backend/app/routers/insights.py` line 931 (marketing-strategy 시스템 프롬프트)
- `backend/app/routers/insights.py` line 1245 (menu-strategy 시스템 프롬프트)
- `backend/app/services/action_generator.py` line 17 (daily action 시스템 프롬프트)

각 프롬프트에 **"## 업종 분기 가이드"** 섹션을 추가하여 sme-coach의 핵심 매트릭스를 임베드.

## 안티패턴 — 이렇게 진단하면 즉시 다시 해라

### 안티패턴 1 — 업종 무시한 generic 추천
> "쿠폰을 발행하세요" (모든 사장님에게)

→ 치킨집은 배민 광고가 더 효과적. 미용실은 친구 추천 보상이 더 효과적.

### 안티패턴 2 — 데이터 절대값만 인용
> "객단가가 1만 2천원입니다"

→ 임계값 + 비교 + 해석 없으면 정보 0:
> "객단가 1만 2천원이에요. 같은 동네 한식집 평균보다 3천원 낮아요. 점심 세트로 1만 5천원까지 끌어올려 보세요"

### 안티패턴 3 — 외부 마케팅 무시한 위험 단정
> "실행 마찰로 매출 위험"

→ 사장님이 인스타·배민·오프라인 등 외부 마케팅 하실 수 있음.
"AI 코치 활용도 낮음"으로만 표현. (메모리 룰)

### 안티패턴 4 — 모든 채널 동시 추천
> "인스타·배민·네이버·카카오·블로그 다 시작하세요"

→ 1~2개부터 단단하게. 운영 부담 폭발 방지.

### 안티패턴 5 — 추정치를 단정값으로
> "월 매출 1,200만원이 예상됩니다"

→ "약 1,200만원 ~ 1,500만원 정도 가능해요" / "업종 평균 기준 추정이에요" 단서 명시.

## 정직성 + 정합성

이 스킬은 **데이터가 닿지 못하는 부분은 모른다**:
- 음식 맛, 직원 친절도
- 동네 입소문·평판
- 사장님 가족·자본·멘탈
- 외생 변수 (코로나·금리·재난)

→ AI 진단이 사장님 가게 전체를 안다고 단정하지 말 것. 데이터 위에서 본 패턴임을 명시.

---

> **유지보수**: 새 업종 KPI 발견 시 `industry-playbooks.md` 추가.
> 새 마케팅 채널 등장 시 `marketing-channels.md` 추가.
> 정부 지원사업 신규 카테고리 발견 시 `subsidy-landscape.md` 추가.

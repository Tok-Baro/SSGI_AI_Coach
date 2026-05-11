---
name: ir-deck-visual
description: Use this skill when designing or fixing the visual layout of IR/pitch deck slides (PPT/Keynote/PDF) — typography, grid, color rhythm, whitespace, big-number patterns, chart minimalism. Triggers when user says "예쁘게 만들어", "디자인 정리", "시각 강화", "한 슬라이드 한 메시지", "이거 너무 빽빽해", "차트 단순화", "타이포 정리", "발표 슬라이드 디자인". Different from frontend-design (web UI) — this is for static slide canvases (16:9 widescreen 1280×720pt). Loads three reference files (typography hierarchy, layout grid, slide patterns) so output reads like Sequoia/Stripe pitch deck rather than corporate PowerPoint.
version: 0.1.0
---

# IR Deck Visual — 슬라이드 시각 디자인

## 언제 호출되는가

- "예쁘게 만들어" / "이 슬라이드 디자인 정리"
- "한 슬라이드 한 메시지로"
- "너무 빽빽해" / "여백 더"
- "타이포 정리" / "헤드라인 강조"
- "차트 단순화" / "데이터 시각화"
- 발표 자료 시각 품질 향상 요청

## 핵심 철학

> 슬라이드는 읽는 게 아니라 **보는 것**이다. 3초 안에 메시지가 전달되어야 한다.
>
> AI가 만든 슬라이드는 **빽빽한 텍스트 + 색 5가지 + 차트 3개**가 한 장에 다 들어간다. 결과: 0초 안에 청중 시선 이탈.
>
> 사람이 잘 만든 슬라이드는 **여백 40% + 색 2~3가지 + 큰 숫자 1개**다. 청중이 발표자에게 집중한다.

## 작업 순서

### Step 1 — 한 슬라이드 한 메시지 검증

각 슬라이드에 대해 묻기: "이 슬라이드의 한 줄 메시지는?"
답이 2개 이상이면 → 슬라이드 분할.

### Step 2 — 정보 위계 (Visual Hierarchy)

`references/typography.md` 참조:
- **헤드라인** (40~52pt, Bold, 검정·진한 네이비)
- **서브헤드** (18~22pt, Medium, 회색)
- **본문** (10~14pt, Regular, 슬레이트)
- **푸터** (8~10pt, Regular, 연회색)

→ 4 레벨 이상은 만들지 마라. 청중이 우선순위 못 잡음.

### Step 3 — 그리드 (12-column 16:9)

`references/grid.md` 참조:
- 16:9 = 13.33in × 7.5in (1280pt × 720pt)
- 좌우 마진 0.5in (가장자리에 텍스트 금지)
- 상단 헤더 0.75in / 하단 푸터 0.55in
- 본문 영역: 12.33in × 6.2in
- 12-column grid (1 column = 1.03in)
- gutter 0.1~0.15in

### Step 4 — 색 리듬 (Color Rhythm)

한 슬라이드 색 ≤ 3개. 반드시 의미 매핑:
- **NAVY (#0F172A)** — 본문 헤드, 신뢰
- **RED (#DC2626)** — 위험, 손실, 긴급
- **GREEN (#059669)** — 안전, 성공, 진전
- **AMBER (#D97706)** — 추정, 가설, 주의
- **GREY (#64748B)** — 보조, 출처, 푸터

→ 의미 없이 알록달록하면 **decorative junk**. 디자인 0점.

### Step 5 — 여백 (Whitespace 40% Rule)

각 슬라이드의 **40%는 빈 공간**이어야 함.
- 텍스트 박스 padding 최소 0.15in
- 카드 사이 간격 최소 0.1in
- 헤드라인과 본문 사이 0.4in
- 본문 끝과 푸터 사이 0.5in

→ 여백 < 30% = 빽빽함. 청중 시선 이탈.

### Step 6 — 큰 숫자 패턴 (Big Number)

핵심 데이터는 큰 숫자 1개로:
- 숫자: 36~48pt Bold
- 단위: 10~11pt Regular Grey
- 캡션: 10pt Slate, 1.35 line spacing
- 색은 의미 매핑 (위험=Red, 안전=Green, 추정=Amber)

→ 한 슬라이드에 큰 숫자 4개까지. 그 이상은 차트로.

### Step 7 — 차트 미니멀리즘

`references/chart-patterns.md` 참조:
- Y축 시작은 항상 0
- gridline 최소 (1~2개)
- legend는 line 끝에 직접 라벨
- 색은 본 메시지에만 강조 (나머지 회색)
- 데이터 포인트에 출처 작은 글씨

## 빠른 참조 — 슬라이드 타입별 레이아웃

### Hero / Cover
```
[좌측 4pt 색 스트라이프]
[작은 카테고리 라벨, 11pt Grey]

[큰 회사명, 44pt Bold Navy]

[큰 슬로건, 32pt Bold Navy, 2 lines max]

[큰 숫자 1개, 44pt Bold Navy] ← 임팩트 신호 1개
[그 의미 1줄]

[3 핵심 차별점 카드 (각 1/3 너비)]

[팀명 · 제출일, 10pt Grey, 하단]
```

### Problem / Why
```
[헤더: 24pt Bold Navy, 한 줄 헤드라인]
[서브: 12pt Grey, 1 줄 컨텍스트]

[큰 숫자 4개 가로 (각 3in 너비, 36pt Bold)]
- Number / Unit / Caption (8pt 출처)

[하단 카드 3개 (3등분, 비대칭/문제 구체화)]

[푸터: 출처 + 페이지]
```

### Solution Hero
```
[헤더: 22pt Bold Navy, 한 줄 솔루션]
[서브: 12pt Grey, 어떻게]

[3-tier 다이어그램 (가로 3등분)]
- 각 tier: 컬러 헤더 / 이름 / 부제 / 본문 / 보장 chip

[하단 핵심 메시지 1줄, 13pt Bold Navy]
```

### Traction / Numbers
```
[헤더: 22pt Bold Navy, 정직 표기]
[서브: 12pt Grey, 가설 라벨]

[큰 숫자 4개 가로]
[하단 인용 카드 3개 (페르소나 발화)]
```

### Roadmap / Quarters
```
[헤더: 22pt Bold Navy, 시간성]

[4 분기 카드 (가로 4등분)]
- 컬러 분기 헤더
- 마일스톤 4개 bullet

[하단 핵심 메시지/CVC 트랙 박스]
```

### Closing
```
[전면 색 (NAVY)]
[페이지 라벨, 11pt Grey]

[큰 헤드라인, 64pt+ Bold White, 2 lines]
[강조 1줄, 22pt Bold AMBER]
[감정 클로징, 18pt White, 2 lines]

[팀 정보, 10pt Grey, 하단]
```

## 안티패턴 — 즉시 다시 그려라

### 안티패턴 1 — 텍스트 빽빽 슬라이드
> 한 슬라이드에 bullet 8개 + 본문 5단락

→ "한 슬라이드 한 메시지" 위배. 분할하거나 카드화.

### 안티패턴 2 — 색 5개 이상
> 빨강·파랑·초록·노랑·보라·핑크 다 사용

→ 색 ≤ 3개. 나머지는 회색/슬레이트.

### 안티패턴 3 — 작은 폰트 빽빽
> 10pt 본문이 페이지 가득

→ 본문 최소 11pt. 시니어 친화 14pt.

### 안티패턴 4 — Stock 이미지 / 아이콘 폭격
> 슬라이드마다 이모지·아이콘 5개

→ 이모지·이콘 슬라이드당 1개 이하. 의미 없으면 빼라.

### 안티패턴 5 — 차트 Y축 왜곡
> Y축 시작이 80%여서 차이가 5배처럼 보임

→ Y축 항상 0부터. 정직 표기.

### 안티패턴 6 — 그라디언트 / 그림자 / 3D
> 박스에 그라디언트 + 그림자 + 3D 효과

→ Flat. 그림자 0. 그라디언트는 색 1개로 한정.

### 안티패턴 7 — 페이지 번호 일관성 없음
> P. 03.5 / 20 같은 잔재

→ 정수 일관. X / Y 형식 통일.

### 안티패턴 8 — 인라인 색 토글
> 한 문장 안에 색 3개

→ 한 카피 안에 강조색 1개. 핵심 1단어.

## 슬라이드 검수 체크리스트

각 슬라이드 빌드 후 즉시 확인:

- [ ] 헤드라인 한 줄 50자 이내
- [ ] 서브헤드 1줄 (있으면)
- [ ] 본문 3 단위 이하 (카드/bullet/숫자)
- [ ] 색 3개 이하 (회색·푸터 제외)
- [ ] 여백 40% 이상
- [ ] 큰 숫자 1~4개 (4개 초과면 차트로)
- [ ] 푸터에 출처 + 페이지 X / Y
- [ ] 폰트 4 레벨 이하 (헤드/서브/본문/푸터)
- [ ] 이모지·이콘 1개 이하
- [ ] 그라디언트·그림자·3D 0개

## 다른 스킬과의 결합

| 스킬 | 언제 같이 쓰나 |
|---|---|
| `human-tone` | 헤드라인·캡션 카피 작성 (필수 결합) |
| `vc-ir-coach` | 슬라이드 채점 + must-answer 매핑 (필수 결합) |
| `sme-coach` | 도메인 정확성 (소상공인·서울 상권) |
| `frontend-design` | 웹 컴포넌트 작업일 때만 (슬라이드 ❌) |

## 레퍼런스 인덱스

| 파일 | 내용 | 언제 |
|---|---|---|
| `references/typography.md` | 폰트 위계·크기·색·줄간격 | Step 2 |
| `references/grid.md` | 16:9 12-column · 마진 · 카드 비율 | Step 3 |
| `references/chart-patterns.md` | 차트 종류별 단순화 룰 | Step 7 |

---

> **유지보수**: 새 슬라이드 패턴 발견하면 SKILL.md 빠른 참조에 추가.

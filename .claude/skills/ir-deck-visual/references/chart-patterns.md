# 차트 / 시각화 패턴

> 차트는 "데이터를 보여주는 게 아니라 **메시지를 보여주는** 것"이다.
> 메시지가 없으면 차트도 없다.

---

## 차트 종류 선택 가이드

| 데이터 타입 | 차트 | 언제 |
|---|---|---|
| 시계열 추세 | Line chart | 월별 매출, MAU, retention |
| 비교 (3~7개) | Bar chart | 업종별 객단가, 채널별 ROI |
| 비율 (≤4개) | Donut chart | Free/Pro/ENT 매출 비중 |
| 비율 (>5개) | Stacked bar | 비용 분배 |
| 분포 | Histogram | 객단가 분포 |
| 상관관계 | Scatter | 가격 vs 만족도 |
| 위계 | Tree map | 시장 세그먼트 |
| 흐름 | Sankey | funnel 변환 |

→ 의심 가면 **Bar 또는 Big Number**.

---

## 차트 미니멀 룰

### 룰 1 — Y축 항상 0부터
- ❌ Y축이 80%부터 시작 → 차이가 5배처럼 보임 (왜곡)
- ✅ Y축 0부터. 진짜 차이가 보임.

### 룰 2 — Gridline ≤ 2개
- ❌ Gridline 5개 = 노이즈
- ✅ Y축에 1~2개 (50%, 100%)

### 룰 3 — Legend는 line 끝에 직접
- ❌ 우측에 legend 박스 (별도 영역)
- ✅ 각 line 끝에 라벨 (시선 이동 0)

### 룰 4 — 색은 메시지에만 강조
- ❌ 5 line 다 다른 색
- ✅ 핵심 1 line만 NAVY, 나머지 회색

### 룰 5 — 데이터 포인트에 출처
- ❌ 차트 어딘가에 "Source: 통계청"만
- ✅ 차트 하단에 "출처: 서울 열린데이터 · 2025 Q4 · 추출일 2026-04"

---

## Big Number 차트 (가장 많이 쓰는 패턴)

PPT에서는 사실상 차트 그리기 어려움 → **Big Number 패턴 권장**.

```
[큰 숫자]    36~48pt Bold (의미 색)
[단위]       11pt Grey
[캡션 1줄]   10pt Slate
[출처 1줄]   8pt Grey (있으면)
```

### 4 Big Numbers 가로 배치 (Hero)
```
4.5년       9.8년       53.7%      240만원
폐업 평균    운영중       정체+축소    미신청 보조금
```

→ **가장 강력한 IR 패턴**. 차트 0개로 4 핵심 메트릭 전달.

---

## 비교 차트 (Before / After)

```
[Before 박스]              [After 박스]
24초 hang                  0.25초 응답
풀 고갈 (10명)              여유 (50명)
              ────→
            "100배 빨라짐"
```

→ 화살표 + 변화량 라벨 명시.

---

## Funnel 차트

```
가입       1,000  ████████████████████  100%
온보딩       880  ██████████████████      88%
첫 액션      640  █████████████           64%
재방문       520  ██████████              52%
결제          80  ██                       8%
```

→ 단계별 % + 절대 수치 동시.

---

## 비율 (Donut/Stacked Bar)

### 4개 이하 → Donut
```
       ▓▓▓▓▓
      ▓     ▓
     ▓  60%  ▓  Pro
      ▓ Free ▓
       ▓▓▓▓▓
       30% Free / 60% Pro / 10% ENT
```

### 5개 이상 → Stacked Bar
```
[████████████████████]
 인건비 60% │ GTM 25% │ R&D 15%
```

---

## 차트 안티패턴

### ❌ 안티패턴 1 — 3D 차트
> 3D 파이 차트, 3D 막대

→ 평면화 (Flat). 3D는 비례 왜곡.

### ❌ 안티패턴 2 — 그라디언트 막대
> 막대마다 색 그라디언트

→ 단색. 의미 매핑.

### ❌ 안티패턴 3 — 차트 안에 텍스트 가득
> 차트 안에 데이터 라벨 + 퍼센트 + 출처 다 적음

→ 차트는 차트만. 출처는 하단.

### ❌ 안티패턴 4 — 한 슬라이드 차트 3개
> 3 종류 차트 동시

→ 차트 1개 슬라이드. 메시지 1개.

### ❌ 안티패턴 5 — 의미 없는 차트
> "Q1 100, Q2 95, Q3 105" — 차이 거의 없음

→ 차트 안 만들고 한 줄로: "분기별 매출 거의 동일 (95~105)"

---

## SSGI 적용 — 어떤 차트를?

### Slide 03 Problem
- ✅ 4 Big Numbers (4.5년 / 9.8년 / 53.7% / 240만원)
- ❌ Bar/Line ❌ (Big Number가 더 강력)

### Slide 13 시스템 (Phased Pattern)
- ✅ Before/After 박스 (24s vs 0.25s)
- ❌ Y축 시간 차트 ❌

### Slide 14 Traction
- ✅ 4 Big Numbers (실 트랙션 — 14 기능 / 31 라우트 / 8 모델 / 7 fix)
- 또는 Funnel (가입 → 액션 → 재방문)

### Slide 15 TAM
- ✅ 3 Big Numbers (TAM / SAM / SOM)
- 또는 Donut (TAM 안 SAM 안 SOM)

### Slide 19 ESG
- ✅ 환경 262 tCO2eq + 사회 23~49명 + 거버넌스 6 ADR (3 Big Numbers)
- ❌ 차트 ❌ (수치만 명확하면 됨)

→ **SSGI 덱 전체에서 진짜 차트는 0~1개로 충분**. 나머지는 Big Number + 카드.

---

## PPT에서 차트 그리기 (python-pptx)

진짜 차트가 필요한 경우:

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

chart_data = CategoryChartData()
chart_data.categories = ['Q3', 'Q4', 'Q1', 'Q2']
chart_data.add_series('MAU', (0, 1000, 5000, 10000))

slide.shapes.add_chart(
    XL_CHART_TYPE.LINE, x, y, cx, cy, chart_data
)
```

스타일링:
- Y축 0부터
- Gridline 최소
- Marker 크기 작게
- Color: NAVY 단색

→ 단, **Big Number로 대체 가능하면 차트 안 만드는 게 낫다**.

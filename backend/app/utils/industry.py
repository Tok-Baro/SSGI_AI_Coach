"""업종 분류 + 업종별 KPI/채널/카피 분기.

sme-coach 스킬의 6대 업종군 매트릭스를 한 곳에 모아 GPT 프롬프트와
점수 함수가 같은 분류를 공유하도록 한다.

치킨집 사장님과 미용실 사장님이 같은 진단을 받지 않게 하기 위함.
"""
from __future__ import annotations

from typing import Optional

# 정규화된 업종 슬러그
SLUG_DELIVERY = "delivery_food"   # 치킨/분식/배달전문
SLUG_CAFE = "cafe"                # 카페/베이커리
SLUG_RESTAURANT = "restaurant"    # 한식/중식/일식/양식
SLUG_RETAIL = "retail"            # 편의점/슈퍼/잡화
SLUG_FASHION = "fashion"          # 의류/화장품/패션
SLUG_SERVICE = "service"          # 미용/네일/세탁/PC방
SLUG_UNKNOWN = "unknown"

# 키워드 → 슬러그 매칭 (입력이 자유 텍스트이므로 부분 일치)
_KEYWORDS: list[tuple[str, list[str]]] = [
    (SLUG_DELIVERY, ["치킨", "분식", "떡볶이", "김밥", "햄버거", "피자", "족발", "보쌈", "도시락", "배달"]),
    (SLUG_CAFE, ["카페", "커피", "베이커리", "빵", "디저트", "제과", "케이크", "브런치"]),
    (SLUG_RESTAURANT, ["한식", "중식", "일식", "양식", "식당", "음식점", "고기", "회", "초밥", "파스타", "스테이크"]),
    (SLUG_FASHION, ["의류", "화장품", "패션", "옷", "쇼핑몰", "악세", "주얼리", "가방", "신발"]),
    (SLUG_SERVICE, ["미용", "헤어", "네일", "에스테틱", "마사지", "세탁", "피시방", "PC방", "노래방", "스튜디오"]),
    (SLUG_RETAIL, ["편의점", "슈퍼", "마트", "잡화", "문구", "철물", "꽃집", "약국"]),
]


def classify_industry(business_type: Optional[str]) -> str:
    """자유 텍스트 업종 → 6대 슬러그."""
    if not business_type:
        return SLUG_UNKNOWN
    text = business_type.strip().lower()
    for slug, keywords in _KEYWORDS:
        for kw in keywords:
            if kw.lower() in text:
                return slug
    return SLUG_UNKNOWN


# ===== GPT 프롬프트용: 업종별 행동 가이드 블록 =====

_PROMPT_BLOCKS: dict[str, str] = {
    SLUG_DELIVERY: """## 업종 분기 가이드 — 치킨/분식/배달전문
- Hero KPI: 객단가(1만~1.8만원) + 배달 비중(60~80%)
- Top 채널: 배민(필수) > 카카오 채널(단골 발송) > 네이버 플레이스 > 인스타
- 운영 리듬: 17~22시 피크, 금/토 강세, 월요일 약함
- 손실 프레임: "배달앱 노출 점수", "야간 단골 카톡"
- 위험 신호: 객단가 < 8천원 / 점심 매출 < 30% / 폐업률 > 5%
- 카피 예: "오늘 저녁 단골 200명에게 카톡 한 번 보내드릴게요"
- 금지: "인스타 사진 톤 통일" 같은 카페형 조언, "예약 시스템" 같은 서비스업 조언""",

    SLUG_CAFE: """## 업종 분기 가이드 — 카페/베이커리
- Hero KPI: 재방문율(60~70%) + 평일 매출(직장인 점심)
- Top 채널: 인스타(필수) > 네이버 플레이스 > 카카오 채널(스탬프)
- 운영 리듬: 카페 11~15시, 베이커리 8~10+16~19시
- 손실 프레임: "단골 락인 부재", "시그니처 사진 부재"
- 위험 신호: 일 손님 < 30명 / 객단가 < 5천원 / 평일 매출 < 주말 60%
- 카피 예: "신메뉴 사진 1장만 인스타에 올려도 단골 평균 +12명 늘어요"
- 금지: "배민 광고비 늘리세요" (카페는 배달 적합도 낮음)""",

    SLUG_RESTAURANT: """## 업종 분기 가이드 — 한식/중식/일식/양식
- Hero KPI: 점심 회전율(2회+) + 객단가(1.5만~3만원)
- Top 채널: 네이버 플레이스(필수) > 카카오맵 > 캐치테이블/예약
- 운영 리듬: 12~13시 점심 + 18~21시 저녁, 직장 상권은 평일 강세
- 손실 프레임: "직장인 점심 동선 미확보", "회식 예약 미수신"
- 위험 신호: 점심 매출 < 30% / 객단가 < 1.2만원 / 신규 손님 < 20%
- 카피 예: "주변 한식집 평균 객단가는 1만 8천원. 우리 가게는 9천원 더 낮아요"
- 금지: "배민 의존도 낮추세요" (홀 위주 가게에 배달 비판은 무관)""",

    SLUG_RETAIL: """## 업종 분기 가이드 — 편의점/슈퍼/잡화
- Hero KPI: 평당 매출(월 100만+) + 단골 비율(70%+)
- Top 채널: 네이버 플레이스 > 카카오 채널(단골방) > 카카오맵 > 오프라인(전단)
- 운영 리듬: 18~21시 퇴근 피크, 금/토 +30%
- 손실 프레임: "동네 인지도 부족", "매대 입구 30cm 황금 구역 미활용"
- 위험 신호: 평당 매출 < 30만원 / 단골 비율 < 50% / 폐기율 > 5%
- 카피 예: "동네 단골 카톡방 만드시면 신상 알림 한 번에 30명 받아요"
- 금지: "인스타 사진 톤 통일" (편의점은 SNS 효과 낮음)""",

    SLUG_FASHION: """## 업종 분기 가이드 — 의류/화장품/패션
- Hero KPI: 재구매율(25~40%) + 인스타 팔로워(1000명당 +50만원)
- Top 채널: 인스타(필수) > 무신사·29CM 입점 > 네이버 톡톡 1:1 > 카카오 채널
- 운영 리듬: 13~16+19~21시, 봄·가을 시즌 신상 + 연말 +25%
- 손실 프레임: "온라인 노출 부족", "단골 1:1 신상 알림 없음"
- 위험 신호: 인스타 팔로워 < 1000명 / 평당 매출 < 100만원 / 단골 재구매 < 20%
- 카피 예: "신상 입고일 단골 카톡 1:1로 30명에게 발송하면 평균 5건 즉시 주문 들어와요"
- 금지: "배민 입점" (의류는 배달앱 무관)""",

    SLUG_SERVICE: """## 업종 분기 가이드 — 미용/네일/세탁/PC방
- Hero KPI: 재방문율(70%+) + 예약 비율(50%+)
- Top 채널: 네이버 플레이스 + 예약 시스템(필수) > 인스타(BEFORE/AFTER) > 친구 추천 보상
- 운영 리듬: 금/토 주말 외출 준비 강세, 결혼·명절 시즌
- 손실 프레임: "워크인 손실", "단골 5회 시 VIP 등급 부재"
- 위험 신호: 재방문율 < 50% / 예약 비율 < 30% / 후기 별점 < 4.5
- 카피 예: "단골 5회 오시면 시술 10% 할인. VIP 등급제 만드시면 재방문율 +15% 통계 있어요"
- 금지: "배달앱 광고" (서비스업은 배달앱 무관)""",

    SLUG_UNKNOWN: """## 업종 분기 가이드 — 업종 미등록
사장님이 업종을 등록 안 하셨어요. 진단을 일반론으로만 내고, 첫 액션으로
**업종 등록**을 권유하세요. ("업종 등록 1분이면 끝나요. 등록하시면
같은 동네 같은 업종 사장님들 평균과 비교해 드릴 수 있어요.")""",
}


def industry_prompt_block(business_type: Optional[str]) -> str:
    """GPT 시스템 프롬프트에 임베드할 업종 분기 가이드."""
    slug = classify_industry(business_type)
    return _PROMPT_BLOCKS.get(slug, _PROMPT_BLOCKS[SLUG_UNKNOWN])


# ===== marketing_audit.py 5-차원 가중치 =====

# 차원별 base score 가중치 (1.0 = 기본). 업종에 따라 일부 차원의 중요도가 다름.
# - 외식 배달업: timing(피크) + message_fit(핵심 고객 맞춤) 중요
# - 카페: positioning(시그니처) + social_proof(리뷰) 중요
# - 미용: friction(예약) + social_proof(BEFORE/AFTER) 중요
_AUDIT_WEIGHTS: dict[str, dict[str, float]] = {
    SLUG_DELIVERY: {"positioning": 0.9, "message_fit": 1.1, "timing": 1.2, "social_proof": 1.0, "friction": 1.0},
    SLUG_CAFE: {"positioning": 1.2, "message_fit": 1.0, "timing": 0.9, "social_proof": 1.2, "friction": 0.9},
    SLUG_RESTAURANT: {"positioning": 1.0, "message_fit": 1.1, "timing": 1.1, "social_proof": 1.0, "friction": 1.0},
    SLUG_RETAIL: {"positioning": 1.0, "message_fit": 0.9, "timing": 1.0, "social_proof": 1.1, "friction": 1.1},
    SLUG_FASHION: {"positioning": 1.2, "message_fit": 1.1, "timing": 0.9, "social_proof": 1.1, "friction": 0.9},
    SLUG_SERVICE: {"positioning": 1.0, "message_fit": 1.0, "timing": 0.9, "social_proof": 1.2, "friction": 1.2},
    SLUG_UNKNOWN: {"positioning": 1.0, "message_fit": 1.0, "timing": 1.0, "social_proof": 1.0, "friction": 1.0},
}


def industry_audit_weights(business_type: Optional[str]) -> dict[str, float]:
    """5-차원 진단 점수에 곱할 업종별 가중치 (1.0 기준)."""
    return _AUDIT_WEIGHTS[classify_industry(business_type)]


# ===== report_generator.py 6-카테고리 가중치 =====

# 합계는 항상 1.0. 업종에 따라 카테고리 중요도 재분배.
# 기본: 매출 0.25 / 보조금 0.20 / 유동인구 0.20 / 경쟁 0.15 / 코치활용 0.10 / 위험도 0.10
_REPORT_WEIGHTS: dict[str, dict[str, float]] = {
    # 치킨/배달: 유동인구보다 채널 마케팅이 더 중요 → 유동인구 ↓, 코치 활용 ↑
    SLUG_DELIVERY: {"매출 트렌드": 0.28, "보조금 활용": 0.18, "유동인구 활용": 0.12, "경쟁 포지셔닝": 0.20, "코치 활용도": 0.12, "위험도 추세": 0.10},
    # 카페: 유동인구 + 경쟁 포지셔닝(시그니처) 둘 다 중요
    SLUG_CAFE: {"매출 트렌드": 0.22, "보조금 활용": 0.15, "유동인구 활용": 0.25, "경쟁 포지셔닝": 0.20, "코치 활용도": 0.08, "위험도 추세": 0.10},
    # 일반음식점: 표준 분포에 가까움
    SLUG_RESTAURANT: {"매출 트렌드": 0.25, "보조금 활용": 0.18, "유동인구 활용": 0.22, "경쟁 포지셔닝": 0.15, "코치 활용도": 0.10, "위험도 추세": 0.10},
    # 편의점/슈퍼: 유동인구 절대적, 경쟁 포지셔닝은 덜 중요
    SLUG_RETAIL: {"매출 트렌드": 0.25, "보조금 활용": 0.18, "유동인구 활용": 0.30, "경쟁 포지셔닝": 0.10, "코치 활용도": 0.07, "위험도 추세": 0.10},
    # 의류/패션: 유동인구보다 채널·경쟁 포지셔닝(시그니처) 중요
    SLUG_FASHION: {"매출 트렌드": 0.25, "보조금 활용": 0.15, "유동인구 활용": 0.15, "경쟁 포지셔닝": 0.25, "코치 활용도": 0.10, "위험도 추세": 0.10},
    # 미용/서비스: 보조금 활용(인테리어 지원) + 경쟁 포지셔닝(차별 시술) 중요
    SLUG_SERVICE: {"매출 트렌드": 0.22, "보조금 활용": 0.22, "유동인구 활용": 0.18, "경쟁 포지셔닝": 0.18, "코치 활용도": 0.10, "위험도 추세": 0.10},
    SLUG_UNKNOWN: {"매출 트렌드": 0.25, "보조금 활용": 0.20, "유동인구 활용": 0.20, "경쟁 포지셔닝": 0.15, "코치 활용도": 0.10, "위험도 추세": 0.10},
}


def industry_report_weights(business_type: Optional[str]) -> dict[str, float]:
    """PDF 리포트 6-카테고리 가중치 (합계 1.0)."""
    return _REPORT_WEIGHTS[classify_industry(business_type)]


# ===== 업종별 KPI 임계값 (참조용) =====

_KPI_THRESHOLDS: dict[str, dict[str, str]] = {
    SLUG_DELIVERY: {"객단가_위험": "< 8,000원", "배달_비중_위험": "> 80% (수수료 압박)", "별점_위험": "< 4.3"},
    SLUG_CAFE: {"일_손님_위험": "< 30명", "객단가_위험": "< 5,000원", "평일_매출_위험": "< 주말 60%"},
    SLUG_RESTAURANT: {"점심_매출_위험": "< 30%", "객단가_위험": "< 12,000원", "신규_비율_위험": "< 20%"},
    SLUG_RETAIL: {"평당_매출_위험": "< 30만원", "단골_비율_위험": "< 50%", "폐기율_위험": "> 5%"},
    SLUG_FASHION: {"인스타_위험": "< 1000명", "평당_매출_위험": "< 100만원", "재구매_위험": "< 20%"},
    SLUG_SERVICE: {"재방문_위험": "< 50%", "예약_비율_위험": "< 30%", "별점_위험": "< 4.5"},
    SLUG_UNKNOWN: {},
}


def industry_kpi_thresholds(business_type: Optional[str]) -> dict[str, str]:
    """업종별 위험 임계값 표 (사람-친화 문자열)."""
    return _KPI_THRESHOLDS.get(classify_industry(business_type), {})

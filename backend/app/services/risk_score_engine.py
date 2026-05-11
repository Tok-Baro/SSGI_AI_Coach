"""복합 경영 위험도 엔진 — GPT 의존 없는 결정론적 점수 산출.

6가지 요인을 가중 평균하여 0.0~1.0 복합 점수를 산출한다.
데이터가 없는 요인은 가중치를 나머지에 비례 재분배한다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    name: str
    label: str
    score: float  # 0.0 (안전) ~ 1.0 (위험)
    weight: float  # 기본 가중치
    description: str
    data_available: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RiskScoreResult:
    composite_score: float
    factors: list[RiskFactor] = field(default_factory=list)
    trend_direction: str = "stable"  # improving / stable / worsening

    def to_dict(self) -> dict:
        return {
            "composite_score": round(self.composite_score, 3),
            "factors": [f.to_dict() for f in self.factors],
            "trend_direction": self.trend_direction,
        }


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _linear_map(value: float, low_val: float, high_val: float) -> float:
    """low_val → 1.0 (위험), high_val → 0.0 (안전)으로 선형 보간."""
    if high_val == low_val:
        return 0.5
    return _clamp((low_val - value) / (low_val - high_val))


# 서울시 공식 상권변화지표 해석 (2x2 매트릭스)
CHANGE_INDEX_INTERPRETATION = {
    "HH": {"label": "정체", "risk": 0.6, "desc": "시장 포화. 생존업체/폐업업체 모두 영업기간이 서울 평균 이상. 신규 진입 시 차별화 필수."},
    "HL": {"label": "상권축소", "risk": 0.8, "desc": "기존 업체 강세, 신규 진입 실패율 높음. 폐업업체 영업기간이 서울 평균 미만."},
    "LH": {"label": "상권확장", "risk": 0.3, "desc": "신규 진입 기회. 생존업체 영업기간이 짧고 시장이 성장 중."},
    "LL": {"label": "다이나믹", "risk": 0.5, "desc": "높은 회전율. 도시재생/신규 개발 지역. 기회와 위험 공존."},
}


class RiskScoreEngine:
    """결정론적 복합 위험도 산출 엔진.

    서울시 우리마을가게 상권분석 알고리즘 기반:
    - 상권변화지표: 2x2 매트릭스 (생존기간 × 폐업기간 vs 서울 평균)
    - 창업위험도: z(폐업률) + z(3년생존율) / 2
    - 매출/유동인구/경쟁: 선형 보간 스코어링
    """

    # 기본 가중치 (합 = 1.0)
    WEIGHTS = {
        "sales_trend": 0.25,
        "competition": 0.20,
        "commercial_vitality": 0.15,  # 상권변화지표 (서울시 공식)
        "subsidy_urgency": 0.10,
        "population_trend": 0.15,
        "action_engagement": 0.08,
        "business_maturity": 0.07,
    }

    def compute(
        self,
        *,
        sales_data: Optional[dict] = None,
        population_data: Optional[dict] = None,
        competition_data: Optional[dict] = None,
        change_index_data: Optional[dict] = None,
        subsidy_matches: Optional[list] = None,
        action_completion_rate: float = 0.0,
        user_created_at: Optional[date] = None,
        business_start_date: Optional[date] = None,
        previous_scores: Optional[list[float]] = None,
    ) -> RiskScoreResult:
        """복합 위험도 산출.

        Args:
            sales_data: {"quarterly_change_percent": float}
            population_data: {"change_percent": float}
            competition_data: {"opening_rate": float, "closing_rate": float, "total_stores": int}
            subsidy_matches: 매칭된 지원사업 리스트
            action_completion_rate: 최근 30일 액션 완료율 (0.0~1.0)
            user_created_at: 사용자 가입일
            previous_scores: 최근 7일 composite_score 리스트 (추이 판단용)
        """
        factors: list[RiskFactor] = []

        # 1. 매출 트렌드 (↓ = 위험)
        if sales_data and sales_data.get("quarterly_change_percent") is not None:
            change = sales_data["quarterly_change_percent"]
            # -20% → 1.0, +10% → 0.0
            score = _clamp(0.5 - (change / 20.0 * 0.5))
            desc = f"전분기 대비 {change:+.1f}%"
            factors.append(RiskFactor(
                name="sales_trend", label="매출 트렌드",
                score=round(score, 3), weight=self.WEIGHTS["sales_trend"],
                description=desc, data_available=True,
            ))
        else:
            factors.append(RiskFactor(
                name="sales_trend", label="매출 트렌드",
                score=0.0, weight=self.WEIGHTS["sales_trend"],
                description="데이터 없음 (서울 외 지역)",
                data_available=False,
            ))

        # 2. 경쟁 압력 (개업률↑ + 폐업률↓ = 위험)
        if competition_data and competition_data.get("opening_rate") is not None:
            opening = competition_data["opening_rate"]
            closing = competition_data["closing_rate"]
            total = competition_data.get("total_stores", 0)
            # 개업률이 높고 폐업률이 낮으면 경쟁 심화
            # net_pressure: 개업률 - 폐업률. 양수 = 경쟁 증가
            net = opening - closing
            score = _clamp(0.5 + net / 20.0)
            desc = f"점포 {total}개, 개업 {opening:.1f}% / 폐업 {closing:.1f}%"
            factors.append(RiskFactor(
                name="competition", label="경쟁 현황",
                score=round(score, 3), weight=self.WEIGHTS["competition"],
                description=desc, data_available=True,
            ))
        else:
            factors.append(RiskFactor(
                name="competition", label="경쟁 현황",
                score=0.0, weight=self.WEIGHTS["competition"],
                description="데이터 없음 (서울 외 지역)",
                data_available=False,
            ))

        # 3. 상권변화지표 (서울시 공식 알고리즘)
        if change_index_data and change_index_data.get("change_index_code"):
            code = change_index_data["change_index_code"]
            interp = CHANGE_INDEX_INTERPRETATION.get(code, {"label": "미분류", "risk": 0.5, "desc": "분류 불가"})
            status = change_index_data.get("dominant_status", interp["label"])
            score = interp["risk"]
            desc = f"{status} — {interp['desc'][:40]}"
            factors.append(RiskFactor(
                name="commercial_vitality", label="상권변화지표",
                score=round(score, 3), weight=self.WEIGHTS["commercial_vitality"],
                description=desc, data_available=True,
            ))
        else:
            factors.append(RiskFactor(
                name="commercial_vitality", label="상권변화지표",
                score=0.0, weight=self.WEIGHTS["commercial_vitality"],
                description="데이터 없음 (서울 외 지역)",
                data_available=False,
            ))

        # 4. 지원사업 긴급도 (마감 임박 + 미신청 = 위험)
        subsidy_matches = subsidy_matches or []
        if subsidy_matches:
            urgent_count = 0
            total_amount = 0
            for s in subsidy_matches:
                days_left = s.get("days_until_deadline")
                if days_left is not None and 0 <= days_left <= 30:
                    urgent_count += 1
                total_amount += s.get("max_amount", 0) or 0
            # 마감 임박 건수가 많을수록 위험 (놓칠 돈이 많다)
            score = _clamp(urgent_count / 3.0)
            desc = f"매칭 {len(subsidy_matches)}건, 마감 임박 {urgent_count}건 (최대 {total_amount}만원)"
            factors.append(RiskFactor(
                name="subsidy_urgency", label="지원사업 긴급도",
                score=round(score, 3), weight=self.WEIGHTS["subsidy_urgency"],
                description=desc, data_available=True,
            ))
        else:
            factors.append(RiskFactor(
                name="subsidy_urgency", label="지원사업 긴급도",
                score=0.2, weight=self.WEIGHTS["subsidy_urgency"],
                description="매칭 지원사업 없음",
                data_available=True,
            ))

        # 4. 유동인구 추이 (↓ = 위험)
        if population_data and population_data.get("change_percent") is not None:
            change = population_data["change_percent"]
            # -15% → 1.0, +15% → 0.0
            score = _clamp(0.5 - (change / 30.0))
            desc = f"전일 대비 {change:+.1f}%"
            factors.append(RiskFactor(
                name="population_trend", label="유동인구",
                score=round(score, 3), weight=self.WEIGHTS["population_trend"],
                description=desc, data_available=True,
            ))
        else:
            factors.append(RiskFactor(
                name="population_trend", label="유동인구",
                score=0.0, weight=self.WEIGHTS["population_trend"],
                description="데이터 없음 (서울 외 지역)",
                data_available=False,
            ))

        # 5. AI 코치 활용도 (초기 30일은 평가 보류 — 외부 마케팅 무시 방지)
        # 메모리 룰: 사장님이 인스타·배민·오프라인 등 외부 마케팅 하실 수 있음.
        # SSGI 액션 실행률만으로 위험 단정 X — "AI 코치 활용도 낮음"으로만 표현.
        days_since_signup = (date.today() - user_created_at).days if user_created_at else 0
        if days_since_signup < 30:
            # 신규 사용자: 데이터 부족으로 평가 보류 (위험 가산 X)
            factors.append(RiskFactor(
                name="action_engagement", label="AI 코치 활용도",
                score=0.0,  # 위험에 가산 X
                weight=self.WEIGHTS["action_engagement"],
                description=f"가입 {days_since_signup}일차 — 30일 후 측정",
                data_available=False,
            ))
        else:
            engagement_score = _clamp(1.0 - action_completion_rate)
            if action_completion_rate > 0:
                desc = f"최근 30일 활용도 {action_completion_rate:.0%}"
            else:
                desc = "AI 코치 활용도 낮음 (외부 마케팅은 별도)"
            factors.append(RiskFactor(
                name="action_engagement", label="AI 코치 활용도",
                score=round(engagement_score, 3),
                weight=self.WEIGHTS["action_engagement"],
                description=desc, data_available=True,
            ))

        # 6. 사업 성숙도 — 실제 가게 운영 기간 기반 (SSGI 가입일 X)
        # 신규 사장님 (가게 개점 1년 미만) = 통계적으로 위험 높음 (KOSIS 자영업 폐업률)
        if business_start_date:
            operating_months = (date.today() - business_start_date).days / 30.0
            # 0개월 → 0.7, 12개월 → 0.4, 60개월+ → 0.1
            if operating_months < 12:
                score = 0.7 - (operating_months / 12.0) * 0.3
                desc = f"개점 {operating_months:.0f}개월 (1년 미만 신규)"
            elif operating_months < 60:
                score = 0.4 - ((operating_months - 12) / 48.0) * 0.3
                desc = f"개점 {operating_months/12:.1f}년 (안정기 진입 중)"
            else:
                score = 0.1
                desc = f"개점 {operating_months/12:.1f}년 (안정기)"
            factors.append(RiskFactor(
                name="business_maturity", label="가게 운영 기간",
                score=round(_clamp(score), 3), weight=self.WEIGHTS["business_maturity"],
                description=desc, data_available=True,
            ))
        else:
            factors.append(RiskFactor(
                name="business_maturity", label="가게 운영 기간",
                score=0.0, weight=self.WEIGHTS["business_maturity"],
                description="개점일 미입력",
                data_available=False,
            ))

        # 가중 평균 (데이터 없는 요인 제외 후 재분배)
        available = [f for f in factors if f.data_available]
        total_weight = sum(f.weight for f in available)

        if total_weight > 0:
            composite = sum(
                f.score * (f.weight / total_weight) for f in available
            )
        else:
            composite = 0.5  # 모든 데이터 없으면 중간값

        composite = round(_clamp(composite), 3)

        # 추이 판단
        trend = "stable"
        if previous_scores and len(previous_scores) >= 3:
            recent_avg = sum(previous_scores[-3:]) / 3
            older_avg = sum(previous_scores[:max(1, len(previous_scores) - 3)]) / max(1, len(previous_scores) - 3)
            diff = recent_avg - older_avg
            if diff > 0.05:
                trend = "worsening"
            elif diff < -0.05:
                trend = "improving"

        return RiskScoreResult(
            composite_score=composite,
            factors=factors,
            trend_direction=trend,
        )

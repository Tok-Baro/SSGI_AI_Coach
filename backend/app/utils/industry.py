"""업종 분류 + 업종별 KPI/채널/카피 — 지식팩 레지스트리(app.knowledge) 위의 호환 shim.

실제 데이터는 backend/app/knowledge/packs/*.yaml 에 있다. 기존 호출부
(insights.py, action_generator.py, marketing_audit.py, report_generator.py)는
이 모듈의 함수·상수를 그대로 쓰면 된다 — 동작은 동일하다.

* 새 코드는 가능하면 `app.knowledge.registry` 의 resolve()/get() 을 직접 쓰는 것을 권장.
"""
from __future__ import annotations

from typing import Optional

from app.knowledge import registry

# 기존 코드가 import 하던 업종 슬러그 상수 ( == pack id ).
SLUG_DELIVERY = "delivery_food"   # 치킨/분식/배달전문
SLUG_CAFE = "cafe"                # 카페/베이커리
SLUG_RESTAURANT = "restaurant"    # 한식/중식/일식/양식
SLUG_RETAIL = "retail"            # 편의점/슈퍼/잡화
SLUG_FASHION = "fashion"          # 의류/화장품/패션
SLUG_SERVICE = "service"          # 미용/네일/세탁/PC방
SLUG_UNKNOWN = "unknown"


def classify_industry(business_type: Optional[str], industry_slug: Optional[str] = None) -> str:
    """자유 텍스트 업종 → 업종 pack id (없으면 'unknown').

    `industry_slug` 가 주어지고 유효하면(존재하는 pack) 그것을 그대로 쓴다.
    (= 온보딩에서 사용자가 명시 선택한 업종을 우선.)
    """
    return registry.resolve_for(industry_slug, business_type).id


def industry_prompt_block(business_type: Optional[str], industry_slug: Optional[str] = None) -> str:
    """GPT 시스템/유저 프롬프트에 임베드할 업종 분기 가이드."""
    return registry.resolve_for(industry_slug, business_type).prompt_block


def industry_audit_weights(business_type: Optional[str], industry_slug: Optional[str] = None) -> dict[str, float]:
    """marketing_audit 5-차원 점수에 곱할 업종별 가중치 (1.0 기준)."""
    return dict(registry.resolve_for(industry_slug, business_type).audit_weights)


def industry_report_weights(business_type: Optional[str], industry_slug: Optional[str] = None) -> dict[str, float]:
    """PDF 리포트 6-카테고리 가중치 (합계 1.0)."""
    return dict(registry.resolve_for(industry_slug, business_type).report_weights)


def industry_risk_weights(business_type: Optional[str], industry_slug: Optional[str] = None) -> dict[str, float]:
    """risk_score_engine 7-시그널 배율 (1.0 기준). RiskScoreEngine.compute(industry_signal_weights=...) 에 전달."""
    return dict(registry.resolve_for(industry_slug, business_type).risk_signal_weights)


def industry_subsidy_tags(business_type: Optional[str], industry_slug: Optional[str] = None) -> list[str]:
    """이 업종이 자격되기 쉬운 지원사업 카테고리 태그 (RAG 매칭 부스트용 — P2c)."""
    return list(registry.resolve_for(industry_slug, business_type).subsidy_tags)


def industry_top_channel(business_type: Optional[str], industry_slug: Optional[str] = None) -> Optional[str]:
    """이 업종의 1순위 마케팅 채널명 (fit=='high' 인 첫 채널). 없으면 None."""
    for ch in registry.resolve_for(industry_slug, business_type).channels:
        if ch.fit == "high" and ch.applicable:
            return ch.name
    return None


def industry_channels_block(business_type: Optional[str], industry_slug: Optional[str] = None) -> str:
    """업종 채널 표(pack.channels)를 GPT 프롬프트용 마크다운으로 렌더. 채널 데이터 없으면 빈 문자열.

    GPT 가 이 표 밖의 ROI/ROAS 숫자를 만들지 못하게 하는 근거 블록.
    """
    pack = registry.resolve_for(industry_slug, business_type)
    if not pack.channels:
        return ""
    lines = [
        "## 업종 채널 근거표 — 이 표 밖의 ROI/ROAS 숫자를 생성하지 마세요 (비용은 출처 있는 값만, 효과는 매장 데이터로만)",
        "",
    ]
    fit_ko = {"high": "적합도 높음", "medium": "보통", "low": "낮음", "avoid": "비추천"}
    for ch in pack.channels:
        if not ch.applicable:
            continue
        bits: list[str] = [fit_ko.get(ch.fit, ch.fit)]
        if ch.entry_cost_won is not None:
            bits.append("진입 무료" if ch.entry_cost_won == 0 else f"진입 {ch.entry_cost_won:,}원")
        if ch.monthly_budget_min_won:
            if ch.monthly_budget_max_won:
                bits.append(f"월 {ch.monthly_budget_min_won:,}~{ch.monthly_budget_max_won:,}원")
            else:
                bits.append(f"월 {ch.monthly_budget_min_won:,}원+")
        if ch.fee_pct is not None:
            bits.append(f"수수료 {ch.fee_pct}%")
        if ch.per_unit_cost_won is not None:
            bits.append(f"건당 {ch.per_unit_cost_won:g}원")
        if ch.primary_metric:
            bits.append(f"지표 {ch.primary_metric}")
        line = f"- {ch.name} ({' / '.join(bits)})"
        if ch.roi_note:
            line += f": {ch.roi_note}"
        lines.append(line)
    return "\n".join(lines)


def industry_kpi_thresholds(business_type: Optional[str], industry_slug: Optional[str] = None) -> dict[str, str]:
    """업종별 위험 임계값 표 (사람-친화 문자열)."""
    return dict(registry.resolve_for(industry_slug, business_type).kpi_thresholds)

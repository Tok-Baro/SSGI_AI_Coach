"""5-차원 마케팅 진단 (병렬 평가).

coreyhaines31/marketingskills의 page-cro 7단계 프레임워크를 소상공인 매장 도메인으로
재해석. zubair의 5-병렬 subagent 패턴(asyncio.gather)을 적용하여 평가 모듈을
서로 독립적으로 실행.

5-차원:
1. positioning   — 차별화 명확성 (메뉴/업종/타겟)
2. message_fit   — 핵심 고객층 메시지 정합성 (성별/연령)
3. timing        — 피크 시간/요일 활용도
4. social_proof  — k-anonymity 신뢰 신호 노출
5. friction      — 액션 실행 마찰 (완료율)
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from typing import Optional

from app.utils.industry import (
    classify_industry,
    industry_audit_weights,
    industry_top_channel,
)

logger = logging.getLogger(__name__)


@dataclass
class DimensionResult:
    name: str
    label: str
    score: int  # 0-100
    severity: str  # critical | high | medium | low
    headline: str  # 손실 프레이밍 한 줄
    insight: str  # 데이터 근거
    recommendation: str  # 1-액션
    cta_type: Optional[str] = None  # create_coupon | apply_subsidy | view_detail | none

    def to_dict(self) -> dict:
        return asdict(self)


def _severity(score: int) -> str:
    if score < 40:
        return "critical"
    if score < 60:
        return "high"
    if score < 75:
        return "medium"
    return "low"


def _industry_channel_hint(business_type: Optional[str], industry_slug: Optional[str] = None) -> str:
    """recommendation 후미에 붙일 '업종 1순위 채널' 힌트 — 업종팩 channels(fit==high)에서 도출."""
    label = industry_top_channel(business_type, industry_slug)
    if not label:
        return ""
    return f" (사장님 업종은 {label} 우선)"


# ===== 1. 포지셔닝 명확성 =====
async def _eval_positioning(
    business_type: Optional[str],
    coupon_count: int,
    radius_summary: Optional[dict],
    competition_data: Optional[dict],
) -> DimensionResult:
    """차별화 명확성: 업종 등록 + 쿠폰 다양성 + 경쟁 대비 포지션."""
    score = 60
    parts: list[str] = []

    if not business_type:
        score -= 30
        parts.append("업종 미등록 — 타겟이 흐림")
    else:
        parts.append(f"업종 등록: {business_type}")

    if coupon_count == 0:
        score -= 15
        parts.append("쿠폰 0건 — 차별화 메시지 없음")
    elif coupon_count >= 3:
        score += 10
        parts.append(f"쿠폰 {coupon_count}종 운영 — 다양화 양호")

    if radius_summary:
        same = radius_summary.get(business_type or "", 0)
        if same >= 5:
            score -= 20
            parts.append(f"반경 500m 동종 {same}곳 — 차별화 시급")
        elif same >= 2:
            parts.append(f"반경 500m 동종 {same}곳 — 차별화 검토")

    if competition_data:
        opening = competition_data.get("opening_rate", 0) or 0
        closing = competition_data.get("closing_rate", 0) or 0
        if opening - closing > 3:
            score -= 10
            parts.append(f"개업률 {opening}% > 폐업률 {closing}% — 후발주자 진입 중")

    score = max(0, min(100, score))
    sev = _severity(score)

    if score < 60:
        headline = "차별화 포인트가 명확하지 않습니다 — 신규 손님이 다른 가게로 가고 있어요."
        rec = "메뉴/서비스에서 단 하나의 차별화 포인트를 정하고 매장/SNS/쿠폰에 반복 노출하세요."
        cta = "create_coupon"
    else:
        headline = "포지셔닝은 양호합니다."
        rec = "현재 포지셔닝을 유지하되, 분기 1회 점검하세요."
        cta = "view_detail"

    return DimensionResult(
        name="positioning",
        label="포지셔닝 명확성",
        score=score,
        severity=sev,
        headline=headline,
        insight=" / ".join(parts) if parts else "데이터 부족",
        recommendation=rec,
        cta_type=cta,
    )


# ===== 2. 고객 메시지 정합성 =====
async def _eval_message_fit(
    sales_detail: Optional[dict],
    coupons: list[dict],
) -> DimensionResult:
    """핵심 고객층(성별/연령) 데이터에 맞는 메시지를 발신 중인가."""
    if not sales_detail:
        return DimensionResult(
            name="message_fit",
            label="고객 메시지 정합성",
            score=50,
            severity="medium",
            headline="고객 데이터가 없어 메시지가 일반론입니다.",
            insight="서울시 매출 상세 데이터 미제공 (서울 외 지역 가능성)",
            recommendation="포스기/배달앱 데이터로 단골 연령/성별 분포를 직접 확인하세요.",
            cta_type="view_detail",
        )

    score = 65
    parts: list[str] = []

    age = sales_detail.get("age_group") or {}
    gender = sales_detail.get("gender") or {}

    peak_age = max(age, key=age.get) if age else None
    if peak_age:
        parts.append(f"핵심 연령대: {peak_age} ({age[peak_age]}%)")

    male = gender.get("남성_비중", gender.get("남성_매출", 0)) or 0
    female = gender.get("여성_비중", gender.get("여성_매출", 0)) or 0
    if male and female:
        if abs(male - female) > 30:
            dominant = "남성" if male > female else "여성"
            parts.append(f"{dominant} 매출 우세 (M{male}% / F{female}%)")
            # 우세 성별을 무시한 쿠폰만 발행 중이면 감점 — 휴리스틱
            if coupons and len(coupons) >= 2:
                # 쿠폰 제목에 우세 성별 키워드 부재시 감점
                titles = " ".join(c.get("title", "") for c in coupons)
                if dominant == "여성" and not any(k in titles for k in ["여성", "여자", "데이트", "친구"]):
                    score -= 15
                    parts.append("발행 쿠폰이 핵심 고객 성별을 반영 안 함")

    if peak_age and coupons:
        titles = " ".join(c.get("title", "") for c in coupons)
        age_keywords = {"20대": ["청년", "MZ", "20대"], "30대": ["직장인", "30대"], "40대": ["가족", "40대"], "50대": ["50대", "단골"], "60대+": ["어르신", "시니어"]}
        kws = age_keywords.get(peak_age, [])
        if kws and not any(k in titles for k in kws):
            score -= 10
            parts.append(f"발행 쿠폰이 핵심 연령({peak_age})을 반영 안 함")

    if not coupons:
        score -= 10
        parts.append("쿠폰 0건 — 메시지 발신 자체가 없음")

    score = max(0, min(100, score))
    sev = _severity(score)

    if score < 60:
        headline = "핵심 고객층에 맞는 메시지가 부족해 단골 전환 기회를 놓치고 있습니다."
        if peak_age:
            rec = f"{peak_age} 고객용 쿠폰을 1주 안에 1개 발행 — 메뉴/할인을 그 연령대 취향으로 좁히세요."
        else:
            rec = "단골 1명에게 직접 '가장 만족한 메뉴'를 묻고 그 답을 쿠폰 카피로 쓰세요."
        cta = "create_coupon"
    else:
        headline = "핵심 고객층 메시지 정합성은 양호합니다."
        rec = "분기마다 타겟 연령/성별 변화를 재확인하세요."
        cta = "view_detail"

    return DimensionResult(
        name="message_fit",
        label="고객 메시지 정합성",
        score=score,
        severity=sev,
        headline=headline,
        insight=" / ".join(parts) if parts else "데이터 부족",
        recommendation=rec,
        cta_type=cta,
    )


# ===== 3. 타이밍 최적화 =====
async def _eval_timing(
    sales_detail: Optional[dict],
    coupons: list[dict],
    floating_population: Optional[dict],
) -> DimensionResult:
    """피크 시간/요일에 활동 집중 여부."""
    if not sales_detail and not floating_population:
        return DimensionResult(
            name="timing",
            label="타이밍 최적화",
            score=50,
            severity="medium",
            headline="피크 시간 데이터가 없어 활동 타이밍을 판단할 수 없습니다.",
            insight="서울시 매출/유동인구 상세 데이터 미제공",
            recommendation="평소 매출이 가장 높은 요일·시간대를 노트에 기록 → 그 시간대에 쿠폰 활성화.",
            cta_type="view_detail",
        )

    score = 65
    parts: list[str] = []

    peak_day = peak_time = None
    if sales_detail:
        dow = sales_detail.get("day_of_week") or {}
        if dow:
            peak_day = max(dow, key=dow.get)
            parts.append(f"매출 피크 요일: {peak_day} ({dow[peak_day]}%)")
        tz = sales_detail.get("time_zone") or {}
        if tz:
            peak_time = max(tz, key=tz.get)
            parts.append(f"매출 피크 시간대: {peak_time} ({tz[peak_time]}%)")

    if floating_population:
        ftz = floating_population.get("time_zone") or {}
        if ftz:
            float_peak = max(ftz, key=ftz.get)
            parts.append(f"유동인구 피크: {float_peak}")
            if peak_time and float_peak != peak_time:
                parts.append("매출 피크와 유동인구 피크 불일치 — 전환 기회 손실")
                score -= 10

    if not coupons:
        score -= 15
        parts.append("쿠폰 0건 — 피크 시간 활용 메커니즘 없음")
    elif coupons:
        recent_active = sum(1 for c in coupons if c.get("scan_count", 0) > 0)
        if recent_active == 0:
            score -= 10
            parts.append(f"발행 쿠폰 {len(coupons)}건 중 스캔 0건 — 노출 부족")

    score = max(0, min(100, score))
    sev = _severity(score)

    if score < 60:
        if peak_day and peak_time:
            headline = f"{peak_day}요일 {peak_time}시 피크에 이벤트가 없어 매출을 놓치고 있습니다."
            rec = f"{peak_day}요일 {peak_time}시 한정 시간 쿠폰을 1주 단위로 자동 발행하세요."
        elif peak_day:
            headline = f"{peak_day}요일 피크에 활동이 부족합니다."
            rec = f"{peak_day}요일 한정 메뉴/쿠폰을 운영하세요."
        else:
            headline = "피크 타이밍 활용이 약합니다."
            rec = "유동인구 피크 시간대에 매장 외관/SNS 노출을 늘리세요."
        cta = "create_coupon"
    else:
        headline = "타이밍 활용은 양호합니다."
        rec = "현재 패턴을 유지하되, 비수기 요일도 보강 검토."
        cta = "view_detail"

    return DimensionResult(
        name="timing",
        label="타이밍 최적화",
        score=score,
        severity=sev,
        headline=headline,
        insight=" / ".join(parts) if parts else "데이터 부족",
        recommendation=rec,
        cta_type=cta,
    )


# ===== 4. 사회적 증거 =====
async def _eval_social_proof(
    same_dong_count: int,
    coupon_scanned: int,
    coupon_created: int,
    nearby_competitors_count: int,
) -> DimensionResult:
    """k-anonymity 사회적 증거 + 쿠폰 스캔 누적 + 주변 비교군."""
    K = 10
    score = 50
    parts: list[str] = []

    if same_dong_count >= K:
        score += 20
        parts.append(f"동네 동종 {same_dong_count}곳 가입 — 신뢰 신호 가능")
    else:
        score -= 10
        parts.append(f"동네 동종 {same_dong_count}곳 (k={K} 미달, 콜드스타트)")

    if coupon_created > 0:
        scan_rate = coupon_scanned / coupon_created
        if scan_rate >= 3:
            score += 15
            parts.append(f"쿠폰 평균 스캔 {scan_rate:.1f}회 — 입소문 가능")
        elif scan_rate < 1:
            score -= 10
            parts.append(f"쿠폰 평균 스캔 {scan_rate:.1f}회 — 노출 부족")
        else:
            parts.append(f"쿠폰 평균 스캔 {scan_rate:.1f}회")

    if nearby_competitors_count >= 5:
        parts.append(f"주변 경쟁점 {nearby_competitors_count}곳 — 비교군 풍부")
    elif nearby_competitors_count == 0:
        score -= 5

    score = max(0, min(100, score))
    sev = _severity(score)

    if score < 60:
        headline = "신뢰 신호(리뷰/단골 수)가 외부에 보이지 않아 신규 고객이 망설입니다."
        rec = "최근 단골 5명에게 한 줄 후기를 받아 매장/SNS에 게시 — 1주 내 가능합니다."
        cta = "create_coupon"
    else:
        headline = "사회적 증거 노출은 양호합니다."
        rec = "월 1회 후기/스캔 통계를 매장에 노출 갱신하세요."
        cta = "view_detail"

    return DimensionResult(
        name="social_proof",
        label="사회적 증거 노출",
        score=score,
        severity=sev,
        headline=headline,
        insight=" / ".join(parts) if parts else "데이터 부족",
        recommendation=rec,
        cta_type=cta,
    )


# ===== 5. 마찰 제거 =====
async def _eval_friction(
    action_completion_rate: float,
    total_actions_30d: int,
    pending_subsidy_amount: int,
) -> DimensionResult:
    """액션 실행 마찰 (완료율 + 미신청 누적 손실)."""
    score = int(action_completion_rate * 100)
    parts: list[str] = [f"30일 액션 완료율 {score}% ({total_actions_30d}건 중)"]

    if pending_subsidy_amount > 0:
        parts.append(f"미신청 지원금 누적 {pending_subsidy_amount}만원")
        if pending_subsidy_amount >= 1000:
            score = max(0, score - 15)
            parts.append("미신청 누적이 큼 — 마찰 큼")

    if total_actions_30d == 0:
        score = 30
        parts.append("최근 30일 액션 0건 (신규 가입 또는 미사용)")

    score = max(0, min(100, score))
    sev = _severity(score)

    if score < 60:
        headline = "액션이 누적만 되고 실행되지 않아 손실이 쌓이고 있습니다."
        if pending_subsidy_amount > 0:
            rec = f"오늘 보조금 1건만 신청 클릭 — 누적 미신청 {pending_subsidy_amount}만원의 첫 단계."
            cta = "apply_subsidy"
        else:
            rec = "오늘 액션 1개만 완료 표시하면 위험도가 즉시 1단계 내려갑니다."
            cta = "view_detail"
    else:
        headline = "실행 마찰은 낮은 편입니다."
        rec = "현재 페이스 유지 — 주 5회 이상 접속 권장."
        cta = "view_detail"

    return DimensionResult(
        name="friction",
        label="실행 마찰",
        score=score,
        severity=sev,
        headline=headline,
        insight=" / ".join(parts),
        recommendation=rec,
        cta_type=cta,
    )


# ===== 공개 API: 5-차원 병렬 평가 =====
async def evaluate(
    *,
    business_type: Optional[str],
    sales_detail: Optional[dict],
    competition_data: Optional[dict],
    floating_population: Optional[dict],
    radius_summary: Optional[dict],
    coupons: list[dict],
    coupon_created: int,
    coupon_scanned: int,
    same_dong_count: int,
    nearby_competitors_count: int,
    action_completion_rate: float,
    total_actions_30d: int,
    pending_subsidy_amount: int,
    industry_slug: Optional[str] = None,
) -> dict:
    """5-차원 병렬 평가 → {dimensions: [...], overall_score: int, weakest: str, summary: str}.

    overall_score는 업종별 가중치를 적용한 가중 평균.
    weakest는 가중치 적용 후 점수 기준 (즉, 그 업종에서 진짜 시급한 차원).
    """
    results = await asyncio.gather(
        _eval_positioning(business_type, coupon_created, radius_summary, competition_data),
        _eval_message_fit(sales_detail, coupons),
        _eval_timing(sales_detail, coupons, floating_population),
        _eval_social_proof(same_dong_count, coupon_scanned, coupon_created, nearby_competitors_count),
        _eval_friction(action_completion_rate, total_actions_30d, pending_subsidy_amount),
    )

    # 업종별 가중치 적용 (예: 카페는 positioning + social_proof 중요, 미용은 friction 중요)
    weights = industry_audit_weights(business_type, industry_slug)
    weighted_sum = sum(r.score * weights.get(r.name, 1.0) for r in results)
    weight_total = sum(weights.get(r.name, 1.0) for r in results)
    overall = int(weighted_sum / weight_total) if weight_total else int(sum(r.score for r in results) / len(results))

    # weakest는 가중치 보정 점수 기준 (그 업종에서 점수 낮으면서 비중 높은 차원)
    weakest = min(results, key=lambda r: r.score / max(weights.get(r.name, 1.0), 0.01))

    # 업종 채널 힌트를 score < 60인 차원의 recommendation 끝에 부착
    channel_hint = _industry_channel_hint(business_type, industry_slug)
    if channel_hint:
        for r in results:
            if r.score < 60 and channel_hint not in (r.recommendation or ""):
                r.recommendation = (r.recommendation or "") + channel_hint

    return {
        "dimensions": [r.to_dict() for r in results],
        "overall_score": overall,
        "weakest_dimension": weakest.name,
        "weakest_label": weakest.label,
        "weakest_headline": weakest.headline,
        "industry_slug": classify_industry(business_type, industry_slug),
        "summary": _build_summary(overall, weakest, results),
    }


def _build_summary(overall: int, weakest: DimensionResult, all_results: list[DimensionResult]) -> str:
    critical = [r for r in all_results if r.severity == "critical"]
    high = [r for r in all_results if r.severity == "high"]
    if critical:
        names = ", ".join(r.label for r in critical)
        return f"종합 {overall}점 — Critical 차원 {len(critical)}건 ({names}). 가장 시급: {weakest.headline}"
    if high:
        names = ", ".join(r.label for r in high)
        return f"종합 {overall}점 — 개선 필요 차원 {len(high)}건 ({names})."
    return f"종합 {overall}점 — 모든 차원이 양호 범위입니다. 약한 차원: {weakest.label}."


def weakest_dimension_for_prompt(audit_result: dict) -> str:
    """action_generator GPT 프롬프트에 주입할 수 있도록 약점 차원만 짧게 요약."""
    if not audit_result:
        return ""
    return (
        f"[5-차원 진단 약점] {audit_result.get('weakest_label', '')}: "
        f"{audit_result.get('weakest_headline', '')}"
    )

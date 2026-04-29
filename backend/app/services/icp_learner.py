"""ICP (Ideal Customer Profile) Learner — 사용자 선호 패턴 학습.

ericosiu/ai-marketing-skills의 sales-pipeline/icp_learning_analyzer.py 패턴을
보조금 매칭 도메인으로 적용. 사용자가 어떤 보조금에 관심을 보였는지(view/click/draft/apply)
누적된 신호를 분석하여 선호 프로필을 자동 추출 → RAG 매칭 결과 재순위에 사용.
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subsidy import Subsidy
from app.models.subsidy_interaction import SubsidyInteraction

logger = logging.getLogger(__name__)

# 신호 강도 기본값 (라우터에서 override 가능)
SIGNAL_WEIGHTS = {
    "view": 0.2,
    "click": 1.0,
    "draft": 3.0,
    "apply": 5.0,
}

# 학습 윈도우 (90일)
LEARNING_WINDOW_DAYS = 90

# 시간 가중치 반감기 (30일)
DECAY_HALF_LIFE_DAYS = 30

# 최소 신호 수 (이하면 ICP 적용 안 함)
MIN_SIGNALS = 2


@dataclass
class ICPProfile:
    """학습된 사용자 선호 프로필."""
    has_signals: bool = False
    signal_count: int = 0
    weighted_signal_total: float = 0.0
    preferred_organizations: dict[str, float] = field(default_factory=dict)
    amount_median: Optional[float] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    keyword_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "has_signals": self.has_signals,
            "signal_count": self.signal_count,
            "weighted_signal_total": round(self.weighted_signal_total, 2),
            "preferred_organizations": [
                {"name": k, "score": round(v, 2)}
                for k, v in sorted(self.preferred_organizations.items(), key=lambda x: -x[1])[:5]
            ],
            "amount_range": {
                "median": self.amount_median,
                "min": self.amount_min,
                "max": self.amount_max,
            } if self.amount_median is not None else None,
            "top_keywords": [
                {"word": k, "score": round(v, 2)}
                for k, v in sorted(self.keyword_scores.items(), key=lambda x: -x[1])[:10]
            ],
        }


# ===== 키워드 추출 =====

_TOKEN_PATTERN = re.compile(r"[가-힣A-Za-z0-9]{2,}")
_STOPWORDS = {
    "지원", "사업", "신청", "안내", "공고", "모집", "선정", "관련",
    "사항", "내용", "위한", "위해", "통해", "기관", "센터", "소상공인",
    "and", "or", "the", "for", "with", "from",
}


def _extract_keywords(*texts: Optional[str]) -> set[str]:
    tokens: set[str] = set()
    for t in texts:
        if not t:
            continue
        for m in _TOKEN_PATTERN.finditer(t):
            tok = m.group()
            if tok in _STOPWORDS:
                continue
            tokens.add(tok)
    return tokens


# ===== 시간 가중치 =====

def _decay_weight(created_at: datetime, now: datetime) -> float:
    """시간 경과에 따른 가중치 감쇠 (반감기 30일)."""
    delta_days = (now - created_at).total_seconds() / 86400
    if delta_days <= 0:
        return 1.0
    return math.pow(0.5, delta_days / DECAY_HALF_LIFE_DAYS)


# ===== 학습 =====

async def learn_user_profile(db: AsyncSession, user_id: UUID) -> ICPProfile:
    """사용자의 누적 신호 → ICP 프로필."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=LEARNING_WINDOW_DAYS)

    stmt = (
        select(SubsidyInteraction, Subsidy)
        .join(Subsidy, SubsidyInteraction.subsidy_id == Subsidy.id)
        .where(
            SubsidyInteraction.user_id == user_id,
            SubsidyInteraction.created_at >= cutoff,
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    if len(rows) < MIN_SIGNALS:
        return ICPProfile()

    profile = ICPProfile(has_signals=True, signal_count=len(rows))
    org_scores: dict[str, float] = {}
    keyword_scores: dict[str, float] = {}
    weighted_amounts: list[tuple[float, float]] = []  # (amount, weight)

    for interaction, subsidy in rows:
        signal_w = interaction.weight or SIGNAL_WEIGHTS.get(interaction.signal_type, 1.0)
        time_w = _decay_weight(
            interaction.created_at if interaction.created_at.tzinfo else interaction.created_at.replace(tzinfo=timezone.utc),
            now,
        )
        w = signal_w * time_w
        profile.weighted_signal_total += w

        if subsidy.organization:
            org_scores[subsidy.organization] = org_scores.get(subsidy.organization, 0.0) + w

        if subsidy.max_amount and subsidy.max_amount > 0:
            weighted_amounts.append((float(subsidy.max_amount), w))

        for kw in _extract_keywords(subsidy.title, subsidy.eligibility_summary):
            keyword_scores[kw] = keyword_scores.get(kw, 0.0) + w

    profile.preferred_organizations = org_scores
    profile.keyword_scores = keyword_scores

    if weighted_amounts:
        # 가중 중앙값/최소/최대
        weighted_amounts.sort()
        total_w = sum(w for _, w in weighted_amounts)
        cum = 0.0
        median = weighted_amounts[-1][0]
        for amt, w in weighted_amounts:
            cum += w
            if cum >= total_w / 2:
                median = amt
                break
        profile.amount_median = median
        profile.amount_min = weighted_amounts[0][0]
        profile.amount_max = weighted_amounts[-1][0]

    return profile


# ===== 적용: 매칭 결과에 ICP 점수 가산 =====

def score_subsidy(subsidy_dict: dict, profile: ICPProfile) -> float:
    """0~1 사이 ICP boost. profile에 신호가 없으면 0."""
    if not profile.has_signals:
        return 0.0

    score = 0.0

    org = subsidy_dict.get("organization", "")
    if org and org in profile.preferred_organizations:
        # 선호 기관일수록 boost (max 0.4)
        org_max = max(profile.preferred_organizations.values())
        score += min(profile.preferred_organizations[org] / org_max * 0.4, 0.4) if org_max else 0

    amount = subsidy_dict.get("max_amount") or 0
    if amount > 0 and profile.amount_median:
        # median 기준 ±50% 이내면 boost (max 0.3)
        ratio = amount / profile.amount_median
        if 0.5 <= ratio <= 1.5:
            score += 0.3
        elif 0.25 <= ratio <= 2.0:
            score += 0.15

    title = subsidy_dict.get("title", "")
    eligibility = subsidy_dict.get("eligibility_summary", "")
    sub_keywords = _extract_keywords(title, eligibility)
    if sub_keywords and profile.keyword_scores:
        kw_max = max(profile.keyword_scores.values())
        overlap_score = sum(
            profile.keyword_scores[k] / kw_max
            for k in sub_keywords
            if k in profile.keyword_scores
        )
        # 키워드 기여 (max 0.3)
        score += min(overlap_score * 0.05, 0.3)

    return min(score, 1.0)


def rerank_with_icp(matches: list[dict], profile: ICPProfile) -> list[dict]:
    """기존 relevance_score + icp_boost로 재정렬. 마감일 가까운 것은 가중 유지."""
    if not profile.has_signals or not matches:
        return matches

    for m in matches:
        boost = score_subsidy(m, profile)
        m["icp_boost"] = round(boost, 3)
        base = m.get("relevance_score", 0) or 0
        deadline_penalty = 0.0
        days = m.get("days_until_deadline")
        if days is not None:
            if days < 0:
                deadline_penalty = 1.0  # 마감 지난 건 강하게 밀림
            elif days < 7:
                deadline_penalty = -0.2  # 임박은 우선

        m["composite_score"] = round(base + boost - deadline_penalty, 3)

    matches.sort(key=lambda x: -(x.get("composite_score", 0)))
    return matches


# ===== 신호 기록 헬퍼 =====

async def log_signal(
    db: AsyncSession,
    user_id: UUID,
    subsidy_id: UUID,
    signal_type: str,
    weight: Optional[float] = None,
) -> None:
    """신호 1건 기록. 라우터에서 호출."""
    if signal_type not in SIGNAL_WEIGHTS:
        logger.warning(f"Unknown signal_type: {signal_type}")
        return

    interaction = SubsidyInteraction(
        user_id=user_id,
        subsidy_id=subsidy_id,
        signal_type=signal_type,
        weight=weight if weight is not None else SIGNAL_WEIGHTS[signal_type],
    )
    db.add(interaction)
    try:
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to log signal: {e}")
        await db.rollback()

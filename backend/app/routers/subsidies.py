"""
지원사업 라우터
- GET  /subsidies/matches:        사용자 맞춤 지원사업 목록 (ICP 재순위)
- POST /subsidies/apply-draft:    사업계획서 초안 생성 (GPT-4o) + draft 신호 로깅
- POST /subsidies/{id}/click:     클릭 신호 로깅 (ICP 학습용)
- GET  /subsidies/icp-profile:    학습된 사용자 선호 프로필 조회
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.subsidy import (
    SubsidyMatchesResponse, SubsidyResponse,
    ApplyDraftRequest, ApplyDraftResponse,
)
from app.services.rag_service import RAGService
from app.services.action_generator import ActionGenerator
from app.services.social_proof_service import SocialProofService
from app.services import icp_learner
from app.utils.auth import get_current_user
from app.models import User, Subsidy

router = APIRouter()


@router.get("/matches", response_model=SubsidyMatchesResponse)
async def get_subsidy_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 업종/지역 기반 지원사업 RAG 매칭."""
    rag = RAGService()
    results = await rag.search_subsidies_filtered(
        db=db,
        gu_name=current_user.gu_name or "",
        business_type=current_user.business_type or "",
        top_k=10,
        user_id=current_user.id,
        industry_slug=current_user.industry_slug,
    )

    # P1-8: N+1 제거 — for-loop 안에서 동일 동네 count 조회를 N회 반복하던 패턴을
    # 한 번의 social_proof get_subsidy_proof 호출로 collapse (동네/업종은 user 단일).
    # subsidy_title은 결과 메시지에 영향 없으므로 한 번만 계산.
    social = SocialProofService(db)
    shared_proof = await social.get_subsidy_proof(
        current_user.dong_name or "", current_user.business_type or "", ""
    )
    enriched = []
    total_amount = 0

    for r in results:
        enriched.append(SubsidyResponse(
            id=r["id"],
            title=r["title"],
            organization=r["organization"],
            deadline=r.get("deadline"),
            max_amount=r.get("max_amount"),
            eligibility_summary=r.get("eligibility_summary"),
            description=r["description"],
            application_url=r.get("application_url"),
            relevance_score=r.get("relevance_score", 0),
            days_until_deadline=r.get("days_until_deadline"),
            social_proof_message=shared_proof,
        ))
        if r.get("max_amount"):
            total_amount += r["max_amount"]

    loss_msg = f"사장님, 지금 신청 가능한 지원금 최대 {total_amount}만원을 놓치고 있습니다."
    if total_amount == 0:
        loss_msg = "현재 매칭되는 지원사업이 없습니다. 새로운 공고가 나오면 알려드리겠습니다."

    return SubsidyMatchesResponse(
        matches=enriched,
        total_potential_amount=total_amount,
        loss_message=loss_msg,
    )


@router.post("/apply-draft", response_model=ApplyDraftResponse)
async def generate_apply_draft(
    req: ApplyDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """지원사업 사업계획서 초안 생성 (GPT-4o). user당 시간당 10회 제한."""
    from app.utils.rate_limit import apply_draft_rate
    apply_draft_rate.check(f"apply_draft:{current_user.id}")
    # free 플랜은 월 N회 제한 (월 5회 예시) — plan_tier 검사
    # 추가: TODO P1 — 월별 카운터 별도 구현 필요. 현재는 시간당만.
    stmt = select(Subsidy).where(Subsidy.id == req.subsidy_id)
    result = await db.execute(stmt)
    subsidy = result.scalar_one_or_none()
    if not subsidy:
        raise HTTPException(status_code=404, detail="해당 지원사업을 찾을 수 없습니다.")

    generator = ActionGenerator()
    draft = await generator.generate_business_plan_draft(
        user=current_user,
        subsidy=subsidy,
        additional_info=req.additional_info,
    )

    # ICP 학습 신호 (강한 신호 — 초안까지 생성한 보조금)
    await icp_learner.log_signal(db, current_user.id, subsidy.id, "draft")

    return ApplyDraftResponse(
        draft_text=draft,
        subsidy_title=subsidy.title,
        estimated_time_saved="약 2시간",
    )


@router.post("/{subsidy_id}/signal")
async def log_subsidy_signal(
    subsidy_id: UUID,
    signal_type: str = "click",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """ICP 학습 신호 로깅. signal_type: view | click | draft | apply.

    UI에서 카드 탭 → 'click', 외부 신청 페이지 이동 → 'apply'.
    """
    if signal_type not in {"view", "click", "draft", "apply"}:
        raise HTTPException(status_code=400, detail="올바르지 않은 signal_type입니다.")

    stmt = select(Subsidy.id).where(Subsidy.id == subsidy_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="해당 지원사업을 찾을 수 없습니다.")

    await icp_learner.log_signal(db, current_user.id, subsidy_id, signal_type)
    return {"ok": True, "signal_type": signal_type}


@router.get("/icp-profile")
async def get_icp_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """학습된 사용자 선호 프로필 조회 (UI에 노출용)."""
    profile = await icp_learner.learn_user_profile(db, current_user.id)
    return profile.to_dict()

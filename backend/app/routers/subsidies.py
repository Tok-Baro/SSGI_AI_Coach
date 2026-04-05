"""
지원사업 라우터
- GET  /subsidies/matches: 사용자 맞춤 지원사업 목록
- POST /subsidies/apply-draft: 사업계획서 초안 생성 (GPT-4o)
"""
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
    query = f"{current_user.gu_name} {current_user.dong_name} {current_user.business_type} 소상공인 지원금 보조금"
    results = await rag.search_subsidies(query, top_k=10)

    social = SocialProofService(db)
    enriched = []
    total_amount = 0

    for r in results:
        proof_msg = await social.get_subsidy_proof(
            current_user.dong_name or "", current_user.business_type or "", r.get("title", "")
        )
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
            social_proof_message=proof_msg,
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
    """지원사업 사업계획서 초안 생성 (GPT-4o)."""
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

    return ApplyDraftResponse(
        draft_text=draft,
        subsidy_title=subsidy.title,
        estimated_time_saved="약 2시간",
    )

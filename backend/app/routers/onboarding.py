"""
온보딩 라우터
- POST /onboarding/verify-business: 사업자등록번호 유효성 검증
- GET  /onboarding/search-business: 카카오 로컬 상호명 검색
- POST /onboarding/complete: 온보딩 완료
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.onboarding import (
    VerifyBusinessRequest, VerifyBusinessResponse,
    KakaoLocalSearchResult, CompleteOnboardingRequest, CompleteOnboardingResponse,
)
from app.services.nts_service import NTSService
from app.services.kakao_service import KakaoService
from app.services.seoul_api_service import SeoulAPIService
from app.services.rag_service import RAGService
from app.services.action_generator import ActionGenerator
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/verify-business", response_model=VerifyBusinessResponse)
async def verify_business(
    req: VerifyBusinessRequest,
    current_user: User = Depends(get_current_user),
):
    """사업자등록번호 유효성 검증 (국세청 API)."""
    nts = NTSService()
    result = await nts.verify_business_number(req.business_number)
    if result is None:
        raise HTTPException(status_code=502, detail="국세청 API 연결에 실패했습니다. 잠시 후 다시 시도해주세요.")
    return result


@router.get("/search-business", response_model=List[KakaoLocalSearchResult])
async def search_business(
    query: str = Query(..., min_length=1, description="상호명 검색어"),
    current_user: User = Depends(get_current_user),
):
    """카카오 로컬 검색으로 상호명 자동완성."""
    kakao = KakaoService()
    results = await kakao.search_local(query, size=5)
    if results is None:
        raise HTTPException(status_code=502, detail="카카오 검색에 실패했습니다.")
    return results


@router.post("/complete", response_model=CompleteOnboardingResponse)
async def complete_onboarding(
    req: CompleteOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    온보딩 완료: 사업 정보 저장 + 서울시 API 병렬 호출 + RAG 지원사업 매칭.
    """
    # 1. 사업 정보 저장
    current_user.business_number = req.business_number
    current_user.business_name = req.business_name
    current_user.business_type = req.business_type
    current_user.address = req.address
    current_user.dong_name = req.dong_name
    current_user.gu_name = req.gu_name
    current_user.lat = req.lat
    current_user.lng = req.lng
    current_user.onboarding_completed = True

    # 2. 서울시 API 3종 병렬 호출
    seoul = SeoulAPIService()
    sales_task = seoul.get_commercial_sales(req.gu_name, req.dong_name, req.business_type)
    population_task = seoul.get_living_population(req.dong_name)
    events_task = seoul.get_cultural_events(req.gu_name)

    sales_data, population_data, events_data = await asyncio.gather(
        sales_task, population_task, events_task,
        return_exceptions=True,
    )

    # 3. RAG 지원사업 매칭
    rag = RAGService()
    query_text = f"{req.gu_name} {req.dong_name} {req.business_type} 소상공인 지원사업"
    matched_subsidies = await rag.search_subsidies(query_text, top_k=5)
    subsidy_count = len(matched_subsidies)

    # 4. 초기 위험 점수
    risk_score = 0.3
    if isinstance(sales_data, dict) and sales_data.get("quarterly_change_percent"):
        change = sales_data["quarterly_change_percent"]
        if change < -10:
            risk_score = 0.7
        elif change < -5:
            risk_score = 0.5
        elif change < 0:
            risk_score = 0.3
        else:
            risk_score = 0.1

    # 5. 첫 daily_action 생성
    generator = ActionGenerator()
    await generator.create_initial_action(
        db=db,
        user=current_user,
        matched_subsidies=matched_subsidies,
        sales_data=sales_data if not isinstance(sales_data, Exception) else None,
        population_data=population_data if not isinstance(population_data, Exception) else None,
        events_data=events_data if not isinstance(events_data, Exception) else None,
    )

    return CompleteOnboardingResponse(
        success=True,
        message=f"사장님, 지원사업 {subsidy_count}건을 찾았습니다!",
        subsidy_count=subsidy_count,
        risk_score=risk_score,
    )

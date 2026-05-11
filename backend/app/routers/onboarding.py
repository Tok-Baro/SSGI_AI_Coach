"""
온보딩 라우터 (보안 강화)
- POST /onboarding/verify-business: 사업자등록번호 유효성 검증 + 검증 토큰 발급
- GET  /onboarding/search-business: 카카오 로컬 상호명 검색
- POST /onboarding/complete: 온보딩 완료 (검증 토큰 필수)
"""
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db, async_session_factory
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
from app.utils.business_type import normalize_business_type
from app.utils.industry import classify_industry, industry_risk_weights
from app.utils.rate_limit import onboarding_rate
from app.utils.verification import create_verification_token, verify_verification_token
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# 온보딩 시도 최대 횟수 (브루트포스 방지)
MAX_ONBOARDING_ATTEMPTS = 10


@router.post("/verify-business", response_model=VerifyBusinessResponse)
async def verify_business(
    req: VerifyBusinessRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사업자등록번호 유효성 검증 (국세청 API).

    보안:
    - 이미 온보딩 완료된 사용자는 재검증 차단
    - 다른 사용자가 이미 등록한 사업자번호 차단
    - 시도 횟수 제한 + IP rate limit (NTS API 비용/할당량 보호)
    """
    # IP-based rate limit (user-level과 별개로 봇 차단)
    onboarding_rate.check(request.client.host if request.client else "unknown")

    # 0. detached 사용자 객체 재부착 (get_current_user 세션 분리 대응)
    db.add(current_user)

    # 1. 이미 온보딩 완료된 사용자 차단
    if current_user.onboarding_completed:
        raise HTTPException(
            status_code=409,
            detail="이미 사업자 등록이 완료되었습니다. 변경이 필요하면 고객센터에 문의하세요.",
        )

    # 2. 시도 횟수 제한
    if current_user.onboarding_attempts >= MAX_ONBOARDING_ATTEMPTS:
        logger.warning(
            "온보딩 시도 초과: user_id=%s, attempts=%d",
            current_user.id, current_user.onboarding_attempts,
        )
        raise HTTPException(
            status_code=429,
            detail="사업자 검증 시도 횟수를 초과했습니다. 고객센터에 문의하세요.",
        )

    # 3. 시도 횟수 증가
    current_user.onboarding_attempts += 1

    # 4. 다른 사용자가 이미 등록한 사업자번호 차단
    stmt = select(User).where(
        User.business_number == req.business_number,
        User.onboarding_completed == True,
        User.id != current_user.id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="이미 등록된 사업자번호입니다.",
        )

    # 5. 국세청 API 검증
    nts = NTSService()
    nts_result = await nts.verify_business_number(req.business_number)
    if nts_result is None:
        raise HTTPException(
            status_code=502,
            detail="국세청 API 연결에 실패했습니다. 잠시 후 다시 시도해주세요.",
        )

    # 6. 검증 성공 시 토큰 발급 (계속사업자만)
    verification_token = None
    if nts_result["is_valid"]:
        verification_token = create_verification_token(
            user_id=str(current_user.id),
            business_number=req.business_number,
        )
        current_user.business_verified_at = datetime.now(timezone.utc)

    nts_result["verification_token"] = verification_token
    return nts_result


@router.get("/search-business", response_model=List[KakaoLocalSearchResult])
async def search_business(
    query: str = Query(..., min_length=1, max_length=100, description="상호명 검색어"),
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
):
    """온보딩 완료: 검증 토큰 확인 → 사업 정보 저장 → 서울시 API → RAG 매칭.

    Phased pattern:
    - A1: dedupe check + user record save (DB short session, commit)
    - B: Seoul API gather (no DB)
    - A2: RAG + first action (DB short session)

    보안:
    - 이미 온보딩 완료된 사용자 차단
    - verification_token으로 사업자 검증 여부 확인
    - 토큰의 user_id + business_number 바인딩 검증
    - 사업자번호 중복 재확인 (race condition 방지)
    """
    # 1. 이미 완료된 사용자 차단 (검증 토큰 전 빠른 cutoff)
    if current_user.onboarding_completed:
        raise HTTPException(
            status_code=409,
            detail="이미 사업자 등록이 완료되었습니다.",
        )

    # 2. 검증 토큰 확인 (verify-business를 거쳤는지)
    if not verify_verification_token(
        token=req.verification_token,
        user_id=str(current_user.id),
        business_number=req.business_number,
    ):
        raise HTTPException(
            status_code=403,
            detail="사업자 검증이 완료되지 않았거나 검증 유효시간(10분)이 초과되었습니다. 다시 검증해주세요.",
        )

    canonical_btype = normalize_business_type(req.business_type)

    # === Phase A1: dedupe + user record persist (DB short session) ===
    async with async_session_factory() as db:
        db.add(current_user)
        # 사업자번호 중복 재확인 (동시 요청 race 방지)
        existing = (await db.execute(
            select(User).where(
                User.business_number == req.business_number,
                User.onboarding_completed == True,
                User.id != current_user.id,
            )
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="이미 등록된 사업자번호입니다.")

        # 사업 정보 저장 (canonical taxonomy로 정규화)
        current_user.business_number = req.business_number
        current_user.business_name = req.business_name
        current_user.business_type = canonical_btype
        # 업종 지식팩 매핑: 피커에서 명시 선택한 industry_slug 가 있으면 우선, 없으면 입력 업종명으로 분류.
        current_user.industry_slug = classify_industry(req.business_type, req.industry_slug)
        current_user.address = req.address
        current_user.dong_name = req.dong_name
        current_user.gu_name = req.gu_name
        current_user.lat = req.lat
        current_user.lng = req.lng
        current_user.business_start_date = req.business_start_date
        current_user.onboarding_completed = True
        await db.commit()
    # === DB session closed ===

    # === Phase B: Seoul API 병렬 호출 (no DB) ===
    seoul = SeoulAPIService()
    sales_data, population_data, events_data = await asyncio.gather(
        seoul.get_commercial_sales(req.gu_name, req.dong_name, canonical_btype),
        seoul.get_living_population(req.dong_name, req.gu_name),
        seoul.get_cultural_events(req.gu_name),
        return_exceptions=True,
    )

    # === Phase A2: RAG + first action (DB short session) ===
    async with async_session_factory() as db:
        db.add(current_user)
        rag = RAGService()
        matched_subsidies = await rag.search_subsidies_filtered(
            db=db,
            gu_name=req.gu_name or "",
            business_type=canonical_btype,
            top_k=5,
            industry_slug=current_user.industry_slug,
        )
        subsidy_count = len(matched_subsidies)

        # 위험도 엔진 (DB 무관)
        from app.services.risk_score_engine import RiskScoreEngine
        engine = RiskScoreEngine()
        risk_result = engine.compute(
            sales_data=sales_data if not isinstance(sales_data, Exception) else None,
            population_data=population_data if not isinstance(population_data, Exception) else None,
            subsidy_matches=matched_subsidies,
            user_created_at=current_user.created_at.date() if current_user.created_at else None,
            business_start_date=current_user.business_start_date,
            industry_signal_weights=industry_risk_weights(current_user.business_type, current_user.industry_slug),
        )
        risk_score = risk_result.composite_score

        # 첫 daily_action 생성 (DB)
        generator = ActionGenerator()
        await generator.create_initial_action(
            db=db,
            user=current_user,
            matched_subsidies=matched_subsidies,
            sales_data=sales_data if not isinstance(sales_data, Exception) else None,
            population_data=population_data if not isinstance(population_data, Exception) else None,
            events_data=events_data if not isinstance(events_data, Exception) else None,
        )
        await db.commit()

    logger.info(
        "온보딩 완료: user_id=%s, business_number=%s",
        current_user.id, req.business_number,
    )

    return CompleteOnboardingResponse(
        success=True,
        message=f"사장님, 지원사업 {subsidy_count}건을 찾았습니다!",
        subsidy_count=subsidy_count,
        risk_score=risk_score,
    )

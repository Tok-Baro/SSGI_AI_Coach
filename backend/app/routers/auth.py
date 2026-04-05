"""
인증 라우터
- POST /auth/kakao/callback: 카카오 OAuth 콜백 처리
- GET  /auth/me: 현재 로그인 사용자 정보
- POST /auth/fcm-token: FCM 토큰 등록
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import TokenResponse, UserResponse
from app.services.kakao_service import KakaoService
from app.utils.auth import create_jwt_token, get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/kakao/callback", response_model=TokenResponse)
async def kakao_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    카카오 OAuth 콜백.
    1. code로 카카오 액세스 토큰 교환
    2. 액세스 토큰으로 사용자 정보 조회
    3. DB에서 kakao_id로 사용자 검색. 없으면 생성.
    4. JWT 토큰 발급하여 반환
    """
    kakao_service = KakaoService()

    # 1. 인가 코드 → 액세스 토큰
    kakao_tokens = await kakao_service.get_token(code)
    if not kakao_tokens:
        raise HTTPException(status_code=400, detail="카카오 인증에 실패했습니다.")

    # 2. 사용자 정보 조회
    kakao_user = await kakao_service.get_user_info(kakao_tokens["access_token"])
    if not kakao_user:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보를 가져올 수 없습니다.")

    # 3. DB에서 사용자 찾기 또는 생성
    stmt = select(User).where(User.kakao_id == kakao_user["id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            kakao_id=kakao_user["id"],
            nickname=kakao_user.get("properties", {}).get("nickname", "사장님"),
            email=kakao_user.get("kakao_account", {}).get("email"),
            profile_image_url=kakao_user.get("properties", {}).get("profile_image"),
            kakao_access_token=kakao_tokens["access_token"],
            kakao_refresh_token=kakao_tokens.get("refresh_token"),
        )
        db.add(user)
        await db.flush()
    else:
        user.kakao_access_token = kakao_tokens["access_token"]
        if kakao_tokens.get("refresh_token"):
            user.kakao_refresh_token = kakao_tokens["refresh_token"]

    # 4. JWT 발급
    jwt_token = create_jwt_token(str(user.id))

    return TokenResponse(
        access_token=jwt_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """현재 로그인 사용자 정보. Authorization: Bearer <jwt> 필요."""
    return UserResponse.model_validate(current_user)


@router.post("/fcm-token")
async def register_fcm_token(
    fcm_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FCM 토큰 등록/갱신."""
    current_user.fcm_token = fcm_token
    return {"success": True}

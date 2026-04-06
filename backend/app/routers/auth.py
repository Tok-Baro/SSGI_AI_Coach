"""
인증 라우터
- POST /auth/kakao/callback: 카카오 OAuth 콜백 처리
- POST /auth/refresh: JWT 토큰 갱신
- GET  /auth/me: 현재 로그인 사용자 정보
- POST /auth/fcm-token: FCM 토큰 등록
"""
import re
import time
from collections import OrderedDict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import TokenResponse, UserResponse
from app.services.kakao_service import KakaoService
from app.utils.auth import create_jwt_token, decode_jwt_token, get_current_user
from app.utils.crypto import encrypt_token
from app.models.user import User

router = APIRouter()

# Rate limiting: IP당 1분에 10회 제한 (LRU 방식 최대 5000 엔트리)
AUTH_RATE_LIMIT = 10
AUTH_RATE_WINDOW = 60
_AUTH_TRACKER_MAX = 5000


class _AuthRateTracker:
    """메모리 제한이 있는 auth rate limiter."""

    def __init__(self, max_entries: int = _AUTH_TRACKER_MAX):
        self._data: OrderedDict[str, list[float]] = OrderedDict()
        self._max = max_entries

    def check(self, key: str):
        now = time.time()
        timestamps = self._data.get(key, [])
        timestamps = [t for t in timestamps if now - t < AUTH_RATE_WINDOW]
        if len(timestamps) >= AUTH_RATE_LIMIT:
            self._data[key] = timestamps
            raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
        timestamps.append(now)
        self._data[key] = timestamps
        self._data.move_to_end(key)
        while len(self._data) > self._max:
            self._data.popitem(last=False)


_auth_rate = _AuthRateTracker()


@router.post("/kakao/callback", response_model=TokenResponse)
async def kakao_callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    카카오 OAuth 콜백.
    1. code로 카카오 액세스 토큰 교환
    2. 액세스 토큰으로 사용자 정보 조회
    3. DB에서 kakao_id로 사용자 검색. 없으면 생성.
    4. JWT 토큰 발급하여 반환
    """
    _auth_rate.check(request.client.host if request.client else "unknown")

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
            kakao_access_token=encrypt_token(kakao_tokens["access_token"]),
            kakao_refresh_token=encrypt_token(kakao_tokens.get("refresh_token")),
        )
        db.add(user)
        await db.flush()
    else:
        user.kakao_access_token = encrypt_token(kakao_tokens["access_token"])
        if kakao_tokens.get("refresh_token"):
            user.kakao_refresh_token = encrypt_token(kakao_tokens["refresh_token"])

    # 4. JWT 발급 (access + refresh)
    access_token = create_jwt_token(str(user.id), token_type="access")
    refresh_token = create_jwt_token(str(user.id), token_type="refresh")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """리프레시 토큰으로 새 액세스 토큰 발급."""
    _auth_rate.check(request.client.host if request.client else "unknown")

    from uuid import UUID as _UUID
    user_id = decode_jwt_token(refresh_token, expected_type="refresh")
    stmt = select(User).where(User.id == _UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    new_access = create_jwt_token(str(user.id), token_type="access")
    new_refresh = create_jwt_token(str(user.id), token_type="refresh")
    return {"access_token": new_access, "refresh_token": new_refresh}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """현재 로그인 사용자 정보. Authorization: Bearer <jwt> 필요."""
    return UserResponse.model_validate(current_user)


FCM_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_:.\-]{32,256}$")


@router.post("/fcm-token")
async def register_fcm_token(
    fcm_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FCM 토큰 등록/갱신."""
    if not FCM_TOKEN_PATTERN.match(fcm_token):
        raise HTTPException(status_code=400, detail="유효하지 않은 FCM 토큰 형식입니다.")
    current_user.fcm_token = fcm_token
    return {"success": True}

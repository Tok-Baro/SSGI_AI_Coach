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
from app.utils.auth import create_jwt_token, decode_jwt_token, decode_jwt_token_full, get_current_user
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
    """카카오 OAuth 콜백."""
    import logging as _l
    _log = _l.getLogger(__name__)
    _log.info(f"[kakao_callback] ENTER code_len={len(code)}")
    _auth_rate.check(request.client.host if request.client else "unknown")
    _log.info("[kakao_callback] rate check OK, calling kakao API...")

    import time as _t
    _t0 = _t.perf_counter()
    kakao_service = KakaoService()
    kakao_tokens = await kakao_service.get_token(code)
    _log.info(f"[kakao_callback] T+{_t.perf_counter()-_t0:.2f}s kakao token received: {bool(kakao_tokens)}")
    if not kakao_tokens:
        raise HTTPException(status_code=400, detail="카카오 인증에 실패했습니다.")

    # 2. 사용자 정보 조회
    kakao_user = await kakao_service.get_user_info(kakao_tokens["access_token"])
    _log.info(f"[kakao_callback] T+{_t.perf_counter()-_t0:.2f}s kakao user info: {bool(kakao_user)}")
    if not kakao_user:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보를 가져올 수 없습니다.")

    # 3. DB에서 사용자 찾기 또는 생성
    stmt = select(User).where(User.kakao_id == kakao_user["id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    _log.info(f"[kakao_callback] T+{_t.perf_counter()-_t0:.2f}s db select done, exists={user is not None}")

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
    _log.info(f"[kakao_callback] T+{_t.perf_counter()-_t0:.2f}s user obj prepared")

    # 4. JWT 발급 (access + refresh) — token_version 포함 (회전 카운터)
    ver = user.token_version or 0
    access_token = create_jwt_token(str(user.id), token_type="access", token_version=ver)
    refresh_token = create_jwt_token(str(user.id), token_type="refresh", token_version=ver)
    _log.info(f"[kakao_callback] T+{_t.perf_counter()-_t0:.2f}s jwt issued, returning response")

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
    """리프레시 토큰으로 새 액세스 토큰 발급. 회전 시 구 토큰 무효화 (token_version +=1)."""
    _auth_rate.check(request.client.host if request.client else "unknown")

    from uuid import UUID as _UUID
    user_id, token_ver = decode_jwt_token_full(refresh_token, expected_type="refresh")
    stmt = select(User).where(User.id == _UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    # 구 refresh 토큰의 ver 가 현재 DB 값과 불일치 → 이미 회전된 토큰. 재사용 거부.
    if (user.token_version or 0) != token_ver:
        raise HTTPException(status_code=401, detail="이미 갱신된 세션입니다. 다시 로그인해주세요.")
    # 회전: token_version += 1 → 이번에 발급되는 새 access/refresh만 유효
    new_ver = (user.token_version or 0) + 1
    user.token_version = new_ver
    new_access = create_jwt_token(str(user.id), token_type="access", token_version=new_ver)
    new_refresh = create_jwt_token(str(user.id), token_type="refresh", token_version=new_ver)
    return {"access_token": new_access, "refresh_token": new_refresh}


# 심사위원 체험용 데모 계정 — 실제 카카오 ID 와 절대 안 겹치는 음수 sentinel
DEMO_KAKAO_ID = -10001


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """심사위원 체험용 데모 계정 로그인 — 카카오 OAuth 없이 둘러보기.

    데모 계정 1개(kakao_id=-10001) 전용. 풍부한 더미 데이터(30일 액션·쿠폰·또래 10명)는
    scripts.seed_demo 가 채우며, 시드가 안 돈 상태여도 최소 프로필로 생성해 버튼이 동작하게 한다.
    """
    from datetime import date as _date
    _auth_rate.check(request.client.host if request.client else "unknown")

    user = (await db.execute(
        select(User).where(User.kakao_id == DEMO_KAKAO_ID)
    )).scalar_one_or_none()
    if user is None:
        today = _date.today()
        user = User(
            kakao_id=DEMO_KAKAO_ID,
            nickname="데모 사장님",
            business_name="또랑수학학원",
            business_type="학원",
            business_category="학원",
            industry_slug="academy.exam",
            address="서울특별시 관악구 신림동",
            dong_name="신림동",
            gu_name="관악구",
            plan_tier="free",
            onboarding_completed=True,
            business_start_date=_date(today.year - 3, 3, 2),
        )
        db.add(user)
        await db.flush()

    ver = user.token_version or 0
    access_token = create_jwt_token(str(user.id), token_type="access", token_version=ver)
    refresh_token = create_jwt_token(str(user.id), token_type="refresh", token_version=ver)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


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
    db.add(current_user)  # get_current_user가 다른 세션에서 fetch했으므로 재부착
    current_user.fcm_token = fcm_token
    return {"success": True}

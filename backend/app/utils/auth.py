"""JWT 토큰 생성/검증 + 현재 사용자 의존성.

토큰 회전 (token_version):
- 사용자 record에 정수 카운터 token_version 보관
- 토큰 발급 시 클레임에 ver 포함
- refresh 회전 시 token_version += 1 → 구 토큰 거부
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models.user import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2
REFRESH_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()


def create_jwt_token(user_id: str, token_type: str = "access", token_version: int = 0) -> str:
    """JWT 액세스/리프레시 토큰 생성.

    token_version: 사용자 회전 카운터. 토큰 검증 시 DB의 현재 값과 일치 확인.
    """
    now = datetime.now(timezone.utc)
    if token_type == "refresh":
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "type": token_type,
        "ver": token_version,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_jwt_token(token: str, expected_type: str = "access") -> str:
    """JWT 디코딩. user_id (str) 반환. (호환성 유지용)"""
    user_id, _ = decode_jwt_token_full(token, expected_type)
    return user_id


def decode_jwt_token_full(token: str, expected_type: str = "access") -> Tuple[str, int]:
    """JWT 디코딩. (user_id, token_version) 반환."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        token_type: str = payload.get("type", "access")
        token_version: int = int(payload.get("ver", 0))
        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        if token_type != expected_type:
            raise HTTPException(status_code=401, detail="토큰 유형이 올바르지 않습니다.")
        return user_id, token_version
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었거나 유효하지 않습니다.")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """현재 인증된 사용자를 반환하는 FastAPI Depends.

    DB 세션을 짧게 잡았다 즉시 풀어서, 외부 API를 호출하는 라우트가
    pool 커넥션을 점유하지 않도록 한다.

    token_version 검증: 토큰 클레임의 ver != DB의 user.token_version 시 401.
    refresh 회전 시 구 토큰을 거부하기 위함 (OWASP A02).
    """
    user_id, token_ver = decode_jwt_token_full(credentials.credentials, expected_type="access")
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    # token_version 불일치 → 회전된 구 토큰
    if (user.token_version or 0) != token_ver:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다. 다시 로그인해주세요.")
    return user

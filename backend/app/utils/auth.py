"""JWT 토큰 생성/검증 + 현재 사용자 의존성."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2
REFRESH_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()


def create_jwt_token(user_id: str, token_type: str = "access") -> str:
    """JWT 액세스/리프레시 토큰 생성."""
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
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_jwt_token(token: str, expected_type: str = "access") -> str:
    """JWT 디코딩. user_id (str) 반환."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        if token_type != expected_type:
            raise HTTPException(status_code=401, detail="토큰 유형이 올바르지 않습니다.")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었거나 유효하지 않습니다.")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """현재 인증된 사용자를 반환하는 FastAPI Depends."""
    user_id = decode_jwt_token(credentials.credentials, expected_type="access")
    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    return user

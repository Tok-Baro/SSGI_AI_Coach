"""사업자 검증 토큰 생성/검증 유틸리티.

verify-business 성공 시 토큰을 발급하고,
complete-onboarding 시 해당 토큰을 검증하여
검증 없이 온보딩을 완료하는 것을 방지한다.
"""
import hashlib
import hmac
import time

from app.config import settings

# 검증 토큰 유효시간: 10분
VERIFICATION_TOKEN_TTL = 600


def create_verification_token(user_id: str, business_number: str) -> str:
    """사업자 검증 성공 시 발급하는 HMAC 토큰.

    형식: {timestamp}.{hmac_signature}
    """
    timestamp = str(int(time.time()))
    message = f"{user_id}:{business_number}:{timestamp}"
    signature = hmac.new(
        settings.secret_key.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{timestamp}.{signature}"


def verify_verification_token(
    token: str, user_id: str, business_number: str
) -> bool:
    """검증 토큰이 유효한지 확인.

    - HMAC 서명 일치 확인
    - TTL(10분) 초과 여부 확인
    - user_id + business_number 바인딩 확인 (다른 사업자번호로 교체 방지)
    """
    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return False
        timestamp_str, provided_sig = parts
        timestamp = int(timestamp_str)

        # TTL 체크
        if time.time() - timestamp > VERIFICATION_TOKEN_TTL:
            return False

        # HMAC 재계산
        message = f"{user_id}:{business_number}:{timestamp_str}"
        expected_sig = hmac.new(
            settings.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(provided_sig, expected_sig)
    except (ValueError, TypeError):
        return False

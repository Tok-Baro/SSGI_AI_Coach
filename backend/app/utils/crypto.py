"""OAuth 토큰 암호화/복호화 유틸리티 (Fernet 대칭키 암호화)."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _derive_key(secret: str) -> bytes:
    """secret_key에서 Fernet 호환 32바이트 키 파생."""
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_token(plaintext: str | None) -> str | None:
    """평문 토큰을 암호화. None이면 None 반환."""
    if not plaintext:
        return None
    f = Fernet(_derive_key(settings.secret_key))
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str | None) -> str | None:
    """암호화된 토큰을 복호화. None이거나 복호화 실패 시 None 반환."""
    if not ciphertext:
        return None
    try:
        f = Fernet(_derive_key(settings.secret_key))
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        return None

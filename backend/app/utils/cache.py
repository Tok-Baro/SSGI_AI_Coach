"""간단한 인메모리 TTL 캐시."""
import time
import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[Any, float]] = {}


def cache(ttl: int = 3600, key_prefix: str = ""):
    """
    인메모리 TTL 캐시 데코레이터.
    ttl: 초 단위 TTL
    key_prefix: 캐시 키 접두사
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # 캐시 히트 체크
            if cache_key in _cache:
                value, expires_at = _cache[cache_key]
                if time.time() < expires_at:
                    return value
                else:
                    del _cache[cache_key]

            # 캐시 미스 - 실제 함수 호출
            result = await func(*args, **kwargs)
            if result is not None:
                _cache[cache_key] = (result, time.time() + ttl)

            return result
        return wrapper
    return decorator


def clear_cache():
    """전체 캐시 초기화."""
    _cache.clear()

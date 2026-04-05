"""외부 API 호출용 재시도 데코레이터."""
import asyncio
import logging
from functools import wraps
from typing import Callable, Type

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS: tuple[Type[Exception], ...] = (
    httpx.HTTPError,
    httpx.TimeoutException,
    ConnectionError,
    TimeoutError,
)


def retry_async(max_retries: int = 2, delay: float = 1.0, backoff: float = 2.0):
    """
    비동기 함수 재시도 데코레이터.
    실패 시 max_retries회 재시도, 지수 백오프.
    최종 실패 시 None 반환 (예외 던지지 않음).
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as e:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        return None
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

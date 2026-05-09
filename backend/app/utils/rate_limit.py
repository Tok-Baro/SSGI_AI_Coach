"""공통 rate limiter — 메모리 기반 sliding window + LRU eviction.

여러 라우터에서 인스턴스를 공유 가능. 단일 워커 가정 (멀티 워커 환경에서는
Redis 백엔드로 교체 필요).
"""
import time
from collections import OrderedDict
from typing import Optional

from fastapi import HTTPException


class SlidingWindowLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int, max_keys: int = 5000, name: str = "rate"):
        self._data: OrderedDict[str, list[float]] = OrderedDict()
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self.name = name

    def check(self, key: str, *, raise_429: bool = True) -> bool:
        """key가 한도를 넘으면 HTTPException(429) 또는 False."""
        now = time.time()
        timestamps = self._data.get(key, [])
        timestamps = [t for t in timestamps if now - t < self.window_seconds]
        if len(timestamps) >= self.max_requests:
            self._data[key] = timestamps
            if raise_429:
                raise HTTPException(
                    status_code=429,
                    detail=f"요청이 너무 많습니다. {self.window_seconds}초 후 다시 시도하세요.",
                )
            return False
        timestamps.append(now)
        self._data[key] = timestamps
        self._data.move_to_end(key)
        while len(self._data) > self.max_keys:
            self._data.popitem(last=False)
        return True


# 라우터별 글로벌 인스턴스
# /onboarding/* — IP당 1분 30회 (NTS 검증 + 사업자 검색 합산)
onboarding_rate = SlidingWindowLimiter(max_requests=30, window_seconds=60, name="onboarding")

# /insights/* — user당 분당 5회 (?refresh GPT 비용 폭주 방지)
insights_rate = SlidingWindowLimiter(max_requests=5, window_seconds=60, name="insights")

# /subsidies/apply-draft — user당 시간당 10회 (GPT 비용)
apply_draft_rate = SlidingWindowLimiter(max_requests=10, window_seconds=3600, name="apply_draft")

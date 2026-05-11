"""기존 users 행의 industry_slug 를 채운다 (마이그레이션 008 적용 후 1회 실행).

업종 분류 우선순위가 아직 ① raw 사용자 입력 밖에 없으므로, 이미 normalize_business_type 으로
canonical 화된 business_type ("음식점"/"카페"/"소매업"/"미용실" …) 기준으로 best-effort 분류한다.
온보딩을 새로 거치는 사용자는 complete_onboarding 에서 raw 입력값으로 더 정확히 채워진다.

사용 (backend/ 에서):
    python -m scripts.backfill_industry
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.database import async_session_factory
from app.models.user import User
from app.utils.industry import SLUG_UNKNOWN, classify_industry


async def main() -> None:
    async with async_session_factory() as db:
        users = (await db.execute(select(User))).scalars().all()
        total = updated = unknown = 0
        for user in users:
            total += 1
            if user.industry_slug:
                continue
            slug = classify_industry(user.business_type)
            user.industry_slug = slug
            updated += 1
            if slug == SLUG_UNKNOWN:
                unknown += 1
        await db.commit()
        print(f"users {total}건 — industry_slug 채움 {updated}건 (그중 unknown {unknown}건)")


if __name__ == "__main__":
    asyncio.run(main())

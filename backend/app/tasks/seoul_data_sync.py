"""매주 월요일 새벽 3시: 서울시 데이터 캐시 사전 워밍."""
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.user import User
from app.services.seoul_api_service import SeoulAPIService

logger = logging.getLogger(__name__)


async def sync_seoul_data():
    """활성 사용자의 지역/업종 조합별 서울시 API 사전 호출."""
    logger.info("Starting Seoul data sync...")

    async with async_session_factory() as db:
        # 유니크한 (gu_name, dong_name, business_type) 조합 수집
        stmt = (
            select(
                User.gu_name,
                User.dong_name,
                User.business_type,
            )
            .where(User.onboarding_completed == True)
            .distinct()
        )
        result = await db.execute(stmt)
        combinations = result.all()

    logger.info(f"Pre-fetching data for {len(combinations)} location/type combos...")

    seoul = SeoulAPIService()
    success_count = 0

    for gu_name, dong_name, business_type in combinations:
        if not gu_name or not dong_name:
            continue

        try:
            # 상권 매출
            await seoul.get_commercial_sales(gu_name, dong_name, business_type or "")
            # 생활인구
            await seoul.get_living_population(dong_name, gu_name)
            # 문화행사
            await seoul.get_cultural_events(gu_name)
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to sync data for {gu_name}/{dong_name}: {e}")

    logger.info(f"Seoul data sync complete: {success_count}/{len(combinations)} success")

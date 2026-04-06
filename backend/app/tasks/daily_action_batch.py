"""매일 오전 7시: 전체 사용자 일일 액션 생성 배치."""
import asyncio
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import async_session_factory
from app.models.user import User
from app.models.daily_action import DailyAction
from app.services.action_generator import ActionGenerator
from app.services.seoul_api_service import SeoulAPIService
from app.services.rag_service import RAGService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# 동시 외부 API 호출 제한 (서울시 API rate limit 고려)
_CONCURRENCY_LIMIT = 5


async def _fetch_data_for_user(
    user: User,
    seoul: SeoulAPIService,
    rag: RAGService,
    data_cache: dict,
) -> dict:
    """사용자별 데이터 수집. 공유 가능한 데이터는 캐시 사용."""
    sales_data = None
    population_data = None
    events_data = None
    subsidy_data = None

    # 유동인구/행사는 동/구 기준이라 캐시 가능
    pop_key = user.dong_name or ""
    event_key = user.gu_name or ""

    try:
        sales_data = await seoul.get_commercial_sales(
            user.gu_name or "", user.dong_name or "", user.business_type or ""
        )
    except Exception:
        pass

    if pop_key not in data_cache.get("population", {}):
        try:
            data_cache.setdefault("population", {})[pop_key] = await seoul.get_living_population(pop_key)
        except Exception:
            data_cache.setdefault("population", {})[pop_key] = None
    population_data = data_cache["population"].get(pop_key)

    if event_key not in data_cache.get("events", {}):
        try:
            data_cache.setdefault("events", {})[event_key] = await seoul.get_cultural_events(event_key)
        except Exception:
            data_cache.setdefault("events", {})[event_key] = None
    events_data = data_cache["events"].get(event_key)

    try:
        query = f"{user.gu_name} {user.dong_name} {user.business_type} 소상공인"
        subsidy_data = await rag.search_subsidies(query, top_k=3)
    except Exception:
        pass

    return {
        "sales_data": sales_data,
        "population_data": population_data,
        "events_data": events_data,
        "subsidy_data": subsidy_data,
    }


async def _process_user(
    user: User,
    generator: ActionGenerator,
    notifier: NotificationService,
    data: dict,
    db: AsyncSession,
) -> bool:
    """단일 사용자의 액션 생성 + 알림. 성공 시 True."""
    action_data = await generator.generate_daily_action(
        user=user,
        sales_data=data["sales_data"],
        population_data=data["population_data"],
        events_data=data["events_data"],
        subsidy_data=data["subsidy_data"],
    )

    # ON CONFLICT DO NOTHING으로 TOCTOU race 방지
    stmt = pg_insert(DailyAction).values(
        user_id=user.id,
        date=date.today(),
        action_type=action_data.get("action_type", "coupon"),
        title=action_data.get("title", "오늘의 액션을 확인하세요"),
        description=action_data.get("description", ""),
        risk_score=action_data.get("risk_score", 0.3),
        data_source=action_data.get("data_source"),
        cta_type=action_data.get("cta_type"),
        cta_payload=action_data.get("cta_payload"),
    ).on_conflict_do_nothing(
        constraint="uq_daily_actions_user_date"
    )
    await db.execute(stmt)

    try:
        await notifier.send_notification(
            user=user,
            title=f"[AI 경영코치] {action_data.get('title', '오늘의 액션')}",
            message=action_data.get("description", ""),
            message_type="daily_action",
            db=db,
        )
    except Exception as e:
        logger.warning(f"Notification failed for user {user.id}: {e}")

    return True


async def generate_daily_actions_for_all():
    """모든 온보딩 완료 사용자에게 일일 액션 생성 + 알림."""
    logger.info("Starting daily action batch...")
    success_count = 0
    fail_count = 0

    async with async_session_factory() as db:
        # 온보딩 완료 사용자 중 오늘 액션이 아직 없는 사용자만 조회
        stmt = (
            select(User)
            .where(User.onboarding_completed == True)
            .outerjoin(
                DailyAction,
                (DailyAction.user_id == User.id) & (DailyAction.date == date.today()),
            )
            .where(DailyAction.id.is_(None))
        )
        result = await db.execute(stmt)
        users = result.scalars().all()

        logger.info(f"Processing {len(users)} users (without today's action)...")

        seoul = SeoulAPIService()
        rag = RAGService()
        generator = ActionGenerator()
        notifier = NotificationService()
        data_cache: dict = {}

        semaphore = asyncio.Semaphore(_CONCURRENCY_LIMIT)

        async def _handle_user(user: User):
            nonlocal success_count, fail_count
            async with semaphore:
                try:
                    data = await _fetch_data_for_user(user, seoul, rag, data_cache)
                    await _process_user(user, generator, notifier, data, db)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to generate action for user {user.id}: {e}")
                    fail_count += 1

        # 병렬 처리
        await asyncio.gather(*[_handle_user(u) for u in users])

        await db.commit()

    logger.info(
        f"Daily action batch complete: {success_count} success, {fail_count} failed"
    )

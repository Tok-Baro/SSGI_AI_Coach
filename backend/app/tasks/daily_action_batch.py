"""매일 오전 7시: 전체 사용자 일일 액션 생성 배치."""
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.user import User
from app.models.daily_action import DailyAction
from app.services.action_generator import ActionGenerator
from app.services.seoul_api_service import SeoulAPIService
from app.services.rag_service import RAGService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


async def generate_daily_actions_for_all():
    """모든 온보딩 완료 사용자에게 일일 액션 생성 + 알림."""
    logger.info("Starting daily action batch...")
    success_count = 0
    fail_count = 0

    async with async_session_factory() as db:
        # 온보딩 완료 사용자 조회
        stmt = select(User).where(User.onboarding_completed == True)
        result = await db.execute(stmt)
        users = result.scalars().all()

        logger.info(f"Processing {len(users)} users...")

        seoul = SeoulAPIService()
        rag = RAGService()
        generator = ActionGenerator()
        notifier = NotificationService()

        for user in users:
            try:
                # 이미 오늘 액션이 있으면 스킵
                existing = await db.execute(
                    select(DailyAction).where(
                        DailyAction.user_id == user.id,
                        DailyAction.date == date.today(),
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                # 데이터 수집 (실패해도 계속 진행)
                sales_data = None
                population_data = None
                events_data = None
                subsidy_data = None

                try:
                    sales_data = await seoul.get_commercial_sales(
                        user.gu_name or "", user.dong_name or "", user.business_type or ""
                    )
                except Exception:
                    pass

                try:
                    population_data = await seoul.get_living_population(user.dong_name or "")
                except Exception:
                    pass

                try:
                    events_data = await seoul.get_cultural_events(user.gu_name or "")
                except Exception:
                    pass

                try:
                    query = f"{user.gu_name} {user.dong_name} {user.business_type} 소상공인"
                    subsidy_data = await rag.search_subsidies(query, top_k=3)
                except Exception:
                    pass

                # 액션 생성
                action_data = await generator.generate_daily_action(
                    user=user,
                    sales_data=sales_data,
                    population_data=population_data,
                    events_data=events_data,
                    subsidy_data=subsidy_data,
                )

                daily_action = DailyAction(
                    user_id=user.id,
                    date=date.today(),
                    action_type=action_data.get("action_type", "coupon"),
                    title=action_data.get("title", "오늘의 액션을 확인하세요"),
                    description=action_data.get("description", ""),
                    risk_score=action_data.get("risk_score", 0.3),
                    data_source=action_data.get("data_source"),
                    cta_type=action_data.get("cta_type"),
                    cta_payload=action_data.get("cta_payload"),
                )
                db.add(daily_action)

                # 알림 전송
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

                success_count += 1

            except Exception as e:
                logger.error(f"Failed to generate action for user {user.id}: {e}")
                fail_count += 1

        await db.commit()

    logger.info(
        f"Daily action batch complete: {success_count} success, {fail_count} failed"
    )

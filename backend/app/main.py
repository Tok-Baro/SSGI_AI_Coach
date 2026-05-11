import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import init_db
from app.routers import auth, onboarding, dashboard, subsidies, actions, coupons, voice, insights, reports, payments, knowledge
from app.tasks.daily_action_batch import generate_daily_actions_for_all
from app.tasks.seoul_data_sync import sync_seoul_data
from app.tasks.subsidy_indexer import reindex_subsidies

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# SECRET_KEY 최소 길이 검증 (모든 환경)
if len(settings.secret_key) < 32:
    raise RuntimeError(
        "SECRET_KEY는 최소 32자 이상이어야 합니다. `openssl rand -hex 32`로 생성하세요."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행."""
    logger.info("Starting AI Coach Backend...")
    await init_db()

    # APScheduler 크론 작업 등록
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_daily_actions_for_all, "cron", hour=7, minute=0, id="daily_actions")
    scheduler.add_job(sync_seoul_data, "cron", day_of_week="mon", hour=3, minute=0, id="seoul_sync")
    scheduler.add_job(reindex_subsidies, "cron", day_of_week="mon", hour=4, minute=0, id="subsidy_index")
    scheduler.start()
    logger.info("Scheduler started: daily_actions(7AM), seoul_sync(Mon 3AM), subsidy_index(Mon 4AM)")

    yield

    scheduler.shutdown()
    logger.info("Shutting down AI Coach Backend...")


app = FastAPI(
    title="소상공인 AI 경영코치 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["인증"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["온보딩"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["대시보드"])
app.include_router(subsidies.router, prefix="/subsidies", tags=["지원사업"])
app.include_router(actions.router, prefix="/actions", tags=["일일 액션"])
app.include_router(coupons.router, prefix="/coupons", tags=["쿠폰"])
app.include_router(voice.router, prefix="/voice", tags=["음성 질의"])
app.include_router(insights.router, prefix="/insights", tags=["경영 인사이트"])
app.include_router(reports.router, prefix="/reports", tags=["주간 리포트"])
app.include_router(payments.router, tags=["결제 (카카오페이)"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["업종 지식"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

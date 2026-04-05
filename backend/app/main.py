import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, onboarding, dashboard, subsidies, actions, coupons, voice

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행."""
    logger.info("Starting AI Coach Backend...")
    await init_db()

    # TODO: Phase 5에서 APScheduler 크론 작업 등록
    # scheduler.add_job(generate_daily_actions_for_all, "cron", hour=7, minute=0)
    # scheduler.add_job(sync_seoul_data, "cron", day_of_week="mon", hour=3, minute=0)
    # scheduler.add_job(reindex_subsidies, "cron", day_of_week="mon", hour=4, minute=0)

    yield

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
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["인증"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["온보딩"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["대시보드"])
app.include_router(subsidies.router, prefix="/subsidies", tags=["지원사업"])
app.include_router(actions.router, prefix="/actions", tags=["일일 액션"])
app.include_router(coupons.router, prefix="/coupons", tags=["쿠폰"])
app.include_router(voice.router, prefix="/voice", tags=["음성 질의"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

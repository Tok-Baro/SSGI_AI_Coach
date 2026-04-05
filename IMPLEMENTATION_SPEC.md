# 소상공인 AI 경영코치 - 구현 명세서 (Implementation Specification)

> **이 문서의 목적**: 개발자(또는 AI 코딩 어시스턴트)가 질문 없이 MVP 전체를 구현할 수 있도록, 모든 파일/함수/API/스키마/환경변수를 상세히 기술한다.
>
> **최종 수정**: 2026-04-04
>
> **기술 스택**: Next.js 14 (App Router, PWA) + FastAPI (Python 3.11+) + PostgreSQL 15 + ChromaDB + GPT-4o

---

## 목차

1. [환경 변수 (Environment Variables)](#1-환경-변수)
2. [데이터베이스 스키마](#2-데이터베이스-스키마)
3. [Backend 구현 상세 (FastAPI)](#3-backend-구현-상세)
4. [Frontend 구현 상세 (Next.js)](#4-frontend-구현-상세)
5. [Kakao OAuth 플로우](#5-kakao-oauth-플로우)
6. [서울시 API 연동](#6-서울시-api-연동)
7. [RAG 파이프라인 (ChromaDB + LangChain)](#7-rag-파이프라인)
8. [GPT-4o 프롬프트 템플릿](#8-gpt-4o-프롬프트-템플릿)
9. [QR 쿠폰 생성](#9-qr-쿠폰-생성)
10. [알림 시스템 (Kakao Talk + FCM)](#10-알림-시스템)
11. [손실 프레이밍 메시지 템플릿](#11-손실-프레이밍-메시지-템플릿)
12. [k-anonymity 사회적 증거](#12-k-anonymity-사회적-증거)
13. [PWA 설정](#13-pwa-설정)
14. [STT 음성 질의](#14-stt-음성-질의)
15. [배포 설정 (Vercel + Railway)](#15-배포-설정)
16. [Fault Tolerance 패턴](#16-fault-tolerance-패턴)
17. [배치 작업 (Cron Tasks)](#17-배치-작업)
18. [파일별 구현 가이드](#18-파일별-구현-가이드)

---

## 1. 환경 변수

> **⚠️ 실제 API 키 값, 발급 방법, 응답 필드 상세는 [`API_SECRETS.md`](./API_SECRETS.md)를 참조.**
> **`API_SECRETS.md`는 Git에 커밋하지 않으며, `.gitignore`에 포함되어야 합니다.**

### Backend 환경변수 목록 (`backend/.env`)

| 변수명 | 설명 | 시크릿 여부 | 예시 형식 |
|---|---|---|---|
| `APP_ENV` | 실행 환경 | ❌ | `development` / `production` |
| `APP_HOST` | 바인드 주소 | ❌ | `0.0.0.0` |
| `APP_PORT` | 바인드 포트 | ❌ | `8000` |
| `SECRET_KEY` | JWT 서명 키 | ✅ | 64자 hex (`openssl rand -hex 32`) |
| `CORS_ORIGINS` | 허용 오리진 (콤마 구분) | ❌ | `http://localhost:3000` |
| `DATABASE_URL` | PostgreSQL 접속 URL | ✅ | `postgresql+asyncpg://user:pass@host:5432/db` |
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 | ✅ | `API_SECRETS.md § 1` 참조 |
| `KAKAO_CLIENT_SECRET` | 카카오 Client Secret | ✅ | `API_SECRETS.md § 1` 참조 |
| `KAKAO_REDIRECT_URI` | OAuth 콜백 URL | ❌ | `http://localhost:3000/api/auth/kakao/callback` |
| `NTS_API_KEY` | 국세청 API 인증키 | ✅ | `API_SECRETS.md § 2` 참조 |
| `SEOUL_API_KEY` | 서울시 열린데이터 인증키 | ✅ | `API_SECRETS.md § 3` 참조 |
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ | `API_SECRETS.md § 4` 참조 |
| `OPENAI_MODEL` | 사용 모델명 | ❌ | `gpt-4o` |
| `OPENAI_MAX_TOKENS` | 최대 응답 토큰 | ❌ | `1024` |
| `OPENAI_TEMPERATURE` | 생성 temperature | ❌ | `0.7` |
| `CHROMA_PERSIST_DIR` | ChromaDB 저장 경로 | ❌ | `./chroma_data` |
| `CHROMA_COLLECTION_NAME` | ChromaDB 컬렉션명 | ❌ | `subsidies` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | FCM 서비스 계정 JSON 경로 | ✅ | `API_SECRETS.md § 5` 참조 |
| `REDIS_URL` | Redis 접속 URL (선택) | ✅ | `redis://localhost:6379/0` |
| `LOG_LEVEL` | 로그 레벨 | ❌ | `INFO` |
| `DAILY_ACTION_CRON` | 일일 액션 생성 크론 | ❌ | `0 7 * * *` |
| `SEOUL_SYNC_CRON` | 서울 데이터 동기화 크론 | ❌ | `0 3 * * 1` |
| `SUBSIDY_INDEX_CRON` | 보조금 인덱싱 크론 | ❌ | `0 4 * * 1` |

### Frontend 환경변수 목록 (`frontend/.env.local`)

| 변수명 | 설명 | 시크릿 여부 | 예시 형식 |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | 백엔드 API URL | ❌ | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_URL` | 프론트엔드 URL | ❌ | `http://localhost:3000` |
| `NEXT_PUBLIC_KAKAO_JS_KEY` | 카카오 JavaScript 키 | ⚠️ 공개 | `API_SECRETS.md § 1` 참조 |
| `NEXT_PUBLIC_KAKAO_REST_API_KEY` | 카카오 REST API 키 | ⚠️ 공개 | `API_SECRETS.md § 1` 참조 |
| `NEXT_PUBLIC_KAKAO_REDIRECT_URI` | OAuth 콜백 URL | ❌ | 개발/프로덕션 URL |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase API 키 | ⚠️ 공개 | `API_SECRETS.md § 5` 참조 |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase 도메인 | ❌ | `{project}.firebaseapp.com` |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase 프로젝트 ID | ❌ | 프로젝트 ID |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | FCM Sender ID | ❌ | 숫자 |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase App ID | ❌ | `1:xxx:web:xxx` |
| `NEXT_PUBLIC_FIREBASE_VAPID_KEY` | 웹 푸시 VAPID 키 | ⚠️ 공개 | `API_SECRETS.md § 5` 참조 |

> **⚠️ `NEXT_PUBLIC_` 접두사 변수는 클라이언트 번들에 포함되어 브라우저에 노출됩니다.**
> 카카오 JS 키, Firebase 공개 키는 설계상 공개되지만, 반드시 도메인 제한 설정을 해야 합니다:
> - 카카오: "플랫폼" 탭에서 허용 도메인만 등록
> - Firebase: Google Cloud Console > API 키 > HTTP 리퍼러 제한

### .env.example 파일 (Git 커밋용 템플릿)

```bash
# backend/.env.example — 실제 값은 API_SECRETS.md 참조
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=CHANGE_ME
CORS_ORIGINS=http://localhost:3000
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_coach
KAKAO_REST_API_KEY=CHANGE_ME
KAKAO_CLIENT_SECRET=CHANGE_ME
KAKAO_REDIRECT_URI=http://localhost:3000/api/auth/kakao/callback
NTS_API_KEY=CHANGE_ME
SEOUL_API_KEY=CHANGE_ME
OPENAI_API_KEY=CHANGE_ME
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1024
OPENAI_TEMPERATURE=0.7
CHROMA_PERSIST_DIR=./chroma_data
CHROMA_COLLECTION_NAME=subsidies
FIREBASE_SERVICE_ACCOUNT_JSON=./firebase-sa.json
LOG_LEVEL=DEBUG
DAILY_ACTION_CRON=0 7 * * *
SEOUL_SYNC_CRON=0 3 * * 1
SUBSIDY_INDEX_CRON=0 4 * * 1
```

---

## 2. 데이터베이스 스키마

### ERD 개요

```
users (1) ──< (N) daily_actions
users (1) ──< (N) coupon_templates
users (1) ──< (N) notification_log
subsidies (독립 테이블, RAG 매칭용)
```

### 2.1 Alembic 초기 마이그레이션 SQL

아래는 `alembic/versions/001_initial_schema.py`에서 생성되는 SQL이다.

```sql
-- ===== users =====
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kakao_id BIGINT UNIQUE NOT NULL,                  -- 카카오 회원번호
    email VARCHAR(255),                                -- 카카오 제공 이메일 (nullable)
    nickname VARCHAR(100) NOT NULL,                    -- 카카오 닉네임
    profile_image_url VARCHAR(500),                    -- 프로필 사진 URL
    business_number VARCHAR(10),                       -- 사업자등록번호 (10자리 숫자)
    business_name VARCHAR(200),                        -- 상호명
    business_type VARCHAR(100),                        -- 업종 (예: "카페", "음식점")
    business_category VARCHAR(100),                    -- 업종 카테고리 (카카오 제공)
    address VARCHAR(500),                              -- 도로명 주소
    dong_name VARCHAR(50),                             -- 행정동명 (예: "혜화동")
    gu_name VARCHAR(50),                               -- 구명 (예: "종로구")
    lat DOUBLE PRECISION,                              -- 위도
    lng DOUBLE PRECISION,                              -- 경도
    plan_tier VARCHAR(10) DEFAULT 'free' NOT NULL,     -- 'free' | 'pro'
    onboarding_completed BOOLEAN DEFAULT FALSE,        -- 온보딩 완료 여부
    fcm_token VARCHAR(500),                            -- Firebase FCM 토큰
    kakao_access_token VARCHAR(500),                   -- 카카오 액세스 토큰 (나에게 보내기용)
    kakao_refresh_token VARCHAR(500),                  -- 카카오 리프레시 토큰
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_users_kakao_id ON users(kakao_id);
CREATE INDEX idx_users_dong_name ON users(dong_name);
CREATE INDEX idx_users_business_type ON users(business_type);

-- ===== daily_actions =====
CREATE TABLE daily_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,                                -- 액션 날짜
    action_type VARCHAR(50) NOT NULL,                  -- 'subsidy' | 'event' | 'coupon' | 'competitor' | 'population'
    title VARCHAR(300) NOT NULL,                       -- 액션 제목 (손실 프레이밍)
    description TEXT NOT NULL,                         -- 상세 설명
    risk_score FLOAT DEFAULT 0.0,                      -- 위험 점수 (0.0~1.0)
    data_source VARCHAR(100),                          -- 데이터 출처 (예: "서울시 상권분석 2025Q3")
    cta_type VARCHAR(50),                              -- CTA 유형: 'create_coupon' | 'apply_subsidy' | 'view_detail'
    cta_payload JSONB,                                 -- CTA 데이터 (subsidy_id, coupon_template 등)
    is_completed BOOLEAN DEFAULT FALSE,                -- 사용자가 실행 완료했는지
    completed_at TIMESTAMPTZ,                          -- 완료 시각
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, date)                              -- 하루에 하나의 액션만
);

CREATE INDEX idx_daily_actions_user_date ON daily_actions(user_id, date);

-- ===== subsidies =====
CREATE TABLE subsidies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,                       -- 지원사업명
    organization VARCHAR(200) NOT NULL,                -- 지원기관
    deadline DATE,                                     -- 마감일 (null이면 상시)
    max_amount INTEGER,                                -- 최대 지원금액 (만원 단위)
    target_business_types TEXT[],                      -- 대상 업종 배열
    target_regions TEXT[],                             -- 대상 지역 배열
    eligibility_summary TEXT,                          -- 자격 요건 요약
    description TEXT NOT NULL,                         -- 상세 설명
    application_url VARCHAR(500),                      -- 신청 페이지 URL
    embedding_id VARCHAR(100),                         -- ChromaDB 문서 ID
    source VARCHAR(100),                               -- 데이터 출처
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_subsidies_deadline ON subsidies(deadline);
CREATE INDEX idx_subsidies_active ON subsidies(is_active);

-- ===== coupon_templates =====
CREATE TABLE coupon_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,                       -- 쿠폰명 (예: "아메리카노 1+1")
    discount_type VARCHAR(20) NOT NULL,                -- 'percent' | 'fixed' | 'bogo' | 'free_item'
    discount_value INTEGER,                            -- 할인율(%) 또는 금액(원)
    description VARCHAR(500),                          -- 부가 설명
    valid_days INTEGER DEFAULT 7,                      -- 유효기간 (일수)
    valid_from DATE,                                   -- 시작일
    valid_until DATE,                                  -- 종료일
    qr_data TEXT NOT NULL,                             -- QR 코드에 인코딩된 데이터 (URL)
    qr_image_base64 TEXT,                              -- QR 이미지 base64 (PNG)
    download_count INTEGER DEFAULT 0,                  -- 다운로드 수
    scan_count INTEGER DEFAULT 0,                      -- 스캔 수
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_coupon_templates_user ON coupon_templates(user_id);

-- ===== notification_log =====
CREATE TABLE notification_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL,                      -- 'kakao' | 'fcm' | 'email'
    message_type VARCHAR(50) NOT NULL,                 -- 'daily_action' | 'subsidy_alert' | 'retention'
    title VARCHAR(300),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',              -- 'pending' | 'sent' | 'failed' | 'delivered'
    error_message TEXT,                                -- 실패 시 에러 메시지
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_notification_log_user ON notification_log(user_id);
CREATE INDEX idx_notification_log_status ON notification_log(status);
```

### 2.2 SQLAlchemy 모델

#### `backend/app/models/user.py`

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kakao_id = Column(BigInteger, unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    nickname = Column(String(100), nullable=False)
    profile_image_url = Column(String(500), nullable=True)
    business_number = Column(String(10), nullable=True)
    business_name = Column(String(200), nullable=True)
    business_type = Column(String(100), nullable=True)
    business_category = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    dong_name = Column(String(50), nullable=True, index=True)
    gu_name = Column(String(50), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    plan_tier = Column(String(10), default="free", nullable=False)
    onboarding_completed = Column(Boolean, default=False)
    fcm_token = Column(String(500), nullable=True)
    kakao_access_token = Column(String(500), nullable=True)
    kakao_refresh_token = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    daily_actions = relationship("DailyAction", back_populates="user", cascade="all, delete-orphan")
    coupon_templates = relationship("CouponTemplate", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")
```

#### `backend/app/models/daily_action.py`

```python
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class DailyAction(Base):
    __tablename__ = "daily_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    action_type = Column(String(50), nullable=False)   # subsidy | event | coupon | competitor | population
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    risk_score = Column(Float, default=0.0)
    data_source = Column(String(100), nullable=True)
    cta_type = Column(String(50), nullable=True)       # create_coupon | apply_subsidy | view_detail
    cta_payload = Column(JSONB, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="daily_actions")

    __table_args__ = (
        # 하루에 하나의 액션만
        {"schema": None},
    )
```

#### `backend/app/models/subsidy.py`

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base


class Subsidy(Base):
    __tablename__ = "subsidies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    organization = Column(String(200), nullable=False)
    deadline = Column(Date, nullable=True)
    max_amount = Column(Integer, nullable=True)          # 만원 단위
    target_business_types = Column(ARRAY(Text), nullable=True)
    target_regions = Column(ARRAY(Text), nullable=True)
    eligibility_summary = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    application_url = Column(String(500), nullable=True)
    embedding_id = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### `backend/app/models/coupon.py`

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CouponTemplate(Base):
    __tablename__ = "coupon_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    discount_type = Column(String(20), nullable=False)   # percent | fixed | bogo | free_item
    discount_value = Column(Integer, nullable=True)
    description = Column(String(500), nullable=True)
    valid_days = Column(Integer, default=7)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    qr_data = Column(Text, nullable=False)
    qr_image_base64 = Column(Text, nullable=True)
    download_count = Column(Integer, default=0)
    scan_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="coupon_templates")
```

#### `backend/app/models/notification.py`

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(20), nullable=False)        # kakao | fcm | email
    message_type = Column(String(50), nullable=False)   # daily_action | subsidy_alert | retention
    title = Column(String(300), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending")      # pending | sent | failed | delivered
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
```

#### `backend/app/models/__init__.py`

```python
from app.models.user import User
from app.models.daily_action import DailyAction
from app.models.subsidy import Subsidy
from app.models.coupon import CouponTemplate
from app.models.notification import NotificationLog

__all__ = ["User", "DailyAction", "Subsidy", "CouponTemplate", "NotificationLog"]
```

---

## 3. Backend 구현 상세

### 3.1 프로젝트 설정 파일

#### `backend/requirements.txt`

```
# 웹 프레임워크
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9

# 데이터베이스
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1

# 인증
python-jose[cryptography]==3.3.0
passlib==1.7.4
httpx==0.27.0

# AI / RAG
openai==1.35.0
langchain==0.2.5
langchain-openai==0.1.9
langchain-community==0.2.5
chromadb==0.5.0

# QR 코드
qrcode[pil]==7.4.2
Pillow==10.3.0

# Firebase
firebase-admin==6.5.0

# 유틸
pydantic==2.7.4
pydantic-settings==2.3.4
python-dotenv==1.0.1
apscheduler==3.10.4
tenacity==8.4.1
redis==5.0.7
```

#### `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 앱
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str
    cors_origins: str = "http://localhost:3000"  # 콤마 구분

    # DB
    database_url: str

    # Kakao
    kakao_rest_api_key: str
    kakao_client_secret: str
    kakao_redirect_uri: str

    # 국세청
    nts_api_key: str

    # 서울시
    seoul_api_key: str

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 1024
    openai_temperature: float = 0.7

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "subsidies"

    # Firebase
    firebase_service_account_json: Optional[str] = None
    firebase_service_account: Optional[str] = None  # JSON 문자열 (Railway용)

    # Redis
    redis_url: Optional[str] = None

    # Cron
    daily_action_cron: str = "0 7 * * *"
    seoul_sync_cron: str = "0 3 * * 1"
    subsidy_index_cron: str = "0 4 * * 1"

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

#### `backend/app/database.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI Depends용 DB 세션 제너레이터."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """앱 시작 시 테이블 생성 (개발용. 프로덕션에서는 Alembic 사용)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

#### `backend/app/main.py`

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import init_db
from app.routers import auth, onboarding, dashboard, subsidies, actions, coupons, voice
from app.tasks.daily_action_batch import generate_daily_actions_for_all
from app.tasks.seoul_data_sync import sync_seoul_data
from app.tasks.subsidy_indexer import reindex_subsidies

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행."""
    logger.info("Starting AI Coach Backend...")
    await init_db()

    # Cron 작업 등록
    # 매일 오전 7시: 일일 액션 생성
    scheduler.add_job(generate_daily_actions_for_all, "cron", hour=7, minute=0)
    # 매주 월요일 새벽 3시: 서울 데이터 동기화
    scheduler.add_job(sync_seoul_data, "cron", day_of_week="mon", hour=3, minute=0)
    # 매주 월요일 새벽 4시: 보조금 ChromaDB 인덱싱
    scheduler.add_job(reindex_subsidies, "cron", day_of_week="mon", hour=4, minute=0)

    scheduler.start()
    logger.info("Scheduler started.")

    yield  # 앱 실행 중

    scheduler.shutdown()
    logger.info("Scheduler stopped.")


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
```

### 3.2 Pydantic 스키마

#### `backend/app/schemas/user.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    kakao_id: int
    email: Optional[str] = None
    nickname: str
    profile_image_url: Optional[str] = None
    business_number: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    address: Optional[str] = None
    dong_name: Optional[str] = None
    gu_name: Optional[str] = None
    plan_tier: str
    onboarding_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

#### `backend/app/schemas/onboarding.py`

```python
from pydantic import BaseModel, Field
from typing import Optional


class VerifyBusinessRequest(BaseModel):
    business_number: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$",
                                  description="사업자등록번호 10자리 숫자")


class VerifyBusinessResponse(BaseModel):
    is_valid: bool
    business_status: str          # "계속사업자" | "휴업자" | "폐업자" | "확인불가"
    business_name: Optional[str] = None
    tax_type: Optional[str] = None


class KakaoLocalSearchResult(BaseModel):
    place_name: str
    address_name: str
    road_address_name: Optional[str] = None
    category_name: str            # 예: "음식점 > 카페 > 커피전문점"
    x: str                        # 경도 (lng)
    y: str                        # 위도 (lat)
    phone: Optional[str] = None


class CompleteOnboardingRequest(BaseModel):
    business_number: str = Field(..., min_length=10, max_length=10)
    business_name: str
    business_type: str            # 사용자 확인한 업종
    address: str
    dong_name: str
    gu_name: str
    lat: float
    lng: float


class CompleteOnboardingResponse(BaseModel):
    success: bool
    message: str
    subsidy_count: int = 0        # 매칭된 지원사업 개수
    risk_score: float = 0.0       # 초기 위험 점수
```

#### `backend/app/schemas/daily_action.py`

```python
from pydantic import BaseModel
from typing import Optional, Any
from datetime import date, datetime
from uuid import UUID


class DailyActionResponse(BaseModel):
    id: UUID
    date: date
    action_type: str
    title: str
    description: str
    risk_score: float
    data_source: Optional[str] = None
    cta_type: Optional[str] = None
    cta_payload: Optional[dict] = None
    is_completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompleteActionRequest(BaseModel):
    pass  # 빈 바디 (URL 파라미터로 action_id 전달)


class CompleteActionResponse(BaseModel):
    success: bool
    message: str
```

#### `backend/app/schemas/subsidy.py`

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID


class SubsidyResponse(BaseModel):
    id: UUID
    title: str
    organization: str
    deadline: Optional[date] = None
    max_amount: Optional[int] = None
    eligibility_summary: Optional[str] = None
    description: str
    application_url: Optional[str] = None
    relevance_score: Optional[float] = None   # RAG 매칭 점수 (0~1)
    days_until_deadline: Optional[int] = None  # 마감까지 남은 일수
    social_proof_message: Optional[str] = None # "같은 동네 N곳이 신청" (k-anon 충족 시)

    class Config:
        from_attributes = True


class SubsidyMatchesResponse(BaseModel):
    matches: List[SubsidyResponse]
    total_potential_amount: int = 0   # 총 잠재 수령액 (만원)
    loss_message: str                 # 손실 프레이밍 메시지


class ApplyDraftRequest(BaseModel):
    subsidy_id: UUID
    additional_info: Optional[str] = None


class ApplyDraftResponse(BaseModel):
    draft_text: str                   # GPT-4o 생성 사업계획서 초안
    subsidy_title: str
    estimated_time_saved: str = "약 2시간"
```

#### `backend/app/schemas/coupon.py`

```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date


class CreateCouponRequest(BaseModel):
    title: str                           # 쿠폰명 (예: "아메리카노 1+1")
    discount_type: str                   # percent | fixed | bogo | free_item
    discount_value: Optional[int] = None # 할인율 또는 금액
    description: Optional[str] = None
    valid_days: int = 7


class CouponResponse(BaseModel):
    id: UUID
    title: str
    discount_type: str
    discount_value: Optional[int] = None
    description: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    qr_data: str
    qr_image_base64: str                 # data:image/png;base64,... 형태
    download_count: int
    scan_count: int
    is_active: bool

    class Config:
        from_attributes = True
```

### 3.3 API 라우터 (Endpoint 상세)

#### `backend/app/routers/auth.py`

```python
"""
인증 라우터
- POST /auth/kakao/callback: 카카오 OAuth 콜백 처리
- GET  /auth/me: 현재 로그인 사용자 정보
- POST /auth/logout: 로그아웃
- POST /auth/fcm-token: FCM 토큰 등록
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import TokenResponse, UserResponse
from app.services.kakao_service import KakaoService
from app.utils.auth import create_jwt_token, get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/kakao/callback", response_model=TokenResponse)
async def kakao_callback(
    code: str,      # 카카오 인가 코드
    db: AsyncSession = Depends(get_db),
):
    """
    카카오 OAuth 콜백.

    플로우:
    1. code로 카카오 액세스 토큰 교환
    2. 액세스 토큰으로 사용자 정보 조회
    3. DB에서 kakao_id로 사용자 검색. 없으면 생성.
    4. JWT 토큰 발급하여 반환

    Request Body:
        code (str): 카카오 인가 코드 (프론트에서 redirect 후 받은 code)

    Response:
        access_token (str): JWT 토큰
        token_type (str): "bearer"
        user (UserResponse): 사용자 정보

    Error Cases:
        400: 카카오 토큰 교환 실패
        500: 서버 오류
    """
    kakao_service = KakaoService()

    # 1. 인가 코드 → 액세스 토큰
    kakao_tokens = await kakao_service.get_token(code)
    if not kakao_tokens:
        raise HTTPException(status_code=400, detail="카카오 인증에 실패했습니다.")

    # 2. 사용자 정보 조회
    kakao_user = await kakao_service.get_user_info(kakao_tokens["access_token"])
    if not kakao_user:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보를 가져올 수 없습니다.")

    # 3. DB에서 사용자 찾기 또는 생성
    from sqlalchemy import select
    stmt = select(User).where(User.kakao_id == kakao_user["id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            kakao_id=kakao_user["id"],
            nickname=kakao_user.get("properties", {}).get("nickname", "사장님"),
            email=kakao_user.get("kakao_account", {}).get("email"),
            profile_image_url=kakao_user.get("properties", {}).get("profile_image"),
            kakao_access_token=kakao_tokens["access_token"],
            kakao_refresh_token=kakao_tokens.get("refresh_token"),
        )
        db.add(user)
        await db.flush()
    else:
        # 토큰 갱신
        user.kakao_access_token = kakao_tokens["access_token"]
        if kakao_tokens.get("refresh_token"):
            user.kakao_refresh_token = kakao_tokens["refresh_token"]

    # 4. JWT 발급
    jwt_token = create_jwt_token(str(user.id))

    return TokenResponse(
        access_token=jwt_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """현재 로그인 사용자 정보. Authorization: Bearer <jwt> 필요."""
    return UserResponse.model_validate(current_user)


@router.post("/fcm-token")
async def register_fcm_token(
    fcm_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FCM 토큰 등록/갱신."""
    current_user.fcm_token = fcm_token
    return {"success": True}
```

#### `backend/app/routers/onboarding.py`

```python
"""
온보딩 라우터
- POST /onboarding/verify-business: 사업자등록번호 유효성 검증
- GET  /onboarding/search-business: 카카오 로컬 상호명 검색
- POST /onboarding/complete: 온보딩 완료 (사업 정보 저장 + 서울시 API 호출 + RAG 매칭)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.onboarding import (
    VerifyBusinessRequest, VerifyBusinessResponse,
    KakaoLocalSearchResult, CompleteOnboardingRequest, CompleteOnboardingResponse,
)
from app.services.nts_service import NTSService
from app.services.kakao_service import KakaoService
from app.services.seoul_api_service import SeoulAPIService
from app.services.rag_service import RAGService
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/verify-business", response_model=VerifyBusinessResponse)
async def verify_business(
    req: VerifyBusinessRequest,
    current_user: User = Depends(get_current_user),
):
    """
    사업자등록번호 유효성 검증 (국세청 API).

    Request Body:
        business_number (str): 10자리 사업자번호

    Response:
        is_valid (bool): 유효 여부
        business_status (str): 사업자 상태
        business_name (str | null): 상호명 (국세청 제공 시)
        tax_type (str | null): 과세유형

    Error Cases:
        400: 잘못된 사업자번호 형식
        502: 국세청 API 호출 실패 (재시도 2회 후)
    """
    nts = NTSService()
    result = await nts.verify_business_number(req.business_number)
    if result is None:
        raise HTTPException(status_code=502, detail="국세청 API 연결에 실패했습니다. 잠시 후 다시 시도해주세요.")
    return result


@router.get("/search-business", response_model=List[KakaoLocalSearchResult])
async def search_business(
    query: str = Query(..., min_length=1, description="상호명 검색어"),
    current_user: User = Depends(get_current_user),
):
    """
    카카오 로컬 검색으로 상호명 자동완성.

    Query Parameters:
        query (str): 상호명 (예: "스타벅스 혜화")

    Response:
        List[KakaoLocalSearchResult]: 검색 결과 목록 (최대 5개)
            - place_name: 상호명
            - address_name: 지번 주소
            - road_address_name: 도로명 주소
            - category_name: 업종 분류
            - x, y: 경도, 위도
            - phone: 전화번호

    Error Cases:
        502: 카카오 API 호출 실패
    """
    kakao = KakaoService()
    results = await kakao.search_local(query, size=5)
    if results is None:
        raise HTTPException(status_code=502, detail="카카오 검색에 실패했습니다.")
    return results


@router.post("/complete", response_model=CompleteOnboardingResponse)
async def complete_onboarding(
    req: CompleteOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    온보딩 완료: 사업 정보 저장 + 서울시 API 병렬 호출 + RAG 지원사업 매칭.

    내부 플로우:
    1. User 테이블에 사업 정보 저장
    2. 서울시 API 3종 병렬 호출 (상권분석, 생활인구, 문화행사)
    3. ChromaDB RAG로 지원사업 매칭
    4. 초기 위험 점수 계산
    5. 첫 번째 daily_action 생성

    Request Body:
        business_number, business_name, business_type,
        address, dong_name, gu_name, lat, lng

    Response:
        success (bool)
        message (str)
        subsidy_count (int): 매칭된 지원사업 수
        risk_score (float): 초기 위험 점수
    """
    import asyncio

    # 1. 사업 정보 저장
    current_user.business_number = req.business_number
    current_user.business_name = req.business_name
    current_user.business_type = req.business_type
    current_user.address = req.address
    current_user.dong_name = req.dong_name
    current_user.gu_name = req.gu_name
    current_user.lat = req.lat
    current_user.lng = req.lng
    current_user.onboarding_completed = True

    # 2. 서울시 API 3종 병렬 호출
    seoul = SeoulAPIService()
    sales_task = seoul.get_commercial_sales(req.gu_name, req.dong_name, req.business_type)
    population_task = seoul.get_living_population(req.dong_name)
    events_task = seoul.get_cultural_events(req.gu_name)

    sales_data, population_data, events_data = await asyncio.gather(
        sales_task, population_task, events_task,
        return_exceptions=True,
    )

    # 3. RAG 지원사업 매칭
    rag = RAGService()
    query_text = f"{req.gu_name} {req.dong_name} {req.business_type} 소상공인 지원사업"
    matched_subsidies = await rag.search_subsidies(query_text, top_k=5)
    subsidy_count = len(matched_subsidies)

    # 4. 초기 위험 점수 (0.0~1.0)
    risk_score = 0.3  # 기본값
    if isinstance(sales_data, dict) and sales_data.get("quarterly_change"):
        change = sales_data["quarterly_change"]
        if change < -10:
            risk_score = 0.7
        elif change < -5:
            risk_score = 0.5
        elif change < 0:
            risk_score = 0.3
        else:
            risk_score = 0.1

    # 5. 첫 daily_action 생성 (지원사업이 있으면 지원사업 알림, 없으면 이벤트 권유)
    from app.services.action_generator import ActionGenerator
    generator = ActionGenerator()
    await generator.create_initial_action(
        db=db,
        user=current_user,
        matched_subsidies=matched_subsidies,
        sales_data=sales_data if not isinstance(sales_data, Exception) else None,
        population_data=population_data if not isinstance(population_data, Exception) else None,
        events_data=events_data if not isinstance(events_data, Exception) else None,
    )

    return CompleteOnboardingResponse(
        success=True,
        message=f"사장님, 지원사업 {subsidy_count}건을 찾았습니다!",
        subsidy_count=subsidy_count,
        risk_score=risk_score,
    )
```

#### `backend/app/routers/dashboard.py`

```python
"""
대시보드 라우터
- GET /dashboard: 메인 대시보드 데이터 (집계)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import Optional

from app.database import get_db
from app.utils.auth import get_current_user
from app.models import User, DailyAction, CouponTemplate, Subsidy
from app.services.rag_service import RAGService
from app.services.seoul_api_service import SeoulAPIService
from app.services.social_proof_service import SocialProofService

router = APIRouter()


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    메인 대시보드 집계 데이터.

    Auth: Bearer JWT 필요.

    Response:
    {
        "user": { nickname, business_name, plan_tier },
        "risk_score": 0.3,
        "today_action": { ... } | null,
        "subsidy_matches": [ ... ],    // 상위 3건
        "total_potential_amount": 700,  // 만원
        "loss_message": "사장님, 연 700만원을 놓치고 있습니다.",
        "upcoming_events": [ ... ],    // 근처 문화행사 (3건)
        "population_trend": { today, yesterday, change_percent },
        "social_proof": "혜화동 카페 12곳이 이번 달 이벤트 진행 중" | null,
        "coupon_stats": { total_created, total_scanned },
        "action_completion_rate": 0.65
    }
    """
    today = date.today()

    # 오늘의 액션
    stmt = select(DailyAction).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date == today,
    )
    result = await db.execute(stmt)
    today_action = result.scalar_one_or_none()

    # 지원사업 매칭 (캐시 우선)
    rag = RAGService()
    query = f"{current_user.gu_name} {current_user.dong_name} {current_user.business_type} 소상공인"
    matched = await rag.search_subsidies(query, top_k=3)

    total_amount = sum(s.get("max_amount", 0) for s in matched if s.get("max_amount"))

    # 문화행사
    seoul = SeoulAPIService()
    events = await seoul.get_cultural_events(current_user.gu_name)
    upcoming_events = []
    if events and not isinstance(events, Exception):
        upcoming_events = events[:3]

    # 유동인구
    pop_data = await seoul.get_living_population(current_user.dong_name)
    population_trend = None
    if pop_data and not isinstance(pop_data, Exception):
        population_trend = pop_data

    # 사회적 증거
    social = SocialProofService(db)
    social_proof = await social.get_message(current_user.dong_name, current_user.business_type)

    # 쿠폰 통계
    stmt = select(
        func.count(CouponTemplate.id),
        func.coalesce(func.sum(CouponTemplate.scan_count), 0),
    ).where(CouponTemplate.user_id == current_user.id)
    result = await db.execute(stmt)
    coupon_row = result.one()

    # 액션 완료율 (최근 30일)
    stmt = select(
        func.count(DailyAction.id),
        func.count(DailyAction.id).filter(DailyAction.is_completed == True),
    ).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date >= today - timedelta(days=30),
    )
    result = await db.execute(stmt)
    action_row = result.one()
    total_actions, completed_actions = action_row
    completion_rate = completed_actions / total_actions if total_actions > 0 else 0.0

    # 손실 프레이밍 메시지
    loss_message = f"사장님, 연 {total_amount}만원을 놓치고 있습니다." if total_amount > 0 else "사장님, 오늘의 기회를 확인하세요."

    return {
        "user": {
            "nickname": current_user.nickname,
            "business_name": current_user.business_name,
            "plan_tier": current_user.plan_tier,
        },
        "risk_score": today_action.risk_score if today_action else 0.0,
        "today_action": today_action,
        "subsidy_matches": matched,
        "total_potential_amount": total_amount,
        "loss_message": loss_message,
        "upcoming_events": upcoming_events,
        "population_trend": population_trend,
        "social_proof": social_proof,
        "coupon_stats": {
            "total_created": coupon_row[0],
            "total_scanned": coupon_row[1],
        },
        "action_completion_rate": round(completion_rate, 2),
    }
```

#### `backend/app/routers/subsidies.py`

```python
"""
지원사업 라우터
- GET  /subsidies/matches: 사용자 맞춤 지원사업 목록
- GET  /subsidies/{id}: 지원사업 상세
- POST /subsidies/apply-draft: 사업계획서 초안 생성 (GPT-4o)
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.subsidy import SubsidyMatchesResponse, SubsidyResponse, ApplyDraftRequest, ApplyDraftResponse
from app.services.rag_service import RAGService
from app.services.action_generator import ActionGenerator
from app.services.social_proof_service import SocialProofService
from app.utils.auth import get_current_user
from app.models import User, Subsidy

router = APIRouter()


@router.get("/matches", response_model=SubsidyMatchesResponse)
async def get_subsidy_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 업종/지역 기반 지원사업 RAG 매칭.

    Auth: Bearer JWT 필요.

    Response:
        matches: List[SubsidyResponse]  -- 관련도 순 정렬, 최대 10건
        total_potential_amount: int      -- 총 잠재 수령액 (만원)
        loss_message: str               -- 손실 프레이밍 메시지

    내부 로직:
    1. ChromaDB 벡터 검색 (사용자 dong_name + business_type)
    2. 마감일 기준 정렬 (임박한 것 우선)
    3. k-anonymity 사회적 증거 메시지 첨부
    """
    rag = RAGService()
    query = f"{current_user.gu_name} {current_user.dong_name} {current_user.business_type} 소상공인 지원금 보조금"
    results = await rag.search_subsidies(query, top_k=10)

    social = SocialProofService(db)
    enriched = []
    total_amount = 0

    for r in results:
        proof_msg = await social.get_subsidy_proof(
            current_user.dong_name, current_user.business_type, r.get("title", "")
        )
        days_left = r.get("days_until_deadline")
        enriched.append(SubsidyResponse(
            id=r["id"],
            title=r["title"],
            organization=r["organization"],
            deadline=r.get("deadline"),
            max_amount=r.get("max_amount"),
            eligibility_summary=r.get("eligibility_summary"),
            description=r["description"],
            application_url=r.get("application_url"),
            relevance_score=r.get("relevance_score", 0),
            days_until_deadline=days_left,
            social_proof_message=proof_msg,
        ))
        if r.get("max_amount"):
            total_amount += r["max_amount"]

    loss_msg = f"사장님, 지금 신청 가능한 지원금 최대 {total_amount}만원을 놓치고 있습니다."
    if total_amount == 0:
        loss_msg = "현재 매칭되는 지원사업이 없습니다. 새로운 공고가 나오면 알려드리겠습니다."

    return SubsidyMatchesResponse(
        matches=enriched,
        total_potential_amount=total_amount,
        loss_message=loss_msg,
    )


@router.post("/apply-draft", response_model=ApplyDraftResponse)
async def generate_apply_draft(
    req: ApplyDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    지원사업 사업계획서 초안 생성 (GPT-4o).

    Auth: Bearer JWT 필요.

    Request Body:
        subsidy_id (UUID): 대상 지원사업 ID
        additional_info (str | null): 추가 정보 (선택)

    Response:
        draft_text (str): 사업계획서 초안 (마크다운)
        subsidy_title (str)
        estimated_time_saved (str): "약 2시간"

    Error Cases:
        404: 지원사업 없음
        503: GPT-4o 호출 실패 (timeout/rate limit 시 간소화 템플릿 반환)
    """
    from sqlalchemy import select
    stmt = select(Subsidy).where(Subsidy.id == req.subsidy_id)
    result = await db.execute(stmt)
    subsidy = result.scalar_one_or_none()
    if not subsidy:
        raise HTTPException(status_code=404, detail="해당 지원사업을 찾을 수 없습니다.")

    generator = ActionGenerator()
    draft = await generator.generate_business_plan_draft(
        user=current_user,
        subsidy=subsidy,
        additional_info=req.additional_info,
    )

    return ApplyDraftResponse(
        draft_text=draft,
        subsidy_title=subsidy.title,
        estimated_time_saved="약 2시간",
    )
```

#### `backend/app/routers/actions.py`

```python
"""
일일 액션 라우터
- GET  /actions/today: 오늘의 액션
- GET  /actions/history: 최근 액션 히스토리 (30일)
- POST /actions/{id}/complete: 액션 완료 처리
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta, datetime
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.daily_action import DailyActionResponse, CompleteActionResponse
from app.utils.auth import get_current_user
from app.models import User, DailyAction

router = APIRouter()


@router.get("/today", response_model=DailyActionResponse)
async def get_today_action(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    오늘의 액션 조회.

    Auth: Bearer JWT 필요.

    Response: DailyActionResponse (오늘 날짜의 액션)

    Error Cases:
        404: 오늘의 액션이 아직 생성되지 않음
    """
    stmt = select(DailyAction).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date == date.today(),
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="오늘의 액션이 아직 준비되지 않았습니다.")

    return DailyActionResponse.model_validate(action)


@router.get("/history", response_model=List[DailyActionResponse])
async def get_action_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """최근 N일간 액션 히스토리."""
    stmt = (
        select(DailyAction)
        .where(
            DailyAction.user_id == current_user.id,
            DailyAction.date >= date.today() - timedelta(days=days),
        )
        .order_by(DailyAction.date.desc())
    )
    result = await db.execute(stmt)
    actions = result.scalars().all()
    return [DailyActionResponse.model_validate(a) for a in actions]


@router.post("/{action_id}/complete", response_model=CompleteActionResponse)
async def complete_action(
    action_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    액션 완료 처리.

    Path Parameters:
        action_id (UUID): 대상 액션 ID

    Auth: Bearer JWT 필요.

    Error Cases:
        404: 액션 없음 또는 다른 사용자의 액션
        400: 이미 완료됨
    """
    stmt = select(DailyAction).where(
        DailyAction.id == action_id,
        DailyAction.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="액션을 찾을 수 없습니다.")
    if action.is_completed:
        raise HTTPException(status_code=400, detail="이미 완료된 액션입니다.")

    action.is_completed = True
    action.completed_at = datetime.utcnow()

    return CompleteActionResponse(success=True, message="잘하셨어요, 사장님! 오늘의 액션을 완료했습니다.")
```

#### `backend/app/routers/coupons.py`

```python
"""
쿠폰 라우터
- POST /coupons/create: QR 쿠폰 생성
- GET  /coupons: 내 쿠폰 목록
- GET  /coupons/{id}: 쿠폰 상세 (QR 이미지 포함)
- POST /coupons/{id}/scan: 쿠폰 스캔 카운트 증가
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.coupon import CreateCouponRequest, CouponResponse
from app.services.coupon_service import CouponService
from app.utils.auth import get_current_user
from app.models import User, CouponTemplate

router = APIRouter()


@router.post("/create", response_model=CouponResponse)
async def create_coupon(
    req: CreateCouponRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    QR 쿠폰 생성 (1탭).

    Auth: Bearer JWT 필요.
    Free 플랜: 월 3개 제한. Pro 플랜: 무제한.

    Request Body:
        title (str): "아메리카노 1+1"
        discount_type (str): "percent" | "fixed" | "bogo" | "free_item"
        discount_value (int | null): 할인율 또는 금액
        description (str | null): 부가 설명
        valid_days (int): 유효기간 (기본 7일)

    Response: CouponResponse (qr_image_base64 포함)

    Error Cases:
        403: 무료 플랜 월 3개 초과
    """
    # Free 플랜 제한 체크
    if current_user.plan_tier == "free":
        from datetime import date
        from sqlalchemy import func
        stmt = select(func.count(CouponTemplate.id)).where(
            CouponTemplate.user_id == current_user.id,
            func.extract("month", CouponTemplate.created_at) == date.today().month,
            func.extract("year", CouponTemplate.created_at) == date.today().year,
        )
        result = await db.execute(stmt)
        count = result.scalar()
        if count >= 3:
            raise HTTPException(
                status_code=403,
                detail="무료 플랜은 월 3개까지 쿠폰을 만들 수 있습니다. 프로 플랜으로 업그레이드하세요.",
            )

    coupon_service = CouponService()
    coupon = await coupon_service.create_coupon(
        db=db,
        user=current_user,
        title=req.title,
        discount_type=req.discount_type,
        discount_value=req.discount_value,
        description=req.description,
        valid_days=req.valid_days,
    )

    return CouponResponse.model_validate(coupon)


@router.get("", response_model=List[CouponResponse])
async def list_coupons(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 쿠폰 목록."""
    stmt = (
        select(CouponTemplate)
        .where(CouponTemplate.user_id == current_user.id)
        .order_by(CouponTemplate.created_at.desc())
    )
    result = await db.execute(stmt)
    coupons = result.scalars().all()
    return [CouponResponse.model_validate(c) for c in coupons]


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon(
    coupon_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """쿠폰 상세 (QR 포함). 인증 불필요 (고객이 QR 스캔 시 접근)."""
    stmt = select(CouponTemplate).where(CouponTemplate.id == coupon_id)
    result = await db.execute(stmt)
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="쿠폰을 찾을 수 없습니다.")
    return CouponResponse.model_validate(coupon)


@router.post("/{coupon_id}/scan")
async def scan_coupon(
    coupon_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """쿠폰 스캔 카운트 증가. 인증 불필요."""
    stmt = select(CouponTemplate).where(CouponTemplate.id == coupon_id)
    result = await db.execute(stmt)
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="쿠폰을 찾을 수 없습니다.")
    coupon.scan_count += 1
    return {"success": True, "scan_count": coupon.scan_count}
```

#### `backend/app/routers/voice.py`

```python
"""
음성 질의 라우터
- POST /voice/query: STT 텍스트 처리 → GPT-4o 응답
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.auth import get_current_user
from app.models import User
from app.services.action_generator import ActionGenerator
from app.services.rag_service import RAGService

router = APIRouter()


class VoiceQueryRequest(BaseModel):
    text: str  # STT로 변환된 텍스트 (예: "사장님 지원금 찾아줘")


class VoiceQueryResponse(BaseModel):
    answer: str             # GPT-4o 응답 텍스트
    intent: str             # 감지된 의도: subsidy | coupon | sales | event | general
    suggestions: list[str]  # 후속 질문 제안


@router.post("/query", response_model=VoiceQueryResponse)
async def process_voice_query(
    req: VoiceQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    음성(STT) 텍스트를 GPT-4o로 처리하여 응답.

    Auth: Bearer JWT 필요.

    Request Body:
        text (str): 사용자 음성을 STT로 변환한 텍스트

    Response:
        answer (str): AI 응답
        intent (str): 의도 분류
        suggestions (list[str]): 후속 질문 제안

    내부 로직:
    1. 의도 분류 (키워드 기반 + GPT fallback)
    2. 의도별 컨텍스트 수집 (RAG 검색, DB 조회 등)
    3. GPT-4o에 컨텍스트 + 사용자 질문 전달
    4. 손실 프레이밍 응답 생성
    """
    generator = ActionGenerator()

    # 1. 간단한 키워드 의도 분류
    text_lower = req.text.lower()
    if any(kw in text_lower for kw in ["지원금", "보조금", "지원사업", "돈"]):
        intent = "subsidy"
    elif any(kw in text_lower for kw in ["쿠폰", "이벤트", "할인"]):
        intent = "coupon"
    elif any(kw in text_lower for kw in ["매출", "매출분석", "실적"]):
        intent = "sales"
    elif any(kw in text_lower for kw in ["행사", "축제", "공연"]):
        intent = "event"
    else:
        intent = "general"

    # 2. 의도별 RAG 컨텍스트
    rag = RAGService()
    context_docs = []
    if intent == "subsidy":
        context_docs = await rag.search_subsidies(
            f"{current_user.dong_name} {current_user.business_type} {req.text}", top_k=3
        )

    # 3. GPT-4o 호출
    answer = await generator.process_voice_query(
        user=current_user,
        query_text=req.text,
        intent=intent,
        context_docs=context_docs,
    )

    # 4. 후속 질문 제안
    suggestions_map = {
        "subsidy": ["지원금 마감일 알려줘", "사업계획서 써줘", "다른 지원사업도 있어?"],
        "coupon": ["QR 쿠폰 만들어줘", "지난 쿠폰 실적 보여줘", "이벤트 문구 추천해줘"],
        "sales": ["매출 올리는 방법 알려줘", "경쟁 가게 분석해줘", "이번 주 유동인구는?"],
        "event": ["이벤트 쿠폰 만들어줘", "행사 연계 이벤트 추천해줘", "행사 일정 알려줘"],
        "general": ["지원금 찾아줘", "오늘 뭐 해야 돼?", "매출 분석해줘"],
    }

    return VoiceQueryResponse(
        answer=answer,
        intent=intent,
        suggestions=suggestions_map.get(intent, suggestions_map["general"]),
    )
```

### 3.4 인증 유틸리티

#### `backend/app/utils/auth.py`

```python
"""JWT 토큰 생성/검증 + 현재 사용자 의존성."""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()


def create_jwt_token(user_id: str) -> str:
    """JWT 액세스 토큰 생성."""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_jwt_token(token: str) -> str:
    """JWT 디코딩. user_id (str) 반환."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었거나 유효하지 않습니다.")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """현재 인증된 사용자를 반환하는 FastAPI Depends."""
    user_id = decode_jwt_token(credentials.credentials)
    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    return user
```

---

## 4. Frontend 구현 상세

### 4.1 프로젝트 설정

#### `frontend/package.json` (핵심 의존성)

```json
{
  "name": "ai-coach-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.4",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "next-pwa": "^5.6.0",
    "tailwindcss": "^3.4.4",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "lucide-react": "^0.396.0",
    "clsx": "^2.1.1",
    "firebase": "^10.12.2",
    "qrcode.react": "^3.1.0",
    "zustand": "^4.5.2"
  },
  "devDependencies": {
    "@types/node": "^20.14.8",
    "@types/react": "^18.3.3",
    "typescript": "^5.5.2",
    "eslint": "^8.57.0",
    "eslint-config-next": "14.2.4"
  }
}
```

#### `frontend/next.config.js`

```js
const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development", // 개발 시 SW 비활성화
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        // /api/backend/* 요청을 백엔드로 프록시 (CORS 우회용, 선택사항)
        source: "/api/backend/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ];
  },
};

module.exports = withPWA(nextConfig);
```

### 4.2 TypeScript 타입 정의

#### `frontend/src/types/index.ts`

```typescript
// ===== 사용자 =====
export interface User {
  id: string;
  kakao_id: number;
  email: string | null;
  nickname: string;
  profile_image_url: string | null;
  business_number: string | null;
  business_name: string | null;
  business_type: string | null;
  address: string | null;
  dong_name: string | null;
  gu_name: string | null;
  plan_tier: "free" | "pro";
  onboarding_completed: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ===== 온보딩 =====
export interface VerifyBusinessResponse {
  is_valid: boolean;
  business_status: string;
  business_name: string | null;
  tax_type: string | null;
}

export interface KakaoLocalSearchResult {
  place_name: string;
  address_name: string;
  road_address_name: string | null;
  category_name: string;
  x: string; // lng
  y: string; // lat
  phone: string | null;
}

export interface CompleteOnboardingResponse {
  success: boolean;
  message: string;
  subsidy_count: number;
  risk_score: number;
}

// ===== 일일 액션 =====
export interface DailyAction {
  id: string;
  date: string;
  action_type: "subsidy" | "event" | "coupon" | "competitor" | "population";
  title: string;
  description: string;
  risk_score: number;
  data_source: string | null;
  cta_type: string | null;
  cta_payload: Record<string, any> | null;
  is_completed: boolean;
  completed_at: string | null;
}

// ===== 지원사업 =====
export interface Subsidy {
  id: string;
  title: string;
  organization: string;
  deadline: string | null;
  max_amount: number | null;
  eligibility_summary: string | null;
  description: string;
  application_url: string | null;
  relevance_score: number | null;
  days_until_deadline: number | null;
  social_proof_message: string | null;
}

export interface SubsidyMatchesResponse {
  matches: Subsidy[];
  total_potential_amount: number;
  loss_message: string;
}

export interface ApplyDraftResponse {
  draft_text: string;
  subsidy_title: string;
  estimated_time_saved: string;
}

// ===== 쿠폰 =====
export interface Coupon {
  id: string;
  title: string;
  discount_type: "percent" | "fixed" | "bogo" | "free_item";
  discount_value: number | null;
  description: string | null;
  valid_from: string | null;
  valid_until: string | null;
  qr_data: string;
  qr_image_base64: string;
  download_count: number;
  scan_count: number;
  is_active: boolean;
}

export interface CreateCouponRequest {
  title: string;
  discount_type: string;
  discount_value?: number;
  description?: string;
  valid_days?: number;
}

// ===== 대시보드 =====
export interface DashboardData {
  user: {
    nickname: string;
    business_name: string;
    plan_tier: string;
  };
  risk_score: number;
  today_action: DailyAction | null;
  subsidy_matches: Subsidy[];
  total_potential_amount: number;
  loss_message: string;
  upcoming_events: any[];
  population_trend: {
    today: number;
    yesterday: number;
    change_percent: number;
  } | null;
  social_proof: string | null;
  coupon_stats: {
    total_created: number;
    total_scanned: number;
  };
  action_completion_rate: number;
}

// ===== 음성 질의 =====
export interface VoiceQueryResponse {
  answer: string;
  intent: string;
  suggestions: string[];
}
```

### 4.3 API 클라이언트

#### `frontend/src/lib/api.ts`

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
  }

  private async request<T>(
    method: string,
    path: string,
    body?: any,
    requireAuth: boolean = true
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (requireAuth) {
      const token = this.getToken();
      if (!token) {
        throw new Error("인증이 필요합니다. 다시 로그인해주세요.");
      }
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config: RequestInit = { method, headers };
    if (body && method !== "GET") {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_URL}${path}`, config);

    if (response.status === 401) {
      this.clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/";
      }
      throw new Error("세션이 만료되었습니다.");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "알 수 없는 오류" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // ===== Auth =====
  kakaoCallback(code: string) {
    return this.request<import("@/types").AuthResponse>(
      "POST", `/auth/kakao/callback?code=${code}`, undefined, false
    );
  }

  getMe() {
    return this.request<import("@/types").User>("GET", "/auth/me");
  }

  registerFcmToken(fcmToken: string) {
    return this.request("POST", `/auth/fcm-token?fcm_token=${fcmToken}`);
  }

  // ===== Onboarding =====
  verifyBusiness(businessNumber: string) {
    return this.request<import("@/types").VerifyBusinessResponse>(
      "POST", "/onboarding/verify-business", { business_number: businessNumber }
    );
  }

  searchBusiness(query: string) {
    return this.request<import("@/types").KakaoLocalSearchResult[]>(
      "GET", `/onboarding/search-business?query=${encodeURIComponent(query)}`
    );
  }

  completeOnboarding(data: any) {
    return this.request<import("@/types").CompleteOnboardingResponse>(
      "POST", "/onboarding/complete", data
    );
  }

  // ===== Dashboard =====
  getDashboard() {
    return this.request<import("@/types").DashboardData>("GET", "/dashboard");
  }

  // ===== Subsidies =====
  getSubsidyMatches() {
    return this.request<import("@/types").SubsidyMatchesResponse>("GET", "/subsidies/matches");
  }

  generateApplyDraft(subsidyId: string, additionalInfo?: string) {
    return this.request<import("@/types").ApplyDraftResponse>(
      "POST", "/subsidies/apply-draft",
      { subsidy_id: subsidyId, additional_info: additionalInfo }
    );
  }

  // ===== Actions =====
  getTodayAction() {
    return this.request<import("@/types").DailyAction>("GET", "/actions/today");
  }

  getActionHistory(days: number = 30) {
    return this.request<import("@/types").DailyAction[]>("GET", `/actions/history?days=${days}`);
  }

  completeAction(actionId: string) {
    return this.request("POST", `/actions/${actionId}/complete`);
  }

  // ===== Coupons =====
  createCoupon(data: import("@/types").CreateCouponRequest) {
    return this.request<import("@/types").Coupon>("POST", "/coupons/create", data);
  }

  getCoupons() {
    return this.request<import("@/types").Coupon[]>("GET", "/coupons");
  }

  getCoupon(couponId: string) {
    return this.request<import("@/types").Coupon>("GET", `/coupons/${couponId}`, undefined, false);
  }

  // ===== Voice =====
  voiceQuery(text: string) {
    return this.request<import("@/types").VoiceQueryResponse>(
      "POST", "/voice/query", { text }
    );
  }
}

export const api = new ApiClient();
```

### 4.4 Auth Hook (Zustand)

#### `frontend/src/hooks/useAuth.ts`

```typescript
import { create } from "zustand";
import { User } from "@/types";
import { api } from "@/lib/api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  login: (code: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: true }),

  login: async (code: string) => {
    try {
      const response = await api.kakaoCallback(code);
      api.setToken(response.access_token);
      set({ user: response.user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    api.clearToken();
    set({ user: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    try {
      const token = api.getToken();
      if (!token) {
        set({ isLoading: false });
        return;
      }
      const user = await api.getMe();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      api.clearToken();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
```

### 4.5 STT Hook

#### `frontend/src/hooks/useSTT.ts`

```typescript
import { useState, useCallback, useRef } from "react";

interface UseSTTReturn {
  isListening: boolean;
  transcript: string;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

export function useSTT(): UseSTTReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const startListening = useCallback(() => {
    setError(null);

    // Web Speech API 지원 여부 확인
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("이 브라우저는 음성 인식을 지원하지 않습니다.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "ko-KR";       // 한국어
    recognition.continuous = false;     // 단일 발화 모드
    recognition.interimResults = true;  // 중간 결과 표시

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (event: any) => {
      const current = event.results[event.results.length - 1];
      const text = current[0].transcript;
      setTranscript(text);
    };

    recognition.onerror = (event: any) => {
      setIsListening(false);
      if (event.error === "no-speech") {
        setError("음성이 감지되지 않았습니다. 다시 시도해주세요.");
      } else if (event.error === "not-allowed") {
        setError("마이크 권한이 필요합니다. 브라우저 설정을 확인해주세요.");
      } else {
        setError(`음성 인식 오류: ${event.error}`);
      }
    };

    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript("");
  }, []);

  return { isListening, transcript, error, startListening, stopListening, resetTranscript };
}
```

### 4.6 주요 페이지 구현

#### `frontend/src/app/layout.tsx`

```tsx
import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 경영코치 - 사장님이 놓치는 돈, AI가 찾아줍니다",
  description: "카카오 로그인 15초. 매일 아침, 놓치면 손해인 것 1개. 지원금 자동 매칭 + QR 쿠폰 1탭 생성.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "AI 경영코치",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#FEE500",  // 카카오 옐로우
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        {/* 카카오 SDK */}
        <script
          src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.1/kakao.min.js"
          integrity="sha384-kDljxUXHaJ9xAb2AzRd59KxjrFowngho0S06z8jxKOFkA5aORDsf8mc/"
          crossOrigin="anonymous"
          async
        />
      </head>
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        {children}
      </body>
    </html>
  );
}
```

#### `frontend/src/app/page.tsx` (랜딩/로그인)

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import KakaoLoginButton from "@/components/onboarding/KakaoLoginButton";

export default function LandingPage() {
  const { isAuthenticated, isLoading, user, checkAuth } = useAuth();
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.onboarding_completed) {
        router.push("/dashboard");
      } else {
        router.push("/onboarding");
      }
    }
  }, [isAuthenticated, user]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500" />
      </div>
    );
  }

  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-6">
      <div className="max-w-md w-full text-center space-y-8">
        {/* 로고/타이틀 */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">AI 경영코치</h1>
          <p className="text-lg text-red-600 font-semibold">
            사장님, 지금 놓치고 있는 돈이 있습니다
          </p>
        </div>

        {/* 가치 제안 */}
        <div className="space-y-4 text-left bg-white rounded-2xl p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <span className="text-2xl">💸</span>
            <div>
              <p className="font-semibold">지원금 최대 700만원</p>
              <p className="text-sm text-gray-500">자격 자동 판별 + 사업계획서 초안</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-2xl">📊</span>
            <div>
              <p className="font-semibold">매일 아침, 오늘 해야 할 것 1개</p>
              <p className="text-sm text-gray-500">안 하면 놓치는 매출 기회 알림</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-2xl">🎫</span>
            <div>
              <p className="font-semibold">QR 쿠폰 1탭 생성</p>
              <p className="text-sm text-gray-500">디자인 필요 없음, 바로 공유</p>
            </div>
          </div>
        </div>

        {/* 소셜 프루프 */}
        <p className="text-sm text-gray-500">
          카카오 로그인 + 상호명 입력 = 15초
        </p>

        {/* 카카오 로그인 버튼 */}
        <KakaoLoginButton />

        {/* 부가 정보 */}
        <p className="text-xs text-gray-400">
          앱 설치 불필요 (PWA) | 무료로 시작
        </p>
      </div>
    </main>
  );
}
```

#### `frontend/src/app/api/auth/kakao/callback/route.ts`

```typescript
import { NextRequest, NextResponse } from "next/server";

/**
 * 카카오 OAuth 콜백 핸들러.
 * 카카오에서 redirect된 code를 받아 백엔드로 전달하고,
 * JWT 토큰을 받은 뒤 클라이언트에 전달.
 *
 * 플로우:
 * 1. 카카오가 ?code=xxx 로 리다이렉트
 * 2. 이 route에서 code를 추출
 * 3. 클라이언트 사이드에서 처리하도록 HTML 반환
 *    (또는 백엔드 콜백 직접 호출 후 쿠키 설정)
 */
export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const error = request.nextUrl.searchParams.get("error");

  if (error) {
    return NextResponse.redirect(new URL("/?error=kakao_denied", request.url));
  }

  if (!code) {
    return NextResponse.redirect(new URL("/?error=no_code", request.url));
  }

  // 클라이언트 사이드에서 code를 처리하도록 리다이렉트
  // (CSR에서 api.kakaoCallback(code) 호출)
  return NextResponse.redirect(
    new URL(`/api/auth/kakao/callback/process?code=${code}`, request.url)
  );
}
```

실제로는 클라이언트 사이드에서 code를 처리하는 것이 더 간단하므로, 아래와 같이 별도 페이지를 만든다.

#### `frontend/src/app/auth/kakao/callback/page.tsx`

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function KakaoCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("인증 코드가 없습니다.");
      return;
    }

    login(code)
      .then(() => {
        // 로그인 성공 → useAuth의 user를 확인해 라우팅
        // (useAuth에서 setUser 후 page.tsx의 useEffect가 동작)
        router.push("/");
      })
      .catch((err) => {
        setError(err.message || "로그인에 실패했습니다.");
      });
  }, [searchParams]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-500">{error}</p>
        <button onClick={() => router.push("/")} className="text-blue-500 underline">
          돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500 mx-auto" />
        <p className="text-gray-500">로그인 중...</p>
      </div>
    </div>
  );
}
```

### 4.7 주요 컴포넌트

#### `frontend/src/components/onboarding/KakaoLoginButton.tsx`

```tsx
"use client";

const KAKAO_REST_API_KEY = process.env.NEXT_PUBLIC_KAKAO_REST_API_KEY;
const REDIRECT_URI = process.env.NEXT_PUBLIC_KAKAO_REDIRECT_URI;

export default function KakaoLoginButton() {
  const handleLogin = () => {
    const kakaoAuthUrl =
      `https://kauth.kakao.com/oauth/authorize` +
      `?client_id=${KAKAO_REST_API_KEY}` +
      `&redirect_uri=${encodeURIComponent(REDIRECT_URI!)}` +
      `&response_type=code` +
      `&scope=profile_nickname,profile_image,account_email,talk_message`;
    window.location.href = kakaoAuthUrl;
  };

  return (
    <button
      onClick={handleLogin}
      className="w-full flex items-center justify-center gap-2 bg-[#FEE500] text-[#191919] font-semibold py-4 rounded-xl text-lg hover:bg-[#FDD835] transition-colors"
    >
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path
          d="M12 3C6.48 3 2 6.48 2 10.8c0 2.76 1.8 5.16 4.5 6.54-.18.66-.66 2.4-.75 2.76-.12.48.18.48.36.36.18-.12 2.4-1.62 3.36-2.28.66.12 1.32.18 2.04.18 5.52 0 10-3.48 10-7.8S17.52 3 12 3z"
          fill="#191919"
        />
      </svg>
      카카오로 15초 만에 시작하기
    </button>
  );
}
```

#### `frontend/src/components/onboarding/BusinessNumberInput.tsx`

```tsx
"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { VerifyBusinessResponse } from "@/types";

interface Props {
  onVerified: (result: VerifyBusinessResponse, businessNumber: string) => void;
}

export default function BusinessNumberInput({ onVerified }: Props) {
  const [number, setNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async () => {
    if (number.length !== 10) {
      setError("사업자등록번호 10자리를 입력해주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.verifyBusiness(number);
      if (!result.is_valid) {
        setError(`사업자 상태: ${result.business_status}. 유효한 사업자번호를 입력해주세요.`);
        return;
      }
      onVerified(result, number);
    } catch (err: any) {
      setError(err.message || "확인에 실패했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">사업자등록번호</label>
      <div className="flex gap-2">
        <input
          type="text"
          inputMode="numeric"
          maxLength={10}
          value={number}
          onChange={(e) => setNumber(e.target.value.replace(/\D/g, ""))}
          placeholder="숫자 10자리 입력"
          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
        />
        <button
          onClick={handleVerify}
          disabled={loading || number.length !== 10}
          className="px-6 py-3 bg-yellow-400 text-black font-semibold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "확인 중..." : "확인"}
        </button>
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
```

#### `frontend/src/components/onboarding/BusinessNameSearch.tsx`

```tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import type { KakaoLocalSearchResult } from "@/types";

interface Props {
  onSelect: (result: KakaoLocalSearchResult) => void;
}

export default function BusinessNameSearch({ onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KakaoLocalSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await api.searchBusiness(query);
        setResults(data);
        setShowDropdown(data.length > 0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms 디바운스

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  const handleSelect = (result: KakaoLocalSearchResult) => {
    setQuery(result.place_name);
    setShowDropdown(false);
    onSelect(result);
  };

  return (
    <div className="space-y-3 relative">
      <label className="block text-sm font-medium text-gray-700">상호명</label>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="상호명을 입력하세요 (예: 스타벅스 혜화)"
        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none"
      />
      {loading && <p className="text-sm text-gray-400">검색 중...</p>}

      {showDropdown && (
        <ul className="absolute z-10 w-full bg-white border border-gray-200 rounded-xl shadow-lg mt-1 max-h-60 overflow-y-auto">
          {results.map((r, idx) => (
            <li
              key={idx}
              onClick={() => handleSelect(r)}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
            >
              <p className="font-medium">{r.place_name}</p>
              <p className="text-sm text-gray-500">{r.road_address_name || r.address_name}</p>
              <p className="text-xs text-gray-400">{r.category_name}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

#### `frontend/src/components/common/STTButton.tsx`

```tsx
"use client";

import { useSTT } from "@/hooks/useSTT";
import { api } from "@/lib/api";
import { useState } from "react";
import type { VoiceQueryResponse } from "@/types";

interface Props {
  onResult?: (response: VoiceQueryResponse) => void;
}

export default function STTButton({ onResult }: Props) {
  const { isListening, transcript, error, startListening, stopListening, resetTranscript } = useSTT();
  const [processing, setProcessing] = useState(false);
  const [response, setResponse] = useState<VoiceQueryResponse | null>(null);

  const handleToggle = () => {
    if (isListening) {
      stopListening();
      // 녹음 종료 시 자동으로 서버에 질의
      if (transcript) {
        processQuery(transcript);
      }
    } else {
      resetTranscript();
      setResponse(null);
      startListening();
    }
  };

  const processQuery = async (text: string) => {
    setProcessing(true);
    try {
      const res = await api.voiceQuery(text);
      setResponse(res);
      onResult?.(res);
    } catch (err) {
      console.error("Voice query failed:", err);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-3">
      <button
        onClick={handleToggle}
        className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
          isListening
            ? "bg-red-500 animate-pulse shadow-lg shadow-red-300"
            : "bg-yellow-400 hover:bg-yellow-500 shadow-md"
        }`}
      >
        {processing ? (
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white" />
        ) : (
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        )}
      </button>

      {/* 실시간 텍스트 표시 */}
      {transcript && (
        <p className="text-sm text-gray-600 bg-gray-100 rounded-lg px-3 py-2">
          &quot;{transcript}&quot;
        </p>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* AI 응답 */}
      {response && (
        <div className="bg-white rounded-xl p-4 shadow-sm space-y-2">
          <p className="text-gray-800">{response.answer}</p>
          <div className="flex flex-wrap gap-2">
            {response.suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => processQuery(s)}
                className="text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-full hover:bg-gray-200"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

#### `frontend/src/components/common/LossFrameMessage.tsx`

```tsx
"use client";

interface Props {
  message: string;
  amount?: number;       // 만원 단위
  daysLeft?: number;     // 마감까지 남은 일수
  variant?: "danger" | "warning" | "info";
}

export default function LossFrameMessage({ message, amount, daysLeft, variant = "danger" }: Props) {
  const bgColors = {
    danger: "bg-red-50 border-red-200",
    warning: "bg-orange-50 border-orange-200",
    info: "bg-yellow-50 border-yellow-200",
  };

  const textColors = {
    danger: "text-red-700",
    warning: "text-orange-700",
    info: "text-yellow-700",
  };

  return (
    <div className={`rounded-xl border p-4 ${bgColors[variant]}`}>
      <p className={`font-semibold ${textColors[variant]}`}>
        {message}
      </p>
      {amount && (
        <p className={`text-2xl font-bold mt-1 ${textColors[variant]}`}>
          최대 {amount.toLocaleString()}만원
        </p>
      )}
      {daysLeft !== undefined && daysLeft >= 0 && (
        <p className={`text-sm mt-1 ${textColors[variant]} opacity-75`}>
          마감까지 {daysLeft}일 남았습니다
        </p>
      )}
    </div>
  );
}
```

#### `frontend/src/components/dashboard/RiskScoreCard.tsx`

```tsx
"use client";

interface Props {
  score: number; // 0.0 ~ 1.0
}

export default function RiskScoreCard({ score }: Props) {
  const getLevel = () => {
    if (score <= 0.2) return { label: "양호", color: "text-green-600", bg: "bg-green-100", emoji: "🟢" };
    if (score <= 0.4) return { label: "주의", color: "text-yellow-600", bg: "bg-yellow-100", emoji: "🟡" };
    if (score <= 0.6) return { label: "경고", color: "text-orange-600", bg: "bg-orange-100", emoji: "🟠" };
    return { label: "위험", color: "text-red-600", bg: "bg-red-100", emoji: "🔴" };
  };

  const level = getLevel();
  const percentage = Math.round(score * 100);

  return (
    <div className={`rounded-2xl p-5 ${level.bg}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">경영 위험도</p>
          <p className={`text-3xl font-bold ${level.color}`}>{percentage}점</p>
          <p className={`text-sm font-medium ${level.color}`}>{level.emoji} {level.label}</p>
        </div>
        <div className="w-20 h-20">
          {/* 원형 프로그레스 */}
          <svg viewBox="0 0 36 36" className="w-full h-full">
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="3"
            />
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeDasharray={`${percentage}, 100`}
              className={level.color}
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
```

#### `frontend/src/components/dashboard/TodayAction.tsx`

```tsx
"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { DailyAction } from "@/types";

interface Props {
  action: DailyAction;
  onComplete?: () => void;
}

export default function TodayAction({ action, onComplete }: Props) {
  const [completing, setCompleting] = useState(false);

  const handleComplete = async () => {
    setCompleting(true);
    try {
      await api.completeAction(action.id);
      onComplete?.();
    } catch (err) {
      console.error(err);
    } finally {
      setCompleting(false);
    }
  };

  const ctaLabels: Record<string, string> = {
    create_coupon: "쿠폰 만들기",
    apply_subsidy: "신청하러 가기",
    view_detail: "자세히 보기",
  };

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-full font-medium">
          오늘의 액션
        </span>
        {action.is_completed && (
          <span className="text-xs bg-green-100 text-green-600 px-2 py-1 rounded-full">
            완료
          </span>
        )}
      </div>

      <h3 className="text-lg font-bold text-gray-900 mb-2">{action.title}</h3>
      <p className="text-sm text-gray-600 mb-4">{action.description}</p>

      {action.data_source && (
        <p className="text-xs text-gray-400 mb-3">출처: {action.data_source}</p>
      )}

      {!action.is_completed && action.cta_type && (
        <button
          onClick={handleComplete}
          disabled={completing}
          className="w-full py-3 bg-yellow-400 text-black font-semibold rounded-xl hover:bg-yellow-500 transition-colors disabled:opacity-50"
        >
          {completing ? "처리 중..." : ctaLabels[action.cta_type] || "실행하기"}
        </button>
      )}
    </div>
  );
}
```

---

## 5. Kakao OAuth 플로우

### 단계별 상세

```
[사용자] → 카카오 로그인 버튼 클릭
   ↓
[프론트엔드] → window.location.href = 카카오 인가 URL
   URL: https://kauth.kakao.com/oauth/authorize
   파라미터:
     client_id = KAKAO_REST_API_KEY
     redirect_uri = https://ai-coach.vercel.app/auth/kakao/callback
     response_type = code
     scope = profile_nickname,profile_image,account_email,talk_message
   ↓
[카카오] → 사용자 동의 화면 → 동의 후 redirect_uri로 리다이렉트
   URL: https://ai-coach.vercel.app/auth/kakao/callback?code=AUTHORIZATION_CODE
   ↓
[프론트엔드] → /auth/kakao/callback 페이지에서 code 추출
   → api.kakaoCallback(code) 호출
   → POST https://api-url/auth/kakao/callback?code=AUTHORIZATION_CODE
   ↓
[백엔드] → 카카오 토큰 교환
   POST https://kauth.kakao.com/oauth/token
   Body (form-urlencoded):
     grant_type = authorization_code
     client_id = KAKAO_REST_API_KEY
     client_secret = KAKAO_CLIENT_SECRET
     redirect_uri = KAKAO_REDIRECT_URI
     code = AUTHORIZATION_CODE
   Response:
     { access_token, refresh_token, expires_in, token_type }
   ↓
[백엔드] → 카카오 사용자 정보 조회
   GET https://kapi.kakao.com/v2/user/me
   Headers: Authorization: Bearer {access_token}
   Response:
     {
       id: 12345678,   ← kakao_id
       properties: { nickname: "이준수", profile_image: "..." },
       kakao_account: { email: "xxx@kakao.com" }
     }
   ↓
[백엔드] → DB에 사용자 upsert (kakao_id 기준)
   → JWT 토큰 생성 (user.id를 sub으로)
   → { access_token: JWT, user: {...} } 반환
   ↓
[프론트엔드] → JWT를 localStorage에 저장
   → 이후 모든 API 요청에 Authorization: Bearer JWT 헤더 추가
```

### `backend/app/services/kakao_service.py`

```python
"""카카오 OAuth + 로컬 검색 서비스."""
import httpx
from typing import Optional, List
from app.config import settings
from app.utils.retry import retry_async


class KakaoService:
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"
    LOCAL_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
    SEND_ME_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    @retry_async(max_retries=2, delay=1.0)
    async def get_token(self, code: str) -> Optional[dict]:
        """인가 코드 → 액세스 토큰 교환."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.kakao_rest_api_key,
                    "client_secret": settings.kakao_client_secret,
                    "redirect_uri": settings.kakao_redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code != 200:
                return None
            return response.json()

    @retry_async(max_retries=2, delay=1.0)
    async def get_user_info(self, access_token: str) -> Optional[dict]:
        """액세스 토큰 → 사용자 정보 조회."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                return None
            return response.json()

    @retry_async(max_retries=2, delay=1.0)
    async def search_local(self, query: str, size: int = 5) -> Optional[List[dict]]:
        """카카오 로컬 키워드 검색 (상호명 자동완성)."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                self.LOCAL_SEARCH_URL,
                params={"query": query, "size": size},
                headers={"Authorization": f"KakaoAK {settings.kakao_rest_api_key}"},
            )
            if response.status_code != 200:
                return None
            data = response.json()
            return data.get("documents", [])

    @retry_async(max_retries=2, delay=1.0)
    async def send_to_me(self, access_token: str, text: str, link_url: str = "") -> bool:
        """
        카카오톡 나에게 보내기.
        사전 조건: 사용자가 talk_message scope에 동의해야 함.
        """
        template_object = {
            "object_type": "text",
            "text": text[:200],  # 최대 200자
            "link": {
                "web_url": link_url or settings.kakao_redirect_uri.rsplit("/", 3)[0],
                "mobile_web_url": link_url or settings.kakao_redirect_uri.rsplit("/", 3)[0],
            },
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.SEND_ME_URL,
                data={"template_object": str(template_object).replace("'", '"')},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            return response.status_code == 200
```

---

## 6. 서울시 API 연동

### `backend/app/services/seoul_api_service.py`

```python
"""
서울시 열린데이터 API 3종 연동.
모든 API는 동일한 인증키(SEOUL_API_KEY) 사용.
"""
import httpx
from typing import Optional
from datetime import date, timedelta
from app.config import settings
from app.utils.retry import retry_async
from app.utils.cache import cache


class SeoulAPIService:

    BASE_URL = "http://openapi.seoul.go.kr:8088"

    # ========================================
    # 1. 상권분석 매출 API (서울시 우리마을가게 상권분석 서비스)
    # ========================================
    # 엔드포인트 형식:
    #   http://openapi.seoul.go.kr:8088/{API_KEY}/json/tbgiRtgFoodCuisineQrtSalesMonthlyItem/{start}/{end}
    # 주요 파라미터: 자치구 코드, 행정동 코드, 업종 대분류
    # 업데이트 주기: 분기별
    # 응답 형태: 분기별 매출액, 매출 건수, 매출 단가 등
    #
    # 실제 사용 API: VwsmTrdarSelngQq (상권_분기별_매출액)
    # URL: http://openapi.seoul.go.kr:8088/{KEY}/json/VwsmTrdarSelngQq/1/20/
    SALES_SERVICE = "VwsmTrdarSelngQq"

    @retry_async(max_retries=2, delay=1.0)
    @cache(ttl=86400 * 7, key_prefix="seoul_sales")  # 7일 캐시
    async def get_commercial_sales(
        self,
        gu_name: str,
        dong_name: str,
        business_type: str,
    ) -> Optional[dict]:
        """
        상권분석 분기별 매출 데이터 조회.

        Parameters:
            gu_name: 구 이름 (예: "종로구")
            dong_name: 동 이름 (예: "혜화동")
            business_type: 업종 (예: "카페")

        Returns:
            {
                "current_quarter_sales": 5200,   # 당분기 평균 매출 (만원)
                "prev_quarter_sales": 5500,       # 전분기 평균 매출 (만원)
                "quarterly_change": -5.45,         # 전분기 대비 변화율 (%)
                "data_period": "2025Q3",
                "area_name": "혜화동"
            }
        """
        url = f"{self.BASE_URL}/{settings.seoul_api_key}/json/{self.SALES_SERVICE}/1/20/"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return None

            data = response.json()
            rows = data.get(self.SALES_SERVICE, {}).get("row", [])

            # dong_name과 business_type으로 필터
            # 실제 필드명: ADSTRD_NM (행정동명), SVC_INDUTY_NM (서비스_업종명)
            filtered = [
                r for r in rows
                if dong_name in r.get("ADSTRD_NM", "") and business_type in r.get("SVC_INDUTY_NM", "")
            ]

            if not filtered:
                # 동 단위 데이터 없으면 구 단위로 fallback
                filtered = [
                    r for r in rows
                    if business_type in r.get("SVC_INDUTY_NM", "")
                ]

            if not filtered:
                return {"current_quarter_sales": 0, "prev_quarter_sales": 0, "quarterly_change": 0, "data_period": "N/A", "area_name": dong_name}

            # 최신 분기 데이터 사용
            latest = filtered[0]
            current_sales = int(latest.get("THSMON_SELNG_AMT", 0)) // 10000  # 원→만원
            # 전분기 대비 변화율 계산 (데이터가 있는 경우)
            prev_sales = int(latest.get("LSTQRT_SELNG_AMT", current_sales)) // 10000 if latest.get("LSTQRT_SELNG_AMT") else current_sales
            change = ((current_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0

            return {
                "current_quarter_sales": current_sales,
                "prev_quarter_sales": prev_sales,
                "quarterly_change": round(change, 2),
                "data_period": latest.get("STDR_YYQU_CD", "N/A"),
                "area_name": dong_name,
            }

    # ========================================
    # 2. 생활인구 API (서울 생활인구 내국인)
    # ========================================
    # 엔드포인트: SPOP_LOCAL_RESD_DONG
    # URL: http://openapi.seoul.go.kr:8088/{KEY}/json/SPOP_LOCAL_RESD_DONG/1/20/{DATE}
    # 업데이트 주기: 일별 (T-1일)
    POPULATION_SERVICE = "SPOP_LOCAL_RESD_DONG"

    @retry_async(max_retries=2, delay=1.0)
    @cache(ttl=86400, key_prefix="seoul_pop")  # 1일 캐시
    async def get_living_population(self, dong_name: str) -> Optional[dict]:
        """
        생활인구 일별 데이터 조회.

        Parameters:
            dong_name: 행정동명

        Returns:
            {
                "today": 45200,           # 오늘(어제) 생활인구
                "yesterday": 42000,        # 전일 생활인구
                "change_percent": 7.62,    # 전일 대비 변화율
                "data_date": "2026-04-03"
            }
        """
        # T-1일 데이터 조회 (오늘 데이터는 아직 없음)
        target_date = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
        prev_date = (date.today() - timedelta(days=2)).strftime("%Y%m%d")

        async with httpx.AsyncClient(timeout=15.0) as client:
            # 어제 데이터
            url_today = f"{self.BASE_URL}/{settings.seoul_api_key}/json/{self.POPULATION_SERVICE}/1/20/{target_date}"
            resp_today = await client.get(url_today)

            # 그저께 데이터
            url_prev = f"{self.BASE_URL}/{settings.seoul_api_key}/json/{self.POPULATION_SERVICE}/1/20/{prev_date}"
            resp_prev = await client.get(url_prev)

        today_pop = self._extract_population(resp_today, dong_name) if resp_today.status_code == 200 else 0
        prev_pop = self._extract_population(resp_prev, dong_name) if resp_prev.status_code == 200 else today_pop

        change = ((today_pop - prev_pop) / prev_pop * 100) if prev_pop > 0 else 0

        return {
            "today": today_pop,
            "yesterday": prev_pop,
            "change_percent": round(change, 2),
            "data_date": target_date,
        }

    def _extract_population(self, response, dong_name: str) -> int:
        """응답에서 행정동 인구 추출."""
        try:
            data = response.json()
            rows = data.get(self.POPULATION_SERVICE, {}).get("row", [])
            for r in rows:
                if dong_name in r.get("ADSTRD_NM", ""):
                    return int(float(r.get("TOT_LVPOP_CO", 0)))
        except Exception:
            pass
        return 0

    # ========================================
    # 3. 문화행사 API (서울시 문화행사 정보)
    # ========================================
    # 엔드포인트: culturalEventInfo
    # URL: http://openapi.seoul.go.kr:8088/{KEY}/json/culturalEventInfo/1/20/
    # 업데이트 주기: 수시
    EVENTS_SERVICE = "culturalEventInfo"

    @retry_async(max_retries=2, delay=1.0)
    @cache(ttl=43200, key_prefix="seoul_events")  # 12시간 캐시
    async def get_cultural_events(self, gu_name: str) -> Optional[list]:
        """
        해당 구의 문화행사 정보 조회.

        Parameters:
            gu_name: 구 이름

        Returns:
            [
                {
                    "title": "혜화 연극제",
                    "place": "대학로",
                    "start_date": "2026-04-10",
                    "end_date": "2026-04-15",
                    "category": "연극",
                    "url": "http://..."
                },
                ...
            ]
        """
        url = f"{self.BASE_URL}/{settings.seoul_api_key}/json/{self.EVENTS_SERVICE}/1/50/"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return None

            data = response.json()
            rows = data.get(self.EVENTS_SERVICE, {}).get("row", [])

            events = []
            for r in rows:
                # GUNAME 필드로 구 필터링
                if gu_name in r.get("GUNAME", ""):
                    events.append({
                        "title": r.get("TITLE", ""),
                        "place": r.get("PLACE", ""),
                        "start_date": r.get("STRTDATE", ""),
                        "end_date": r.get("END_DATE", ""),
                        "category": r.get("CODENAME", ""),
                        "url": r.get("ORG_LINK", ""),
                    })

            # 시작일 기준 정렬 (가까운 순)
            events.sort(key=lambda x: x["start_date"])
            return events
```

---

## 7. RAG 파이프라인

### `backend/app/services/rag_service.py`

```python
"""
ChromaDB + LangChain RAG 서비스.
보조금/지원사업 문서를 벡터 검색하여 사용자에게 매칭.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Optional
from datetime import date
from uuid import UUID

from app.config import settings


class RAGService:
    _client = None
    _collection = None
    _embeddings = None

    def __init__(self):
        if RAGService._client is None:
            RAGService._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        if RAGService._collection is None:
            RAGService._collection = RAGService._client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},  # 코사인 유사도
            )
        if RAGService._embeddings is None:
            RAGService._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",  # $0.02/1M tokens, 1536 차원
                openai_api_key=settings.openai_api_key,
            )

    async def index_subsidy(self, subsidy_id: str, text: str, metadata: dict):
        """
        보조금 문서를 ChromaDB에 인덱싱.

        Chunking 전략:
        - chunk_size: 500자 (한국어 특성상 영어보다 작게)
        - chunk_overlap: 50자
        - separator: ["\n\n", "\n", ". ", " "]

        metadata에 포함할 정보:
        - subsidy_id, title, organization, deadline, max_amount
        - target_business_types, target_regions
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_text(text)

        for i, chunk in enumerate(chunks):
            doc_id = f"{subsidy_id}_{i}"
            embedding = await self._get_embedding(chunk)

            RAGService._collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{
                    **metadata,
                    "chunk_index": i,
                    "subsidy_id": subsidy_id,
                }],
            )

    async def search_subsidies(self, query: str, top_k: int = 5) -> List[dict]:
        """
        사용자 쿼리로 보조금 벡터 검색.

        Parameters:
            query: 검색 쿼리 (예: "종로구 혜화동 카페 소상공인 지원금")
            top_k: 반환할 최대 결과 수

        Returns:
            [
                {
                    "id": "uuid",
                    "title": "소상공인 디지털전환 지원",
                    "organization": "소상공인시장진흥공단",
                    "max_amount": 400,
                    "deadline": "2026-05-31",
                    "days_until_deadline": 57,
                    "description": "...",
                    "relevance_score": 0.85,
                    ...
                }
            ]

        관련도 임계값: 0.3 미만은 제외 (코사인 거리 기준)
        """
        query_embedding = await self._get_embedding(query)

        results = RAGService._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # 중복 제거 위해 2배 조회
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        # 중복 subsidy_id 제거 + 관련도 필터링
        seen_ids = set()
        matched = []

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            relevance = 1.0 - distance  # 코사인 거리 → 유사도

            if relevance < 0.3:  # 임계값 미달
                continue

            meta = results["metadatas"][0][i]
            subsidy_id = meta.get("subsidy_id", doc_id)

            if subsidy_id in seen_ids:
                continue
            seen_ids.add(subsidy_id)

            # 마감일까지 남은 일수 계산
            days_left = None
            deadline = meta.get("deadline")
            if deadline:
                try:
                    deadline_date = date.fromisoformat(deadline)
                    days_left = (deadline_date - date.today()).days
                except ValueError:
                    pass

            matched.append({
                "id": subsidy_id,
                "title": meta.get("title", ""),
                "organization": meta.get("organization", ""),
                "max_amount": meta.get("max_amount"),
                "deadline": deadline,
                "days_until_deadline": days_left,
                "description": results["documents"][0][i],
                "eligibility_summary": meta.get("eligibility_summary"),
                "application_url": meta.get("application_url"),
                "relevance_score": round(relevance, 3),
            })

        # 마감일 임박 순 정렬 (마감일 없는 것은 뒤로)
        matched.sort(key=lambda x: x.get("days_until_deadline") or 9999)
        return matched[:top_k]

    async def _get_embedding(self, text: str) -> List[float]:
        """텍스트 → 임베딩 벡터."""
        result = RAGService._embeddings.embed_query(text)
        return result
```

---

## 8. GPT-4o 프롬프트 템플릿

### `backend/app/services/action_generator.py`

```python
"""
GPT-4o 기반 일일 액션 생성 + 사업계획서 초안 + 음성 질의 처리.
모든 프롬프트는 손실 프레이밍(Loss Framing) 기반.
"""
import json
from datetime import date, timedelta
from typing import Optional, List
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, DailyAction, Subsidy


class ActionGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    # ========================================
    # 프롬프트 1: 일일 액션 생성
    # ========================================
    DAILY_ACTION_SYSTEM_PROMPT = """당신은 소상공인 전문 AI 경영코치입니다.
사장님에게 매일 아침 "오늘 놓치면 손해인 것 1가지"를 알려줍니다.

## 핵심 원칙
1. **손실 프레이밍**: "추천합니다"가 아니라 "놓치고 있습니다". 손실 회피(Loss Aversion) 원리를 적용합니다.
2. **구체적 행동**: 모호한 조언이 아니라, 1탭으로 실행 가능한 구체적 행동을 제시합니다.
3. **데이터 기반**: 제공된 데이터를 근거로 메시지를 작성합니다. 데이터가 없으면 만들어내지 마세요.
4. **간결함**: 제목 1줄 + 설명 2~3줄. 사장님은 바쁩니다.

## 응답 형식 (JSON)
{
    "action_type": "subsidy|event|coupon|competitor|population",
    "title": "손실 프레이밍 제목 (30자 이내)",
    "description": "구체적 행동 설명 (100자 이내)",
    "risk_score": 0.0~1.0,
    "cta_type": "create_coupon|apply_subsidy|view_detail",
    "data_source": "데이터 출처"
}"""

    DAILY_ACTION_USER_PROMPT = """## 사장님 정보
- 상호: {business_name}
- 업종: {business_type}
- 위치: {gu_name} {dong_name}

## 오늘 데이터
- 날짜: {today} ({weekday})
- 매출 트렌드: {sales_summary}
- 유동인구: {population_summary}
- 근처 문화행사: {events_summary}
- 매칭 지원사업: {subsidy_summary}

## 지시사항
위 데이터를 바탕으로 오늘 사장님이 가장 놓치면 안 되는 행동 1가지를 JSON으로 생성하세요.
"추천합니다"가 아니라 "놓치고 있습니다" 톤으로 작성하세요.
데이터가 부족한 항목은 무시하고, 확실한 데이터만 활용하세요."""

    async def generate_daily_action(
        self,
        user: User,
        sales_data: Optional[dict],
        population_data: Optional[dict],
        events_data: Optional[list],
        subsidy_data: Optional[list],
    ) -> dict:
        """일일 액션 생성."""
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        today = date.today()
        weekday = weekdays[today.weekday()]

        # 데이터 요약 문자열 구성
        sales_summary = "데이터 없음"
        if sales_data and sales_data.get("quarterly_change") is not None:
            change = sales_data["quarterly_change"]
            sales_summary = f"전분기 대비 {'+' if change >= 0 else ''}{change}% ({sales_data.get('data_period', 'N/A')} 기준)"

        population_summary = "데이터 없음"
        if population_data and population_data.get("change_percent") is not None:
            change = population_data["change_percent"]
            population_summary = f"전일 대비 {'+' if change >= 0 else ''}{change}% (약 {population_data.get('today', 0):,}명)"

        events_summary = "없음"
        if events_data:
            event_list = [f"{e['title']} ({e['start_date']}~)" for e in events_data[:3]]
            events_summary = ", ".join(event_list)

        subsidy_summary = "매칭 없음"
        if subsidy_data:
            sub_list = [f"{s['title']} (최대 {s.get('max_amount', '?')}만원, D-{s.get('days_until_deadline', '?')})" for s in subsidy_data[:3]]
            subsidy_summary = " / ".join(sub_list)

        user_prompt = self.DAILY_ACTION_USER_PROMPT.format(
            business_name=user.business_name or "미등록",
            business_type=user.business_type or "미분류",
            gu_name=user.gu_name or "",
            dong_name=user.dong_name or "",
            today=today.isoformat(),
            weekday=weekday,
            sales_summary=sales_summary,
            population_summary=population_summary,
            events_summary=events_summary,
            subsidy_summary=subsidy_summary,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.DAILY_ACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # GPT-4o 실패 시 템플릿 기반 간소화 응답
            return self._fallback_action(user, sales_data, population_data, subsidy_data)

    def _fallback_action(self, user, sales_data, population_data, subsidy_data) -> dict:
        """GPT-4o 실패 시 템플릿 기반 기본 액션."""
        if subsidy_data:
            s = subsidy_data[0]
            return {
                "action_type": "subsidy",
                "title": f"지원금 {s.get('max_amount', '')}만원 마감 임박",
                "description": f"{s['title']} 신청 기한이 다가오고 있습니다. 놓치면 내년까지 기다려야 합니다.",
                "risk_score": 0.6,
                "cta_type": "apply_subsidy",
                "data_source": "지원사업 매칭",
            }
        if population_data and population_data.get("change_percent", 0) > 10:
            return {
                "action_type": "population",
                "title": f"유동인구 {population_data['change_percent']}%↑ 놓치지 마세요",
                "description": "오늘 유동인구가 급증 예상입니다. 이벤트 쿠폰으로 고객을 잡으세요.",
                "risk_score": 0.4,
                "cta_type": "create_coupon",
                "data_source": "서울시 생활인구",
            }
        return {
            "action_type": "coupon",
            "title": "이번 주 이벤트 없이 지나가고 있어요",
            "description": "QR 쿠폰을 만들어 가게에 부착하세요. 1분이면 됩니다.",
            "risk_score": 0.3,
            "cta_type": "create_coupon",
            "data_source": "기본 추천",
        }

    async def create_initial_action(self, db: AsyncSession, user: User, **kwargs):
        """온보딩 직후 첫 액션 생성."""
        action_data = await self.generate_daily_action(
            user=user,
            sales_data=kwargs.get("sales_data"),
            population_data=kwargs.get("population_data"),
            events_data=kwargs.get("events_data"),
            subsidy_data=kwargs.get("matched_subsidies"),
        )

        action = DailyAction(
            user_id=user.id,
            date=date.today(),
            action_type=action_data.get("action_type", "general"),
            title=action_data.get("title", "오늘의 행동을 확인하세요"),
            description=action_data.get("description", ""),
            risk_score=action_data.get("risk_score", 0.3),
            data_source=action_data.get("data_source"),
            cta_type=action_data.get("cta_type"),
            cta_payload=action_data.get("cta_payload"),
        )
        db.add(action)

    # ========================================
    # 프롬프트 2: 사업계획서 초안 생성
    # ========================================
    BUSINESS_PLAN_SYSTEM_PROMPT = """당신은 소상공인 지원사업 사업계획서 전문 작성가입니다.
사장님의 사업 정보와 지원사업 요건을 바탕으로 사업계획서 초안을 작성합니다.

## 작성 원칙
1. 지원사업의 심사 기준에 맞춰 작성합니다.
2. 사장님의 실제 사업 정보만 사용합니다. 없는 정보를 만들어내지 마세요.
3. 비워야 할 칸은 [사장님 작성 필요] 로 표시합니다.
4. 마크다운 형식으로 작성합니다.
5. 한국어로 작성합니다.

## 구조
1. 사업 개요
2. 현재 경영 현황
3. 지원사업 활용 계획
4. 기대 효과
5. 사업 일정"""

    BUSINESS_PLAN_USER_PROMPT = """## 사장님 정보
- 상호: {business_name}
- 업종: {business_type}
- 위치: {address}
- 사업자번호: {business_number}

## 지원사업 정보
- 사업명: {subsidy_title}
- 지원기관: {subsidy_org}
- 최대 지원금: {max_amount}만원
- 자격 요건: {eligibility}
- 사업 설명: {subsidy_description}

## 추가 정보
{additional_info}

위 정보를 바탕으로 사업계획서 초안을 마크다운으로 작성하세요.
사장님이 수정할 부분은 [사장님 작성 필요]로 표시하세요."""

    async def generate_business_plan_draft(
        self, user: User, subsidy: Subsidy, additional_info: Optional[str] = None
    ) -> str:
        """사업계획서 초안 생성."""
        user_prompt = self.BUSINESS_PLAN_USER_PROMPT.format(
            business_name=user.business_name or "[사장님 작성 필요]",
            business_type=user.business_type or "[사장님 작성 필요]",
            address=user.address or "[사장님 작성 필요]",
            business_number=user.business_number or "[사장님 작성 필요]",
            subsidy_title=subsidy.title,
            subsidy_org=subsidy.organization,
            max_amount=subsidy.max_amount or "미정",
            eligibility=subsidy.eligibility_summary or "상세 내용 확인 필요",
            subsidy_description=subsidy.description[:500],
            additional_info=additional_info or "없음",
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.BUSINESS_PLAN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception:
            return self._fallback_plan_template(user, subsidy)

    def _fallback_plan_template(self, user: User, subsidy: Subsidy) -> str:
        """GPT 실패 시 기본 템플릿."""
        return f"""# {subsidy.title} 사업계획서 초안

## 1. 사업 개요
- 상호명: {user.business_name or '[작성 필요]'}
- 업종: {user.business_type or '[작성 필요]'}
- 소재지: {user.address or '[작성 필요]'}
- 사업자등록번호: {user.business_number or '[작성 필요]'}

## 2. 현재 경영 현황
[사장님 작성 필요 - 현재 매출, 직원 수, 주요 고객층 등]

## 3. 지원사업 활용 계획
- 신청 사업: {subsidy.title}
- 지원 기관: {subsidy.organization}
- 최대 지원금: {subsidy.max_amount or '확인 필요'}만원
- 활용 계획: [사장님 작성 필요]

## 4. 기대 효과
[사장님 작성 필요 - 매출 증가, 고용 효과, 디지털화 등]

## 5. 사업 일정
[사장님 작성 필요 - 월별 추진 계획]

---
*이 초안은 AI가 자동 생성했습니다. 사장님의 실제 정보로 수정해주세요.*"""

    # ========================================
    # 프롬프트 3: 음성 질의 처리
    # ========================================
    VOICE_QUERY_SYSTEM_PROMPT = """당신은 소상공인 AI 경영코치입니다. 사장님의 음성 질의에 친절하고 실용적으로 답변합니다.

## 응답 원칙
1. 존댓말, 간결하게 (3문장 이내)
2. 구체적 행동 제안 포함
3. 손실 프레이밍 톤: "놓치고 있습니다" > "추천합니다"
4. 제공된 컨텍스트 데이터만 사용. 없는 정보는 만들지 마세요.
5. "잘 모르겠습니다" 대신 "확인해서 알려드리겠습니다"

## 사장님 정보
- 상호: {business_name}
- 업종: {business_type}
- 위치: {gu_name} {dong_name}"""

    VOICE_QUERY_USER_PROMPT = """## 사장님 질문
"{query_text}"

## 감지된 의도
{intent}

## 관련 데이터
{context}

위 정보를 바탕으로 사장님 질문에 답변하세요. 3문장 이내, 실행 가능한 조언 포함."""

    async def process_voice_query(
        self, user: User, query_text: str, intent: str, context_docs: list
    ) -> str:
        """음성 질의 GPT-4o 처리."""
        context_str = "\n".join([
            f"- {doc.get('title', '')}: {doc.get('description', '')[:200]}"
            for doc in context_docs
        ]) if context_docs else "관련 데이터 없음"

        system_prompt = self.VOICE_QUERY_SYSTEM_PROMPT.format(
            business_name=user.business_name or "미등록",
            business_type=user.business_type or "미분류",
            gu_name=user.gu_name or "",
            dong_name=user.dong_name or "",
        )

        user_prompt = self.VOICE_QUERY_USER_PROMPT.format(
            query_text=query_text,
            intent=intent,
            context=context_str,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=256,
            )
            return response.choices[0].message.content
        except Exception:
            return "죄송합니다, 잠시 연결이 불안정합니다. 다시 한번 말씀해주세요."
```

---

## 9. QR 쿠폰 생성

### `backend/app/services/coupon_service.py`

```python
"""
QR 쿠폰 생성 서비스.
qrcode 라이브러리로 QR 이미지 생성, base64로 인코딩하여 DB 저장.
"""
import qrcode
import io
import base64
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, CouponTemplate


class CouponService:
    # QR에 인코딩할 URL 형식
    # 고객이 스캔하면 이 URL로 이동 → 쿠폰 상세 페이지
    COUPON_URL_TEMPLATE = "{app_url}/coupon/{coupon_id}"

    async def create_coupon(
        self,
        db: AsyncSession,
        user: User,
        title: str,
        discount_type: str,
        discount_value: int = None,
        description: str = None,
        valid_days: int = 7,
    ) -> CouponTemplate:
        """
        QR 쿠폰 생성.

        플로우:
        1. CouponTemplate 레코드 생성 (ID 확보)
        2. 쿠폰 URL 생성: {APP_URL}/coupon/{coupon_id}
        3. QR 코드 이미지 생성 (PNG, base64)
        4. DB 업데이트
        """
        import uuid

        coupon_id = uuid.uuid4()
        valid_from = date.today()
        valid_until = date.today() + timedelta(days=valid_days)

        # 쿠폰 URL
        app_url = settings.cors_origins.split(",")[0].strip()  # 프론트엔드 URL
        qr_data = self.COUPON_URL_TEMPLATE.format(app_url=app_url, coupon_id=str(coupon_id))

        # QR 코드 생성
        qr_image_base64 = self._generate_qr_base64(qr_data)

        coupon = CouponTemplate(
            id=coupon_id,
            user_id=user.id,
            title=title,
            discount_type=discount_type,
            discount_value=discount_value,
            description=description,
            valid_days=valid_days,
            valid_from=valid_from,
            valid_until=valid_until,
            qr_data=qr_data,
            qr_image_base64=qr_image_base64,
        )
        db.add(coupon)
        await db.flush()

        return coupon

    def _generate_qr_base64(self, data: str) -> str:
        """
        QR 코드 PNG 이미지를 base64 문자열로 생성.

        설정:
        - version=1: 최소 크기 (21x21 모듈)
        - error_correction=ERROR_CORRECT_M: 15% 복원 (적당한 내구성)
        - box_size=10: 각 모듈 10px
        - border=4: 여백 4모듈 (표준)
        - fill_color="#000000"
        - back_color="#FFFFFF"
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # PNG → base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{b64}"
```

---

## 10. 알림 시스템

### `backend/app/services/notification_service.py`

```python
"""
알림 서비스: Kakao Talk 나에게 보내기 + Firebase FCM.
우선순위: Kakao > FCM > (향후 이메일)
"""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, NotificationLog
from app.services.kakao_service import KakaoService


class NotificationService:
    def __init__(self):
        self._fcm_initialized = False

    def _init_fcm(self):
        """Firebase Admin SDK 초기화 (lazy)."""
        if self._fcm_initialized:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials
            if settings.firebase_service_account_json:
                cred = credentials.Certificate(settings.firebase_service_account_json)
            elif settings.firebase_service_account:
                cred = credentials.Certificate(json.loads(settings.firebase_service_account))
            else:
                return
            firebase_admin.initialize_app(cred)
            self._fcm_initialized = True
        except Exception:
            pass

    async def send_notification(
        self,
        db: AsyncSession,
        user: User,
        title: str,
        message: str,
        message_type: str = "daily_action",
        link_url: str = "",
    ) -> bool:
        """
        알림 발송. 우선순위:
        1. 카카오톡 나에게 보내기 (kakao_access_token 있을 때)
        2. FCM 푸시 (fcm_token 있을 때)

        둘 다 실패하면 notification_log에 failed 기록.
        """
        sent = False
        channel = "kakao"

        # 1. 카카오톡 시도
        if user.kakao_access_token:
            kakao = KakaoService()
            text = f"[AI 경영코치] {title}\n\n{message}"
            try:
                success = await kakao.send_to_me(user.kakao_access_token, text, link_url)
                if success:
                    sent = True
            except Exception:
                pass

        # 2. FCM 시도
        if not sent and user.fcm_token:
            channel = "fcm"
            try:
                self._init_fcm()
                if self._fcm_initialized:
                    from firebase_admin import messaging
                    fcm_message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=message[:100],
                        ),
                        data={"link_url": link_url, "message_type": message_type},
                        token=user.fcm_token,
                    )
                    messaging.send(fcm_message)
                    sent = True
            except Exception:
                pass

        # 로그 기록
        log = NotificationLog(
            user_id=user.id,
            channel=channel,
            message_type=message_type,
            title=title,
            message=message,
            status="sent" if sent else "failed",
            sent_at=datetime.utcnow() if sent else None,
        )
        db.add(log)

        return sent
```

---

## 11. 손실 프레이밍 메시지 템플릿

### `backend/app/utils/loss_framing.py`

```python
"""
손실 프레이밍 메시지 템플릿.
모든 메시지는 "추천합니다"가 아니라 "놓치고 있습니다" 톤.
"""

# ===== 지원금 관련 =====
SUBSIDY_LOSS_TEMPLATES = {
    "deadline_urgent": "사장님, {subsidy_name} 마감 D-{days_left}입니다. {amount}만원, 안 하면 내년까지 없어요.",
    "deadline_week": "사장님, {subsidy_name} 마감이 일주일 남았습니다. {social_proof}",
    "new_match": "사장님 업종에 딱 맞는 지원금 {amount}만원을 놓치고 있습니다.",
    "multiple_match": "사장님, 지금 신청 가능한 지원금 {count}건, 최대 {total_amount}만원을 놓치고 있습니다.",
}

# ===== 유동인구 관련 =====
POPULATION_LOSS_TEMPLATES = {
    "surge": "오늘 {dong_name} 유동인구 {change}%↑ 예상인데 이벤트 없으면 놓쳐요.",
    "weekend_surge": "주말 유동인구 {change}%↑ 예상. 이벤트 없이 지나가면 기회 손실입니다.",
    "decline": "유동인구가 {change}% 줄었습니다. 쿠폰 이벤트로 고객을 붙잡으세요.",
}

# ===== 매출 관련 =====
SALES_LOSS_TEMPLATES = {
    "decline": "사장님 업종 매출이 전분기 대비 {change}% 감소했습니다. 대응이 필요합니다.",
    "competitor_event": "같은 동네 {count}곳이 이벤트 중인데, 사장님만 안 하고 계세요.",
    "weekly_loss": "이번 주 이벤트 없이 지나가고 있어요. 매출 기회를 놓치고 있습니다.",
}

# ===== 문화행사 관련 =====
EVENT_LOSS_TEMPLATES = {
    "nearby_event": "{event_name} D-{days_left}. 옆 가게가 이벤트 시작했는데, 사장님은요?",
    "ongoing_event": "{event_name} 진행 중! 이벤트 연계 쿠폰으로 유입을 잡으세요.",
}

# ===== 리텐션 (FOMO) =====
RETENTION_TEMPLATES = {
    "welcome": "{dong_name}에서 {rank}번째로 가입하셨어요! 사장님의 첫 번째 지원금을 찾아볼게요.",
    "week1": "이번 주 쿠폰 만든 가게 {count}곳. 사장님은 아직 안 만드셨어요.",
    "week2": "옆 가게가 지원금 {amount}만원 받았대요. 사장님은 아직 미신청입니다.",
    "week3": "이벤트 한 가게가 매출 +{percent}%. 사장님도 시작하세요.",
    "monthly": "이번 달 절약한 시간: {hours}시간. AI 경영코치가 대신 찾아드리고 있어요.",
}

# ===== 쿠폰 관련 =====
COUPON_LOSS_TEMPLATES = {
    "no_coupon": "이번 달 쿠폰 0개. 같은 동네 가게들은 평균 {avg_count}개 만들었어요.",
    "low_scan": "쿠폰 스캔 {scan_count}건. 더 많은 고객에게 노출시키세요.",
}


def format_loss_message(template_key: str, category: str, **kwargs) -> str:
    """
    손실 프레이밍 메시지 생성.

    Parameters:
        template_key: 템플릿 키 (예: "deadline_urgent")
        category: 카테고리 (예: "subsidy")
        **kwargs: 템플릿 변수

    Returns:
        포맷된 메시지 문자열
    """
    template_maps = {
        "subsidy": SUBSIDY_LOSS_TEMPLATES,
        "population": POPULATION_LOSS_TEMPLATES,
        "sales": SALES_LOSS_TEMPLATES,
        "event": EVENT_LOSS_TEMPLATES,
        "retention": RETENTION_TEMPLATES,
        "coupon": COUPON_LOSS_TEMPLATES,
    }

    templates = template_maps.get(category, {})
    template = templates.get(template_key, "사장님, 오늘의 기회를 확인하세요.")

    try:
        return template.format(**kwargs)
    except KeyError:
        return template  # 변수 누락 시 원본 반환
```

---

## 12. k-anonymity 사회적 증거

### `backend/app/services/social_proof_service.py`

```python
"""
k-anonymity 기반 사회적 증거 메시지 생성.
동일 동+업종에 10곳 이상일 때만 "N곳이 신청" 메시지 노출.
"""
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import User


class SocialProofService:
    # k-anonymity 최소 임계값
    K_THRESHOLD = 10

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_message(self, dong_name: str, business_type: str) -> Optional[str]:
        """
        동+업종 기준 사회적 증거 메시지.
        10곳 미만이면 None 반환 (역추적 방지).

        SQL:
            SELECT COUNT(*) FROM users
            WHERE dong_name = :dong AND business_type = :type
            AND onboarding_completed = TRUE
        """
        stmt = select(func.count(User.id)).where(
            User.dong_name == dong_name,
            User.business_type == business_type,
            User.onboarding_completed == True,
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        if count < self.K_THRESHOLD:
            # k-anonymity 미충족 → 콜드스타트 메시지 (공공데이터 기반)
            return self._cold_start_message(dong_name, business_type)

        return f"{dong_name} {business_type} {count}곳이 AI 경영코치를 사용하고 있습니다."

    async def get_subsidy_proof(
        self, dong_name: str, business_type: str, subsidy_title: str
    ) -> Optional[str]:
        """
        특정 지원사업에 대한 사회적 증거.
        MVP에서는 실제 신청 데이터가 없으므로 콜드스타트 메시지 사용.
        """
        # MVP: 공공데이터 기반 과거 수혜 실적
        return self._cold_start_message(dong_name, business_type, subsidy_title)

    def _cold_start_message(
        self, dong_name: str, business_type: str, subsidy_title: str = None
    ) -> Optional[str]:
        """
        콜드스타트 시 공공데이터 과거 실적 기반 메시지.
        서울시 공공데이터에서 과거 지원사업 수혜 실적을 미리 수집하여 사용.

        예시:
        - "2025년 혜화동 카페 47%가 디지털전환 지원금 수혜"
        - "작년 종로구 소상공인 320곳이 지원금 수령"

        TODO: 실제 공공데이터 수혜 실적 DB 구축 후 연동
        """
        # MVP 하드코딩 (실제 서비스에서는 DB 조회)
        if subsidy_title and "디지털" in subsidy_title:
            return f"2025년 {dong_name} {business_type} 업종의 47%가 디지털전환 지원금을 수혜했습니다."
        return f"작년 {dong_name} 소상공인 중 다수가 정부 지원금을 수령했습니다."
```

---

## 13. PWA 설정

### `frontend/public/manifest.json`

```json
{
  "name": "AI 경영코치 - 소상공인 경영 지원",
  "short_name": "AI경영코치",
  "description": "사장님이 놓치는 돈, AI가 찾아줍니다. 지원금 자동 매칭 + QR 쿠폰 + 매일 행동 추천.",
  "start_url": "/dashboard",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#FFFFFF",
  "theme_color": "#FEE500",
  "lang": "ko",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "categories": ["business", "finance"],
  "screenshots": []
}
```

### Service Worker 전략

`next-pwa`가 자동 생성하는 SW에 추가로, 오프라인 fallback을 설정한다.

#### `frontend/public/sw.js` (커스텀 오버라이드, 선택)

`next-pwa`를 사용하므로 기본적으로 자동 생성된다. 커스텀이 필요한 경우:

```js
// next-pwa가 생성하는 sw.js를 확장
// 이 파일은 next-pwa의 disable: false일 때 자동 생성됨

// 오프라인 fallback 페이지 캐시
const OFFLINE_URL = "/offline.html";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open("offline-v1").then((cache) => cache.add(OFFLINE_URL))
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
  }
});
```

#### `frontend/public/offline.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI 경영코치 - 오프라인</title>
  <style>
    body { font-family: -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f9fafb; }
    .container { text-align: center; padding: 2rem; }
    h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
    p { color: #6b7280; }
    button { margin-top: 1rem; padding: 0.75rem 1.5rem; background: #FEE500; border: none; border-radius: 0.75rem; font-weight: 600; cursor: pointer; }
  </style>
</head>
<body>
  <div class="container">
    <h1>인터넷 연결을 확인해주세요</h1>
    <p>AI 경영코치는 온라인 상태에서 사용할 수 있습니다.</p>
    <button onclick="window.location.reload()">다시 시도</button>
  </div>
</body>
</html>
```

### FCM 클라이언트 설정

#### `frontend/src/lib/fcm.ts`

```typescript
import { initializeApp, getApps } from "firebase/app";
import { getMessaging, getToken, onMessage, Messaging } from "firebase/messaging";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

let messaging: Messaging | null = null;

export function initFCM() {
  if (typeof window === "undefined") return null;
  if (!getApps().length) {
    const app = initializeApp(firebaseConfig);
    messaging = getMessaging(app);
  }
  return messaging;
}

export async function requestFCMToken(): Promise<string | null> {
  try {
    const m = initFCM();
    if (!m) return null;

    const permission = await Notification.requestPermission();
    if (permission !== "granted") return null;

    const token = await getToken(m, {
      vapidKey: process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY,
    });
    return token;
  } catch {
    return null;
  }
}

export function onFCMMessage(callback: (payload: any) => void) {
  const m = initFCM();
  if (!m) return;
  onMessage(m, callback);
}
```

---

## 14. STT 음성 질의

Web Speech API는 브라우저 내장 기능이므로 별도 라이브러리 불필요.

전체 플로우:
```
[사용자] → 마이크 버튼 탭
   ↓
[브라우저] → Web Speech API (SpeechRecognition) 시작
   → lang: "ko-KR"
   → continuous: false (단일 발화)
   → interimResults: true (중간 결과 표시)
   ↓
[사용자] → "사장님, 지원금 찾아줘" 발화
   ↓
[브라우저] → STT 변환 → transcript: "사장님 지원금 찾아줘"
   ↓
[프론트엔드] → POST /voice/query { text: "사장님 지원금 찾아줘" }
   ↓
[백엔드] → 의도 분류 (키워드 기반)
   → "지원금" 키워드 → intent: "subsidy"
   → ChromaDB RAG 검색
   → GPT-4o 응답 생성
   ↓
[프론트엔드] → 응답 표시 + 후속 질문 제안 버튼
```

지원 브라우저: Chrome, Edge, Safari (iOS 14.5+). Firefox는 미지원.

구현: 위의 `frontend/src/hooks/useSTT.ts`와 `frontend/src/components/common/STTButton.tsx` 참조.

---

## 15. 배포 설정

### 15.1 Vercel (Frontend)

#### `frontend/vercel.json`

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://ai-coach-backend.up.railway.app",
    "NEXT_PUBLIC_APP_URL": "https://ai-coach.vercel.app"
  }
}
```

Vercel 설정 단계:
1. GitHub 레포 연결
2. Framework Preset: Next.js
3. Root Directory: `frontend`
4. Environment Variables 등록 (위 `.env.local` 내용)
5. 배포

### 15.2 Railway (Backend)

#### `backend/railway.toml`

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 10
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

#### `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY . .

# ChromaDB 데이터 디렉토리
RUN mkdir -p /app/chroma_data

# 포트 (Railway가 $PORT 환경변수 제공)
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Railway 설정 단계:
1. New Project > Deploy from GitHub repo
2. Root Directory: `backend`
3. Add PostgreSQL plugin (DATABASE_URL 자동 주입)
4. Add Redis plugin (선택, REDIS_URL 자동 주입)
5. Environment Variables 등록
6. Custom Domain 설정 (선택)

---

## 16. Fault Tolerance 패턴

### `backend/app/utils/retry.py`

```python
"""
재시도 데코레이터. 모든 외부 API 호출에 적용.
- 최대 재시도: 2회
- 지수 백오프: 1초, 2초
- 재시도 대상: httpx.HTTPError, TimeoutError, ConnectionError
"""
import asyncio
import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def retry_async(max_retries: int = 2, delay: float = 1.0, backoff: float = 2.0):
    """비동기 함수용 재시도 데코레이터."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"[Retry {attempt + 1}/{max_retries}] {func.__name__} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[Final Failure] {func.__name__} failed after {max_retries} retries: {e}"
                        )

            # 모든 재시도 실패 → None 반환 (호출자가 graceful degradation 처리)
            return None

        return wrapper
    return decorator
```

### `backend/app/utils/cache.py`

```python
"""
캐시 유틸. Redis 있으면 Redis, 없으면 인메모리 dict.
모든 외부 API 응답에 캐시 적용.
"""
import json
import time
import functools
import hashlib
from typing import Optional

from app.config import settings

# 인메모리 캐시 (Redis 없을 때 fallback)
_memory_cache: dict = {}


class CacheBackend:
    _redis = None

    @classmethod
    def get_redis(cls):
        if cls._redis is not None:
            return cls._redis
        if settings.redis_url:
            try:
                import redis
                cls._redis = redis.from_url(settings.redis_url, decode_responses=True)
                cls._redis.ping()
                return cls._redis
            except Exception:
                cls._redis = None
        return None


def cache(ttl: int = 3600, key_prefix: str = ""):
    """
    캐시 데코레이터.

    Parameters:
        ttl: 캐시 유효시간 (초). 기본 1시간.
        key_prefix: 캐시 키 프리픽스

    사용 예:
        @cache(ttl=86400, key_prefix="seoul_sales")
        async def get_sales(gu_name, dong_name):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            key_parts = [key_prefix, func.__name__] + [str(a) for a in args[1:]] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            raw_key = ":".join(key_parts)
            cache_key = hashlib.md5(raw_key.encode()).hexdigest()

            # 캐시 조회
            cached = _get_cache(cache_key)
            if cached is not None:
                return cached

            # 실행
            result = await func(*args, **kwargs)

            # 캐시 저장
            if result is not None:
                _set_cache(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def _get_cache(key: str) -> Optional[any]:
    """캐시에서 값 조회."""
    r = CacheBackend.get_redis()
    if r:
        try:
            val = r.get(key)
            return json.loads(val) if val else None
        except Exception:
            pass

    # 인메모리 fallback
    entry = _memory_cache.get(key)
    if entry and entry["expires_at"] > time.time():
        return entry["value"]
    elif entry:
        del _memory_cache[key]
    return None


def _set_cache(key: str, value: any, ttl: int):
    """캐시에 값 저장."""
    r = CacheBackend.get_redis()
    if r:
        try:
            r.setex(key, ttl, json.dumps(value, default=str))
            return
        except Exception:
            pass

    # 인메모리 fallback
    _memory_cache[key] = {
        "value": value,
        "expires_at": time.time() + ttl,
    }
```

---

## 17. 배치 작업

### `backend/app/tasks/daily_action_batch.py`

```python
"""
매일 오전 7시 실행: 모든 온보딩 완료 사용자에게 일일 액션 생성.
"""
import logging
from datetime import date
from sqlalchemy import select

from app.database import async_session_factory
from app.models import User, DailyAction
from app.services.action_generator import ActionGenerator
from app.services.seoul_api_service import SeoulAPIService
from app.services.rag_service import RAGService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


async def generate_daily_actions_for_all():
    """전체 사용자 일일 액션 배치 생성."""
    logger.info("Starting daily action batch...")

    async with async_session_factory() as db:
        # 온보딩 완료 사용자 조회
        stmt = select(User).where(User.onboarding_completed == True)
        result = await db.execute(stmt)
        users = result.scalars().all()

        generator = ActionGenerator()
        seoul = SeoulAPIService()
        rag = RAGService()
        notifier = NotificationService()

        success_count = 0
        for user in users:
            try:
                # 이미 오늘 액션이 있는지 확인
                existing = await db.execute(
                    select(DailyAction).where(
                        DailyAction.user_id == user.id,
                        DailyAction.date == date.today(),
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                # 데이터 수집
                import asyncio
                sales, pop, events = await asyncio.gather(
                    seoul.get_commercial_sales(user.gu_name, user.dong_name, user.business_type),
                    seoul.get_living_population(user.dong_name),
                    seoul.get_cultural_events(user.gu_name),
                    return_exceptions=True,
                )

                query = f"{user.gu_name} {user.dong_name} {user.business_type} 소상공인 지원금"
                subsidies = await rag.search_subsidies(query, top_k=3)

                # 액션 생성
                action_data = await generator.generate_daily_action(
                    user=user,
                    sales_data=sales if not isinstance(sales, Exception) else None,
                    population_data=pop if not isinstance(pop, Exception) else None,
                    events_data=events if not isinstance(events, Exception) else None,
                    subsidy_data=subsidies,
                )

                action = DailyAction(
                    user_id=user.id,
                    date=date.today(),
                    action_type=action_data.get("action_type", "general"),
                    title=action_data.get("title", "오늘의 행동을 확인하세요"),
                    description=action_data.get("description", ""),
                    risk_score=action_data.get("risk_score", 0.3),
                    data_source=action_data.get("data_source"),
                    cta_type=action_data.get("cta_type"),
                    cta_payload=action_data.get("cta_payload"),
                )
                db.add(action)

                # 알림 발송
                await notifier.send_notification(
                    db=db,
                    user=user,
                    title=action_data.get("title", "오늘의 행동"),
                    message=action_data.get("description", ""),
                    message_type="daily_action",
                )

                success_count += 1

            except Exception as e:
                logger.error(f"Failed to generate action for user {user.id}: {e}")

        await db.commit()
        logger.info(f"Daily action batch completed: {success_count}/{len(users)} users")
```

### `backend/app/tasks/seoul_data_sync.py`

```python
"""
매주 월요일 새벽 3시: 서울시 API 데이터를 캐시에 사전 적재.
사용자 요청 시 캐시 히트율 향상을 위함.
"""
import logging
from sqlalchemy import select, distinct

from app.database import async_session_factory
from app.models import User
from app.services.seoul_api_service import SeoulAPIService

logger = logging.getLogger(__name__)


async def sync_seoul_data():
    """서울시 API 데이터 사전 캐싱."""
    logger.info("Starting Seoul data sync...")

    async with async_session_factory() as db:
        # 등록된 사용자들의 동/구/업종 조합 수집
        stmt = select(
            distinct(User.dong_name),
            User.gu_name,
            User.business_type,
        ).where(User.onboarding_completed == True)
        result = await db.execute(stmt)
        rows = result.all()

        seoul = SeoulAPIService()
        synced = 0

        for dong_name, gu_name, business_type in rows:
            if not dong_name or not gu_name:
                continue
            try:
                # 이 호출들이 자동으로 캐시에 저장됨 (@cache 데코레이터)
                await seoul.get_commercial_sales(gu_name, dong_name, business_type)
                await seoul.get_living_population(dong_name)
                await seoul.get_cultural_events(gu_name)
                synced += 1
            except Exception as e:
                logger.warning(f"Sync failed for {dong_name}: {e}")

        logger.info(f"Seoul data sync completed: {synced} areas synced")
```

### `backend/app/tasks/subsidy_indexer.py`

```python
"""
매주 월요일 새벽 4시: subsidies 테이블의 데이터를 ChromaDB에 인덱싱.
새로 추가되거나 업데이트된 보조금 문서를 벡터화.
"""
import logging
from sqlalchemy import select

from app.database import async_session_factory
from app.models import Subsidy
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


async def reindex_subsidies():
    """보조금 데이터 ChromaDB 재인덱싱."""
    logger.info("Starting subsidy re-indexing...")

    async with async_session_factory() as db:
        stmt = select(Subsidy).where(Subsidy.is_active == True)
        result = await db.execute(stmt)
        subsidies = result.scalars().all()

        rag = RAGService()
        indexed = 0

        for s in subsidies:
            try:
                # 인덱싱할 텍스트: 제목 + 기관 + 설명 + 자격요건
                text = f"{s.title}\n{s.organization}\n{s.description}"
                if s.eligibility_summary:
                    text += f"\n자격요건: {s.eligibility_summary}"

                metadata = {
                    "title": s.title,
                    "organization": s.organization,
                    "deadline": s.deadline.isoformat() if s.deadline else None,
                    "max_amount": s.max_amount,
                    "target_business_types": ",".join(s.target_business_types) if s.target_business_types else "",
                    "target_regions": ",".join(s.target_regions) if s.target_regions else "",
                    "eligibility_summary": s.eligibility_summary or "",
                    "application_url": s.application_url or "",
                }

                await rag.index_subsidy(str(s.id), text, metadata)
                s.embedding_id = str(s.id)
                indexed += 1

            except Exception as e:
                logger.error(f"Failed to index subsidy {s.id}: {e}")

        await db.commit()
        logger.info(f"Subsidy indexing completed: {indexed}/{len(subsidies)}")
```

---

## 18. 파일별 구현 가이드

### 18.1 국세청 사업자등록상태 서비스

#### `backend/app/services/nts_service.py`

```python
"""
국세청 사업자등록상태 조회 API.
엔드포인트: https://api.odcloud.kr/api/nts-businessman/v1/status
"""
import httpx
from typing import Optional

from app.config import settings
from app.schemas.onboarding import VerifyBusinessResponse
from app.utils.retry import retry_async


class NTSService:
    BASE_URL = "https://api.odcloud.kr/api/nts-businessman/v1/status"

    @retry_async(max_retries=2, delay=1.0)
    async def verify_business_number(self, business_number: str) -> Optional[VerifyBusinessResponse]:
        """
        사업자등록번호 유효성 검증.

        API 요청:
            POST https://api.odcloud.kr/api/nts-businessman/v1/status
            Headers:
                Authorization: Infuser {API_KEY}
                Content-Type: application/json
            Body:
                { "b_no": ["1234567890"] }

        API 응답:
            {
                "data": [
                    {
                        "b_no": "1234567890",
                        "b_stt": "계속사업자",     # 사업자 상태
                        "b_stt_cd": "01",           # 01:계속, 02:휴업, 03:폐업
                        "tax_type": "일반과세자"
                    }
                ]
            }
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.BASE_URL,
                json={"b_no": [business_number]},
                headers={
                    "Authorization": f"Infuser {settings.nts_api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            items = data.get("data", [])

            if not items:
                return VerifyBusinessResponse(
                    is_valid=False,
                    business_status="확인불가",
                )

            item = items[0]
            status_code = item.get("b_stt_cd", "")
            status_text = item.get("b_stt", "확인불가")

            return VerifyBusinessResponse(
                is_valid=(status_code == "01"),  # 01: 계속사업자
                business_status=status_text,
                business_name=item.get("b_nm"),
                tax_type=item.get("tax_type"),
            )
```

### 18.2 Alembic 설정

#### `backend/alembic.ini`

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/ai_coach

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### `backend/alembic/env.py`

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config import settings
from app.database import Base
from app.models import *  # 모든 모델 임포트 (metadata 등록)

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 18.3 Dashboard 페이지 (Frontend)

#### `frontend/src/app/dashboard/page.tsx`

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { DashboardData } from "@/types";

import RiskScoreCard from "@/components/dashboard/RiskScoreCard";
import TodayAction from "@/components/dashboard/TodayAction";
import LossFrameMessage from "@/components/common/LossFrameMessage";
import STTButton from "@/components/common/STTButton";

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading, checkAuth } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
    if (isAuthenticated && user && !user.onboarding_completed) {
      router.push("/onboarding");
    }
  }, [isLoading, isAuthenticated, user]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboard();
    }
  }, [isAuthenticated]);

  const fetchDashboard = async () => {
    try {
      const d = await api.getDashboard();
      setData(d);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <main className="max-w-md mx-auto px-4 py-6 space-y-6 pb-24">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">안녕하세요,</p>
          <h1 className="text-xl font-bold">{data.user.business_name || data.user.nickname} 사장님</h1>
        </div>
        <STTButton />
      </div>

      {/* 손실 프레이밍 메시지 */}
      <LossFrameMessage
        message={data.loss_message}
        amount={data.total_potential_amount}
        variant={data.total_potential_amount > 0 ? "danger" : "info"}
      />

      {/* 위험도 */}
      <RiskScoreCard score={data.risk_score} />

      {/* 오늘의 액션 */}
      {data.today_action && (
        <TodayAction action={data.today_action} onComplete={fetchDashboard} />
      )}

      {/* 지원사업 매칭 */}
      {data.subsidy_matches.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-lg">놓치고 있는 지원금</h2>
            <button
              onClick={() => router.push("/subsidies")}
              className="text-sm text-blue-500"
            >
              전체 보기
            </button>
          </div>
          <div className="space-y-3">
            {data.subsidy_matches.slice(0, 3).map((s) => (
              <div
                key={s.id}
                className="bg-white rounded-xl p-4 shadow-sm border cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => router.push(`/subsidies?id=${s.id}`)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-semibold text-sm">{s.title}</p>
                    <p className="text-xs text-gray-500 mt-1">{s.organization}</p>
                  </div>
                  {s.max_amount && (
                    <p className="text-lg font-bold text-red-600">{s.max_amount}만원</p>
                  )}
                </div>
                {s.days_until_deadline !== null && s.days_until_deadline >= 0 && (
                  <p className="text-xs text-red-500 mt-2">
                    마감 D-{s.days_until_deadline}
                  </p>
                )}
                {s.social_proof_message && (
                  <p className="text-xs text-gray-400 mt-1">{s.social_proof_message}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 유동인구 트렌드 */}
      {data.population_trend && (
        <section className="bg-white rounded-xl p-4 shadow-sm border">
          <h3 className="font-semibold text-sm mb-2">유동인구</h3>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold">
              {data.population_trend.today.toLocaleString()}명
            </span>
            <span className={`text-sm font-medium ${
              data.population_trend.change_percent >= 0 ? "text-green-600" : "text-red-600"
            }`}>
              {data.population_trend.change_percent >= 0 ? "+" : ""}
              {data.population_trend.change_percent}%
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">전일 대비 (어제 기준)</p>
        </section>
      )}

      {/* 사회적 증거 */}
      {data.social_proof && (
        <p className="text-sm text-center text-gray-500 bg-gray-50 rounded-lg py-3 px-4">
          {data.social_proof}
        </p>
      )}

      {/* 문화행사 */}
      {data.upcoming_events.length > 0 && (
        <section>
          <h2 className="font-bold text-lg mb-3">근처 문화행사</h2>
          <div className="space-y-2">
            {data.upcoming_events.map((e: any, i: number) => (
              <div key={i} className="bg-white rounded-xl p-3 shadow-sm border text-sm">
                <p className="font-medium">{e.title}</p>
                <p className="text-xs text-gray-500">{e.place} | {e.start_date}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 하단 네비게이션 */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t flex justify-around py-3 max-w-md mx-auto">
        <button onClick={() => router.push("/dashboard")} className="text-yellow-500 text-xs font-medium flex flex-col items-center gap-1">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          홈
        </button>
        <button onClick={() => router.push("/subsidies")} className="text-gray-400 text-xs flex flex-col items-center gap-1">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>
          지원금
        </button>
        <button onClick={() => router.push("/coupon")} className="text-gray-400 text-xs flex flex-col items-center gap-1">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/></svg>
          쿠폰
        </button>
        <button onClick={() => router.push("/action")} className="text-gray-400 text-xs flex flex-col items-center gap-1">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
          기록
        </button>
      </nav>
    </main>
  );
}
```

### 18.4 `.env.example` 파일

#### `backend/.env.example`

```bash
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=change-this-to-a-random-32-char-string
CORS_ORIGINS=http://localhost:3000

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_coach

KAKAO_REST_API_KEY=your-kakao-rest-api-key
KAKAO_CLIENT_SECRET=your-kakao-client-secret
KAKAO_REDIRECT_URI=http://localhost:3000/auth/kakao/callback

NTS_API_KEY=your-nts-api-key

SEOUL_API_KEY=your-seoul-openapi-key

OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1024
OPENAI_TEMPERATURE=0.7

CHROMA_PERSIST_DIR=./chroma_data
CHROMA_COLLECTION_NAME=subsidies

FIREBASE_SERVICE_ACCOUNT_JSON=./firebase-sa.json

REDIS_URL=

LOG_LEVEL=INFO
```

### 18.5 globals.css

#### `frontend/src/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    -webkit-tap-highlight-color: transparent;
  }

  body {
    @apply bg-gray-50 text-gray-900 antialiased;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;
  }

  /* PWA 안전영역 */
  .safe-area-top {
    padding-top: env(safe-area-inset-top, 0px);
  }
  .safe-area-bottom {
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
```

### 18.6 Tailwind 설정

#### `frontend/tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        kakao: {
          yellow: "#FEE500",
          brown: "#3C1E1E",
          black: "#191919",
        },
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Noto Sans KR", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## 부록: 빠른 시작 가이드

### 로컬 개발 환경 세팅

```bash
# 1. 레포 클론
git clone https://github.com/your-org/ai-coach.git
cd ai-coach

# 2. Backend 세팅
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 실제 키값 입력

# PostgreSQL 실행 (Docker)
docker run -d --name ai-coach-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ai_coach \
  -p 5432:5432 \
  postgres:15

# DB 마이그레이션
alembic upgrade head

# 백엔드 실행
uvicorn app.main:app --reload --port 8000

# 3. Frontend 세팅 (새 터미널)
cd frontend
npm install
cp .env.example .env.local
# .env.local에 실제 키값 입력

# 프론트엔드 실행
npm run dev

# 4. 브라우저에서 http://localhost:3000 접속
```

### 보조금 초기 데이터 투입

보조금 데이터는 수동으로 DB에 INSERT하거나, 관리자 스크립트를 실행한다.

```bash
# backend 디렉토리에서
python -c "
import asyncio
from app.database import async_session_factory
from app.models import Subsidy

async def seed():
    async with async_session_factory() as db:
        subsidies = [
            Subsidy(
                title='소상공인 디지털전환 지원',
                organization='소상공인시장진흥공단',
                deadline='2026-06-30',
                max_amount=400,
                target_business_types=['카페', '음식점', '소매업'],
                target_regions=['서울'],
                eligibility_summary='매출액 10억원 이하 소상공인',
                description='소상공인의 디지털 역량 강화를 위한 지원사업. 키오스크, POS, 온라인 마케팅 등 디지털 전환 비용을 최대 400만원까지 지원합니다.',
                application_url='https://www.sbiz.or.kr',
                source='소상공인시장진흥공단',
            ),
            Subsidy(
                title='소공인특화지원사업',
                organization='소상공인시장진흥공단',
                deadline='2026-05-31',
                max_amount=200,
                target_business_types=['제조업', '수공예'],
                target_regions=['서울'],
                eligibility_summary='상시근로자 10인 미만 제조업',
                description='소공인의 기술개발, 장비구입, 판로개척 등을 지원하는 사업. 최대 200만원까지 지원.',
                application_url='https://www.sbiz.or.kr',
                source='소상공인시장진흥공단',
            ),
            Subsidy(
                title='고용보험료 지원',
                organization='근로복지공단',
                deadline=None,
                max_amount=110,
                target_business_types=['전업종'],
                target_regions=['전국'],
                eligibility_summary='10인 미만 사업장, 월평균보수 260만원 미만 근로자',
                description='소규모 사업장의 고용보험료 부담을 줄여주는 사업. 사업주와 근로자의 고용보험료 최대 80%를 지원합니다.',
                application_url='https://www.comwel.or.kr',
                source='근로복지공단',
            ),
        ]
        for s in subsidies:
            db.add(s)
        await db.commit()
        print(f'{len(subsidies)}건 투입 완료')

asyncio.run(seed())
"

# ChromaDB 인덱싱 수동 실행
python -c "
import asyncio
from app.tasks.subsidy_indexer import reindex_subsidies
asyncio.run(reindex_subsidies())
"
```

---

## 19. 보안 설계

### 19.1 시크릿 관리 원칙

```
┌─────────────────────────────────────────────────┐
│  Git 저장소 (공개 가능)                            │
│  ├── IMPLEMENTATION_SPEC.md  (구현 명세)          │
│  ├── backend/.env.example    (변수명만, 값 없음)   │
│  └── .gitignore              (시크릿 파일 차단)    │
├─────────────────────────────────────────────────┤
│  로컬 전용 (Git 제외)                              │
│  ├── API_SECRETS.md          (키 발급/관리 가이드)  │
│  ├── backend/.env            (실제 키 값)          │
│  ├── frontend/.env.local     (실제 키 값)          │
│  └── backend/firebase-sa.json (FCM 서비스 계정)    │
├─────────────────────────────────────────────────┤
│  배포 환경 (환경변수만)                              │
│  ├── Railway Variables       (백엔드 시크릿)        │
│  └── Vercel Env Variables    (프론트엔드 설정)      │
└─────────────────────────────────────────────────┘
```

### 19.2 .gitignore (프로젝트 루트)

```gitignore
# ===== 시크릿 (절대 커밋 금지) =====
API_SECRETS.md
*.env
*.env.*
.env.local
.env.production
.env.development
firebase-sa.json
firebase-service-account*.json
*-sa.json

# ===== 데이터/빌드 =====
node_modules/
__pycache__/
*.pyc
.next/
dist/
chroma_data/
*.db

# ===== IDE =====
.vscode/settings.json
.idea/
*.swp
.DS_Store
```

### 19.3 Backend 보안 패턴

#### JWT 토큰 보안

```python
# backend/app/routers/auth.py 내 JWT 설정
from datetime import datetime, timedelta
import jwt

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24  # 액세스 토큰 만료: 24시간

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """
    토큰 검증. 실패 시 HTTPException(401) 발생.
    반드시 알고리즘을 명시적으로 지정 (alg confusion attack 방지).
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[JWT_ALGORITHM],  # 배열로 명시
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "토큰이 만료되었습니다. 다시 로그인하세요.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "유효하지 않은 토큰입니다.")
```

#### API Rate Limiting

```python
# backend/app/main.py 에 추가
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 전역 기본: 분당 60회
# 인증 엔드포인트: 분당 10회 (브루트포스 방지)
# AI 생성 엔드포인트: 분당 5회 (비용 보호)

@app.post("/auth/kakao/callback")
@limiter.limit("10/minute")
async def kakao_callback(request: Request, ...):
    ...

@app.post("/voice/query")
@limiter.limit("5/minute")
async def voice_query(request: Request, ...):
    ...

@app.post("/coupons/create")
@limiter.limit("10/minute")
async def create_coupon(request: Request, ...):
    ...
```

#### 입력 검증 패턴

```python
# backend/app/schemas/onboarding.py
from pydantic import BaseModel, validator
import re

class VerifyBusinessRequest(BaseModel):
    business_number: str

    @validator("business_number")
    def validate_business_number(cls, v):
        # 사업자등록번호: 숫자 10자리만 허용
        cleaned = re.sub(r"[^0-9]", "", v)
        if len(cleaned) != 10:
            raise ValueError("사업자등록번호는 10자리 숫자입니다.")
        return cleaned

class BusinessSearchRequest(BaseModel):
    query: str

    @validator("query")
    def validate_query(cls, v):
        # XSS/Injection 방지: 특수문자 제거, 최대 50자
        cleaned = re.sub(r"[<>\"';\\]", "", v.strip())
        if len(cleaned) > 50:
            raise ValueError("검색어는 50자 이내로 입력하세요.")
        if len(cleaned) < 2:
            raise ValueError("검색어는 2자 이상 입력하세요.")
        return cleaned
```

#### GPT-4o 프롬프트 인젝션 방지

```python
# backend/app/services/action_generator.py 내 안전 장치

def sanitize_user_input(text: str) -> str:
    """사용자 입력에서 프롬프트 인젝션 시도를 필터링."""
    # 시스템 프롬프트 조작 시도 차단
    injection_patterns = [
        r"ignore previous",
        r"ignore above",
        r"system:",
        r"assistant:",
        r"you are now",
        r"forget everything",
        r"new instructions",
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "[필터링된 입력]"
    # HTML/스크립트 태그 제거
    text = re.sub(r"<[^>]+>", "", text)
    # 최대 500자 제한
    return text[:500]

# GPT-4o 호출 시 사용자 입력은 반드시 sanitize 후 전달
user_message = sanitize_user_input(raw_user_input)
```

#### 카카오 토큰 저장 보안

```python
# backend/app/models/user.py
from cryptography.fernet import Fernet

# 카카오 액세스 토큰은 암호화 저장 (카카오톡 나에게 보내기에 필요)
class User(Base):
    ...
    kakao_access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kakao_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def set_kakao_token(self, token: str):
        """Fernet 대칭키로 카카오 토큰 암호화 저장."""
        f = Fernet(settings.secret_key[:32].encode().ljust(32, b'='))
        self.kakao_access_token_encrypted = f.encrypt(token.encode()).decode()

    def get_kakao_token(self) -> Optional[str]:
        """카카오 토큰 복호화."""
        if not self.kakao_access_token_encrypted:
            return None
        f = Fernet(settings.secret_key[:32].encode().ljust(32, b'='))
        return f.decrypt(self.kakao_access_token_encrypted.encode()).decode()
```

### 19.4 Frontend 보안 패턴

#### XSS 방지

```typescript
// src/lib/sanitize.ts
// 서버에서 온 데이터를 렌더링할 때 반드시 sanitize
export function sanitizeHTML(dirty: string): string {
  // React는 기본적으로 JSX에서 이스케이프하지만,
  // dangerouslySetInnerHTML 사용 시 반드시 sanitize
  return dirty
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// ❌ 절대 하지 말 것
// <div dangerouslySetInnerHTML={{ __html: userInput }} />
// ✅ React JSX 기본 렌더링 사용 (자동 이스케이프)
// <p>{userInput}</p>
```

#### JWT 저장 전략

```typescript
// src/lib/api.ts
// localStorage 대신 httpOnly 쿠키가 이상적이지만,
// PWA 특성상 localStorage 사용 시 추가 보호 적용

const TOKEN_KEY = 'ai_coach_token';

export function setToken(token: string) {
  // 토큰 만료 시간 체크 후 저장
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp * 1000 < Date.now()) {
      console.error('만료된 토큰 저장 시도 차단');
      return;
    }
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    console.error('잘못된 토큰 형식');
  }
}

export function getToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;

  // 매번 만료 확인
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp * 1000 < Date.now()) {
      localStorage.removeItem(TOKEN_KEY);
      return null;
    }
    return token;
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
}
```

#### CORS 설정

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),  # 명시적 오리진만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 필요한 메서드만
    allow_headers=["Authorization", "Content-Type"],  # 필요한 헤더만
    # allow_origins=["*"] 절대 금지 (프로덕션)
)
```

### 19.5 보안 헤더 (FastAPI 미들웨어)

```python
# backend/app/main.py
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "microphone=(self)"  # STT용 마이크만 허용
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### 19.6 의존성 보안

```bash
# requirements.txt 에 버전 고정 (supply chain attack 방지)
fastapi==0.115.0
pydantic==2.9.0
sqlalchemy==2.0.35
httpx==0.27.0
PyJWT==2.9.0
cryptography==43.0.0
python-qrcode==7.4.2
langchain==0.3.0
chromadb==0.5.0
openai==1.50.0
slowapi==0.1.9

# 정기 취약점 스캔
# pip install pip-audit
# pip-audit
```

---

## 부록: 문서 관계도

```
소상공인_AI경영코치_설계문서_FINAL.md   ← 기획서 (Why + What)
         │
         ▼
IMPLEMENTATION_SPEC.md                ← 구현 명세서 (How) [이 문서]
         │
         ├── API_SECRETS.md           ← 시크릿 관리 (.gitignore)
         │     └── 발급 방법, 실제 키 값, 로테이션 스케줄
         │
         └── 코드 구현                ← 이 명세서를 보고 구현
               ├── frontend/          (Next.js 14 PWA)
               └── backend/           (FastAPI + PostgreSQL)
```

> **이 문서로 MVP 전체 구현이 가능합니다.**
> 모든 파일 경로, 함수 시그니처, API 스펙, 프롬프트, 환경변수가 명시되어 있습니다.
> API 키 발급/관리 → [`API_SECRETS.md`](./API_SECRETS.md)
> 기획 배경/수치 근거 → [`소상공인_AI경영코치_설계문서_FINAL.md`](./소상공인_AI경영코치_설계문서_FINAL.md)

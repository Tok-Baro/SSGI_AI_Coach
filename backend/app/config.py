from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 앱
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "dev-secret-change-me"
    cors_origins: str = "http://localhost:3000"

    # DB
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_coach"

    # Kakao
    kakao_rest_api_key: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = "http://localhost:3000/auth/kakao/callback"

    # 국세청
    nts_api_key: str = ""

    # 서울시
    seoul_api_key: str = ""

    # OpenAI
    openai_api_key: str = ""
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

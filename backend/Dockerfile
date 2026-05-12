FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 (한글 폰트는 PDF 리포트 렌더링용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드
COPY . .

# ChromaDB 데이터 디렉토리
RUN mkdir -p /app/chroma_data

EXPOSE 8000

# 컨테이너 시작 시: DB 마이그레이션 → 데모 시드(멱등, 실패해도 무시) → uvicorn 기동.
# (alembic 실패 시 컨테이너도 기동 실패 → 잘못된 스키마로 뜨는 일 방지 / seed_demo 는 || true 로 비치명적)
CMD ["sh", "-c", "alembic upgrade head && (python -m scripts.seed_demo || true) && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

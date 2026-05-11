"""RAG 파이프라인 서비스: ChromaDB + OpenAI Embeddings."""
import asyncio
import logging
from datetime import date
from typing import Optional
from uuid import UUID

import chromadb
from openai import AsyncOpenAI
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.utils.industry import industry_subsidy_tags
from app.utils.subsidy_tags import infer_subsidy_category_tags

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class RAGService:
    _instance = None
    _client = None
    _collection = None
    _openai = None
    _init_lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _init_clients(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=settings.openai_api_key)

    def _chunk_text(self, text: str) -> list[str]:
        """텍스트를 청크로 분리."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunks.append(text[start:end])
            start = end - CHUNK_OVERLAP
        return chunks

    async def _get_embedding(self, text: str) -> list[float]:
        """OpenAI 임베딩 생성."""
        async with self._init_lock:
            self._init_clients()
        response = await self._openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    async def index_subsidy(
        self, subsidy_id: str, text: str, metadata: dict
    ) -> None:
        """보조금 문서를 ChromaDB에 인덱싱."""
        self._init_clients()
        chunks = self._chunk_text(text)

        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{subsidy_id}_{i}"
            embedding = await self._get_embedding(chunk)

            ids.append(chunk_id)
            embeddings.append(embedding)
            metadatas.append({**metadata, "subsidy_id": subsidy_id, "chunk_index": i})
            documents.append(chunk)

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )
        logger.info(f"Indexed subsidy {subsidy_id}: {len(chunks)} chunks")

    async def search_subsidies_filtered(
        self,
        db: AsyncSession,
        gu_name: str,
        business_type: str,
        top_k: int = 5,
        user_id: Optional[UUID] = None,
        industry_slug: Optional[str] = None,
    ) -> list[dict]:
        """DB 기반 정확한 지역+업종 필터링 후 지원사업 반환.

        매칭 로직:
        - target_regions에 사용자 지역(gu_name), "전국", "서울시 전체" 포함
        - target_business_types에 사용자 업종 또는 "전 업종" 포함
        - 마감일이 지나지 않은 활성 지원사업만
        - 공고 category_tags 가 사용자 업종팩의 subsidy_tags 와 겹치면 relevance_score 부스트
        - user_id 제공 시 ICP Learner로 학습된 선호 프로필 기반 재순위 적용
        """
        from app.models.subsidy import Subsidy

        today = date.today()

        # 태그 부스트·ICP 재순위가 의미 있도록 후보 풀을 넉넉히 확장 후 정렬·자르기
        candidate_limit = max(top_k * 4, 12)

        stmt = select(Subsidy).where(
            Subsidy.is_active == True,
            or_(Subsidy.deadline.is_(None), Subsidy.deadline >= today),
            or_(
                Subsidy.target_regions.any("전국"),
                Subsidy.target_regions.any("서울시 전체"),
                Subsidy.target_regions.any(gu_name) if gu_name else False,
            ),
            or_(
                Subsidy.target_business_types.any("전 업종"),
                Subsidy.target_business_types.any(business_type) if business_type else False,
            ),
        ).order_by(
            Subsidy.deadline.asc().nulls_last()
        ).limit(candidate_limit)

        result = await db.execute(stmt)
        subsidies = result.scalars().all()

        user_tags = set(industry_subsidy_tags(business_type, industry_slug))

        matches = []
        for s in subsidies:
            days_left = (s.deadline - today).days if s.deadline else None
            cats = s.category_tags or infer_subsidy_category_tags(f"{s.title} {s.description}")
            overlap = len(set(cats) & user_tags) if user_tags else 0
            boost = min(0.3, 0.12 * overlap)  # 태그 1개당 +0.12, 최대 +0.3
            matches.append({
                "id": str(s.id),
                "title": s.title,
                "organization": s.organization,
                "deadline": s.deadline.isoformat() if s.deadline else None,
                "max_amount": s.max_amount,
                "eligibility_summary": s.eligibility_summary,
                "description": s.description,
                "application_url": s.application_url,
                "category_tags": list(cats),
                "tag_match": overlap > 0,
                "relevance_score": round(1.0 + boost, 3),
                "days_until_deadline": days_left,
            })

        # 태그 부스트 → 마감 임박 순으로 정렬 (ICP 재순위 전 기본 순서)
        matches.sort(key=lambda m: (-m["relevance_score"], m["days_until_deadline"] if m["days_until_deadline"] is not None else 99999))

        # ICP 재순위 (user_id 제공 시)
        if user_id and matches:
            try:
                from app.services.icp_learner import learn_user_profile, rerank_with_icp
                profile = await learn_user_profile(db, user_id)
                if profile.has_signals:
                    matches = rerank_with_icp(matches, profile)
                    logger.info(
                        f"ICP rerank applied for user={user_id}: "
                        f"{profile.signal_count} signals, top boost={matches[0].get('icp_boost', 0)}"
                    )
            except Exception as e:
                logger.warning(f"ICP rerank failed (using base order): {e}")

        return matches[:top_k]

    async def search_subsidies(
        self, query: str, top_k: int = 5, user_region: str = ""
    ) -> list[dict]:
        """벡터 유사도 검색으로 지원사업 매칭 (레거시, ChromaDB only)."""
        self._init_clients()

        query_embedding = await self._get_embedding(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 4,
        )

        if not results or not results["ids"][0]:
            return []

        seen_ids = set()
        matches = []

        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i] if results.get("distances") else 0
            relevance = 1 - distance

            if relevance < 0.3:
                continue

            sid = meta.get("subsidy_id", "")
            if sid in seen_ids:
                continue
            seen_ids.add(sid)

            days_left = None
            deadline_str = meta.get("deadline")
            if deadline_str:
                try:
                    deadline = date.fromisoformat(deadline_str)
                    days_left = (deadline - date.today()).days
                except (ValueError, TypeError):
                    pass

            matches.append({
                "id": sid,
                "title": meta.get("title", ""),
                "organization": meta.get("organization", ""),
                "deadline": deadline_str,
                "max_amount": meta.get("max_amount"),
                "eligibility_summary": meta.get("eligibility_summary"),
                "description": results["documents"][0][i],
                "application_url": meta.get("application_url"),
                "relevance_score": round(relevance, 3),
                "days_until_deadline": days_left,
            })

            if len(matches) >= top_k:
                break

        return sorted(
            matches,
            key=lambda m: m.get("days_until_deadline") or 9999,
        )

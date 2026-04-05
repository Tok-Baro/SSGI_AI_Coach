"""RAG 파이프라인 서비스: ChromaDB + OpenAI Embeddings."""
import logging
from datetime import date
from typing import Optional
from uuid import UUID

import chromadb
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class RAGService:
    _instance = None
    _client = None
    _collection = None
    _openai = None

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

    async def search_subsidies(
        self, query: str, top_k: int = 5
    ) -> list[dict]:
        """벡터 유사도 검색으로 지원사업 매칭."""
        self._init_clients()

        query_embedding = await self._get_embedding(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # 중복 제거 여유분
        )

        if not results or not results["ids"][0]:
            return []

        # 중복 subsidy_id 제거 + 관련도 필터링
        seen_ids = set()
        matches = []

        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i] if results.get("distances") else 0
            relevance = 1 - distance  # cosine distance → similarity

            if relevance < 0.3:
                continue

            sid = meta.get("subsidy_id", "")
            if sid in seen_ids:
                continue
            seen_ids.add(sid)

            # 마감일까지 남은 일수 계산
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

        # 마감 임박순 정렬
        return sorted(
            matches,
            key=lambda m: m.get("days_until_deadline") or 9999,
        )

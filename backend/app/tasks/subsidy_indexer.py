"""매주 월요일 새벽 4시: 보조금 ChromaDB 재인덱싱."""
import logging

from sqlalchemy import select

from app.database import async_session_factory
from app.models.subsidy import Subsidy
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


async def reindex_subsidies():
    """활성 보조금 전체를 ChromaDB에 재인덱싱."""
    logger.info("Starting subsidy re-indexing...")

    async with async_session_factory() as db:
        stmt = select(Subsidy).where(Subsidy.is_active == True)
        result = await db.execute(stmt)
        subsidies = result.scalars().all()

    logger.info(f"Re-indexing {len(subsidies)} active subsidies...")

    rag = RAGService()
    success_count = 0

    for subsidy in subsidies:
        try:
            # 인덱싱할 텍스트 조합
            text = f"""
            {subsidy.title}
            기관: {subsidy.organization}
            자격요건: {subsidy.eligibility_summary or ''}
            설명: {subsidy.description}
            대상업종: {', '.join(subsidy.target_business_types or [])}
            대상지역: {', '.join(subsidy.target_regions or [])}
            """

            metadata = {
                "title": subsidy.title,
                "organization": subsidy.organization,
                "deadline": subsidy.deadline.isoformat() if subsidy.deadline else None,
                "max_amount": subsidy.max_amount,
                "eligibility_summary": subsidy.eligibility_summary,
                "application_url": subsidy.application_url,
                "target_business_types": ", ".join(subsidy.target_business_types or []),
                "target_regions": ", ".join(subsidy.target_regions or []),
            }

            await rag.index_subsidy(
                subsidy_id=str(subsidy.id),
                text=text.strip(),
                metadata=metadata,
            )
            success_count += 1

        except Exception as e:
            logger.error(f"Failed to index subsidy {subsidy.id}: {e}")

    logger.info(f"Subsidy re-indexing complete: {success_count}/{len(subsidies)} success")

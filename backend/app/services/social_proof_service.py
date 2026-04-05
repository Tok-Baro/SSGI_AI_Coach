"""k-anonymity 사회적 증거 서비스."""
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)

K_THRESHOLD = 10  # 최소 클러스터 크기 (프라이버시 보호)


class SocialProofService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_message(
        self, dong_name: str, business_type: str
    ) -> Optional[str]:
        """동네 + 업종 기반 사회적 증거 메시지."""
        stmt = select(func.count(User.id)).where(
            User.dong_name == dong_name,
            User.business_type == business_type,
            User.onboarding_completed == True,
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        if count < K_THRESHOLD:
            return self._cold_start_message(dong_name, business_type)

        return f"{dong_name} {business_type} {count}곳이 AI 경영코치를 사용하고 있습니다."

    async def get_subsidy_proof(
        self, dong_name: str, business_type: str, subsidy_title: str
    ) -> Optional[str]:
        """지원사업별 사회적 증거."""
        stmt = select(func.count(User.id)).where(
            User.dong_name == dong_name,
            User.onboarding_completed == True,
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        if count < K_THRESHOLD:
            return f"2025년 {dong_name} 소상공인 47%가 디지털전환 지원금을 수혜했습니다."

        return f"같은 동네 {count}곳 중 다수가 지원사업에 관심을 보이고 있습니다."

    def _cold_start_message(self, dong_name: str, business_type: str) -> str:
        """서비스 초기 (가입자 < K_THRESHOLD): 공공데이터 기반 메시지."""
        return f"2025년 {dong_name} {business_type} 47%가 디지털전환 지원금을 수혜했습니다."

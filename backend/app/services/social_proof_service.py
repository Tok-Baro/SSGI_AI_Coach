"""k-anonymity 사회적 증거 서비스.

ADR-002 정신: 출처 없는 통계는 표시하지 않는다.
- count >= K_THRESHOLD (10명+): "동네 X곳이 사용 중" 검증 가능 메시지
- count >= 3: "인근 N곳 함께 사용 중" 약한 사회적 증거
- count < 3: None 반환 → UI 카드 자체를 숨김
"""
import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)

K_THRESHOLD = 10  # 최소 클러스터 크기 (프라이버시 보호)
SOFT_THRESHOLD = 3  # 부드러운 사회적 증거 노출 최소치


class SocialProofService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_message(
        self, dong_name: str, business_type: str
    ) -> Optional[str]:
        """동네 + 업종 기반 사회적 증거 메시지.

        반환값이 None이면 UI는 카드 자체를 노출하지 않음.
        """
        if not dong_name or not business_type:
            return None

        stmt = select(func.count(User.id)).where(
            User.dong_name == dong_name,
            User.business_type == business_type,
            User.onboarding_completed == True,
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        if count >= K_THRESHOLD:
            return f"{dong_name} {business_type} {count}곳이 AI 경영코치를 사용하고 있습니다."
        if count >= SOFT_THRESHOLD:
            return f"{dong_name} 인근 {count}곳이 함께 사용 중입니다."
        return None  # 출처 없는 하드코딩 메시지 노출 금지 (ADR-002)

    async def get_subsidy_proof(
        self, dong_name: str, business_type: str, subsidy_title: str
    ) -> Optional[str]:
        """지원사업별 사회적 증거. 표본 부족 시 None."""
        if not dong_name:
            return None

        stmt = select(func.count(User.id)).where(
            User.dong_name == dong_name,
            User.onboarding_completed == True,
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        if count >= K_THRESHOLD:
            return f"같은 동네 {count}곳 중 다수가 지원사업에 관심을 보이고 있습니다."
        return None  # cold-start 시 47% 같은 출처 없는 통계 노출 금지

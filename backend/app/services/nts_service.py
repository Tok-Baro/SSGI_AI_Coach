"""국세청 사업자등록 상태조회 서비스."""
import logging
from typing import Optional

import httpx

from app.config import settings
from app.utils.retry import retry_async

logger = logging.getLogger(__name__)

NTS_API_URL = "https://api.odcloud.kr/api/nts-businessman/v1/status"


class NTSService:
    @retry_async(max_retries=2, delay=1.0)
    async def verify_business_number(self, business_number: str) -> Optional[dict]:
        """
        국세청 API로 사업자등록번호 유효성 검증.
        Returns: { is_valid, business_status, business_name, tax_type }
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                NTS_API_URL,
                params={"serviceKey": settings.nts_api_key},
                json={"b_no": [business_number]},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        items = data.get("data", [])
        if not items:
            return {
                "is_valid": False,
                "business_status": "확인불가",
                "business_name": None,
                "tax_type": None,
            }

        item = items[0]
        b_stt = item.get("b_stt", "")          # "계속사업자", "휴업자", "폐업자"
        b_stt_cd = item.get("b_stt_cd", "")     # "01", "02", "03"
        tax_type = item.get("tax_type", "")

        return {
            "is_valid": b_stt_cd == "01",
            "business_status": b_stt or "확인불가",
            "business_name": item.get("b_nm") or None,
            "tax_type": tax_type or None,
        }

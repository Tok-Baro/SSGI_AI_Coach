"""서울시 열린데이터 API 서비스: 상권분석, 생활인구, 문화행사."""
import logging
from datetime import date, timedelta
from typing import Optional

import httpx

from app.config import settings
from app.utils.retry import retry_async

logger = logging.getLogger(__name__)

BASE_URL = "http://openapi.seoul.go.kr:8088"


class SeoulAPIService:
    @retry_async(max_retries=2, delay=1.0)
    async def get_commercial_sales(
        self, gu_name: str, dong_name: str, business_type: str
    ) -> Optional[dict]:
        """
        분기별 상권 매출 분석.
        Returns: { current_quarter_sales, prev_quarter_sales, quarterly_change_percent, area_name }
        """
        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarSelngQq/1/20/"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarSelngQq", {}).get("row", [])
        if not rows:
            return None

        # dong_name + business_type과 가장 관련 있는 row 필터링
        matched = [
            r for r in rows
            if dong_name in r.get("ADSTRD_NM", "")
            and business_type in r.get("SVC_INDUTY_NM", "")
        ]

        if not matched:
            # 넓은 필터: gu_name만으로
            matched = [r for r in rows if gu_name in r.get("ADSTRD_NM", "")]

        if not matched:
            return None

        row = matched[0]
        current = float(row.get("THSMON_SELNG_AMT", 0))
        prev = float(row.get("LSTQRT_SELNG_AMT", 0))
        change = ((current - prev) / prev * 100) if prev > 0 else 0

        return {
            "current_quarter_sales": current,
            "prev_quarter_sales": prev,
            "quarterly_change_percent": round(change, 1),
            "data_period": row.get("STDR_YYQU_CD", ""),
            "area_name": row.get("ADSTRD_NM", ""),
        }

    # 서울시 구별 행정동 코드 앞 5자리 매핑 (통계청 기준)
    GU_CODE_MAP = {
        "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200",
        "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290",
        "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380",
        "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500",
        "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590",
        "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710",
        "강동구": "11740",
    }

    @retry_async(max_retries=2, delay=1.0)
    async def get_living_population(self, dong_name: str, gu_name: str = "") -> Optional[dict]:
        """
        일별 생활인구 데이터 (T-1). gu_name으로 구 코드 필터링.
        Returns: { today, yesterday, change_percent, data_date }
        """
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
        day_before = (date.today() - timedelta(days=2)).strftime("%Y%m%d")

        # 구 이름 → 코드 앞 5자리
        gu_code = self.GU_CODE_MAP.get(gu_name, "")

        async with httpx.AsyncClient(timeout=15.0) as client:
            # 어제 데이터 (전체 가져와서 필터)
            url_y = f"{BASE_URL}/{settings.seoul_api_key}/json/SPOP_LOCAL_RESD_DONG/1/1000/{yesterday}"
            resp_y = await client.get(url_y)
            resp_y.raise_for_status()
            data_y = resp_y.json()

            # 그저께 데이터
            url_db = f"{BASE_URL}/{settings.seoul_api_key}/json/SPOP_LOCAL_RESD_DONG/1/1000/{day_before}"
            resp_db = await client.get(url_db)
            resp_db.raise_for_status()
            data_db = resp_db.json()

        rows_y = data_y.get("SPOP_LOCAL_RESD_DONG", {}).get("row", [])
        rows_db = data_db.get("SPOP_LOCAL_RESD_DONG", {}).get("row", [])

        # 구 코드 앞 5자리로 필터 (행정동 코드는 8자리, 앞 5자리가 구)
        def _match(row: dict) -> bool:
            code = row.get("ADSTRD_CODE_SE", "")
            return code.startswith(gu_code) if gu_code else False

        pop_y = sum(float(r.get("TOT_LVPOP_CO", 0)) for r in rows_y if _match(r))
        pop_db = sum(float(r.get("TOT_LVPOP_CO", 0)) for r in rows_db if _match(r))

        if pop_y == 0 and pop_db == 0:
            return None

        change = ((pop_y - pop_db) / pop_db * 100) if pop_db > 0 else 0

        return {
            "today": pop_y,
            "yesterday": pop_db,
            "change_percent": round(change, 1),
            "data_date": yesterday,
        }

    @retry_async(max_retries=2, delay=1.0)
    async def get_cultural_events(self, gu_name: str) -> Optional[list]:
        """
        문화행사 정보.
        Returns: [{ title, place, start_date, end_date, category, url }]
        """
        url = f"{BASE_URL}/{settings.seoul_api_key}/json/culturalEventInfo/1/50/"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("culturalEventInfo", {}).get("row", [])

        # gu_name 필터
        filtered = [r for r in rows if gu_name in r.get("GUNAME", "")]

        events = []
        for r in filtered[:10]:
            events.append({
                "title": r.get("TITLE", ""),
                "place": r.get("PLACE", ""),
                "start_date": r.get("STRTDATE", ""),
                "end_date": r.get("END_DATE", ""),
                "category": r.get("CODENAME", ""),
                "url": r.get("ORG_LINK", ""),
            })

        return sorted(events, key=lambda e: e.get("start_date", ""))

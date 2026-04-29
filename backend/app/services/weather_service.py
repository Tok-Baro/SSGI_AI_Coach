"""기상청 단기예보 서비스."""
import logging
from datetime import date, datetime
from typing import Optional

import httpx

from app.config import settings
from app.utils.retry import retry_async

logger = logging.getLogger(__name__)

# 서울시 구별 기상청 격자 좌표 (nx, ny)
GU_GRID_MAP = {
    "종로구": (60, 127), "중구": (60, 127), "용산구": (60, 126),
    "성동구": (61, 127), "광진구": (62, 126), "동대문구": (61, 127),
    "중랑구": (62, 128), "성북구": (61, 128), "강북구": (61, 128),
    "도봉구": (61, 129), "노원구": (61, 129), "은평구": (59, 128),
    "서대문구": (59, 127), "마포구": (59, 127), "양천구": (58, 126),
    "강서구": (58, 126), "구로구": (58, 125), "금천구": (59, 125),
    "영등포구": (58, 126), "동작구": (59, 125), "관악구": (59, 125),
    "서초구": (61, 125), "강남구": (61, 126), "송파구": (62, 126),
    "강동구": (62, 126),
}

WEATHER_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"


class WeatherService:
    @retry_async(max_retries=2, delay=1.0)
    async def get_today_weather(self, gu_name: str = "") -> Optional[dict]:
        """오늘 날씨 예보 (기상청 단기예보)."""
        nx, ny = GU_GRID_MAP.get(gu_name, (60, 127))  # 기본: 서울 중심
        today = date.today().strftime("%Y%m%d")

        # 가장 가까운 발표 시각 계산 (02, 05, 08, 11, 14, 17, 20, 23시)
        hour = datetime.now().hour
        base_times = [23, 20, 17, 14, 11, 8, 5, 2]
        base_time = "0500"
        for bt in base_times:
            if hour >= bt + 1:  # 발표 후 1시간 뒤부터 조회 가능
                base_time = f"{bt:02d}00"
                break

        params = {
            "serviceKey": settings.nts_api_key,  # data.go.kr 키 (NTS 키와 동일 포털)
            "numOfRows": 60,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": today,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(WEATHER_URL, params=params)
            response.raise_for_status()
            data = response.json()

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items:
            return None

        # 오늘 예보 정리
        weather = {}
        for item in items:
            cat = item.get("category")
            val = item.get("fcstValue")
            if cat == "TMP":
                weather["temperature"] = f"{val}°C"
            elif cat == "POP":
                weather["rain_probability"] = f"{val}%"
            elif cat == "PTY":
                pty_map = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}
                weather["precipitation"] = pty_map.get(str(val), "없음")
            elif cat == "SKY":
                sky_map = {"1": "맑음", "3": "구름많음", "4": "흐림"}
                weather["sky"] = sky_map.get(str(val), "맑음")
            elif cat == "REH":
                weather["humidity"] = f"{val}%"

        if not weather:
            return None

        # 마케팅 인사이트 추가
        rain_prob = int(weather.get("rain_probability", "0").replace("%", "") or 0)
        temp = int(weather.get("temperature", "20").replace("°C", "") or 20)

        insights = []
        if rain_prob >= 60:
            insights.append("비 예보로 방문 고객 감소 예상. 배달/온라인 프로모션을 준비하세요.")
        if temp >= 30:
            insights.append("폭염 예보. 음료/빙수류 프로모션에 유리합니다.")
        elif temp <= 0:
            insights.append("한파 예보. 따뜻한 메뉴 강조 + 배달 프로모션을 추천합니다.")
        if weather.get("sky") == "맑음" and rain_prob < 30:
            insights.append("맑은 날씨. 야외 이벤트/전단지 배포에 좋은 날입니다.")

        weather["insights"] = insights
        return weather

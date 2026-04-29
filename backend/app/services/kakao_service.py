"""카카오 API 서비스: OAuth, 로컬 검색, 카카오톡 나에게 보내기."""
import logging
from typing import Optional

import httpx

from app.config import settings
from app.utils.retry import retry_async

logger = logging.getLogger(__name__)


class KakaoService:
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"
    LOCAL_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
    SEND_TO_ME_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    @retry_async(max_retries=1, delay=0.5)
    async def refresh_token(self, refresh_token: str) -> Optional[dict]:
        """카카오 리프레시 토큰으로 액세스 토큰 갱신."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": settings.kakao_rest_api_key,
                    "client_secret": settings.kakao_client_secret,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
            )
            response.raise_for_status()
            return response.json()

    @retry_async(max_retries=2, delay=1.0)
    async def get_token(self, code: str) -> Optional[dict]:
        """카카오 인가 코드 → 액세스 토큰 교환."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.kakao_rest_api_key,
                    "client_secret": settings.kakao_client_secret,
                    "redirect_uri": settings.kakao_redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
            )
            response.raise_for_status()
            return response.json()

    @retry_async(max_retries=2, delay=1.0)
    async def get_user_info(self, access_token: str) -> Optional[dict]:
        """카카오 액세스 토큰으로 사용자 정보 조회."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    @retry_async(max_retries=2, delay=1.0)
    async def search_local(self, query: str, size: int = 5) -> Optional[list]:
        """카카오 로컬 검색 (상호명 자동완성)."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                self.LOCAL_SEARCH_URL,
                params={"query": query, "size": size},
                headers={"Authorization": f"KakaoAK {settings.kakao_rest_api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("documents", [])

    @retry_async(max_retries=2, delay=1.0)
    async def count_nearby_by_category(
        self, lat: float, lng: float, category_code: str, radius: int = 500
    ) -> int:
        """반경 내 카테고리별 업체 수 (카카오 카테고리 검색)."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://dapi.kakao.com/v2/local/search/category.json",
                params={
                    "category_group_code": category_code,
                    "x": lng, "y": lat,
                    "radius": radius, "size": 1,
                },
                headers={"Authorization": f"KakaoAK {settings.kakao_rest_api_key}"},
            )
            response.raise_for_status()
            return response.json().get("meta", {}).get("total_count", 0)

    async def get_radius_competitor_summary(
        self, lat: float, lng: float
    ) -> dict:
        """반경 500m 내 업종별 업체 수 종합."""
        categories = {
            "FD6": "음식점",
            "CE7": "카페",
            "CS2": "편의점",
            "HP8": "병원",
            "BK9": "은행",
            "MT1": "대형마트",
            "CT1": "문화시설",
            "AT4": "관광명소",
        }
        results = {}
        for code, name in categories.items():
            try:
                count = await self.count_nearby_by_category(lat, lng, code)
                results[name] = count
            except Exception:
                results[name] = 0
        return results

    @retry_async(max_retries=2, delay=1.0)
    async def send_to_me(
        self, access_token: str, text: str, link_url: str = ""
    ) -> Optional[bool]:
        """카카오톡 나에게 보내기."""
        import json

        template = {
            "object_type": "text",
            "text": text[:200],  # 최대 200자
            "link": {"web_url": link_url, "mobile_web_url": link_url},
            "button_title": "자세히 보기",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.SEND_TO_ME_URL,
                data={"template_object": json.dumps(template)},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            response.raise_for_status()
            return True

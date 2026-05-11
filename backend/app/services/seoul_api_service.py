"""서울시 열린데이터 API 서비스: 상권분석, 생활인구, 문화행사."""
import asyncio
import logging
from datetime import date, timedelta
from typing import Optional

import httpx

from app.config import settings
from app.utils.retry import retry_async

logger = logging.getLogger(__name__)

BASE_URL = "http://openapi.seoul.go.kr:8088"


class SeoulAPIService:
    # 상권코드 → 행정동/자치구 매핑 캐시
    _trdar_mapping: dict | None = None
    # 동시 호출 시 중복 로드 방지용 lock (gather 호출 시 5번 중복 fetch 방지)
    _trdar_lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def _load_trdar_mapping(cls) -> dict:
        """TbgisTrdarRelm API에서 상권-행정동 매핑 로드 (1회 캐싱)."""
        # Fast path: 이미 캐시됨
        if cls._trdar_mapping is not None:
            return cls._trdar_mapping

        # Slow path: lock + double-check (한 번만 로드 보장)
        async with cls._trdar_lock:
            if cls._trdar_mapping is not None:
                return cls._trdar_mapping

            mapping = {}
            async with httpx.AsyncClient(timeout=20.0) as client:
                for start in range(1, 2000, 1000):
                    end = start + 999
                    url = f"{BASE_URL}/{settings.seoul_api_key}/json/TbgisTrdarRelm/{start}/{end}/"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        rows = data.get("TbgisTrdarRelm", {}).get("row", [])
                        if not rows:
                            break
                        for r in rows:
                            mapping[str(r.get("TRDAR_CD", ""))] = {
                                "signgu_cd": r.get("SIGNGU_CD", ""),
                                "signgu_nm": r.get("SIGNGU_CD_NM", ""),
                                "adstrd_cd": r.get("ADSTRD_CD", ""),
                                "adstrd_nm": r.get("ADSTRD_CD_NM", ""),
                            }
                    except Exception as e:
                        logger.warning(f"TbgisTrdarRelm 로드 실패: {e}")
                        break

            cls._trdar_mapping = mapping
            logger.info(f"상권-행정동 매핑 로드: {len(mapping)}건")
            return mapping
    # 사용자 업종 → 서울시 우리마을가게 상권분석 API 업종명(SVC_INDUTY_CD_NM) 매핑.
    # 키는 사용자가 입력할 만한 한글 단어. 값은 서울시 API가 실제 사용하는 업종 코드명.
    # 매칭은 dict 순서대로 부분 일치 (앞에 있는 키일수록 우선).
    # 서울시 코드명 출처: 서울 우리마을가게 상권분석 API 매뉴얼.
    BUSINESS_TYPE_MAP = {
        # ── 외식 (각 업종 별도 코드) ──
        "치킨": "치킨전문점",
        "분식": "분식전문점", "떡볶이": "분식전문점", "김밥": "분식전문점",
        "햄버거": "패스트푸드점", "버거": "패스트푸드점",
        "피자": "패스트푸드점",
        "한식": "한식음식점", "백반": "한식음식점", "국밥": "한식음식점",
        "중식": "중식음식점", "짜장": "중식음식점",
        "일식": "일식음식점", "초밥": "일식음식점", "스시": "일식음식점", "라멘": "일식음식점",
        "양식": "양식음식점", "파스타": "양식음식점", "스테이크": "양식음식점",
        "음식점": "한식음식점",  # 일반 표기 fallback (가장 마지막에 두려고 일부러 뒤)
        # ── 카페·디저트 ──
        "카페": "커피-음료", "커피": "커피-음료", "디저트": "커피-음료",
        "베이커리": "제과점", "빵집": "제과점", "제과": "제과점",
        # ── 주점 ──
        "호프": "호프-간이주점", "술집": "호프-간이주점", "주점": "호프-간이주점", "이자카야": "호프-간이주점",
        # ── 서비스 ──
        "미용": "미용실", "헤어": "미용실", "미용실": "미용실",
        "네일": "네일숍",
        "학원": "일반교습학원", "교육": "일반교습학원",
        "세탁": "세탁소",
        "부동산": "부동산중개업",
        "약국": "의약품", "병원": "일반의원", "치과": "치과의원", "한의원": "한의원",
        "편의점": "편의점",  # 서울시 API에 별도 코드 있음 (이전 "전자상거래업" 매핑 오류)
        "슈퍼": "슈퍼마켓", "마트": "슈퍼마켓",
        "소매": "전자상거래업",
        "PC": "PC방", "피시방": "PC방",
        "노래방": "노래방", "당구": "당구장",
        "골프": "골프연습장", "스포츠": "스포츠 강습", "헬스": "스포츠클럽",
    }

    def _map_business_type(self, user_type: str) -> str:
        """사용자 업종을 서울시 API 업종으로 매핑.

        부분 일치 + dict 순서 우선. "치킨"이 "한식음식점"보다 앞에 있어
        "치킨한마리"·"BBQ치킨" 같은 입력도 치킨전문점으로 매칭됨.
        매칭 실패 시 입력 그대로 반환 (서울시 API에서 매칭되지 않으면 fallback 단계에 의존).
        """
        if not user_type:
            return user_type
        for key, val in self.BUSINESS_TYPE_MAP.items():
            if key in user_type:
                return val
        return user_type

    @retry_async(max_retries=2, delay=1.0)
    async def get_commercial_sales(
        self, gu_name: str, dong_name: str, business_type: str
    ) -> Optional[dict]:
        """
        분기별 상권 매출 분석 (행정동 매핑으로 지역 필터링).
        Returns: { current_quarter_sales, prev_quarter_sales, quarterly_change_percent, area_name }
        """
        mapped_type = self._map_business_type(business_type)
        trdar_map = await self._load_trdar_mapping()

        # 해당 구의 상권코드 목록 추출
        gu_trdar_codes = set()
        dong_trdar_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                gu_trdar_codes.add(code)
                if dong_name and dong_name in info["adstrd_nm"]:
                    dong_trdar_codes.add(code)

        target_codes = dong_trdar_codes if dong_trdar_codes else gu_trdar_codes

        # 매출 데이터 가져오기
        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarSelngQq/1/1000/"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarSelngQq", {}).get("row", [])
        if not rows:
            return None

        # 지역 + 업종 필터
        matched = [
            r for r in rows
            if str(r.get("TRDAR_CD", "")) in target_codes
            and r.get("SVC_INDUTY_CD_NM") == mapped_type
        ]

        # 지역 필터만 (업종 넓히기)
        if not matched and target_codes:
            matched = [r for r in rows if str(r.get("TRDAR_CD", "")) in target_codes]

        # 그래도 없으면 같은 업종 서울 전체
        area_label = f"{gu_name} {dong_name}" if dong_name else gu_name
        if not matched:
            matched = [r for r in rows if r.get("SVC_INDUTY_CD_NM") == mapped_type]
            area_label = f"{mapped_type} (서울 전체)"

        if not matched:
            return None

        # ── 분기별 그룹핑 ──
        # STDR_YYQU_CD 형식: "20251" = 2025년 1분기. 최신 2개 분기로 진짜 QoQ 산출.
        from collections import defaultdict
        by_quarter: dict[str, list] = defaultdict(list)
        for r in matched:
            q = str(r.get("STDR_YYQU_CD", "")).strip()
            if q:
                by_quarter[q].append(r)

        sorted_quarters = sorted(by_quarter.keys(), reverse=True)
        cur_q = sorted_quarters[0] if sorted_quarters else ""
        prev_q = sorted_quarters[1] if len(sorted_quarters) >= 2 else ""
        cur_rows = by_quarter.get(cur_q, matched)  # fallback 전체

        # 현재 분기 합산
        total_sales = sum(float(r.get("THSMON_SELNG_AMT", 0)) for r in cur_rows)
        total_count = sum(float(r.get("THSMON_SELNG_CO", 0)) for r in cur_rows)
        avg_area_sales = total_sales / len(cur_rows) if cur_rows else 0
        avg_ticket = (total_sales / total_count) if total_count > 0 else 0

        # 진짜 QoQ — 이전 분기 합산과 비교
        qoq_change_pct: Optional[float] = None
        if prev_q:
            prev_rows = by_quarter[prev_q]
            prev_total = sum(float(r.get("THSMON_SELNG_AMT", 0)) for r in prev_rows)
            if prev_total > 0:
                qoq_change_pct = round((total_sales - prev_total) / prev_total * 100, 1)

        # 분기 내 분산 (평균 vs 중앙값) — 별도 필드 (시계열 아님 명시)
        sales_list = sorted([float(r.get("THSMON_SELNG_AMT", 0)) for r in cur_rows])
        median = sales_list[len(sales_list) // 2] if sales_list else 0
        dispersion_pct = ((avg_area_sales - median) / median * 100) if median > 0 else 0

        return {
            "area_total_sales": round(avg_area_sales),
            "area_total_count": round(total_count / len(cur_rows)) if cur_rows else 0,
            "avg_ticket_price": round(avg_ticket),
            # 진짜 분기 변화율 (이전 분기 데이터 없으면 None)
            "quarterly_change_percent": qoq_change_pct,
            # 분기 내 상권별 분포 비대칭 (이전 의미. 시계열 아님 — 명칭 분리)
            "area_dispersion_percent": round(dispersion_pct, 1),
            "current_quarter": cur_q,
            "prev_quarter": prev_q if prev_q else None,
            "data_period": cur_q or rows[0].get("STDR_YYQU_CD", ""),
            "area_name": area_label,
            "sample_count": len(matched),
            "note": "상권 내 동종업종 전체 합산 매출 (개별 점포 매출 아님)",
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

    async def _fetch_population_for_date(
        self, client: httpx.AsyncClient, date_str: str
    ) -> Optional[list]:
        """특정 날짜의 생활인구 데이터를 가져온다. 없으면 None."""
        url = f"{BASE_URL}/{settings.seoul_api_key}/json/SPOP_LOCAL_RESD_DONG/1/1000/{date_str}"
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("SPOP_LOCAL_RESD_DONG", {}).get("row", [])
        return rows if rows else None

    @retry_async(max_retries=2, delay=1.0)
    async def get_living_population(self, dong_name: str, gu_name: str = "") -> Optional[dict]:
        """
        일별 생활인구 데이터. 최신 데이터를 자동 탐색 (T-1 ~ T-7).
        Returns: { today, yesterday, change_percent, data_date }
        """
        gu_code = self.GU_CODE_MAP.get(gu_name, "")
        if not gu_code:
            return None

        async with httpx.AsyncClient(timeout=15.0) as client:
            # 최신 데이터 찾기 (T-1부터 T-7까지)
            rows_recent = None
            rows_prev = None
            recent_date = None

            for days_ago in range(1, 8):
                d = (date.today() - timedelta(days=days_ago)).strftime("%Y%m%d")
                rows = await self._fetch_population_for_date(client, d)
                if rows:
                    if rows_recent is None:
                        rows_recent = rows
                        recent_date = d
                    elif rows_prev is None:
                        rows_prev = rows
                        break

        if not rows_recent:
            return None

        def _match(row: dict) -> bool:
            code = row.get("ADSTRD_CODE_SE", "")
            return code.startswith(gu_code)

        pop_recent = sum(float(r.get("TOT_LVPOP_CO", 0)) for r in rows_recent if _match(r))
        pop_prev = sum(float(r.get("TOT_LVPOP_CO", 0)) for r in (rows_prev or []) if _match(r))

        if pop_recent == 0 and pop_prev == 0:
            return None

        change = ((pop_recent - pop_prev) / pop_prev * 100) if pop_prev > 0 else 0

        return {
            "today": pop_recent,
            "yesterday": pop_prev,
            "change_percent": round(change, 1),
            "data_date": recent_date,
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

    @retry_async(max_retries=2, delay=1.0)
    async def get_commercial_floating_pop(
        self, gu_name: str, dong_name: str, business_type: str
    ) -> Optional[dict]:
        """상권 유동인구 (VwsmTrdarFlpopQq): 시간대/요일/성별/연령대별."""
        trdar_map = await self._load_trdar_mapping()
        target_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                if dong_name and dong_name in info["adstrd_nm"]:
                    target_codes.add(code)
        if not target_codes:
            for code, info in trdar_map.items():
                if info["signgu_nm"] == gu_name:
                    target_codes.add(code)

        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarFlpopQq/1/1000/"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarFlpopQq", {}).get("row", [])
        if not rows:
            return None

        matched = [r for r in rows if str(r.get("TRDAR_CD", "")) in target_codes]
        if not matched:
            return None

        n = len(matched)

        def _avg(field: str) -> float:
            return sum(float(r.get(field, 0)) for r in matched) / n

        return {
            "total": round(_avg("TOT_FLPOP_CO")),
            "gender": {
                "남성": round(_avg("ML_FLPOP_CO")),
                "여성": round(_avg("FML_FLPOP_CO")),
            },
            "age_group": {
                "10대": round(_avg("AGRDE_10_FLPOP_CO")),
                "20대": round(_avg("AGRDE_20_FLPOP_CO")),
                "30대": round(_avg("AGRDE_30_FLPOP_CO")),
                "40대": round(_avg("AGRDE_40_FLPOP_CO")),
                "50대": round(_avg("AGRDE_50_FLPOP_CO")),
                "60대+": round(_avg("AGRDE_60_ABOVE_FLPOP_CO")),
            },
            "time_zone": {
                "00~06": round(_avg("TMZON_00_06_FLPOP_CO")),
                "06~11": round(_avg("TMZON_06_11_FLPOP_CO")),
                "11~14": round(_avg("TMZON_11_14_FLPOP_CO")),
                "14~17": round(_avg("TMZON_14_17_FLPOP_CO")),
                "17~21": round(_avg("TMZON_17_21_FLPOP_CO")),
                "21~24": round(_avg("TMZON_21_24_FLPOP_CO")),
            },
            "day_of_week": {
                "월": round(_avg("MON_FLPOP_CO")),
                "화": round(_avg("TUES_FLPOP_CO")),
                "수": round(_avg("WED_FLPOP_CO")),
                "목": round(_avg("THUR_FLPOP_CO")),
                "금": round(_avg("FRI_FLPOP_CO")),
                "토": round(_avg("SAT_FLPOP_CO")),
                "일": round(_avg("SUN_FLPOP_CO")),
            },
            "sample_count": n,
        }

    @retry_async(max_retries=2, delay=1.0)
    async def get_commercial_change_index(
        self, gu_name: str, dong_name: str
    ) -> Optional[dict]:
        """상권변화지표 (VwsmTrdarIxQq): 활성화/정체/쇠퇴 판정."""
        trdar_map = await self._load_trdar_mapping()
        target_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                if dong_name and dong_name in info["adstrd_nm"]:
                    target_codes.add(code)
        if not target_codes:
            for code, info in trdar_map.items():
                if info["signgu_nm"] == gu_name:
                    target_codes.add(code)

        # 최신 분기 코드 확인 후 필터 (총 1650건으로 줄어듦)
        async with httpx.AsyncClient(timeout=20.0) as client:
            # 최신 분기 확인
            peek_url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarIxQq/1/1/"
            peek_resp = await client.get(peek_url)
            peek_data = peek_resp.json()
            latest_q = peek_data.get("VwsmTrdarIxQq", {}).get("row", [{}])[0].get("STDR_YYQU_CD", "")

            # 페이지네이션으로 전체 가져오기
            rows_all = []
            for start in range(1, 2000, 1000):
                end = start + 999
                page_url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarIxQq/{start}/{end}/{latest_q}"
                resp = await client.get(page_url)
                resp.raise_for_status()
                page_data = resp.json()
                page_rows = page_data.get("VwsmTrdarIxQq", {}).get("row", [])
                if not page_rows:
                    break
                rows_all.extend(page_rows)

        rows = rows_all
        if not rows:
            return None

        matched = [r for r in rows if str(r.get("TRDAR_CD", "")) in target_codes]
        if not matched:
            return None

        # 상권변화 지표 집계
        status_count = {}
        for r in matched:
            status = r.get("TRDAR_CHNGE_IX_NM", "미분류")
            status_count[status] = status_count.get(status, 0) + 1

        dominant = max(status_count, key=status_count.get) if status_count else "미분류"
        n = len(matched)

        def _avg_numeric(field: str) -> float:
            vals = []
            for r in matched:
                v = r.get(field)
                if v is not None:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
            return sum(vals) / len(vals) if vals else 0

        # 폐업/생존 분포 비율 계산
        closing_keywords = ("쇠퇴", "축소", "정체")
        growing_keywords = ("확장", "다이나믹")
        closing_count = sum(c for k, c in status_count.items() if any(kw in k for kw in closing_keywords))
        growing_count = sum(c for k, c in status_count.items() if any(kw in k for kw in growing_keywords))

        return {
            "dominant_status": dominant,
            "status_distribution": status_count,
            "change_index_code": matched[0].get("TRDAR_CHNGE_IX", "") if matched else "",
            "avg_monthly_sales": round(_avg_numeric("OPR_SALE_MT_AVRG")),
            # 폐업/생존 분석 추가 필드 (Phase 12 Survival Matrix)
            "survival_avg_months": round(_avg_numeric("SU_BIZS_MT_AVRG")),  # 생존업체 평균 영업개월
            "closed_avg_months": round(_avg_numeric("CLSBIZ_MT_AVRG")),  # 폐업업체 평균 영업개월
            "closing_area_count": closing_count,
            "growing_area_count": growing_count,
            "sample_count": n,
        }

    @retry_async(max_retries=2, delay=1.0)
    async def get_anchor_facilities(
        self, gu_name: str, dong_name: str
    ) -> Optional[dict]:
        """집객시설 (VwsmTrdarFcltyQq): 주변 인프라 현황."""
        trdar_map = await self._load_trdar_mapping()
        target_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                if dong_name and dong_name in info["adstrd_nm"]:
                    target_codes.add(code)
        if not target_codes:
            for code, info in trdar_map.items():
                if info["signgu_nm"] == gu_name:
                    target_codes.add(code)

        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarFcltyQq/1/1000/"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarFcltyQq", {}).get("row", [])
        matched = [r for r in rows if str(r.get("TRDAR_CD", "")) in target_codes]
        if not matched:
            return None

        n = len(matched)

        def _avg(field: str) -> int:
            return round(sum(float(r.get(field, 0)) for r in matched) / n)

        return {
            "관공서": _avg("PBLOFC_CO"),
            "은행": _avg("BANK_CO"),
            "병원": _avg("HSPTL_CO"),
            "약국": _avg("PHRM_CO"),
            "대형마트": _avg("LRGE_MART_CO"),
            "버스정류장": _avg("BUS_STTN_CO"),
            "지하철역": _avg("SUBWAY_STTN_CO"),
            "유치원/어린이집": _avg("KNDRGR_CO"),
            "대학교": _avg("UNIV_CO"),
            "sample_count": n,
        }

    @retry_async(max_retries=2, delay=1.0)
    async def get_workplace_population(
        self, gu_name: str, dong_name: str
    ) -> Optional[dict]:
        """직장인구 (VwsmTrdarWrcPopltnQq): 상권 내 직장인 수."""
        trdar_map = await self._load_trdar_mapping()
        target_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                if dong_name and dong_name in info["adstrd_nm"]:
                    target_codes.add(code)
        if not target_codes:
            for code, info in trdar_map.items():
                if info["signgu_nm"] == gu_name:
                    target_codes.add(code)

        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarWrcPopltnQq/1/1000/"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarWrcPopltnQq", {}).get("row", [])
        matched = [r for r in rows if str(r.get("TRDAR_CD", "")) in target_codes]
        if not matched:
            return None

        n = len(matched)

        def _avg(field: str) -> float:
            return sum(float(r.get(field, 0)) for r in matched) / n

        return {
            "total": round(_avg("TOT_WRC_POPLTN_CO")),
            "gender": {
                "남성": round(_avg("ML_WRC_POPLTN_CO")),
                "여성": round(_avg("FML_WRC_POPLTN_CO")),
            },
            "age_group": {
                "10대": round(_avg("AGRDE_10_WRC_POPLTN_CO")),
                "20대": round(_avg("AGRDE_20_WRC_POPLTN_CO")),
                "30대": round(_avg("AGRDE_30_WRC_POPLTN_CO")),
                "40대": round(_avg("AGRDE_40_WRC_POPLTN_CO")),
                "50대": round(_avg("AGRDE_50_WRC_POPLTN_CO")),
                "60대+": round(_avg("AGRDE_60_ABOVE_WRC_POPLTN_CO")),
            },
            "sample_count": n,
        }

    @retry_async(max_retries=2, delay=1.0)
    async def get_benchmark(
        self, gu_name: str, dong_name: str, business_type: str
    ) -> Optional[dict]:
        """서울 평균 대비 벤치마킹: 매출, 점포수, 유동인구 비교."""
        mapped_type = self._map_business_type(business_type)
        trdar_map = await self._load_trdar_mapping()

        # 해당 구 상권코드
        gu_codes = set()
        dong_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                gu_codes.add(code)
                if dong_name and dong_name in info["adstrd_nm"]:
                    dong_codes.add(code)
        local_codes = dong_codes if dong_codes else gu_codes

        # 매출 데이터
        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarSelngQq/1/1000/"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarSelngQq", {}).get("row", [])
        if not rows:
            return None

        # 같은 업종 전체 (서울 평균)
        all_same_type = [r for r in rows if r.get("SVC_INDUTY_CD_NM") == mapped_type]
        # 내 지역 같은 업종
        local_same = [r for r in rows if str(r.get("TRDAR_CD", "")) in local_codes and r.get("SVC_INDUTY_CD_NM") == mapped_type]
        # 내 지역 전체
        if not local_same:
            local_same = [r for r in rows if str(r.get("TRDAR_CD", "")) in local_codes]

        if not all_same_type or not local_same:
            return None

        def _avg_ticket(rlist: list) -> float:
            """평균 객단가 = 총매출 / 총건수"""
            total_amt = sum(float(r.get("THSMON_SELNG_AMT", 0)) for r in rlist)
            total_cnt = sum(float(r.get("THSMON_SELNG_CO", 0)) for r in rlist)
            return (total_amt / total_cnt) if total_cnt > 0 else 0

        seoul_avg = _avg_ticket(all_same_type)
        local_avg = _avg_ticket(local_same)
        diff_pct = ((local_avg - seoul_avg) / seoul_avg * 100) if seoul_avg > 0 else 0

        # 주말 비중 비교
        def _weekend_ratio(rlist: list) -> float:
            total = sum(float(r.get("THSMON_SELNG_AMT", 0)) for r in rlist)
            weekend = sum(float(r.get("WKEND_SELNG_AMT", 0)) for r in rlist)
            return (weekend / total * 100) if total > 0 else 0

        # 여성 비중 비교
        def _female_ratio(rlist: list) -> float:
            total = sum(float(r.get("THSMON_SELNG_AMT", 0)) for r in rlist)
            female = sum(float(r.get("FML_SELNG_AMT", 0)) for r in rlist)
            return (female / total * 100) if total > 0 else 0

        return {
            "local_avg_ticket": round(local_avg),
            "seoul_avg_ticket": round(seoul_avg),
            "ticket_diff_pct": round(diff_pct, 1),
            "local_weekend_ratio": round(_weekend_ratio(local_same), 1),
            "seoul_weekend_ratio": round(_weekend_ratio(all_same_type), 1),
            "local_female_ratio": round(_female_ratio(local_same), 1),
            "seoul_female_ratio": round(_female_ratio(all_same_type), 1),
            "local_sample": len(local_same),
            "seoul_sample": len(all_same_type),
            "business_type": mapped_type,
        }

    @retry_async(max_retries=2, delay=1.0)
    async def get_sales_detail(
        self, gu_name: str, dong_name: str, business_type: str
    ) -> Optional[dict]:
        """
        상세 매출 분석: 요일별, 시간대별, 성별, 연령대별.
        TbgisTrdarRelm 매핑으로 지역 필터링.
        """
        mapped_type = self._map_business_type(business_type)
        trdar_map = await self._load_trdar_mapping()

        # 해당 구/동의 상권코드
        target_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                if dong_name and dong_name in info["adstrd_nm"]:
                    target_codes.add(code)
        if not target_codes:
            for code, info in trdar_map.items():
                if info["signgu_nm"] == gu_name:
                    target_codes.add(code)

        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarSelngQq/1/1000/"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarSelngQq", {}).get("row", [])
        if not rows:
            return None

        # 지역 + 업종 필터 — fallback 단계마다 data_scope 라벨링
        # exact: 동 + 정확한 업종 매칭 (가장 신뢰도 높음)
        # dong_all_industry: 그 동의 모든 업종 평균 (업종 매핑 실패 시)
        # seoul_industry: 서울 전체에서 같은 업종 평균 (지역 매핑 실패 시)
        matched = [
            r for r in rows
            if str(r.get("TRDAR_CD", "")) in target_codes
            and r.get("SVC_INDUTY_CD_NM") == mapped_type
        ]
        data_scope = "exact"
        scope_note = f"{gu_name} {dong_name} · {mapped_type} 평균"
        if not matched:
            matched = [r for r in rows if str(r.get("TRDAR_CD", "")) in target_codes]
            data_scope = "dong_all_industry"
            scope_note = f"{gu_name} {dong_name} 전체 업종 평균 ({mapped_type} 데이터 부족)"
        if not matched:
            matched = [r for r in rows if r.get("SVC_INDUTY_CD_NM") == mapped_type]
            data_scope = "seoul_industry"
            scope_note = f"서울 전체 {mapped_type} 평균 (이 동 데이터 부족)"
        if not matched:
            return None

        # 집계 — 비율(%)로 변환 (상권 전체 합산이므로 절대금액보다 비율이 유의미)
        n = len(matched)

        def _avg(field: str) -> float:
            return sum(float(r.get(field, 0)) for r in matched) / n

        total_sales = _avg("THSMON_SELNG_AMT") or 1
        total_count = _avg("THSMON_SELNG_CO") or 1

        def _pct(field: str) -> float:
            return round(_avg(field) / total_sales * 100, 1)

        def _pct_count(field: str) -> float:
            return round(_avg(field) / total_count * 100, 1)

        return {
            "sample_count": n,
            "data_scope": data_scope,  # exact | dong_all_industry | seoul_industry
            "scope_note": scope_note,  # 사람-친화 라벨 (차트/PDF에 노출)
            "note": "상권 내 동종업종 매출 비중 분석 (%)",
            "day_of_week": {
                "월": _pct("MON_SELNG_AMT"),
                "화": _pct("TUES_SELNG_AMT"),
                "수": _pct("WED_SELNG_AMT"),
                "목": _pct("THUR_SELNG_AMT"),
                "금": _pct("FRI_SELNG_AMT"),
                "토": _pct("SAT_SELNG_AMT"),
                "일": _pct("SUN_SELNG_AMT"),
            },
            "time_zone": {
                "00~06": _pct("TMZON_00_06_SELNG_AMT"),
                "06~11": _pct("TMZON_06_11_SELNG_AMT"),
                "11~14": _pct("TMZON_11_14_SELNG_AMT"),
                "14~17": _pct("TMZON_14_17_SELNG_AMT"),
                "17~21": _pct("TMZON_17_21_SELNG_AMT"),
                "21~24": _pct("TMZON_21_24_SELNG_AMT"),
            },
            "gender": {
                "남성_비중": _pct("ML_SELNG_AMT"),
                "여성_비중": _pct("FML_SELNG_AMT"),
                "남성_건수비중": _pct_count("ML_SELNG_CO"),
                "여성_건수비중": _pct_count("FML_SELNG_CO"),
            },
            "age_group": {
                "10대": _pct("AGRDE_10_SELNG_AMT"),
                "20대": _pct("AGRDE_20_SELNG_AMT"),
                "30대": _pct("AGRDE_30_SELNG_AMT"),
                "40대": _pct("AGRDE_40_SELNG_AMT"),
                "50대": _pct("AGRDE_50_SELNG_AMT"),
                "60대+": _pct("AGRDE_60_ABOVE_SELNG_AMT"),
            },
            "age_group_count": {
                "10대": _pct_count("AGRDE_10_SELNG_CO"),
                "20대": _pct_count("AGRDE_20_SELNG_CO"),
                "30대": _pct_count("AGRDE_30_SELNG_CO"),
                "40대": _pct_count("AGRDE_40_SELNG_CO"),
                "50대": _pct_count("AGRDE_50_SELNG_CO"),
                "60대+": _pct_count("AGRDE_60_ABOVE_SELNG_CO"),
            },
            "weekday_vs_weekend": {
                "주중": _pct("MDWK_SELNG_AMT"),
                "주말": _pct("WKEND_SELNG_AMT"),
            },
            "avg_ticket_price": round(_avg("THSMON_SELNG_AMT") / _avg("THSMON_SELNG_CO")) if _avg("THSMON_SELNG_CO") > 0 else 0,
        }

    @retry_async(max_retries=2, delay=1.0)
    async def get_business_openclose(
        self, gu_name: str, business_type: str
    ) -> Optional[dict]:
        """
        상권 점포 개폐업 분석 (행정동 매핑으로 지역 필터링).
        Returns: { total_stores, opening_rate, closing_rate, net_change }
        """
        mapped_type = self._map_business_type(business_type)
        trdar_map = await self._load_trdar_mapping()

        # 해당 구의 상권코드 목록
        gu_trdar_codes = set()
        for code, info in trdar_map.items():
            if info["signgu_nm"] == gu_name:
                gu_trdar_codes.add(code)

        url = f"{BASE_URL}/{settings.seoul_api_key}/json/VwsmTrdarStorQq/1/1000/"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rows = data.get("VwsmTrdarStorQq", {}).get("row", [])
        if not rows:
            return None

        # 지역 + 업종 필터
        matched = [
            r for r in rows
            if str(r.get("TRDAR_CD", "")) in gu_trdar_codes
            and r.get("SVC_INDUTY_CD_NM") == mapped_type
        ]

        area_label = f"{gu_name} {mapped_type}"
        if not matched and gu_trdar_codes:
            matched = [r for r in rows if str(r.get("TRDAR_CD", "")) in gu_trdar_codes]
            area_label = f"{gu_name} 전체 업종"

        if not matched:
            matched = [r for r in rows if r.get("SVC_INDUTY_CD_NM") == mapped_type]
            area_label = f"{mapped_type} (서울 전체)"

        if not matched:
            return None

        total_stores = sum(int(float(r.get("STOR_CO", 0))) for r in matched)
        avg_stores = total_stores // len(matched) if matched else 0
        avg_opening = sum(float(r.get("OPBIZ_RT", 0)) for r in matched) / len(matched)
        avg_closing = sum(float(r.get("CLSBIZ_RT", 0)) for r in matched) / len(matched)

        return {
            "total_stores": avg_stores,
            "opening_rate": round(avg_opening, 1),
            "closing_rate": round(avg_closing, 1),
            "net_change": round(avg_opening - avg_closing, 1),
            "sample_count": len(matched),
            "area_name": area_label,
        }

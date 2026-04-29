"""부동산학 기반 상권 입지 분석기.

기존 API 데이터에서 부동산/입지 분석 지표를 산출한다.
- 직주비율 (직장인구 vs 상주인구)
- 업종 다양성 지수 (허핀달-허쉬만 지수)
- 집객력 점수 (앵커 시설 기반)
- 유동인구 효율 (유동인구 대비 매출)
- 상권 밀집도 (반경 내 업체 수 / 면적)
"""
from __future__ import annotations

import math
from typing import Optional


def analyze_location(
    *,
    facilities: Optional[dict] = None,
    workplace_pop: Optional[dict] = None,
    floating_pop: Optional[dict] = None,
    population_data: Optional[dict] = None,
    radius_summary: Optional[dict] = None,
    sales_data: Optional[dict] = None,
    benchmark: Optional[dict] = None,
    change_index: Optional[dict] = None,
) -> dict:
    """부동산학 기반 입지 분석 종합 리포트."""
    result = {}

    # 1. 직장인구 밀도 분석 (상권 내 직장인 규모)
    if workplace_pop:
        work = workplace_pop.get("total", 0)
        if work > 0:
            if work >= 5000:
                profile = "고밀도 업무지구 — 직장인 점심/퇴근 수요 매우 높음, 런치 세트/퇴근 할인 필수"
            elif work >= 2000:
                profile = "업무 밀집 지역 — 직장인 대상 점심 특화 메뉴와 퇴근 시간대 프로모션 유효"
            elif work >= 500:
                profile = "직주 혼합 지역 — 직장인 + 주민 이중 수요, 시간대별 메뉴 차별화"
            else:
                profile = "주거 우세 지역 — 가족/주민 대상 마케팅, 주말 집객에 집중"

            # 성별 비율
            m = workplace_pop.get("gender", {}).get("남성", 0)
            f = workplace_pop.get("gender", {}).get("여성", 0)
            gender_note = ""
            if m + f > 0:
                m_pct = round(m / (m + f) * 100)
                gender_note = f", 직장인 남녀비 {m_pct}:{100 - m_pct}"

            result["workplace_density"] = {
                "total": work,
                "profile": profile + gender_note,
            }

    # 2. 업종 다양성 지수 (허핀달-허쉬만 지수, HHI)
    # HHI가 낮을수록 다양, 높을수록 특정 업종 편중
    if radius_summary:
        total = sum(v for v in radius_summary.values() if isinstance(v, (int, float)))
        if total > 0:
            shares = [(v / total) for v in radius_summary.values() if isinstance(v, (int, float)) and v > 0]
            hhi = sum(s ** 2 for s in shares)
            # HHI: 0~1, 낮을수록 다양
            if hhi < 0.15:
                diversity = "매우 다양 — 다양한 업종이 공존하는 복합 상권"
            elif hhi < 0.25:
                diversity = "적정 다양 — 주요 업종 중심의 균형 잡힌 상권"
            elif hhi < 0.4:
                diversity = "편중 — 특정 업종에 집중된 특화 상권"
            else:
                diversity = "고도 편중 — 단일 업종 위주 상권, 리스크 높음"

            dominant = max(radius_summary, key=lambda k: radius_summary[k] if isinstance(radius_summary[k], (int, float)) else 0)
            result["diversity_index"] = {
                "hhi": round(hhi, 3),
                "interpretation": diversity,
                "total_businesses": total,
                "dominant_category": dominant,
                "dominant_share": round(radius_summary.get(dominant, 0) / total * 100, 1),
            }

    # 3. 집객력 점수 (앵커 시설 가중 합산)
    if facilities:
        weights = {
            "지하철역": 30, "버스정류장": 10, "대형마트": 20,
            "대학교": 25, "병원": 15, "은행": 5,
            "관공서": 10, "약국": 5, "유치원/어린이집": 8,
        }
        score = 0
        detail = {}
        for fac, count in facilities.items():
            if fac == "sample_count" or not isinstance(count, (int, float)):
                continue
            w = weights.get(fac, 5)
            contribution = min(count * w, w * 3)  # 최대 3배까지
            score += contribution
            if count > 0:
                detail[fac] = count

        # 정규화 (0~100)
        max_possible = sum(w * 3 for w in weights.values())
        normalized = min(round(score / max_possible * 100), 100) if max_possible > 0 else 0

        if normalized >= 70:
            grade = "A (우수) — 다양한 집객시설로 자연 유입 높음"
        elif normalized >= 50:
            grade = "B (양호) — 주요 시설 보유, 추가 마케팅으로 보완 가능"
        elif normalized >= 30:
            grade = "C (보통) — 집객시설 부족, 능동적 고객 유치 필요"
        else:
            grade = "D (미흡) — 집객시설 부재, 배달/온라인 채널 필수"

        result["anchor_score"] = {
            "score": normalized,
            "grade": grade,
            "facilities": detail,
        }

    # 4. 유동인구 효율 (유동인구 대비 매출 전환)
    if floating_pop and sales_data:
        fp_total = floating_pop.get("total", 0)
        sales_amt = sales_data.get("current_quarter_sales", 0)
        if fp_total > 0 and sales_amt > 0:
            efficiency = sales_amt / fp_total
            result["traffic_efficiency"] = {
                "sales_per_visitor": round(efficiency),
                "interpretation": (
                    "높은 전환율 — 방문 고객의 구매율이 높음" if efficiency > 50000
                    else "보통 전환율 — 구매 유도 마케팅으로 개선 가능" if efficiency > 20000
                    else "낮은 전환율 — 유동인구 대비 매출이 낮음, 간판/홍보 강화 필요"
                ),
            }

    # 5. 시간대 집중도 (유동인구 기반)
    if floating_pop and floating_pop.get("time_zone"):
        tz = floating_pop["time_zone"]
        total_fp = sum(tz.values())
        if total_fp > 0:
            peak_time = max(tz, key=tz.get)
            peak_share = tz[peak_time] / total_fp * 100
            off_peak = min(tz, key=lambda k: tz[k] if tz[k] > 0 else float('inf'))

            result["time_concentration"] = {
                "peak_time": peak_time,
                "peak_share": round(peak_share, 1),
                "off_peak_time": off_peak,
                "interpretation": (
                    f"피크 시간({peak_time})에 유동인구 {peak_share:.0f}% 집중. "
                    f"{'피크 집중형 — 피크 타임 마케팅 집중 투자' if peak_share > 30 else '분산형 — 종일 영업 전략 유효'}"
                ),
            }

    # 6. 서울 평균 대비 포지셔닝
    if benchmark:
        diff = benchmark.get("ticket_diff_pct", 0)
        if diff > 20:
            position = "상위 상권 — 서울 평균 대비 매출 우위, 프리미엄 전략 가능"
        elif diff > 0:
            position = "평균 이상 — 안정적이나 추가 성장 여지 존재"
        elif diff > -20:
            position = "평균 이하 — 마케팅 강화로 서울 평균 달성 가능"
        else:
            position = "하위 상권 — 근본적 경쟁력 개선 필요 (메뉴/서비스/입지)"

        result["seoul_positioning"] = {
            "sales_diff_pct": diff,
            "position": position,
        }

    # 7. 상권 생애주기 판정
    if change_index:
        status = change_index.get("dominant_status", "")
        lifecycle_map = {
            "상권확장": "성장기 — 적극적 투자와 시장 선점이 유리한 시기",
            "다이나믹": "전환기 — 변화가 빠른 시장, 트렌드 대응력이 핵심",
            "정체": "성숙기 — 차별화와 효율화로 기존 고객 유지에 집중",
            "상권축소": "쇠퇴기 — 비용 절감 + 온라인 채널 확대로 리스크 관리",
        }
        result["lifecycle"] = {
            "stage": status,
            "strategy": lifecycle_map.get(status, "판정 불가"),
        }

    return result


def format_location_analysis(analysis: dict) -> str:
    """GPT 프롬프트용 텍스트 포맷."""
    lines = ["\n[부동산학 입지 분석]"]

    if "workplace_density" in analysis:
        wd = analysis["workplace_density"]
        lines.append(f"- 직장인구: {wd['total']:,}명")
        lines.append(f"  → {wd['profile']}")

    if "diversity_index" in analysis:
        di = analysis["diversity_index"]
        lines.append(f"- 업종 다양성(HHI): {di['hhi']} — {di['interpretation']}")
        lines.append(f"  주력 업종: {di['dominant_category']} ({di['dominant_share']}%), 총 {di['total_businesses']}개 업체")

    if "anchor_score" in analysis:
        anc = analysis["anchor_score"]
        lines.append(f"- 집객력 점수: {anc['score']}/100 — {anc['grade']}")
        fac_str = ", ".join(f"{k} {v}개" for k, v in anc["facilities"].items())
        lines.append(f"  시설: {fac_str}")

    if "traffic_efficiency" in analysis:
        te = analysis["traffic_efficiency"]
        lines.append(f"- 유동인구 전환: 방문객당 {te['sales_per_visitor']:,}원 — {te['interpretation']}")

    if "time_concentration" in analysis:
        tc = analysis["time_concentration"]
        lines.append(f"- 시간 집중도: {tc['interpretation']}")

    if "seoul_positioning" in analysis:
        sp = analysis["seoul_positioning"]
        lines.append(f"- 서울 포지셔닝: 평균 대비 {sp['sales_diff_pct']:+.1f}% — {sp['position']}")

    if "lifecycle" in analysis:
        lc = analysis["lifecycle"]
        lines.append(f"- 상권 생애주기: {lc['stage']} — {lc['strategy']}")

    return "\n".join(lines)

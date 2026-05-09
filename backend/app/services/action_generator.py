"""일일 액션 생성 서비스: GPT-4o 프롬프트 + 폴백 템플릿."""
import json
import logging
from datetime import date, datetime
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.models.user import User
from app.models.daily_action import DailyAction

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 소상공인 전문 AI 경영코치입니다.
핵심 원칙:
1. 손실 프레이밍: '추천합니다'가 아니라 '놓치고 있습니다'
2. 구체적 행동: 1탭으로 실행 가능한 것
3. 데이터 기반: 제공된 데이터만 사용
4. 간결함: 제목 1줄 + 설명 2-3줄

응답 형식 (JSON):
{
  "action_type": "subsidy|event|coupon|competitor|population",
  "title": "손실 프레이밍 제목 (30자 이내)",
  "description": "구체적 행동 설명 (100자 이내)",
  "cta_type": "create_coupon|apply_subsidy|view_detail",
  "data_source": "데이터 출처"
}
주의: risk_score는 별도 알고리즘이 산출합니다. 생성하지 마세요."""

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


class ActionGenerator:
    def __init__(self):
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_daily_action(
        self,
        user: User,
        sales_data: Optional[dict] = None,
        population_data: Optional[dict] = None,
        events_data: Optional[list] = None,
        subsidy_data: Optional[list] = None,
        competition_data: Optional[dict] = None,
        risk_result: Optional[dict] = None,
        recent_actions: Optional[list] = None,
        audit_weakness: Optional[str] = None,
    ) -> dict:
        """GPT-4o로 오늘의 액션 생성. 실패 시 폴백 템플릿 사용."""
        today = date.today()
        weekday = WEEKDAY_KR[today.weekday()]

        # 데이터 요약
        sales_summary = "데이터 없음 (서울 외 지역)"
        if sales_data:
            change = sales_data.get("quarterly_change_percent", 0)
            sales_summary = f"전분기 대비 {change:+.1f}% ({sales_data.get('area_name', '')})"

        pop_summary = "데이터 없음 (서울 외 지역)"
        if population_data:
            change = population_data.get("change_percent", 0)
            pop_summary = f"전일 대비 {change:+.1f}%"

        events_summary = "없음"
        if events_data:
            titles = [e.get("title", "") for e in events_data[:3]]
            events_summary = ", ".join(titles)

        subsidy_summary = "매칭 없음"
        if subsidy_data:
            titles = [s.get("title", "") for s in subsidy_data[:3]]
            amounts = sum(s.get("max_amount", 0) for s in subsidy_data if s.get("max_amount"))
            subsidy_summary = f"{len(subsidy_data)}건 매칭 (최대 {amounts}만원): {', '.join(titles)}"

        competition_summary = "데이터 없음"
        if competition_data:
            total = competition_data.get("total_stores", 0)
            opening = competition_data.get("opening_rate", 0)
            closing = competition_data.get("closing_rate", 0)
            competition_summary = f"같은 업종 점포 {total}개, 개업률 {opening}% / 폐업률 {closing}%"

        # 위험도 분석 컨텍스트
        risk_context = ""
        if risk_result:
            factors = risk_result.get("factors", [])
            score = risk_result.get("composite_score", 0)
            trend = risk_result.get("trend_direction", "stable")
            trend_kr = {"improving": "개선 추세", "stable": "유지", "worsening": "악화 추세"}.get(trend, "유지")
            risk_lines = [f"종합: {score:.0%} ({trend_kr})"]
            for f in factors:
                if f.get("data_available"):
                    risk_lines.append(f"- {f['label']}: {f['score']:.0%} ({f['description']})")
            risk_context = f"\n## 경영 위험도 분석 (알고리즘 산출)\n" + "\n".join(risk_lines)

        # 5-차원 진단 약점 (지정 시 손실 프레이밍을 해당 차원으로 집중)
        audit_context = ""
        if audit_weakness:
            audit_context = f"\n## 5-차원 진단 약점 (이 영역을 우선 다루세요)\n{audit_weakness}"

        # 최근 액션 히스토리 (반복 방지)
        history_context = ""
        if recent_actions:
            history_lines = []
            for a in recent_actions[-7:]:
                status = "완료" if a.get("is_completed") else "미완료"
                history_lines.append(f"- {a.get('action_type', '?')}: {a.get('title', '')} ({status})")
            history_context = f"\n## 최근 7일 액션\n" + "\n".join(history_lines)
            history_context += "\n주의: 같은 유형의 액션을 연속 반복하지 마세요."

        user_prompt = f"""## 사장님 정보
상호: {user.business_name or '미등록'}
업종: {user.business_type or '미등록'}
위치: {user.gu_name or ''} {user.dong_name or ''}

## 오늘 데이터
날짜: {today} ({weekday}요일)
매출 트렌드: {sales_summary}
유동인구: {pop_summary}
경쟁 현황: {competition_summary}
문화행사: {events_summary}
매칭 지원사업: {subsidy_summary}
{risk_context}
{audit_context}
{history_context}

## 지시사항
위 데이터에서 가장 위험한 요인에 초점을 맞춰, 놓치면 안 될 행동 1가지를 JSON으로 생성하세요.
5-차원 진단 약점이 제공된 경우 그 영역을 우선 다루세요.
데이터 없는 항목은 무시하세요."""

        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=512,
                temperature=settings.openai_temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            data["is_fallback"] = False
            return data
        except Exception as e:
            logger.error(f"GPT-4o daily action failed: {e}")
            return self._fallback_action(subsidy_data, population_data, events_data)

    def _fallback_action(
        self,
        subsidy_data: Optional[list],
        population_data: Optional[dict],
        events_data: Optional[list],
    ) -> dict:
        """GPT 실패 시 결정론적 폴백."""
        # 모든 fallback에 is_fallback=True flag 명시 (P0-12 / P1-5)
        if subsidy_data:
            s = subsidy_data[0]
            amount = s.get("max_amount", 0)
            return {
                "is_fallback": True,
                "fallback_reason": "GPT API unavailable, using deterministic subsidy match",
                "action_type": "subsidy",
                "title": f"지원금 {amount}만원 마감 임박, 놓치지 마세요",
                "description": f"{s.get('title', '지원사업')} 신청 가능합니다. 지금 확인하세요.",
                "risk_score": 0.7,
                "cta_type": "apply_subsidy",
                "data_source": "보조금 매칭",
            }

        if population_data and population_data.get("change_percent", 0) > 10:
            change = population_data["change_percent"]
            return {
                "is_fallback": True,
                "fallback_reason": "GPT API unavailable, using population threshold rule",
                "action_type": "population",
                "title": f"유동인구 {change}%↑ 놓치지 마세요",
                "description": "오늘 유동인구가 급증합니다. 이벤트 쿠폰으로 고객을 잡으세요.",
                "risk_score": 0.5,
                "cta_type": "create_coupon",
                "data_source": "서울시 생활인구",
            }

        return {
            "is_fallback": True,
            "fallback_reason": "GPT API unavailable + no actionable data",
            "action_type": "coupon",
            "title": "이번 주 이벤트 없이 지나가고 있어요",
            "description": "QR 쿠폰 이벤트로 매출 기회를 만들어보세요.",
            "risk_score": 0.3,
            "cta_type": "create_coupon",
            "data_source": "기본 권유",
        }

    async def create_initial_action(
        self,
        db: AsyncSession,
        user: User,
        matched_subsidies: list,
        sales_data: Optional[dict],
        population_data: Optional[dict],
        events_data: Optional[list],
    ) -> DailyAction:
        """온보딩 완료 후 첫 daily_action 생성."""
        from app.services.risk_score_engine import RiskScoreEngine

        action_data = await self.generate_daily_action(
            user=user,
            sales_data=sales_data,
            population_data=population_data,
            events_data=events_data,
            subsidy_data=matched_subsidies,
        )

        # 복합 위험도 엔진으로 risk_score 산출 (GPT 대신)
        engine = RiskScoreEngine()
        risk_result = engine.compute(
            sales_data=sales_data,
            population_data=population_data,
            subsidy_matches=matched_subsidies,
            user_created_at=user.created_at.date() if user.created_at else None,
        )

        # ON CONFLICT DO NOTHING으로 race condition 방지
        values = dict(
            user_id=user.id,
            date=date.today(),
            action_type=action_data.get("action_type", "coupon"),
            title=action_data.get("title", "오늘의 액션을 확인하세요"),
            description=action_data.get("description", ""),
            risk_score=risk_result.composite_score,
            risk_factors=risk_result.to_dict(),
            data_source=action_data.get("data_source"),
            cta_type=action_data.get("cta_type"),
            cta_payload=action_data.get("cta_payload"),
        )
        stmt = pg_insert(DailyAction).values(**values).on_conflict_do_nothing(
            constraint="uq_daily_actions_user_date"
        ).returning(DailyAction)
        result = await db.execute(stmt)
        daily_action = result.scalar_one_or_none()
        if daily_action is None:
            # 이미 존재하는 경우 기존 것 조회
            from sqlalchemy import select
            existing = await db.execute(
                select(DailyAction).where(
                    DailyAction.user_id == user.id,
                    DailyAction.date == date.today(),
                )
            )
            daily_action = existing.scalar_one()
        return daily_action

    async def generate_business_plan_draft(
        self,
        user: User,
        subsidy,
        additional_info: Optional[str] = None,
    ) -> str:
        """지원사업 사업계획서 초안 생성 — 전문 컨설턴트 수준."""
        system_prompt = """당신은 소상공인 지원사업 사업계획서 전문 작성가입니다.
사장님의 사업 정보와 지원사업 요건을 바탕으로 사업계획서 초안을 작성합니다.

## 작성 원칙
1. 지원사업의 **심사 기준에 맞춰** 작성합니다 (정량 지표, 구체적 수치 포함).
2. 사장님의 **실제 사업 정보만** 사용합니다. 없는 정보를 만들어내지 마세요.
3. 비워야 할 칸은 **[사장님 작성 필요]** 로 표시합니다.
4. **마크다운** 형식으로 작성합니다.
5. 한국어, 존댓말로 작성합니다.
6. 지원금 활용 계획은 **구체적 항목과 예상 금액**을 포함합니다.
7. 기대 효과는 **정량적 수치**(매출 증가율, 고객 수 등)를 포함합니다.

## 필수 구조
1. **사업 개요** — 상호, 업종, 위치, 대표자, 사업 연혁
2. **현재 경영 현황** — 매출 동향, 고객 특성, 경쟁 환경 (제공된 데이터 활용)
3. **지원사업 활용 계획** — 지원금 사용처, 세부 항목별 예산, 추진 일정
4. **기대 효과** — 매출 개선 목표, 고용 효과, 지역 경제 기여
5. **사업 추진 일정** — 월별 마일스톤 (3~6개월)
6. **자부담 계획** — 자부담 비율 및 조달 방법"""

        # 사업자번호 PII 마스킹 (외부 LLM에 전송 시)
        masked_biz_num = f"{user.business_number[:3]}-**-*****" if user.business_number else "[사장님 작성 필요]"

        user_prompt = f"""## 사장님 정보
- 상호: {user.business_name or '[사장님 작성 필요]'}
- 업종: {user.business_type or '[사장님 작성 필요]'}
- 위치: {user.address or '[사장님 작성 필요]'}
- 사업자번호: {masked_biz_num}
- 지역: {user.gu_name or ''} {user.dong_name or ''}

## 지원사업 정보
- 사업명: {subsidy.title}
- 지원기관: {subsidy.organization}
- 최대 지원금: {subsidy.max_amount or '미정'}만원
- 자격 요건: {subsidy.eligibility_summary or '상세 내용 확인 필요'}
- 사업 설명: {subsidy.description[:800]}

## 추가 정보
{additional_info or '없음'}

위 정보를 바탕으로 사업계획서 초안을 마크다운으로 작성하세요.
사장님이 직접 수정해야 할 부분은 [사장님 작성 필요]로 표시하세요.
지원금 활용 계획에는 구체적인 항목과 예상 금액을 반드시 포함하세요."""

        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=3000,
                temperature=0.5,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Business plan draft failed: {e}")
            return f"""# {subsidy.title} 사업계획서 초안

## 1. 사업 개요
- 상호명: {user.business_name or '[작성 필요]'}
- 업종: {user.business_type or '[작성 필요]'}
- 소재지: {user.address or '[작성 필요]'}
- 사업자등록번호: {masked_biz_num}

## 2. 현재 경영 현황
[사장님 작성 필요 — 최근 매출 동향, 주요 고객층, 경쟁 환경]

## 3. 지원사업 활용 계획
- 지원금 사용처: [사장님 작성 필요]
- 세부 예산: [사장님 작성 필요]

## 4. 기대 효과
- 매출 목표: [사장님 작성 필요]
- 고용 효과: [사장님 작성 필요]

## 5. 사업 추진 일정
- 1개월차: [사장님 작성 필요]
- 2개월차: [사장님 작성 필요]
- 3개월차: [사장님 작성 필요]

*AI가 초안 생성에 실패하여 기본 템플릿을 제공합니다.*"""

    async def process_voice_query(
        self,
        user: User,
        query_text: str,
        intent: str,
        context_docs: list,
    ) -> str:
        """음성 질의 처리."""
        system_prompt = f"""당신은 소상공인 AI 경영코치입니다. 음성 질의에 친절하게 답변합니다.

응답 원칙:
1. 존댓말, 3문장 이내
2. 구체적 행동 제안 포함
3. '놓치고 있습니다' 톤
4. 제공된 컨텍스트만 사용

사장님 정보:
상호: {user.business_name}
위치: {user.gu_name} {user.dong_name}"""

        context_str = ""
        if context_docs:
            context_str = "\n".join(
                f"- {doc.get('title', '')}: {doc.get('description', '')[:100]}"
                for doc in context_docs[:3]
            )

        user_prompt = f"""## 질문
'{query_text}'

## 감지된 의도
{intent}

## 관련 데이터
{context_str or '관련 데이터 없음'}"""

        try:
            response = await self._openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=256,
                temperature=settings.openai_temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Voice query failed: {e}")
            return "죄송합니다, 잠시 후 다시 시도해주세요."

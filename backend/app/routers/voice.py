"""
음성 질의 라우터
- POST /voice/query: STT 텍스트 → GPT-4o 응답
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.auth import get_current_user
from app.models import User
from app.services.action_generator import ActionGenerator
from app.services.rag_service import RAGService

router = APIRouter()


class VoiceQueryRequest(BaseModel):
    text: str


class VoiceQueryResponse(BaseModel):
    answer: str
    intent: str
    suggestions: list[str]


@router.post("/query", response_model=VoiceQueryResponse)
async def process_voice_query(
    req: VoiceQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """음성(STT) 텍스트를 GPT-4o로 처리하여 응답."""
    generator = ActionGenerator()

    # 의도 분류
    text_lower = req.text.lower()
    if any(kw in text_lower for kw in ["지원금", "보조금", "지원사업", "돈"]):
        intent = "subsidy"
    elif any(kw in text_lower for kw in ["쿠폰", "이벤트", "할인"]):
        intent = "coupon"
    elif any(kw in text_lower for kw in ["매출", "매출분석", "실적"]):
        intent = "sales"
    elif any(kw in text_lower for kw in ["행사", "축제", "공연"]):
        intent = "event"
    else:
        intent = "general"

    # RAG 컨텍스트
    rag = RAGService()
    context_docs = []
    if intent == "subsidy":
        context_docs = await rag.search_subsidies(
            f"{current_user.dong_name} {current_user.business_type} {req.text}", top_k=3
        )

    # GPT-4o 응답
    answer = await generator.process_voice_query(
        user=current_user,
        query_text=req.text,
        intent=intent,
        context_docs=context_docs,
    )

    suggestions_map = {
        "subsidy": ["지원금 마감일 알려줘", "사업계획서 써줘", "다른 지원사업도 있어?"],
        "coupon": ["QR 쿠폰 만들어줘", "지난 쿠폰 실적 보여줘", "이벤트 문구 추천해줘"],
        "sales": ["매출 올리는 방법 알려줘", "경쟁 가게 분석해줘", "이번 주 유동인구는?"],
        "event": ["이벤트 쿠폰 만들어줘", "행사 연계 이벤트 추천해줘", "행사 일정 알려줘"],
        "general": ["지원금 찾아줘", "오늘 뭐 해야 돼?", "매출 분석해줘"],
    }

    return VoiceQueryResponse(
        answer=answer,
        intent=intent,
        suggestions=suggestions_map.get(intent, suggestions_map["general"]),
    )

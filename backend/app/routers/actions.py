"""
일일 액션 라우터
- GET  /actions/today: 오늘의 액션
- GET  /actions/history: 최근 액션 히스토리
- POST /actions/{id}/complete: 액션 완료 처리
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta, datetime
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.daily_action import DailyActionResponse, CompleteActionResponse
from app.utils.auth import get_current_user
from app.models import User, DailyAction

router = APIRouter()


@router.get("/today", response_model=DailyActionResponse)
async def get_today_action(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """오늘의 액션 조회."""
    stmt = select(DailyAction).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date == date.today(),
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="오늘의 액션이 아직 준비되지 않았습니다.")

    return DailyActionResponse.model_validate(action)


@router.get("/history", response_model=List[DailyActionResponse])
async def get_action_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """최근 N일간 액션 히스토리."""
    stmt = (
        select(DailyAction)
        .where(
            DailyAction.user_id == current_user.id,
            DailyAction.date >= date.today() - timedelta(days=days),
        )
        .order_by(DailyAction.date.desc())
    )
    result = await db.execute(stmt)
    actions = result.scalars().all()
    return [DailyActionResponse.model_validate(a) for a in actions]


@router.post("/{action_id}/complete", response_model=CompleteActionResponse)
async def complete_action(
    action_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """액션 완료 처리."""
    stmt = select(DailyAction).where(
        DailyAction.id == action_id,
        DailyAction.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="액션을 찾을 수 없습니다.")
    if action.is_completed:
        raise HTTPException(status_code=400, detail="이미 완료된 액션입니다.")

    action.is_completed = True
    action.completed_at = datetime.utcnow()

    return CompleteActionResponse(
        success=True, message="잘하셨어요, 사장님! 오늘의 액션을 완료했습니다."
    )

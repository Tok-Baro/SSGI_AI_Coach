from pydantic import BaseModel
from typing import Optional, Any
from datetime import date, datetime
from uuid import UUID


class DailyActionResponse(BaseModel):
    id: UUID
    date: date
    action_type: str
    title: str
    description: str
    risk_score: float
    data_source: Optional[str] = None
    cta_type: Optional[str] = None
    cta_payload: Optional[dict] = None
    is_completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompleteActionRequest(BaseModel):
    pass


class CompleteActionResponse(BaseModel):
    success: bool
    message: str

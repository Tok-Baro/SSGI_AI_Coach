from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID


class SubsidyResponse(BaseModel):
    id: UUID
    title: str
    organization: str
    deadline: Optional[date] = None
    max_amount: Optional[int] = None
    eligibility_summary: Optional[str] = None
    description: str
    application_url: Optional[str] = None
    relevance_score: Optional[float] = None
    days_until_deadline: Optional[int] = None
    social_proof_message: Optional[str] = None

    class Config:
        from_attributes = True


class SubsidyMatchesResponse(BaseModel):
    matches: List[SubsidyResponse]
    total_potential_amount: int = 0
    loss_message: str


class ApplyDraftRequest(BaseModel):
    subsidy_id: UUID
    additional_info: Optional[str] = None


class ApplyDraftResponse(BaseModel):
    draft_text: str
    subsidy_title: str
    estimated_time_saved: str = "약 2시간"

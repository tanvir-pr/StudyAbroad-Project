from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    country: str | None = Field(
        default=None, description="Optional ISO country code filter, e.g. HU"
    )
    limit_per_band: int = Field(default=20, ge=1, le=50)


class MatchItemOut(BaseModel):
    program_id: UUID
    program_name: str
    university_name: str
    city_name: str
    country_code: str
    degree: str
    language: str
    tuition_eur: Decimal
    intake_deadline: date
    scholarship: bool
    score: float
    band: str
    reasons: list[str]
    estimated_year_cost_eur: Decimal


class MatchResponse(BaseModel):
    safe: list[MatchItemOut]
    target: list[MatchItemOut]
    reach: list[MatchItemOut]
    total_considered: int
    total_matched: int

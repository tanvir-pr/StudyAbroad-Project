from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentProfileBase(BaseModel):
    cgpa: Decimal = Field(ge=0, le=4)
    ielts: Decimal | None = Field(default=None, ge=0, le=9)
    budget_eur: Decimal = Field(ge=0)
    subject: str = Field(min_length=1, max_length=120)
    target_degree: str = Field(min_length=1, max_length=30)
    target_intake: str = Field(min_length=1, max_length=40)
    current_country: str = Field(min_length=1, max_length=100)
    bank_balance_eur: Decimal = Field(default=Decimal("0"), ge=0)
    study_gap_years: int = Field(default=0, ge=0)
    gap_explained: bool = False
    prior_rejection: bool = False


class StudentProfileCreate(StudentProfileBase):
    pass


class StudentProfileUpdate(BaseModel):
    cgpa: Decimal | None = Field(default=None, ge=0, le=4)
    ielts: Decimal | None = Field(default=None, ge=0, le=9)
    budget_eur: Decimal | None = Field(default=None, ge=0)
    subject: str | None = Field(default=None, min_length=1, max_length=120)
    target_degree: str | None = Field(default=None, min_length=1, max_length=30)
    target_intake: str | None = Field(default=None, min_length=1, max_length=40)
    current_country: str | None = Field(default=None, min_length=1, max_length=100)
    bank_balance_eur: Decimal | None = Field(default=None, ge=0)
    study_gap_years: int | None = Field(default=None, ge=0)
    gap_explained: bool | None = None
    prior_rejection: bool | None = None


class StudentProfileOut(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class MentorProfileBase(BaseModel):
    university_id: UUID
    program: str = Field(min_length=1, max_length=200)
    hourly_rate: Decimal = Field(ge=0)


class MentorProfileCreate(MentorProfileBase):
    pass


class MentorProfileUpdate(BaseModel):
    university_id: UUID | None = None
    program: str | None = Field(default=None, min_length=1, max_length=200)
    hourly_rate: Decimal | None = Field(default=None, ge=0)


class MentorProfileOut(MentorProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    verified: bool
    created_at: datetime
    updated_at: datetime
    university_name: str | None = None


class ResidencePermitBase(BaseModel):
    country_id: UUID
    permit_type: str = Field(min_length=1, max_length=80)
    expiry_date: date


class ResidencePermitCreate(ResidencePermitBase):
    pass


class ResidencePermitUpdate(BaseModel):
    permit_type: str | None = Field(default=None, min_length=1, max_length=80)
    expiry_date: date | None = None


class ResidencePermitOut(ResidencePermitBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    country_code: str | None = None
    country_name: str | None = None

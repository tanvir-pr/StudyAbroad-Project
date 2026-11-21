from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CountryBase(BaseModel):
    code: str = Field(min_length=2, max_length=2)
    name: str = Field(min_length=1, max_length=100)
    work_hours_limit: int = Field(ge=0)
    work_hours_limit_holiday: int = Field(ge=0)
    limit_period: str = Field(default="week", max_length=20)
    post_study_visa_months: int = Field(ge=0)
    required_funds_eur: Decimal = Field(ge=0)
    avg_living_cost: Decimal = Field(ge=0)


class CountryCreate(CountryBase):
    pass


class CountryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    work_hours_limit: int | None = Field(default=None, ge=0)
    work_hours_limit_holiday: int | None = Field(default=None, ge=0)
    limit_period: str | None = Field(default=None, max_length=20)
    post_study_visa_months: int | None = Field(default=None, ge=0)
    required_funds_eur: Decimal | None = Field(default=None, ge=0)
    avg_living_cost: Decimal | None = Field(default=None, ge=0)


class CountryOut(CountryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class CityBase(BaseModel):
    country_id: UUID
    name: str = Field(min_length=1, max_length=120)
    rent_avg: Decimal = Field(ge=0)
    food_avg: Decimal = Field(ge=0)
    transport_avg: Decimal = Field(ge=0)


class CityCreate(CityBase):
    pass


class CityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    rent_avg: Decimal | None = Field(default=None, ge=0)
    food_avg: Decimal | None = Field(default=None, ge=0)
    transport_avg: Decimal | None = Field(default=None, ge=0)


class CityOut(CityBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class UniversityBase(BaseModel):
    city_id: UUID
    name: str = Field(min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    admission_email: EmailStr | None = None


class UniversityCreate(UniversityBase):
    pass


class UniversityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    admission_email: EmailStr | None = None


class UniversityOut(UniversityBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ProgramCourseBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    semester: int = Field(ge=1)
    credits: Decimal = Field(gt=0)
    description: str | None = None


class ProgramCourseOut(ProgramCourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    program_id: UUID


class ProgramBase(BaseModel):
    university_id: UUID
    name: str = Field(min_length=1, max_length=200)
    degree: str = Field(min_length=1, max_length=30)
    language: str = Field(min_length=1, max_length=40)
    tuition_eur: Decimal = Field(ge=0)
    min_cgpa: Decimal = Field(ge=0, le=4)
    min_ielts: Decimal = Field(ge=0, le=9)
    intake_deadline: date
    scholarship: bool = False


class ProgramCreate(ProgramBase):
    courses: list[ProgramCourseBase] = Field(default_factory=list)


class ProgramUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    degree: str | None = Field(default=None, min_length=1, max_length=30)
    language: str | None = Field(default=None, min_length=1, max_length=40)
    tuition_eur: Decimal | None = Field(default=None, ge=0)
    min_cgpa: Decimal | None = Field(default=None, ge=0, le=4)
    min_ielts: Decimal | None = Field(default=None, ge=0, le=9)
    intake_deadline: date | None = None
    scholarship: bool | None = None


class ProgramOut(ProgramBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    courses: list[ProgramCourseOut] = Field(default_factory=list)
    country_code: str | None = None
    country_name: str | None = None
    city_name: str | None = None
    university_name: str | None = None


class ProgramCompareItem(BaseModel):
    id: UUID
    name: str
    degree: str
    language: str
    tuition_eur: Decimal
    min_cgpa: Decimal
    min_ielts: Decimal
    intake_deadline: date
    scholarship: bool
    university_name: str
    city_name: str
    country_code: str
    courses: list[ProgramCourseOut]


class DocumentTemplateBase(BaseModel):
    country_id: UUID
    degree: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    is_required: bool = True
    lead_days: int = Field(default=0, ge=0)
    needs_attestation: bool = False


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_required: bool | None = None
    lead_days: int | None = Field(default=None, ge=0)
    needs_attestation: bool | None = None


class DocumentTemplateOut(DocumentTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

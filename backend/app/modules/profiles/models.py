import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import BaseModel


class StudentProfile(BaseModel):
    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
        CheckConstraint("cgpa >= 0 AND cgpa <= 4", name="student_cgpa_range"),
        CheckConstraint(
            "ielts IS NULL OR (ielts >= 0 AND ielts <= 9)", name="student_ielts_range"
        ),
        CheckConstraint("budget_eur >= 0", name="student_budget_nonneg"),
        CheckConstraint("bank_balance_eur >= 0", name="student_bank_nonneg"),
        CheckConstraint("study_gap_years >= 0", name="student_gap_nonneg"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cgpa: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    ielts: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    budget_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subject: Mapped[str] = mapped_column(String(120), nullable=False)
    target_degree: Mapped[str] = mapped_column(String(30), nullable=False)
    target_intake: Mapped[str] = mapped_column(String(40), nullable=False)
    current_country: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_balance_eur: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    study_gap_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gap_explained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prior_rejection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class MentorProfile(BaseModel):
    __tablename__ = "mentor_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mentor_profiles_user_id"),
        CheckConstraint("hourly_rate >= 0", name="mentor_rate_nonneg"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    university_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    program: Mapped[str] = mapped_column(String(200), nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    university = relationship("University", lazy="selectin")


class ResidencePermit(BaseModel):
    __tablename__ = "residence_permits"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "country_id", "permit_type", name="uq_residence_permits_user_country_type"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    country_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    permit_type: Mapped[str] = mapped_column(String(80), nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)

    country = relationship("Country", lazy="selectin")

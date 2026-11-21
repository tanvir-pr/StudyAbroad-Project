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
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import BaseModel, SoftDeleteModel


class Country(SoftDeleteModel):
    __tablename__ = "countries"
    __table_args__ = (
        CheckConstraint("work_hours_limit >= 0", name="work_hours_limit_nonneg"),
        CheckConstraint(
            "work_hours_limit_holiday >= 0", name="work_hours_limit_holiday_nonneg"
        ),
        CheckConstraint("post_study_visa_months >= 0", name="post_study_visa_nonneg"),
        CheckConstraint("required_funds_eur >= 0", name="required_funds_nonneg"),
    )

    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    work_hours_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    work_hours_limit_holiday: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_period: Mapped[str] = mapped_column(String(20), nullable=False, default="week")
    post_study_visa_months: Mapped[int] = mapped_column(Integer, nullable=False)
    required_funds_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    avg_living_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    cities: Mapped[list["City"]] = relationship(back_populates="country")


class City(SoftDeleteModel):
    __tablename__ = "cities"
    __table_args__ = (
        UniqueConstraint("country_id", "name", name="uq_cities_country_id_name"),
        CheckConstraint("rent_avg >= 0", name="rent_avg_nonneg"),
        CheckConstraint("food_avg >= 0", name="food_avg_nonneg"),
        CheckConstraint("transport_avg >= 0", name="transport_avg_nonneg"),
    )

    country_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    rent_avg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    food_avg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transport_avg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    country: Mapped[Country] = relationship(back_populates="cities")
    universities: Mapped[list["University"]] = relationship(back_populates="city")


class University(SoftDeleteModel):
    __tablename__ = "universities"
    __table_args__ = (
        UniqueConstraint("city_id", "name", name="uq_universities_city_id_name"),
    )

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    admission_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    city: Mapped[City] = relationship(back_populates="universities")
    programs: Mapped[list["Program"]] = relationship(back_populates="university")


class Program(SoftDeleteModel):
    __tablename__ = "programs"
    __table_args__ = (
        CheckConstraint("tuition_eur >= 0", name="tuition_eur_nonneg"),
        CheckConstraint("min_cgpa >= 0 AND min_cgpa <= 4", name="min_cgpa_range"),
        CheckConstraint("min_ielts >= 0 AND min_ielts <= 9", name="min_ielts_range"),
    )

    university_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    degree: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    tuition_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_cgpa: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    min_ielts: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    intake_deadline: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scholarship: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    university: Mapped[University] = relationship(back_populates="programs")
    courses: Mapped[list["ProgramCourse"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
    )


class ProgramCourse(BaseModel):
    __tablename__ = "program_courses"
    __table_args__ = (
        UniqueConstraint(
            "program_id", "name", "semester", name="uq_program_courses_prog_name_sem"
        ),
        CheckConstraint("credits > 0", name="credits_positive"),
        CheckConstraint("semester >= 1", name="semester_positive"),
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    credits: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    program: Mapped[Program] = relationship(back_populates="courses")


class DocumentTemplate(SoftDeleteModel):
    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint(
            "country_id",
            "degree",
            "name",
            name="uq_document_templates_country_degree_name",
        ),
        CheckConstraint("lead_days >= 0", name="lead_days_nonneg"),
    )

    country_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    degree: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    lead_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    needs_attestation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    country: Mapped[Country] = relationship()

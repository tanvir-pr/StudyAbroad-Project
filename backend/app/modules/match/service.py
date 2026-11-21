from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import NotFound
from app.core.models import SoftDeleteModel
from app.modules.auth.models import User
from app.modules.catalog.models import City, Country, Program, University
from app.modules.match.engine import (
    MatchWeights,
    ProgramMatchInput,
    StudentMatchInput,
    match_programs,
)
from app.modules.match.schemas import MatchItemOut, MatchRequest, MatchResponse
from app.modules.profiles.repository import ProfileRepository


def _not_deleted(model: type[SoftDeleteModel]):
    return model.deleted_at.is_(None)


class MatchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profiles = ProfileRepository(session)

    async def match_for_user(
        self, user: User, payload: MatchRequest
    ) -> MatchResponse:
        profile = await self.profiles.get_student_by_user_id(user.id)
        if profile is None:
            raise NotFound("Student profile not found")

        settings = get_settings()
        weights = MatchWeights(
            cgpa=settings.match_weight_cgpa,
            ielts=settings.match_weight_ielts,
            budget=settings.match_weight_budget,
            deadline=settings.match_weight_deadline,
            safe_threshold=settings.match_safe_threshold,
            target_threshold=settings.match_target_threshold,
            deadline_full_days=settings.match_deadline_full_days,
            cgpa_full_margin=settings.match_cgpa_full_margin,
        )

        student = StudentMatchInput(
            cgpa=profile.cgpa,
            ielts=profile.ielts,
            budget_eur=profile.budget_eur,
            target_degree=profile.target_degree,
            subject=profile.subject,
        )

        programs, considered = await self._load_programs(country=payload.country)
        grouped = match_programs(
            student, programs, weights=weights, today=date.today()
        )

        def trim(items):
            return [
                MatchItemOut(
                    program_id=UUID(i.program_id),
                    program_name=i.program_name,
                    university_name=i.university_name,
                    city_name=i.city_name,
                    country_code=i.country_code,
                    degree=i.degree,
                    language=i.language,
                    tuition_eur=i.tuition_eur,
                    intake_deadline=i.intake_deadline,
                    scholarship=i.scholarship,
                    score=i.score,
                    band=i.band,
                    reasons=i.reasons,
                    estimated_year_cost_eur=i.estimated_year_cost_eur,
                )
                for i in items[: payload.limit_per_band]
            ]

        matched = (
            len(grouped["Safe"]) + len(grouped["Target"]) + len(grouped["Reach"])
        )
        return MatchResponse(
            safe=trim(grouped["Safe"]),
            target=trim(grouped["Target"]),
            reach=trim(grouped["Reach"]),
            total_considered=considered,
            total_matched=matched,
        )

    async def _load_programs(
        self, *, country: str | None
    ) -> tuple[list[ProgramMatchInput], int]:
        stmt = (
            select(Program)
            .join(University, Program.university_id == University.id)
            .join(City, University.city_id == City.id)
            .join(Country, City.country_id == Country.id)
            .where(
                _not_deleted(Program),
                _not_deleted(University),
                _not_deleted(City),
                _not_deleted(Country),
            )
            .options(
                selectinload(Program.university)
                .selectinload(University.city)
                .selectinload(City.country)
            )
        )
        if country:
            stmt = stmt.where(Country.code == country.upper())

        rows = list(
            (await self.session.execute(stmt)).scalars().unique().all()
        )
        inputs: list[ProgramMatchInput] = []
        for p in rows:
            city = p.university.city
            country_obj = city.country
            monthly = city.rent_avg + city.food_avg + city.transport_avg
            inputs.append(
                ProgramMatchInput(
                    id=str(p.id),
                    name=p.name,
                    degree=p.degree,
                    language=p.language,
                    tuition_eur=p.tuition_eur,
                    min_cgpa=p.min_cgpa,
                    min_ielts=p.min_ielts,
                    intake_deadline=p.intake_deadline,
                    scholarship=p.scholarship,
                    university_name=p.university.name,
                    city_name=city.name,
                    country_code=country_obj.code,
                    monthly_living_cost=Decimal(monthly),
                )
            )
        return inputs, len(inputs)

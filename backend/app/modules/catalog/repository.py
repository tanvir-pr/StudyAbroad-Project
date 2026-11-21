from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.models import (
    City,
    Country,
    DocumentTemplate,
    Program,
    ProgramCourse,
    University,
)


def _not_deleted(model):
    return model.deleted_at.is_(None)


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---- countries ----
    async def list_countries(self, *, limit: int, offset: int) -> tuple[list[Country], int]:
        base = select(Country).where(_not_deleted(Country))
        total = await self._count(base)
        rows = await self.session.execute(
            base.order_by(Country.name).limit(limit).offset(offset)
        )
        return list(rows.scalars().all()), total

    async def get_country(self, country_id: UUID) -> Country | None:
        result = await self.session.execute(
            select(Country).where(Country.id == country_id, _not_deleted(Country))
        )
        return result.scalar_one_or_none()

    async def get_country_by_code(self, code: str) -> Country | None:
        result = await self.session.execute(
            select(Country).where(Country.code == code.upper(), _not_deleted(Country))
        )
        return result.scalar_one_or_none()

    async def add_country(self, country: Country) -> Country:
        self.session.add(country)
        await self.session.flush()
        return country

    # ---- cities ----
    async def list_cities(
        self, *, country_id: UUID | None, limit: int, offset: int
    ) -> tuple[list[City], int]:
        base = select(City).where(_not_deleted(City))
        if country_id is not None:
            base = base.where(City.country_id == country_id)
        total = await self._count(base)
        rows = await self.session.execute(
            base.order_by(City.name).limit(limit).offset(offset)
        )
        return list(rows.scalars().all()), total

    async def get_city(self, city_id: UUID) -> City | None:
        result = await self.session.execute(
            select(City).where(City.id == city_id, _not_deleted(City))
        )
        return result.scalar_one_or_none()

    async def add_city(self, city: City) -> City:
        self.session.add(city)
        await self.session.flush()
        return city

    # ---- universities ----
    async def list_universities(
        self, *, city_id: UUID | None, limit: int, offset: int
    ) -> tuple[list[University], int]:
        base = select(University).where(_not_deleted(University))
        if city_id is not None:
            base = base.where(University.city_id == city_id)
        total = await self._count(base)
        rows = await self.session.execute(
            base.order_by(University.name).limit(limit).offset(offset)
        )
        return list(rows.scalars().all()), total

    async def get_university(self, university_id: UUID) -> University | None:
        result = await self.session.execute(
            select(University).where(
                University.id == university_id, _not_deleted(University)
            )
        )
        return result.scalar_one_or_none()

    async def add_university(self, university: University) -> University:
        self.session.add(university)
        await self.session.flush()
        return university

    # ---- programs ----
    def _program_base_query(self) -> Select:
        return (
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
                selectinload(Program.courses),
                selectinload(Program.university)
                .selectinload(University.city)
                .selectinload(City.country),
            )
        )

    async def list_programs(
        self,
        *,
        country: str | None,
        degree: str | None,
        max_tuition: Decimal | None,
        language: str | None,
        ielts: Decimal | None,
        deadline_before: date | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Program], int]:
        base = self._program_base_query()
        if country:
            base = base.where(Country.code == country.upper())
        if degree:
            base = base.where(func.lower(Program.degree) == degree.lower())
        if max_tuition is not None:
            base = base.where(Program.tuition_eur <= max_tuition)
        if language:
            base = base.where(func.lower(Program.language) == language.lower())
        if ielts is not None:
            base = base.where(Program.min_ielts <= ielts)
        if deadline_before is not None:
            base = base.where(Program.intake_deadline <= deadline_before)
        if q:
            pattern = f"%{q}%"
            base = base.where(
                or_(
                    Program.name.ilike(pattern),
                    University.name.ilike(pattern),
                )
            )

        total = await self._count(base)
        rows = await self.session.execute(
            base.order_by(Program.intake_deadline, Program.name)
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars().unique().all()), total

    async def get_program(self, program_id: UUID) -> Program | None:
        result = await self.session.execute(
            self._program_base_query().where(Program.id == program_id)
        )
        return result.scalars().unique().one_or_none()

    async def get_programs_by_ids(self, ids: list[UUID]) -> list[Program]:
        if not ids:
            return []
        result = await self.session.execute(
            self._program_base_query().where(Program.id.in_(ids))
        )
        found = {p.id: p for p in result.scalars().unique().all()}
        return [found[i] for i in ids if i in found]

    async def add_program(self, program: Program) -> Program:
        self.session.add(program)
        await self.session.flush()
        return await self.get_program(program.id)  # type: ignore[return-value]

    # ---- document templates ----
    async def list_document_templates(
        self,
        *,
        country_id: UUID | None,
        degree: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DocumentTemplate], int]:
        base = select(DocumentTemplate).where(_not_deleted(DocumentTemplate))
        if country_id is not None:
            base = base.where(DocumentTemplate.country_id == country_id)
        if degree:
            base = base.where(func.lower(DocumentTemplate.degree) == degree.lower())
        total = await self._count(base)
        rows = await self.session.execute(
            base.order_by(DocumentTemplate.name).limit(limit).offset(offset)
        )
        return list(rows.scalars().all()), total

    async def get_document_template(self, template_id: UUID) -> DocumentTemplate | None:
        result = await self.session.execute(
            select(DocumentTemplate).where(
                DocumentTemplate.id == template_id,
                _not_deleted(DocumentTemplate),
            )
        )
        return result.scalar_one_or_none()

    async def add_document_template(self, template: DocumentTemplate) -> DocumentTemplate:
        self.session.add(template)
        await self.session.flush()
        return template

    async def soft_delete(self, entity) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def _count(self, stmt: Select) -> int:
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        result = await self.session.execute(count_stmt)
        return int(result.scalar_one())

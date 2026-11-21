from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, NotFound
from app.core.pagination import Page
from app.modules.audit.service import write_audit
from app.modules.auth.models import User
from app.modules.catalog.models import (
    City,
    Country,
    DocumentTemplate,
    Program,
    ProgramCourse,
    University,
)
from app.modules.catalog.repository import CatalogRepository
from app.modules.catalog.schemas import (
    CityCreate,
    CityOut,
    CityUpdate,
    CountryCreate,
    CountryOut,
    CountryUpdate,
    DocumentTemplateCreate,
    DocumentTemplateOut,
    DocumentTemplateUpdate,
    ProgramCompareItem,
    ProgramCreate,
    ProgramOut,
    ProgramUpdate,
    UniversityCreate,
    UniversityOut,
    UniversityUpdate,
)


def _program_out(program: Program) -> ProgramOut:
    uni = program.university
    city = uni.city if uni else None
    country = city.country if city else None
    data = ProgramOut.model_validate(program)
    return data.model_copy(
        update={
            "university_name": uni.name if uni else None,
            "city_name": city.name if city else None,
            "country_code": country.code if country else None,
            "country_name": country.name if country else None,
        }
    )


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CatalogRepository(session)

    # ---- countries ----
    async def list_countries(self, *, limit: int, offset: int) -> Page[CountryOut]:
        rows, total = await self.repo.list_countries(limit=limit, offset=offset)
        return Page(
            items=[CountryOut.model_validate(r) for r in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_country(self, country_id: UUID) -> CountryOut:
        country = await self.repo.get_country(country_id)
        if country is None:
            raise NotFound("Country not found")
        return CountryOut.model_validate(country)

    async def create_country(self, payload: CountryCreate, actor: User) -> CountryOut:
        if await self.repo.get_country_by_code(payload.code):
            raise Conflict("Country code already exists")
        country = Country(**payload.model_dump())
        country.code = country.code.upper()
        await self.repo.add_country(country)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="create",
            entity_type="country",
            entity_id=str(country.id),
            payload=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return CountryOut.model_validate(country)

    async def update_country(
        self, country_id: UUID, payload: CountryUpdate, actor: User
    ) -> CountryOut:
        country = await self.repo.get_country(country_id)
        if country is None:
            raise NotFound("Country not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(country, key, value)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="update",
            entity_type="country",
            entity_id=str(country.id),
            payload=payload.model_dump(mode="json", exclude_unset=True),
        )
        await self.session.commit()
        return CountryOut.model_validate(country)

    async def delete_country(self, country_id: UUID, actor: User) -> None:
        country = await self.repo.get_country(country_id)
        if country is None:
            raise NotFound("Country not found")
        await self.repo.soft_delete(country)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="delete",
            entity_type="country",
            entity_id=str(country.id),
        )
        await self.session.commit()

    # ---- cities ----
    async def list_cities(
        self, *, country_id: UUID | None, limit: int, offset: int
    ) -> Page[CityOut]:
        rows, total = await self.repo.list_cities(
            country_id=country_id, limit=limit, offset=offset
        )
        return Page(
            items=[CityOut.model_validate(r) for r in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_city(self, city_id: UUID) -> CityOut:
        city = await self.repo.get_city(city_id)
        if city is None:
            raise NotFound("City not found")
        return CityOut.model_validate(city)

    async def create_city(self, payload: CityCreate, actor: User) -> CityOut:
        if await self.repo.get_country(payload.country_id) is None:
            raise NotFound("Country not found")
        city = City(**payload.model_dump())
        await self.repo.add_city(city)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="create",
            entity_type="city",
            entity_id=str(city.id),
            payload=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return CityOut.model_validate(city)

    async def update_city(
        self, city_id: UUID, payload: CityUpdate, actor: User
    ) -> CityOut:
        city = await self.repo.get_city(city_id)
        if city is None:
            raise NotFound("City not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(city, key, value)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="update",
            entity_type="city",
            entity_id=str(city.id),
            payload=payload.model_dump(mode="json", exclude_unset=True),
        )
        await self.session.commit()
        return CityOut.model_validate(city)

    async def delete_city(self, city_id: UUID, actor: User) -> None:
        city = await self.repo.get_city(city_id)
        if city is None:
            raise NotFound("City not found")
        await self.repo.soft_delete(city)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="delete",
            entity_type="city",
            entity_id=str(city.id),
        )
        await self.session.commit()

    # ---- universities ----
    async def list_universities(
        self, *, city_id: UUID | None, limit: int, offset: int
    ) -> Page[UniversityOut]:
        rows, total = await self.repo.list_universities(
            city_id=city_id, limit=limit, offset=offset
        )
        return Page(
            items=[UniversityOut.model_validate(r) for r in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_university(self, university_id: UUID) -> UniversityOut:
        university = await self.repo.get_university(university_id)
        if university is None:
            raise NotFound("University not found")
        return UniversityOut.model_validate(university)

    async def create_university(
        self, payload: UniversityCreate, actor: User
    ) -> UniversityOut:
        if await self.repo.get_city(payload.city_id) is None:
            raise NotFound("City not found")
        university = University(**payload.model_dump())
        await self.repo.add_university(university)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="create",
            entity_type="university",
            entity_id=str(university.id),
            payload=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return UniversityOut.model_validate(university)

    async def update_university(
        self, university_id: UUID, payload: UniversityUpdate, actor: User
    ) -> UniversityOut:
        university = await self.repo.get_university(university_id)
        if university is None:
            raise NotFound("University not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(university, key, value)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="update",
            entity_type="university",
            entity_id=str(university.id),
            payload=payload.model_dump(mode="json", exclude_unset=True),
        )
        await self.session.commit()
        return UniversityOut.model_validate(university)

    async def delete_university(self, university_id: UUID, actor: User) -> None:
        university = await self.repo.get_university(university_id)
        if university is None:
            raise NotFound("University not found")
        await self.repo.soft_delete(university)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="delete",
            entity_type="university",
            entity_id=str(university.id),
        )
        await self.session.commit()

    # ---- programs ----
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
    ) -> Page[ProgramOut]:
        rows, total = await self.repo.list_programs(
            country=country,
            degree=degree,
            max_tuition=max_tuition,
            language=language,
            ielts=ielts,
            deadline_before=deadline_before,
            q=q,
            limit=limit,
            offset=offset,
        )
        return Page(
            items=[_program_out(r) for r in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_program(self, program_id: UUID) -> ProgramOut:
        program = await self.repo.get_program(program_id)
        if program is None:
            raise NotFound("Program not found")
        return _program_out(program)

    async def compare_programs(self, ids: list[UUID]) -> list[ProgramCompareItem]:
        if len(ids) < 2 or len(ids) > 5:
            raise Conflict("Compare requires 2 to 5 program ids")
        programs = await self.repo.get_programs_by_ids(ids)
        if len(programs) != len(set(ids)):
            raise NotFound("One or more programs not found")
        items: list[ProgramCompareItem] = []
        for p in programs:
            uni = p.university
            city = uni.city
            country = city.country
            items.append(
                ProgramCompareItem(
                    id=p.id,
                    name=p.name,
                    degree=p.degree,
                    language=p.language,
                    tuition_eur=p.tuition_eur,
                    min_cgpa=p.min_cgpa,
                    min_ielts=p.min_ielts,
                    intake_deadline=p.intake_deadline,
                    scholarship=p.scholarship,
                    university_name=uni.name,
                    city_name=city.name,
                    country_code=country.code,
                    courses=p.courses,
                )
            )
        return items

    async def create_program(self, payload: ProgramCreate, actor: User) -> ProgramOut:
        if await self.repo.get_university(payload.university_id) is None:
            raise NotFound("University not found")
        data = payload.model_dump(exclude={"courses"})
        program = Program(**data)
        program.courses = [
            ProgramCourse(**course.model_dump()) for course in payload.courses
        ]
        created = await self.repo.add_program(program)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="create",
            entity_type="program",
            entity_id=str(program.id),
            payload=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return _program_out(created)

    async def update_program(
        self, program_id: UUID, payload: ProgramUpdate, actor: User
    ) -> ProgramOut:
        program = await self.repo.get_program(program_id)
        if program is None:
            raise NotFound("Program not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(program, key, value)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="update",
            entity_type="program",
            entity_id=str(program.id),
            payload=payload.model_dump(mode="json", exclude_unset=True),
        )
        await self.session.commit()
        refreshed = await self.repo.get_program(program_id)
        return _program_out(refreshed)  # type: ignore[arg-type]

    async def delete_program(self, program_id: UUID, actor: User) -> None:
        program = await self.repo.get_program(program_id)
        if program is None:
            raise NotFound("Program not found")
        await self.repo.soft_delete(program)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="delete",
            entity_type="program",
            entity_id=str(program.id),
        )
        await self.session.commit()

    # ---- document templates ----
    async def list_document_templates(
        self,
        *,
        country_id: UUID | None,
        degree: str | None,
        limit: int,
        offset: int,
    ) -> Page[DocumentTemplateOut]:
        rows, total = await self.repo.list_document_templates(
            country_id=country_id, degree=degree, limit=limit, offset=offset
        )
        return Page(
            items=[DocumentTemplateOut.model_validate(r) for r in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def create_document_template(
        self, payload: DocumentTemplateCreate, actor: User
    ) -> DocumentTemplateOut:
        if await self.repo.get_country(payload.country_id) is None:
            raise NotFound("Country not found")
        template = DocumentTemplate(**payload.model_dump())
        await self.repo.add_document_template(template)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="create",
            entity_type="document_template",
            entity_id=str(template.id),
            payload=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return DocumentTemplateOut.model_validate(template)

    async def update_document_template(
        self, template_id: UUID, payload: DocumentTemplateUpdate, actor: User
    ) -> DocumentTemplateOut:
        template = await self.repo.get_document_template(template_id)
        if template is None:
            raise NotFound("Document template not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(template, key, value)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="update",
            entity_type="document_template",
            entity_id=str(template.id),
            payload=payload.model_dump(mode="json", exclude_unset=True),
        )
        await self.session.commit()
        return DocumentTemplateOut.model_validate(template)

    async def delete_document_template(self, template_id: UUID, actor: User) -> None:
        template = await self.repo.get_document_template(template_id)
        if template is None:
            raise NotFound("Document template not found")
        await self.repo.soft_delete(template)
        await write_audit(
            self.session,
            actor_user_id=actor.id,
            action="delete",
            entity_type="document_template",
            entity_id=str(template.id),
        )
        await self.session.commit()

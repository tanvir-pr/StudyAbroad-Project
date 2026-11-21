from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.pagination import Page
from app.modules.auth.dependencies import require_roles
from app.modules.auth.models import User
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
from app.modules.catalog.service import CatalogService

router = APIRouter(tags=["catalog"])
admin_deps = Depends(require_roles("admin", "super_admin"))


# ---- countries ----
@router.get("/countries", response_model=Page[CountryOut])
async def list_countries(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> Page[CountryOut]:
    return await CatalogService(session).list_countries(limit=limit, offset=offset)


@router.get("/countries/{country_id}", response_model=CountryOut)
async def get_country(
    country_id: UUID, session: AsyncSession = Depends(get_db)
) -> CountryOut:
    return await CatalogService(session).get_country(country_id)


@router.post(
    "/countries", response_model=CountryOut, status_code=status.HTTP_201_CREATED
)
async def create_country(
    payload: CountryCreate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> CountryOut:
    return await CatalogService(session).create_country(payload, actor)


@router.patch("/countries/{country_id}", response_model=CountryOut)
async def update_country(
    country_id: UUID,
    payload: CountryUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> CountryOut:
    return await CatalogService(session).update_country(country_id, payload, actor)


@router.delete("/countries/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_country(
    country_id: UUID,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> None:
    await CatalogService(session).delete_country(country_id, actor)


# ---- cities ----
@router.get("/cities", response_model=Page[CityOut])
async def list_cities(
    country_id: UUID | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> Page[CityOut]:
    return await CatalogService(session).list_cities(
        country_id=country_id, limit=limit, offset=offset
    )


@router.get("/cities/{city_id}", response_model=CityOut)
async def get_city(city_id: UUID, session: AsyncSession = Depends(get_db)) -> CityOut:
    return await CatalogService(session).get_city(city_id)


@router.post("/cities", response_model=CityOut, status_code=status.HTTP_201_CREATED)
async def create_city(
    payload: CityCreate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> CityOut:
    return await CatalogService(session).create_city(payload, actor)


@router.patch("/cities/{city_id}", response_model=CityOut)
async def update_city(
    city_id: UUID,
    payload: CityUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> CityOut:
    return await CatalogService(session).update_city(city_id, payload, actor)


@router.delete("/cities/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_city(
    city_id: UUID,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> None:
    await CatalogService(session).delete_city(city_id, actor)


# ---- universities ----
@router.get("/universities", response_model=Page[UniversityOut])
async def list_universities(
    city_id: UUID | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> Page[UniversityOut]:
    return await CatalogService(session).list_universities(
        city_id=city_id, limit=limit, offset=offset
    )


@router.get("/universities/{university_id}", response_model=UniversityOut)
async def get_university(
    university_id: UUID, session: AsyncSession = Depends(get_db)
) -> UniversityOut:
    return await CatalogService(session).get_university(university_id)


@router.post(
    "/universities",
    response_model=UniversityOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_university(
    payload: UniversityCreate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> UniversityOut:
    return await CatalogService(session).create_university(payload, actor)


@router.patch("/universities/{university_id}", response_model=UniversityOut)
async def update_university(
    university_id: UUID,
    payload: UniversityUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> UniversityOut:
    return await CatalogService(session).update_university(
        university_id, payload, actor
    )


@router.delete(
    "/universities/{university_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_university(
    university_id: UUID,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> None:
    await CatalogService(session).delete_university(university_id, actor)


# ---- programs ----
@router.get("/programs/compare", response_model=list[ProgramCompareItem])
async def compare_programs(
    ids: list[UUID] = Query(..., min_length=2, max_length=5),
    session: AsyncSession = Depends(get_db),
) -> list[ProgramCompareItem]:
    return await CatalogService(session).compare_programs(ids)


@router.get("/programs", response_model=Page[ProgramOut])
async def list_programs(
    country: str | None = None,
    degree: str | None = None,
    max_tuition: Decimal | None = None,
    language: str | None = None,
    ielts: Decimal | None = None,
    deadline_before: date | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> Page[ProgramOut]:
    return await CatalogService(session).list_programs(
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


@router.get("/programs/{program_id}", response_model=ProgramOut)
async def get_program(
    program_id: UUID, session: AsyncSession = Depends(get_db)
) -> ProgramOut:
    return await CatalogService(session).get_program(program_id)


@router.post(
    "/programs", response_model=ProgramOut, status_code=status.HTTP_201_CREATED
)
async def create_program(
    payload: ProgramCreate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> ProgramOut:
    return await CatalogService(session).create_program(payload, actor)


@router.patch("/programs/{program_id}", response_model=ProgramOut)
async def update_program(
    program_id: UUID,
    payload: ProgramUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> ProgramOut:
    return await CatalogService(session).update_program(program_id, payload, actor)


@router.delete("/programs/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: UUID,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> None:
    await CatalogService(session).delete_program(program_id, actor)


# ---- document templates ----
@router.get("/document-templates", response_model=Page[DocumentTemplateOut])
async def list_document_templates(
    country_id: UUID | None = None,
    degree: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> Page[DocumentTemplateOut]:
    return await CatalogService(session).list_document_templates(
        country_id=country_id, degree=degree, limit=limit, offset=offset
    )


@router.post(
    "/document-templates",
    response_model=DocumentTemplateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_document_template(
    payload: DocumentTemplateCreate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> DocumentTemplateOut:
    return await CatalogService(session).create_document_template(payload, actor)


@router.patch(
    "/document-templates/{template_id}", response_model=DocumentTemplateOut
)
async def update_document_template(
    template_id: UUID,
    payload: DocumentTemplateUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> DocumentTemplateOut:
    return await CatalogService(session).update_document_template(
        template_id, payload, actor
    )


@router.delete(
    "/document-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_document_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_db),
    actor: User = admin_deps,
) -> None:
    await CatalogService(session).delete_document_template(template_id, actor)

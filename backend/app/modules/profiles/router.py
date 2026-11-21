from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.pagination import Page
from app.modules.auth.dependencies import get_current_user, get_optional_user, require_roles
from app.modules.auth.models import User
from app.modules.profiles.schemas import (
    MentorProfileCreate,
    MentorProfileOut,
    MentorProfileUpdate,
    ResidencePermitCreate,
    ResidencePermitOut,
    ResidencePermitUpdate,
    StudentProfileCreate,
    StudentProfileOut,
    StudentProfileUpdate,
)
from app.modules.profiles.service import ProfileService

router = APIRouter(tags=["profiles"])


# ---- student profile ----
@router.post(
    "/profiles/student",
    response_model=StudentProfileOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_student_profile(
    payload: StudentProfileCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudentProfileOut:
    return await ProfileService(session).upsert_student(user, payload, create=True)


@router.get("/profiles/student/me", response_model=StudentProfileOut)
async def get_my_student_profile(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudentProfileOut:
    return await ProfileService(session).get_my_student(user)


@router.patch("/profiles/student/me", response_model=StudentProfileOut)
async def update_my_student_profile(
    payload: StudentProfileUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudentProfileOut:
    return await ProfileService(session).upsert_student(user, payload, create=False)


@router.get("/profiles/student/{user_id}", response_model=StudentProfileOut)
async def get_student_profile(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudentProfileOut:
    return await ProfileService(session).get_student_for_user(user_id, user)


# ---- mentor profile ----
@router.get("/profiles/mentors", response_model=Page[MentorProfileOut])
async def list_verified_mentors(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> Page[MentorProfileOut]:
    return await ProfileService(session).list_verified_mentors(
        limit=limit, offset=offset
    )


@router.post(
    "/profiles/mentor",
    response_model=MentorProfileOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_mentor_profile(
    payload: MentorProfileCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MentorProfileOut:
    return await ProfileService(session).create_mentor(user, payload)


@router.get("/profiles/mentor/me", response_model=MentorProfileOut)
async def get_my_mentor_profile(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MentorProfileOut:
    return await ProfileService(session).get_my_mentor(user)


@router.patch("/profiles/mentor/me", response_model=MentorProfileOut)
async def update_my_mentor_profile(
    payload: MentorProfileUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MentorProfileOut:
    return await ProfileService(session).update_mentor(user, payload)


@router.get("/profiles/mentor/{mentor_id}", response_model=MentorProfileOut)
async def get_mentor_profile(
    mentor_id: UUID,
    session: AsyncSession = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
) -> MentorProfileOut:
    return await ProfileService(session).get_mentor_public(mentor_id, viewer)


@router.post(
    "/profiles/mentor/{mentor_id}/verify",
    response_model=MentorProfileOut,
)
async def verify_mentor_profile(
    mentor_id: UUID,
    verified: bool = True,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles("admin", "super_admin")),
) -> MentorProfileOut:
    return await ProfileService(session).set_mentor_verified(
        mentor_id, verified, actor
    )


# ---- residence permits ----
@router.get("/residence-permits", response_model=list[ResidencePermitOut])
async def list_residence_permits(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ResidencePermitOut]:
    return await ProfileService(session).list_my_permits(user)


@router.post(
    "/residence-permits",
    response_model=ResidencePermitOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_residence_permit(
    payload: ResidencePermitCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResidencePermitOut:
    return await ProfileService(session).create_permit(user, payload)


@router.patch(
    "/residence-permits/{permit_id}", response_model=ResidencePermitOut
)
async def update_residence_permit(
    permit_id: UUID,
    payload: ResidencePermitUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResidencePermitOut:
    return await ProfileService(session).update_permit(permit_id, user, payload)


@router.delete(
    "/residence-permits/{permit_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_residence_permit(
    permit_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    await ProfileService(session).delete_permit(permit_id, user)

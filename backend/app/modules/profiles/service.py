from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, NotFound
from app.core.pagination import Page
from app.modules.auth.models import User
from sqlalchemy.exc import IntegrityError

from app.modules.catalog.repository import CatalogRepository
from app.modules.profiles.models import MentorProfile, ResidencePermit, StudentProfile
from app.modules.profiles.repository import ProfileRepository
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


def _role_names(user: User) -> set[str]:
    return {r.name for r in user.roles}


def _is_admin(user: User) -> bool:
    return bool(_role_names(user) & {"admin", "super_admin"})


def _mentor_out(profile: MentorProfile) -> MentorProfileOut:
    data = MentorProfileOut.model_validate(profile)
    name = profile.university.name if profile.university else None
    return data.model_copy(update={"university_name": name})


def _permit_out(permit: ResidencePermit) -> ResidencePermitOut:
    data = ResidencePermitOut.model_validate(permit)
    country = permit.country
    return data.model_copy(
        update={
            "country_code": country.code if country else None,
            "country_name": country.name if country else None,
        }
    )


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProfileRepository(session)
        self.catalog = CatalogRepository(session)

    # ---- student ----
    async def get_my_student(self, user: User) -> StudentProfileOut:
        profile = await self.repo.get_student_by_user_id(user.id)
        if profile is None:
            raise NotFound("Student profile not found")
        return StudentProfileOut.model_validate(profile)

    async def get_student_for_user(
        self, target_user_id: UUID, viewer: User
    ) -> StudentProfileOut:
        if target_user_id != viewer.id and not _is_admin(viewer):
            # Ownership rule: do not reveal existence.
            raise NotFound("Student profile not found")
        profile = await self.repo.get_student_by_user_id(target_user_id)
        if profile is None:
            raise NotFound("Student profile not found")
        return StudentProfileOut.model_validate(profile)

    async def upsert_student(
        self, user: User, payload: StudentProfileCreate | StudentProfileUpdate, *, create: bool
    ) -> StudentProfileOut:
        existing = await self.repo.get_student_by_user_id(user.id)
        if create:
            if existing is not None:
                raise Conflict("Student profile already exists")
            assert isinstance(payload, StudentProfileCreate)
            profile = StudentProfile(user_id=user.id, **payload.model_dump())
            await self.repo.add_student(profile)
        else:
            if existing is None:
                raise NotFound("Student profile not found")
            for key, value in payload.model_dump(exclude_unset=True).items():
                setattr(existing, key, value)
            profile = existing
        await self.session.commit()
        await self.session.refresh(profile)
        return StudentProfileOut.model_validate(profile)

    # ---- mentor ----
    async def get_my_mentor(self, user: User) -> MentorProfileOut:
        profile = await self.repo.get_mentor_by_user_id(user.id)
        if profile is None:
            raise NotFound("Mentor profile not found")
        return _mentor_out(profile)

    async def get_mentor_public(
        self, mentor_profile_id: UUID, viewer: User | None
    ) -> MentorProfileOut:
        profile = await self.repo.get_mentor_by_id(mentor_profile_id)
        if profile is None:
            raise NotFound("Mentor profile not found")
        is_owner = viewer is not None and profile.user_id == viewer.id
        is_admin = viewer is not None and _is_admin(viewer)
        if not profile.verified and not is_owner and not is_admin:
            raise NotFound("Mentor profile not found")
        return _mentor_out(profile)

    async def list_verified_mentors(
        self, *, limit: int, offset: int
    ) -> Page[MentorProfileOut]:
        rows, total = await self.repo.list_verified_mentors(limit=limit, offset=offset)
        return Page(
            items=[_mentor_out(r) for r in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def create_mentor(
        self, user: User, payload: MentorProfileCreate
    ) -> MentorProfileOut:
        if await self.repo.get_mentor_by_user_id(user.id) is not None:
            raise Conflict("Mentor profile already exists")
        uni = await self.catalog.get_university(payload.university_id)
        if uni is None:
            raise NotFound("University not found")
        profile = MentorProfile(
            user_id=user.id,
            university_id=payload.university_id,
            program=payload.program,
            hourly_rate=payload.hourly_rate,
            verified=False,
        )
        created = await self.repo.add_mentor(profile)
        await self.repo.ensure_mentor_role(user.id)
        await self.session.commit()
        refreshed = await self.repo.get_mentor_by_user_id(user.id)
        return _mentor_out(refreshed)  # type: ignore[arg-type]

    async def update_mentor(
        self, user: User, payload: MentorProfileUpdate
    ) -> MentorProfileOut:
        profile = await self.repo.get_mentor_by_user_id(user.id)
        if profile is None:
            raise NotFound("Mentor profile not found")
        data = payload.model_dump(exclude_unset=True)
        if "university_id" in data:
            uni = await self.catalog.get_university(data["university_id"])
            if uni is None:
                raise NotFound("University not found")
        for key, value in data.items():
            setattr(profile, key, value)
        # Edits after verification require re-check.
        if data:
            profile.verified = False
        await self.session.commit()
        refreshed = await self.repo.get_mentor_by_user_id(user.id)
        return _mentor_out(refreshed)  # type: ignore[arg-type]

    async def set_mentor_verified(
        self, mentor_profile_id: UUID, verified: bool, actor: User
    ) -> MentorProfileOut:
        if "super_admin" not in _role_names(actor) and "admin" not in _role_names(actor):
            # router already guards; keep defense in depth
            raise NotFound("Mentor profile not found")
        profile = await self.repo.get_mentor_by_id(mentor_profile_id)
        if profile is None:
            raise NotFound("Mentor profile not found")
        profile.verified = verified
        await self.session.commit()
        refreshed = await self.repo.get_mentor_by_id(mentor_profile_id)
        return _mentor_out(refreshed)  # type: ignore[arg-type]

    # ---- residence permits ----
    async def list_my_permits(self, user: User) -> list[ResidencePermitOut]:
        rows = await self.repo.list_permits_for_user(user.id)
        return [_permit_out(r) for r in rows]

    async def create_permit(
        self, user: User, payload: ResidencePermitCreate
    ) -> ResidencePermitOut:
        country = await self.catalog.get_country(payload.country_id)
        if country is None:
            raise NotFound("Country not found")
        permit = ResidencePermit(user_id=user.id, **payload.model_dump())
        try:
            created = await self.repo.add_permit(permit)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise Conflict(
                "Residence permit already exists for this country and type"
            ) from None
        refreshed = await self.repo.get_permit(created.id)
        return _permit_out(refreshed)  # type: ignore[arg-type]

    async def update_permit(
        self, permit_id: UUID, user: User, payload: ResidencePermitUpdate
    ) -> ResidencePermitOut:
        permit = await self.repo.get_permit(permit_id)
        if permit is None or (permit.user_id != user.id and not _is_admin(user)):
            raise NotFound("Residence permit not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(permit, key, value)
        await self.session.commit()
        refreshed = await self.repo.get_permit(permit_id)
        return _permit_out(refreshed)  # type: ignore[arg-type]

    async def delete_permit(self, permit_id: UUID, user: User) -> None:
        permit = await self.repo.get_permit(permit_id)
        if permit is None or (permit.user_id != user.id and not _is_admin(user)):
            raise NotFound("Residence permit not found")
        await self.session.delete(permit)
        await self.session.commit()

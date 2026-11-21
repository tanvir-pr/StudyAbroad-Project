from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import Role, UserRole
from app.modules.profiles.models import MentorProfile, ResidencePermit, StudentProfile


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_student_by_user_id(self, user_id: UUID) -> StudentProfile | None:
        result = await self.session.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add_student(self, profile: StudentProfile) -> StudentProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def get_mentor_by_user_id(self, user_id: UUID) -> MentorProfile | None:
        result = await self.session.execute(
            select(MentorProfile)
            .where(MentorProfile.user_id == user_id)
            .options(selectinload(MentorProfile.university))
        )
        return result.scalar_one_or_none()

    async def get_mentor_by_id(self, mentor_id: UUID) -> MentorProfile | None:
        result = await self.session.execute(
            select(MentorProfile)
            .where(MentorProfile.id == mentor_id)
            .options(selectinload(MentorProfile.university))
        )
        return result.scalar_one_or_none()

    async def list_verified_mentors(
        self, *, limit: int, offset: int
    ) -> tuple[list[MentorProfile], int]:
        from sqlalchemy import func

        base = select(MentorProfile).where(MentorProfile.verified.is_(True))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        rows = await self.session.execute(
            base.options(selectinload(MentorProfile.university))
            .order_by(MentorProfile.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars().all()), total

    async def add_mentor(self, profile: MentorProfile) -> MentorProfile:
        self.session.add(profile)
        await self.session.flush()
        return await self.get_mentor_by_user_id(profile.user_id)  # type: ignore[return-value]

    async def ensure_mentor_role(self, user_id: UUID) -> None:
        role = (
            await self.session.execute(select(Role).where(Role.name == "mentor"))
        ).scalar_one_or_none()
        if role is None:
            return
        existing = (
            await self.session.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id, UserRole.role_id == role.id
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            self.session.add(UserRole(user_id=user_id, role_id=role.id))
            await self.session.flush()

    async def list_permits_for_user(self, user_id: UUID) -> list[ResidencePermit]:
        result = await self.session.execute(
            select(ResidencePermit)
            .where(ResidencePermit.user_id == user_id)
            .options(selectinload(ResidencePermit.country))
            .order_by(ResidencePermit.expiry_date)
        )
        return list(result.scalars().all())

    async def get_permit(self, permit_id: UUID) -> ResidencePermit | None:
        result = await self.session.execute(
            select(ResidencePermit)
            .where(ResidencePermit.id == permit_id)
            .options(selectinload(ResidencePermit.country))
        )
        return result.scalar_one_or_none()

    async def add_permit(self, permit: ResidencePermit) -> ResidencePermit:
        self.session.add(permit)
        await self.session.flush()
        return await self.get_permit(permit.id)  # type: ignore[return-value]

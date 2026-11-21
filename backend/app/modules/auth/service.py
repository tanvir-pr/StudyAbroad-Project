from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, Unauthorized
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut

# Same message for missing email and wrong password (PDF auth rule).
_INVALID_CREDENTIALS = "Invalid email or password"


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuthRepository(session)

    async def register(self, payload: RegisterRequest) -> UserOut:
        existing = await self.repo.get_user_by_email(payload.email)
        if existing is not None:
            raise Conflict("Email already registered")

        role = await self.repo.get_role_by_name("student")
        if role is None:
            raise Conflict("Default role 'student' is missing; run seed/migrations")

        user = await self.repo.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            name=payload.name,
            role=role,
        )
        await self.session.commit()
        await self.session.refresh(user, attribute_names=["roles"])
        return UserOut.model_validate(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.repo.get_user_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise Unauthorized(_INVALID_CREDENTIALS)
        token = create_access_token(user_id=user.id)
        return TokenResponse(access_token=token)

    async def get_me(self, user_id: UUID) -> UserOut:
        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise Unauthorized(_INVALID_CREDENTIALS)
        return UserOut.model_validate(user)

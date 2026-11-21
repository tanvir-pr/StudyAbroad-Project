from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.errors import Forbidden, Unauthorized
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    user = await get_optional_user(credentials=credentials, session=session)
    if user is None:
        raise Unauthorized("Authentication required")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    return await AuthRepository(session).get_user_by_id(user_id)


def require_roles(*allowed: str) -> Callable:
    allowed_set = set(allowed)

    async def _checker(user: User = Depends(get_current_user)) -> User:
        names = {role.name for role in user.roles}
        if names.isdisjoint(allowed_set):
            raise Forbidden("Insufficient role")
        return user

    return _checker

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.match.schemas import MatchRequest, MatchResponse
from app.modules.match.service import MatchService

router = APIRouter(tags=["match"])


@router.post("/match", response_model=MatchResponse)
async def match_programs(
    payload: MatchRequest | None = None,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MatchResponse:
    body = payload or MatchRequest()
    return await MatchService(session).match_for_user(user, body)

from typing import Annotated

from fastapi import APIRouter, Depends

from apps.api.app.api.dependencies import get_current_user
from apps.api.app.domain.users.models import User
from apps.api.app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        primary_organization_id=current_user.primary_organization_id,
    )

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.config import Settings, get_settings
from apps.api.app.db.session import get_session_factory
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.auth import AuthRepository, SqlAlchemyAuthRepository
from apps.api.app.services.auth import AuthenticationError, AuthorizationError, AuthService
from apps.api.app.services.auth import build_auth_service as create_auth_service


async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory(str(settings.database_url))
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_auth_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthRepository:
    return SqlAlchemyAuthRepository(session)


def get_auth_service(
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> AuthService:
    return create_auth_service(
        repository=repository,
        secret_key=settings.auth_secret_key,
        access_token_minutes=settings.access_token_minutes,
        refresh_token_days=settings.refresh_token_days,
    )


async def get_current_user(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    try:
        return await auth_service.authenticate_access_token(authorization.removeprefix("Bearer "))
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        ) from exc
    except AuthorizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is disabled",
        ) from exc

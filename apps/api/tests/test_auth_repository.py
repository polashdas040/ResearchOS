from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.app.db.base import Base
from apps.api.app.repositories.auth import SqlAlchemyAuthRepository


@pytest.mark.asyncio
async def test_sqlalchemy_auth_repository_registers_and_consumes_refresh_token() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        repository = SqlAlchemyAuthRepository(session)
        user = await repository.create_registration(
            email="db-user@example.com",
            password_hash="hashed",
            full_name="DB User",
            organization_name="DB Lab",
        )
        await repository.store_refresh_token(
            user_id=user.id,
            fingerprint="abc123",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        await session.commit()

    async with session_factory() as session:
        repository = SqlAlchemyAuthRepository(session)

        stored = await repository.get_user_by_email("DB-USER@example.com")
        first_use = await repository.consume_refresh_token("abc123")
        second_use = await repository.consume_refresh_token("abc123")

    assert stored is not None
    assert stored.password_hash == "hashed"
    assert first_use
    assert not second_use

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.auth import (
    MembershipRecord,
    OrganizationRecord,
    RefreshTokenRecord,
    UserRecord,
)
from apps.api.app.domain.organizations.models import Membership, Organization, OrganizationRole
from apps.api.app.domain.users.models import User


@dataclass(frozen=True)
class StoredUser:
    user: User
    password_hash: str


class AuthRepository(Protocol):
    async def create_registration(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        organization_name: str,
    ) -> User: ...

    async def get_user_by_email(self, email: str) -> StoredUser | None: ...

    async def get_user_by_id(self, user_id: UUID) -> StoredUser | None: ...

    async def list_memberships(self, user_id: UUID) -> list[Membership]: ...

    async def store_refresh_token(
        self,
        user_id: UUID,
        fingerprint: str,
        expires_at: datetime,
    ) -> None: ...

    async def consume_refresh_token(self, fingerprint: str) -> bool: ...

    async def revoke_refresh_token(self, fingerprint: str) -> None: ...


def _user_from_record(record: UserRecord) -> User:
    return User(
        id=record.id,
        email=record.email,
        full_name=record.full_name,
        is_active=record.is_active,
        primary_organization_id=record.primary_organization_id,
    )


def _membership_from_record(record: MembershipRecord) -> Membership:
    return Membership(
        id=record.id,
        user_id=record.user_id,
        organization_id=record.organization_id,
        role=OrganizationRole(record.role),
    )


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class SqlAlchemyAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_registration(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        organization_name: str,
    ) -> User:
        normalized_email = email.lower()
        existing = await self.get_user_by_email(normalized_email)
        if existing is not None:
            raise ValueError("Email already registered")

        now = datetime.now(UTC)
        organization = OrganizationRecord(id=uuid4(), name=organization_name, created_at=now)
        user = UserRecord(
            id=uuid4(),
            email=normalized_email,
            full_name=full_name,
            password_hash=password_hash,
            is_active=True,
            primary_organization_id=organization.id,
            created_at=now,
        )
        membership = MembershipRecord(
            id=uuid4(),
            user_id=user.id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER.value,
            created_at=now,
        )
        self._session.add_all([organization, user, membership])
        await self._session.flush()
        return _user_from_record(user)

    async def get_user_by_email(self, email: str) -> StoredUser | None:
        result = await self._session.execute(
            select(UserRecord).where(UserRecord.email == email.lower())
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return StoredUser(user=_user_from_record(record), password_hash=record.password_hash)

    async def get_user_by_id(self, user_id: UUID) -> StoredUser | None:
        record = await self._session.get(UserRecord, user_id)
        if record is None:
            return None
        return StoredUser(user=_user_from_record(record), password_hash=record.password_hash)

    async def list_memberships(self, user_id: UUID) -> list[Membership]:
        result = await self._session.execute(
            select(MembershipRecord).where(MembershipRecord.user_id == user_id)
        )
        return [_membership_from_record(record) for record in result.scalars()]

    async def store_refresh_token(
        self,
        user_id: UUID,
        fingerprint: str,
        expires_at: datetime,
    ) -> None:
        self._session.add(
            RefreshTokenRecord(
                id=uuid4(),
                user_id=user_id,
                token_fingerprint=fingerprint,
                expires_at=expires_at,
                created_at=datetime.now(UTC),
            )
        )
        await self._session.flush()

    async def consume_refresh_token(self, fingerprint: str) -> bool:
        result = await self._session.execute(
            select(RefreshTokenRecord).where(
                RefreshTokenRecord.token_fingerprint == fingerprint
            )
        )
        record = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if (
            record is None
            or record.consumed_at is not None
            or record.revoked_at is not None
            or _as_aware_utc(record.expires_at) < now
        ):
            return False
        record.consumed_at = now
        await self._session.flush()
        return True

    async def revoke_refresh_token(self, fingerprint: str) -> None:
        result = await self._session.execute(
            select(RefreshTokenRecord).where(
                RefreshTokenRecord.token_fingerprint == fingerprint
            )
        )
        record = result.scalar_one_or_none()
        if record is not None and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            await self._session.flush()


class InMemoryAuthRepository:
    def __init__(self) -> None:
        self._users_by_email: dict[str, StoredUser] = {}
        self._users_by_id: dict[UUID, StoredUser] = {}
        self._organizations: dict[UUID, Organization] = {}
        self._memberships_by_user: dict[UUID, list[Membership]] = {}
        self._refresh_tokens: dict[str, tuple[bool, datetime]] = {}

    async def create_registration(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        organization_name: str,
    ) -> User:
        normalized_email = email.lower()
        if normalized_email in self._users_by_email:
            raise ValueError("Email already registered")

        organization = Organization(id=uuid4(), name=organization_name)
        user = User(
            id=uuid4(),
            email=normalized_email,
            full_name=full_name,
            is_active=True,
            primary_organization_id=organization.id,
        )
        membership = Membership(
            id=uuid4(),
            user_id=user.id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
        )
        stored = StoredUser(user=user, password_hash=password_hash)
        self._organizations[organization.id] = organization
        self._memberships_by_user[user.id] = [membership]
        self._users_by_email[normalized_email] = stored
        self._users_by_id[user.id] = stored
        return user

    async def get_user_by_email(self, email: str) -> StoredUser | None:
        return self._users_by_email.get(email.lower())

    async def get_user_by_id(self, user_id: UUID) -> StoredUser | None:
        return self._users_by_id.get(user_id)

    async def list_memberships(self, user_id: UUID) -> list[Membership]:
        return list(self._memberships_by_user.get(user_id, []))

    async def store_refresh_token(
        self,
        user_id: UUID,
        fingerprint: str,
        expires_at: datetime,
    ) -> None:
        self._refresh_tokens[fingerprint] = (False, expires_at)

    async def consume_refresh_token(self, fingerprint: str) -> bool:
        stored = self._refresh_tokens.get(fingerprint)
        if stored is None:
            return False
        consumed, expires_at = stored
        if consumed or expires_at < datetime.now(UTC):
            return False
        self._refresh_tokens[fingerprint] = (True, expires_at)
        return True

    async def revoke_refresh_token(self, fingerprint: str) -> None:
        if fingerprint in self._refresh_tokens:
            _, expires_at = self._refresh_tokens[fingerprint]
            self._refresh_tokens[fingerprint] = (True, expires_at)

    async def disable_user(self, user_id: UUID) -> bool:
        return self.disable_user_sync(user_id)

    def disable_user_sync(self, user_id: UUID) -> bool:
        stored = self._users_by_id.get(user_id)
        if stored is None:
            return False
        disabled = stored.user.model_copy(update={"is_active": False})
        updated = StoredUser(user=disabled, password_hash=stored.password_hash)
        self._users_by_id[user_id] = updated
        self._users_by_email[disabled.email] = updated
        return True


_auth_repository = InMemoryAuthRepository()


def get_auth_repository() -> InMemoryAuthRepository:
    return _auth_repository


def reset_auth_repository() -> None:
    global _auth_repository
    _auth_repository = InMemoryAuthRepository()

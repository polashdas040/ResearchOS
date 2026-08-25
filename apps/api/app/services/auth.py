from datetime import UTC, datetime, timedelta
from uuid import UUID

from apps.api.app.domain.organizations.models import Membership
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.auth import AuthRepository, StoredUser
from apps.api.app.schemas.auth import TokenResponse
from apps.api.app.security.passwords import PasswordHasher
from apps.api.app.security.tokens import TokenClaims, TokenError, TokenService


class AuthenticationError(Exception):
    """Raised when credentials or tokens cannot authenticate a user."""


class AuthorizationError(Exception):
    """Raised when an authenticated user is not allowed to proceed."""


class RegistrationConflictError(Exception):
    """Raised when a registration request conflicts with an existing account."""


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
    ) -> User:
        try:
            return await self._repository.create_registration(
                email=email,
                password_hash=self._password_hasher.hash_password(password),
                full_name=full_name,
                organization_name=organization_name,
            )
        except ValueError as exc:
            raise RegistrationConflictError("Email already registered") from exc

    async def login(self, email: str, password: str) -> TokenResponse:
        stored = await self._repository.get_user_by_email(email)
        if stored is None:
            raise AuthenticationError("Invalid credentials")
        if not self._password_hasher.verify_password(password, stored.password_hash):
            raise AuthenticationError("Invalid credentials")
        if not stored.user.is_active:
            raise AuthorizationError("User is disabled")
        return await self._issue_tokens(stored.user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        claims = self._decode_refresh(refresh_token)
        consumed = await self._repository.consume_refresh_token(
            self._token_service.fingerprint(refresh_token)
        )
        if not consumed:
            raise AuthenticationError("Refresh token has already been used")

        stored = await self._require_active_user(claims.subject)
        return await self._issue_tokens(stored.user)

    async def logout(self, refresh_token: str) -> None:
        self._decode_refresh(refresh_token)
        await self._repository.revoke_refresh_token(self._token_service.fingerprint(refresh_token))

    async def authenticate_access_token(self, access_token: str) -> User:
        try:
            claims = self._token_service.decode(access_token, expected_type="access")
        except TokenError as exc:
            raise AuthenticationError("Invalid access token") from exc
        stored = await self._require_active_user(claims.subject)
        return stored.user

    async def memberships_for_user(self, user_id: UUID) -> list[Membership]:
        return await self._repository.list_memberships(user_id)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = self._token_service.create_access_token(
            user_id=user.id,
            organization_id=user.primary_organization_id,
        )
        refresh_token = self._token_service.create_refresh_token(
            user_id=user.id,
            organization_id=user.primary_organization_id,
        )
        refresh_claims = self._token_service.decode(refresh_token, expected_type="refresh")
        await self._repository.store_refresh_token(
            user_id=user.id,
            fingerprint=self._token_service.fingerprint(refresh_token),
            expires_at=datetime.fromtimestamp(refresh_claims.expires_at, UTC),
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def _require_active_user(self, user_id: UUID) -> StoredUser:
        stored = await self._repository.get_user_by_id(user_id)
        if stored is None:
            raise AuthenticationError("User does not exist")
        if not stored.user.is_active:
            raise AuthorizationError("User is disabled")
        return stored

    def _decode_refresh(self, refresh_token: str) -> TokenClaims:
        try:
            return self._token_service.decode(refresh_token, expected_type="refresh")
        except TokenError as exc:
            raise AuthenticationError("Invalid refresh token") from exc


def build_auth_service(
    repository: AuthRepository,
    secret_key: str,
    access_token_minutes: int,
    refresh_token_days: int,
) -> AuthService:
    return AuthService(
        repository=repository,
        password_hasher=PasswordHasher(),
        token_service=TokenService(
            secret_key=secret_key,
            access_token_ttl=timedelta(minutes=access_token_minutes),
            refresh_token_ttl=timedelta(days=refresh_token_days),
        ),
    )

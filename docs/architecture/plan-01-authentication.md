# PLAN 01 Authentication And Tenant Security

PLAN 01 adds the first production authentication boundary for ResearchOS.

## Scope

- Users register with email, password, full name, and initial organization name.
- Registration creates one organization and an `OWNER` membership.
- Passwords are stored only as salted PBKDF2-SHA256 hashes.
- Access and refresh tokens are signed, typed, expiring bearer tokens.
- Refresh tokens are stored only by SHA-256 fingerprint.
- Refresh tokens are single-use; refresh reuse is rejected.
- Logout revokes the submitted refresh token fingerprint.
- Disabled users cannot authenticate protected requests.
- `GET /users/me` is protected by bearer-token authentication.
- Tenant decisions are routed through `AuthorizationService`.

## Architecture

HTTP routes validate request/response schemas and delegate to `AuthService`.
`AuthService` owns credential checks, token issue, refresh rotation, and logout.
Persistence is behind `AuthRepository`; the default implementation is
`SqlAlchemyAuthRepository`, backed by PostgreSQL through SQLAlchemy sessions.
Tests inject `InMemoryAuthRepository` explicitly.

The route layer does not perform SQL, password hashing, or authorization
decisions directly.

## Tables

- `users`
- `organizations`
- `memberships`
- `refresh_tokens`

The Alembic migration is
`migrations/versions/20260825_0001_auth_tenant_security.py`.

## Limits

OAuth is not implemented in this phase. The auth service boundary leaves room
for additional identity providers in a later phase without changing API routes.

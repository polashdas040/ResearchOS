# Authentication API

## Register

`POST /auth/register`

Creates a user, organization, and owner membership.

```json
{
  "email": "ada@example.com",
  "password": "Correct Horse Battery Staple 1!",
  "full_name": "Ada Lovelace",
  "organization_name": "Analytical Engines Lab"
}
```

Returns `201 Created` with the public user shape.

## Login

`POST /auth/login`

Returns bearer access and refresh tokens.

```json
{
  "email": "ada@example.com",
  "password": "Correct Horse Battery Staple 1!"
}
```

## Refresh

`POST /auth/refresh`

Refresh tokens are single-use. Reusing the same refresh token returns `401`.

```json
{
  "refresh_token": "<token>"
}
```

## Logout

`POST /auth/logout`

Revokes the submitted refresh token and returns `204 No Content`.

## Current User

`GET /users/me`

Requires:

```http
Authorization: Bearer <access_token>
```

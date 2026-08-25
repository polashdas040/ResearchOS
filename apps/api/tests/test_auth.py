from collections.abc import Generator
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies import get_auth_repository
from apps.api.app.main import app
from apps.api.app.repositories.auth import InMemoryAuthRepository
from apps.api.app.security.tokens import TokenService


@pytest.fixture()
def client() -> Generator[TestClient]:
    app.dependency_overrides.clear()
    repository = InMemoryAuthRepository()
    app.dependency_overrides[get_auth_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_register_login_and_get_current_user(client: TestClient) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "email": "ada@example.com",
            "password": "Correct Horse Battery Staple 1!",
            "full_name": "Ada Lovelace",
            "organization_name": "Analytical Engines Lab",
        },
    )

    assert register_response.status_code == 201
    created = register_response.json()
    assert created["email"] == "ada@example.com"
    assert created["full_name"] == "Ada Lovelace"
    assert "password" not in created

    login_response = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "Correct Horse Battery Staple 1!"},
    )

    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ada@example.com"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "grace@example.com",
            "password": "Correct Horse Battery Staple 1!",
            "full_name": "Grace Hopper",
            "organization_name": "Compiler Lab",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": "grace@example.com", "password": "wrong password"},
    )

    assert response.status_code == 401


def test_protected_route_requires_token(client: TestClient) -> None:
    response = client.get("/users/me")

    assert response.status_code == 401


def test_expired_access_token_is_rejected(client: TestClient) -> None:
    token_service = TokenService(
        secret_key="test-secret",
        access_token_ttl=timedelta(seconds=-1),
    )
    token = token_service.create_access_token(user_id=uuid4(), organization_id=uuid4())

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_refresh_token_reuse_is_rejected(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "katherine@example.com",
            "password": "Correct Horse Battery Staple 1!",
            "full_name": "Katherine Johnson",
            "organization_name": "Orbital Mechanics Lab",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "katherine@example.com", "password": "Correct Horse Battery Staple 1!"},
    )
    refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    second_refresh = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert first_refresh.status_code == 200
    assert second_refresh.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "rosalind@example.com",
            "password": "Correct Horse Battery Staple 1!",
            "full_name": "Rosalind Franklin",
            "organization_name": "X-ray Diffraction Lab",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "rosalind@example.com", "password": "Correct Horse Battery Staple 1!"},
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post("/auth/logout", json={"refresh_token": refresh_token})
    refresh_response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert logout_response.status_code == 204
    assert refresh_response.status_code == 401


def test_disabled_user_cannot_use_access_token(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "disabled@example.com",
            "password": "Correct Horse Battery Staple 1!",
            "full_name": "Disabled User",
            "organization_name": "Inactive Lab",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "disabled@example.com", "password": "Correct Horse Battery Staple 1!"},
    )
    user_id = UUID(client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    ).json()["id"])

    repository = app.dependency_overrides[get_auth_repository]()
    disabled = repository.disable_user_sync(user_id)
    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert disabled
    assert me_response.status_code == 403

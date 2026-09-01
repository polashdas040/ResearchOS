from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies import get_auth_repository
from apps.api.app.api.routers.jobs import get_job_repository
from apps.api.app.main import app
from apps.api.app.repositories.auth import InMemoryAuthRepository
from apps.api.app.repositories.jobs import InMemoryJobRepository


@pytest.fixture()
def client() -> Generator[TestClient]:
    app.dependency_overrides.clear()
    auth_repository = InMemoryAuthRepository()
    job_repository = InMemoryJobRepository()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repository
    app.dependency_overrides[get_job_repository] = lambda: job_repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_api_creates_job_and_reads_status(client: TestClient) -> None:
    headers = auth_headers(client)

    created = client.post(
        "/jobs",
        json={"job_type": "DOCUMENT_PARSE", "payload": {"file_id": "file-1"}},
        headers=headers,
    )

    assert created.status_code == 201
    body = created.json()
    assert body["job_type"] == "DOCUMENT_PARSE"
    assert body["status"] == "QUEUED"
    assert body["payload"] == {"file_id": "file-1"}

    loaded = client.get(f"/jobs/{body['id']}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["id"] == body["id"]


def test_job_access_is_tenant_scoped(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner-job@example.com", "Owner Job Lab")
    outsider_headers = auth_headers(client, "outsider-job@example.com", "Other Job Lab")
    created = client.post(
        "/jobs",
        json={"job_type": "RESEARCH_RUN", "payload": {"goal": "test"}},
        headers=owner_headers,
    ).json()

    response = client.get(f"/jobs/{created['id']}", headers=outsider_headers)

    assert response.status_code == 404


def test_job_creation_is_idempotent_per_organization(client: TestClient) -> None:
    headers = auth_headers(client, "idempotent-job@example.com", "Idempotent Job Lab")
    body = {
        "job_type": "DATASET_PROFILE",
        "payload": {"file_id": "file-1"},
        "idempotency_key": "profile-file-1",
    }

    first = client.post("/jobs", json=body, headers=headers)
    second = client.post("/jobs", json=body, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


def auth_headers(
    client: TestClient,
    email: str = "jobs@example.com",
    organization: str = "Jobs Lab",
) -> dict[str, str]:
    password = "Correct Horse Battery Staple 1!"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": email.split("@")[0],
            "organization_name": organization,
        },
    )
    login_response = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

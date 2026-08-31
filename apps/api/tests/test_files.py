from collections.abc import Generator
from typing import cast

import pytest
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies import get_auth_repository
from apps.api.app.api.routers.files import get_file_repository, get_object_storage
from apps.api.app.api.routers.projects import get_project_repository
from apps.api.app.main import app
from apps.api.app.repositories.auth import InMemoryAuthRepository
from apps.api.app.repositories.files import InMemoryFileRepository
from apps.api.app.repositories.projects import InMemoryProjectRepository
from apps.api.app.services.storage import InMemoryObjectStorage


@pytest.fixture()
def client() -> Generator[TestClient]:
    app.dependency_overrides.clear()
    auth_repository = InMemoryAuthRepository()
    project_repository = InMemoryProjectRepository()
    file_repository = InMemoryFileRepository()
    object_storage = InMemoryObjectStorage()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repository
    app.dependency_overrides[get_project_repository] = lambda: project_repository
    app.dependency_overrides[get_file_repository] = lambda: file_repository
    app.dependency_overrides[get_object_storage] = lambda: object_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_upload_list_download_and_delete_project_file(client: TestClient) -> None:
    headers = auth_headers(client, "files@example.com", "Files Lab")
    project = client.post("/projects", json={"name": "File Project"}, headers=headers).json()

    upload = client.post(
        f"/projects/{project['id']}/files",
        files={"file": ("notes.txt", b"hello research", "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 201
    uploaded = upload.json()
    assert uploaded["filename"] == "notes.txt"
    assert uploaded["status"] == "READY"
    assert uploaded["sha256"]

    listed = client.get(f"/projects/{project['id']}/files", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [uploaded["id"]]

    downloaded = client.get(f"/files/{uploaded['id']}/download", headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.content == b"hello research"
    assert downloaded.headers["content-type"].startswith("text/plain")

    deleted = client.delete(f"/files/{uploaded['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/files/{uploaded['id']}/download", headers=headers).status_code == 404


def test_duplicate_hash_is_recorded(client: TestClient) -> None:
    headers = auth_headers(client, "duplicate@example.com", "Duplicate Lab")
    project = client.post("/projects", json={"name": "Duplicate Project"}, headers=headers).json()

    first = upload_file(client, project["id"], headers, "a.txt", b"same")
    second = upload_file(client, project["id"], headers, "b.txt", b"same")

    assert first["sha256"] == second["sha256"]
    assert second["duplicate_of_file_id"] == first["id"]


def test_invalid_mime_is_rejected(client: TestClient) -> None:
    headers = auth_headers(client, "mime@example.com", "Mime Lab")
    project = client.post("/projects", json={"name": "Mime Project"}, headers=headers).json()

    response = client.post(
        f"/projects/{project['id']}/files",
        files={"file": ("script.exe", b"MZ", "application/x-msdownload")},
        headers=headers,
    )

    assert response.status_code == 400


def test_cross_organization_file_access_is_blocked(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner-files@example.com", "Owner Files Lab")
    outsider_headers = auth_headers(client, "outsider-files@example.com", "Other Files Lab")
    project = client.post("/projects", json={"name": "Private Files"}, headers=owner_headers).json()
    uploaded = upload_file(client, project["id"], owner_headers, "private.txt", b"secret")

    list_response = client.get(f"/projects/{project['id']}/files", headers=outsider_headers)
    download_response = client.get(f"/files/{uploaded['id']}/download", headers=outsider_headers)
    delete_response = client.delete(f"/files/{uploaded['id']}", headers=outsider_headers)

    assert list_response.status_code == 404
    assert download_response.status_code == 404
    assert delete_response.status_code == 404


def upload_file(
    client: TestClient,
    project_id: str,
    headers: dict[str, str],
    filename: str,
    content: bytes,
) -> dict[str, object]:
    response = client.post(
        f"/projects/{project_id}/files",
        files={"file": (filename, content, "text/plain")},
        headers=headers,
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def auth_headers(client: TestClient, email: str, organization: str) -> dict[str, str]:
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

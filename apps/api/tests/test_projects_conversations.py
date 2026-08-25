from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies import get_auth_repository
from apps.api.app.api.routers.projects import get_project_repository
from apps.api.app.main import app
from apps.api.app.repositories.auth import InMemoryAuthRepository
from apps.api.app.repositories.projects import InMemoryProjectRepository


@pytest.fixture()
def client() -> Generator[TestClient]:
    app.dependency_overrides.clear()
    auth_repository = InMemoryAuthRepository()
    project_repository = InMemoryProjectRepository()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repository
    app.dependency_overrides[get_project_repository] = lambda: project_repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


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
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_project_crud_is_scoped_to_authenticated_user(client: TestClient) -> None:
    headers = auth_headers(client, "ada@example.com", "Analytical Engines Lab")

    create_response = client.post(
        "/projects",
        json={"name": "ADNI", "description": "Alzheimer disease imaging cohort"},
        headers=headers,
    )
    assert create_response.status_code == 201
    project = create_response.json()
    assert project["name"] == "ADNI"

    list_response = client.get("/projects", headers=headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [project["id"]]

    update_response = client.patch(
        f"/projects/{project['id']}",
        json={"name": "ADNI MRI", "description": "Updated description"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "ADNI MRI"

    get_response = client.get(f"/projects/{project['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "Updated description"


def test_cross_organization_project_access_is_blocked(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner@example.com", "Owner Lab")
    outsider_headers = auth_headers(client, "outsider@example.com", "Other Lab")
    created = client.post(
        "/projects",
        json={"name": "Private Project"},
        headers=owner_headers,
    ).json()

    get_response = client.get(f"/projects/{created['id']}", headers=outsider_headers)
    patch_response = client.patch(
        f"/projects/{created['id']}",
        json={"name": "Stolen Project"},
        headers=outsider_headers,
    )

    assert get_response.status_code == 404
    assert patch_response.status_code == 404


def test_conversation_lifecycle_and_messages_persist_in_order(client: TestClient) -> None:
    headers = auth_headers(client, "grace@example.com", "Compiler Lab")
    project = client.post("/projects", json={"name": "Literature Review"}, headers=headers).json()

    conversation_response = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "Hypothesis notes"},
        headers=headers,
    )
    assert conversation_response.status_code == 201
    conversation = conversation_response.json()

    for content in ["Find related work", "Search queued", "Found 3 papers"]:
        message_response = client.post(
            f"/conversations/{conversation['id']}/messages",
            json={"message_type": "USER", "content": content},
            headers=headers,
        )
        assert message_response.status_code == 201

    get_response = client.get(f"/conversations/{conversation['id']}", headers=headers)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["project_id"] == project["id"]
    assert [message["content"] for message in body["messages"]["items"]] == [
        "Find related work",
        "Search queued",
        "Found 3 papers",
    ]

    delete_response = client.delete(f"/conversations/{conversation['id']}", headers=headers)
    after_delete_response = client.get(f"/conversations/{conversation['id']}", headers=headers)

    assert delete_response.status_code == 204
    assert after_delete_response.status_code == 404


def test_message_pagination(client: TestClient) -> None:
    headers = auth_headers(client, "pager@example.com", "Pagination Lab")
    project = client.post("/projects", json={"name": "Paged Project"}, headers=headers).json()
    conversation = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "Paged conversation"},
        headers=headers,
    ).json()
    for index in range(5):
        client.post(
            f"/conversations/{conversation['id']}/messages",
            json={"message_type": "ASSISTANT", "content": f"message {index}"},
            headers=headers,
        )

    response = client.get(
        f"/conversations/{conversation['id']}?limit=2&offset=2",
        headers=headers,
    )

    assert response.status_code == 200
    messages = response.json()["messages"]
    assert messages["total"] == 5
    assert [item["content"] for item in messages["items"]] == ["message 2", "message 3"]


def test_conversations_belong_to_project_and_tenant(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner2@example.com", "Conversation Lab")
    outsider_headers = auth_headers(client, "outsider2@example.com", "External Lab")
    project = client.post("/projects", json={"name": "Owned Project"}, headers=owner_headers).json()
    conversation = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "Owned conversation"},
        headers=owner_headers,
    ).json()

    owner_list = client.get(f"/projects/{project['id']}/conversations", headers=owner_headers)
    outsider_list = client.get(f"/projects/{project['id']}/conversations", headers=outsider_headers)
    outsider_conversation = client.get(
        f"/conversations/{conversation['id']}",
        headers=outsider_headers,
    )

    assert owner_list.status_code == 200
    assert [item["id"] for item in owner_list.json()["items"]] == [conversation["id"]]
    assert outsider_list.status_code == 404
    assert outsider_conversation.status_code == 404

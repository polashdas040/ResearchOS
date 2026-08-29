from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies import get_auth_repository
from apps.api.app.api.routers.chat import get_model_gateway, get_usage_repository
from apps.api.app.api.routers.projects import get_project_repository
from apps.api.app.main import app
from apps.api.app.repositories.auth import InMemoryAuthRepository
from apps.api.app.repositories.projects import InMemoryProjectRepository
from apps.api.app.repositories.usage import InMemoryUsageRepository
from apps.api.app.services.model_gateway import DeterministicModelGateway, FailingModelGateway


@pytest.fixture()
def client() -> Generator[TestClient]:
    app.dependency_overrides.clear()
    auth_repository = InMemoryAuthRepository()
    project_repository = InMemoryProjectRepository()
    usage_repository = InMemoryUsageRepository()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repository
    app.dependency_overrides[get_project_repository] = lambda: project_repository
    app.dependency_overrides[get_usage_repository] = lambda: usage_repository
    app.dependency_overrides[get_model_gateway] = lambda: DeterministicModelGateway()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_chat_stream_emits_sse_events_and_persists_messages(client: TestClient) -> None:
    headers = _auth_headers(client)
    project = client.post("/projects", json={"name": "Streaming Project"}, headers=headers).json()
    conversation = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "Streaming conversation"},
        headers=headers,
    ).json()

    with client.stream(
        "POST",
        f"/conversations/{conversation['id']}/messages/stream",
        json={"content": "Hello stream"},
        headers=headers,
    ) as response:
        body = response.read().decode()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: message.started" in body
    assert "event: message.delta" in body
    assert "event: message.completed" in body
    assert "Echo:" in body

    loaded = client.get(f"/conversations/{conversation['id']}", headers=headers).json()
    assert [message["message_type"] for message in loaded["messages"]["items"]] == [
        "USER",
        "ASSISTANT",
    ]
    assert loaded["messages"]["items"][1]["content"] == "Echo: Hello stream"


def test_provider_failure_emits_failed_event_without_partial_assistant_message(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_model_gateway] = lambda: FailingModelGateway()
    headers = _auth_headers(client, email="failure@example.com")
    project = client.post("/projects", json={"name": "Failure Project"}, headers=headers).json()
    conversation = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "Failure conversation"},
        headers=headers,
    ).json()

    with client.stream(
        "POST",
        f"/conversations/{conversation['id']}/messages/stream",
        json={"content": "fail after partial"},
        headers=headers,
    ) as response:
        body = response.read().decode()

    loaded = client.get(f"/conversations/{conversation['id']}", headers=headers).json()

    assert response.status_code == 200
    assert "event: message.delta" in body
    assert "event: message.failed" in body
    assert [message["message_type"] for message in loaded["messages"]["items"]] == ["USER"]


def test_usage_is_recorded_after_completed_stream(client: TestClient) -> None:
    usage_repository = InMemoryUsageRepository()
    app.dependency_overrides[get_usage_repository] = lambda: usage_repository
    headers = _auth_headers(client, email="usage@example.com")
    project = client.post("/projects", json={"name": "Usage Project"}, headers=headers).json()
    conversation = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "Usage conversation"},
        headers=headers,
    ).json()

    with client.stream(
        "POST",
        f"/conversations/{conversation['id']}/messages/stream",
        json={"content": "count tokens"},
        headers=headers,
    ) as response:
        response.read()

    events = usage_repository.events
    assert len(events) == 1
    assert events[0].provider_name == "deterministic"
    assert events[0].total_tokens > 0


def test_missing_conversation_returns_404_before_stream_starts(client: TestClient) -> None:
    headers = _auth_headers(client, email="missing@example.com")

    response = client.post(
        f"/conversations/{uuid4()}/messages/stream",
        json={"content": "hello"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def _auth_headers(
    client: TestClient,
    email: str = "streamer@example.com",
) -> dict[str, str]:
    password = "Correct Horse Battery Staple 1!"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Streaming User",
            "organization_name": "Streaming Lab",
        },
    )
    login_response = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

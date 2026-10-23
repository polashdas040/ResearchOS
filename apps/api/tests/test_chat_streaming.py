from collections.abc import Generator
from typing import cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import AnyHttpUrl

from apps.api.app.api.dependencies import get_auth_repository
from apps.api.app.api.routers.chat import get_model_gateway, get_usage_repository
from apps.api.app.api.routers.files import get_file_repository, get_object_storage
from apps.api.app.api.routers.projects import get_project_repository
from apps.api.app.config import Settings
from apps.api.app.main import app
from apps.api.app.repositories.auth import InMemoryAuthRepository
from apps.api.app.repositories.files import InMemoryFileRepository
from apps.api.app.repositories.projects import InMemoryProjectRepository
from apps.api.app.repositories.usage import InMemoryUsageRepository
from apps.api.app.services.chat_streaming import _cited_reference_lines
from apps.api.app.services.model_gateway import (
    DeterministicModelGateway,
    FailingModelGateway,
    OllamaModelGateway,
)
from apps.api.app.services.storage import InMemoryObjectStorage


@pytest.fixture()
def client() -> Generator[TestClient]:
    app.dependency_overrides.clear()
    auth_repository = InMemoryAuthRepository()
    project_repository = InMemoryProjectRepository()
    usage_repository = InMemoryUsageRepository()
    file_repository = InMemoryFileRepository()
    object_storage = InMemoryObjectStorage()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repository
    app.dependency_overrides[get_project_repository] = lambda: project_repository
    app.dependency_overrides[get_usage_repository] = lambda: usage_repository
    app.dependency_overrides[get_file_repository] = lambda: file_repository
    app.dependency_overrides[get_object_storage] = lambda: object_storage
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
    assert "Echo:" not in body
    assert "ResearchOS" in body

    loaded = client.get(f"/conversations/{conversation['id']}", headers=headers).json()
    assert [message["message_type"] for message in loaded["messages"]["items"]] == [
        "USER",
        "ASSISTANT",
    ]
    assert "Echo:" not in loaded["messages"]["items"][1]["content"]
    assert "ResearchOS" in loaded["messages"]["items"][1]["content"]


def test_chat_stream_accepts_attachment_only_empty_content(client: TestClient) -> None:
    headers = _auth_headers(client, email="attachment-only@example.com")
    project = client.post("/projects", json={"name": "Attachment Project"}, headers=headers).json()
    conversation = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "Attachment conversation"},
        headers=headers,
    ).json()

    with client.stream(
        "POST",
        f"/conversations/{conversation['id']}/messages/stream",
        json={"content": ""},
        headers=headers,
    ) as response:
        body = response.read().decode()

    assert response.status_code == 200
    assert "event: message.delta" in body
    assert "ResearchOS" in body

    loaded = client.get(f"/conversations/{conversation['id']}", headers=headers).json()
    assert [message["message_type"] for message in loaded["messages"]["items"]] == [
        "USER",
        "ASSISTANT",
    ]
    assert loaded["messages"]["items"][0]["content"] == ""
    assert "ResearchOS received the attached file" in loaded["messages"]["items"][1]["content"]


def test_chat_stream_uses_uploaded_pdf_context_for_answer(client: TestClient) -> None:
    headers = _auth_headers(client, email="pdf-context@example.com")
    project = client.post("/projects", json={"name": "PDF Project"}, headers=headers).json()
    conversation = client.post(
        f"/projects/{project['id']}/conversations",
        json={"title": "PDF conversation"},
        headers=headers,
    ).json()
    upload = client.post(
        f"/projects/{project['id']}/files",
        files={
            "file": (
                "paper.pdf",
                b"""%PDF-1.4
PAGE 1
TITLE: Biomarker Paper
HEADING: Results
PARAGRAPH: The main result was that the ViT model achieved the highest AUC of 0.94.
%%EOF
""",
                "application/pdf",
            )
        },
        headers=headers,
    ).json()

    with client.stream(
        "POST",
        f"/conversations/{conversation['id']}/messages/stream",
        json={
            "content": "according to the pdf file pls tell me about the result",
            "file_ids": [upload["id"]],
        },
        headers=headers,
    ) as response:
        response.read()

    loaded = client.get(f"/conversations/{conversation['id']}", headers=headers).json()
    assistant_content = loaded["messages"]["items"][1]["content"]
    assert "According to the uploaded file" in assistant_content
    assert "ViT model achieved the highest AUC of 0.94" in assistant_content
    assert "metadata now" not in assistant_content


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


def test_ollama_compatible_url_selects_native_ollama_gateway() -> None:
    gateway = get_model_gateway(
        Settings(
            openai_compatible_api_key="ollama",
            openai_compatible_base_url=cast(
                AnyHttpUrl,
                "http://host.docker.internal:11434/v1",
            ),
            openai_compatible_chat_model="qwen3:1.7b",
        )
    )

    assert isinstance(gateway, OllamaModelGateway)
    assert gateway.provider_name == "ollama"


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

def test_cited_reference_lines_only_returns_sources_used_in_answer() -> None:
    context = (
        '[1] A. Author, "First Paper," Journal, 2024.\n'
        'INLINE CITATION: [1]\n'
        'EVIDENCE: First evidence.\n\n'
        '[2] B. Author, "Second Paper," Journal, 2025.\n'
        'INLINE CITATION: [2]\n'
        'EVIDENCE: Second evidence.'
    )

    assert _cited_reference_lines("The supported claim [2].", context) == [
        '[2] B. Author, "Second Paper," Journal, 2025.'
    ]


def test_cited_reference_lines_supports_author_date_markers() -> None:
    context = (
        'A. Author (2024). First Paper. Journal.\n'
        'INLINE CITATION: (Author, 2024)\n'
        'EVIDENCE: First evidence.'
    )

    assert _cited_reference_lines("The supported claim (Author, 2024).", context) == [
        "A. Author (2024). First Paper. Journal."
    ]

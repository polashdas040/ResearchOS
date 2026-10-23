from collections.abc import AsyncIterator

import pytest

from apps.api.app.services.model_gateway import (
    ChatMessageInput,
    DeterministicChatModel,
    GeminiChatModel,
    ModelRequest,
    OllamaChatModel,
    OpenAIChatModel,
    OpenAICompatibleModelGateway,
    _provider_error,
)


@pytest.mark.asyncio
async def test_deterministic_chat_model_streams_tokens_and_usage() -> None:
    model = DeterministicChatModel(model_name="test-model")

    chunks = [
        chunk
        async for chunk in model.stream(
            ModelRequest(messages=[ChatMessageInput(role="user", content="Hello world")])
        )
    ]

    response = "".join(chunk.delta for chunk in chunks)

    assert "Echo:" not in response
    assert "Hello world" not in response
    assert "ResearchOS" in response
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens > 4


@pytest.mark.asyncio
async def test_openai_chat_model_streams_answer_from_provider() -> None:
    model = OpenAIChatModel(
        api_key="test-key",
        model_name="gpt-test",
        client=FakeOpenAIClient(),
    )

    chunks = [
        chunk
        async for chunk in model.stream(
            ModelRequest(messages=[ChatMessageInput(role="user", content="What is AI?")])
        )
    ]

    assert "".join(chunk.delta for chunk in chunks) == "An AI agent acts toward a goal."
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 12


@pytest.mark.asyncio
async def test_openai_compatible_gateway_uses_configured_base_url() -> None:
    client = FakeOpenAIClient()
    gateway = OpenAICompatibleModelGateway(
        api_key="compatible-key",
        base_url="https://api.deepseek.com/v1",
        model_name="deepseek-chat",
        client=client,
    )

    chunks = [
        chunk
        async for chunk in gateway.chat_model().stream(
            ModelRequest(messages=[ChatMessageInput(role="user", content="What is AI?")])
        )
    ]

    assert "".join(chunk.delta for chunk in chunks) == "An AI agent acts toward a goal."
    assert client.base_url == "https://api.deepseek.com/v1"


@pytest.mark.asyncio
async def test_gemini_chat_model_streams_answer_from_provider() -> None:
    model = GeminiChatModel(
        api_key="gemini-key",
        model_name="gemini-test",
        client=FakeGeminiClient(),
    )

    chunks = [
        chunk
        async for chunk in model.stream(
            ModelRequest(messages=[ChatMessageInput(role="user", content="What is AI?")])
        )
    ]

    assert "".join(chunk.delta for chunk in chunks) == "An AI agent acts toward a goal."
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 6


@pytest.mark.asyncio
async def test_ollama_chat_model_disables_thinking_and_streams_content() -> None:
    client = FakeOllamaClient()
    model = OllamaChatModel(
        base_url="http://host.docker.internal:11434",
        model_name="qwen3:1.7b",
        client=client,
    )

    chunks = [
        chunk
        async for chunk in model.stream(
            ModelRequest(messages=[ChatMessageInput(role="user", content="What is AI?")])
        )
    ]

    assert "".join(chunk.delta for chunk in chunks) == "An AI agent acts toward a goal."
    assert client.think is False
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 12


def test_provider_error_includes_openai_error_message() -> None:
    message = _provider_error(
        "OpenAI",
        429,
        (
            b'{"error":{"message":"You have no credits remaining.",'
            b'"code":"credit_balance_exhausted"}}'
        ),
    )

    assert message == "OpenAI request failed: You have no credits remaining."


class FakeOpenAIClient:
    base_url: str | None = None

    async def stream_chat_completion(
        self,
        api_key: str,
        model_name: str,
        messages: list[dict[str, str]],
        base_url: str = "https://api.openai.com/v1",
    ) -> AsyncIterator[dict[str, object]]:
        assert api_key in {"test-key", "compatible-key"}
        assert model_name in {"gpt-test", "deepseek-chat"}
        assert messages[-1]["content"] == "What is AI?"
        self.base_url = base_url
        yield {"choices": [{"delta": {"content": "An AI agent "}}]}
        yield {"choices": [{"delta": {"content": "acts toward a goal."}}]}
        yield {
            "choices": [{"delta": {}}],
            "usage": {
                "prompt_tokens": 4,
                "completion_tokens": 8,
                "total_tokens": 12,
            },
        }


class FakeGeminiClient:
    async def stream_generate_content(
        self,
        api_key: str,
        model_name: str,
        contents: list[dict[str, object]],
    ) -> AsyncIterator[dict[str, object]]:
        assert api_key == "gemini-key"
        assert model_name == "gemini-test"
        assert contents[-1] == {
            "role": "user",
            "parts": [{"text": "What is AI?"}],
        }
        yield {
            "candidates": [
                {"content": {"parts": [{"text": "An AI agent "}]}}
            ]
        }
        yield {
            "candidates": [
                {"content": {"parts": [{"text": "acts toward a goal."}]}}
            ],
            "usageMetadata": {
                "promptTokenCount": 2,
                "candidatesTokenCount": 4,
                "totalTokenCount": 6,
            },
        }


class FakeOllamaClient:
    think: bool | None = None

    async def stream_chat(
        self,
        base_url: str,
        model_name: str,
        messages: list[dict[str, str]],
        think: bool,
    ) -> AsyncIterator[dict[str, object]]:
        assert base_url == "http://host.docker.internal:11434"
        assert model_name == "qwen3:1.7b"
        assert messages[-1]["content"] == "What is AI?"
        self.think = think
        yield {"message": {"content": "An AI agent "}}
        yield {"message": {"content": "acts toward a goal."}}
        yield {
            "done": True,
            "prompt_eval_count": 4,
            "eval_count": 8,
        }

import json
from collections.abc import AsyncIterator
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel, ConfigDict


class ChatMessageInput(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class UsageSummary(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ModelRequest(BaseModel):
    messages: list[ChatMessageInput]


class ModelChunk(BaseModel):
    delta: str
    usage: UsageSummary | None = None


class ModelResponse(BaseModel):
    content: str
    usage: UsageSummary


class EmbeddingResponse(BaseModel):
    vectors: list[list[float]]


class RerankResult(BaseModel):
    index: int
    score: float


class VisionInput(BaseModel):
    content_type: str
    data: bytes

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ModelProviderError(Exception):
    """Raised when a model provider fails during generation."""


class ChatModel(Protocol):
    def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]: ...


class OpenAIClient(Protocol):
    def stream_chat_completion(
        self,
        api_key: str,
        model_name: str,
        messages: list[dict[str, str]],
        base_url: str = "https://api.openai.com/v1",
    ) -> AsyncIterator[dict[str, object]]: ...


class GeminiClient(Protocol):
    def stream_generate_content(
        self,
        api_key: str,
        model_name: str,
        contents: list[dict[str, object]],
    ) -> AsyncIterator[dict[str, object]]: ...


class OllamaClient(Protocol):
    def stream_chat(
        self,
        base_url: str,
        model_name: str,
        messages: list[dict[str, str]],
        think: bool,
    ) -> AsyncIterator[dict[str, object]]: ...


class ReasoningModel(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse: ...


class VisionModel(Protocol):
    async def describe(self, inputs: list[VisionInput], prompt: str) -> ModelResponse: ...


class EmbeddingModel(Protocol):
    async def embed(self, texts: list[str]) -> EmbeddingResponse: ...


class RerankingModel(Protocol):
    async def rerank(self, query: str, documents: list[str]) -> list[RerankResult]: ...


class ModelGateway(Protocol):
    def chat_model(self) -> ChatModel: ...


class DeterministicChatModel:
    def __init__(self, model_name: str = "researchos-deterministic-chat") -> None:
        self.model_name = model_name

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        user_content = _latest_user_content(request.messages)
        prompt_tokens = _count_tokens(user_content)
        response = _local_researchos_response(user_content)
        response_tokens = response.split()
        completion_tokens = len(response_tokens)
        usage = UsageSummary(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

        for index, token in enumerate(response_tokens):
            prefix = "" if index == 0 else " "
            yield ModelChunk(
                delta=f"{prefix}{token}",
                usage=usage if index == len(response_tokens) - 1 else None,
            )


class OpenAIStreamingClient:
    def __init__(self, timeout_seconds: float = 60.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def stream_chat_completion(
        self,
        api_key: str,
        model_name: str,
        messages: list[dict[str, str]],
        base_url: str = "https://api.openai.com/v1",
    ) -> AsyncIterator[dict[str, object]]:
        normalized_base_url = base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{normalized_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": True,
                    "stream_options": {"include_usage": True},
                },
            ) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise ModelProviderError(
                        _provider_error("OpenAI", response.status_code, detail)
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ")
                    if data == "[DONE]":
                        break
                    yield json.loads(data)


class OpenAIChatModel:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: str = "https://api.openai.com/v1",
        provider_name: str = "OpenAI",
        client: OpenAIClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.provider_name = provider_name
        self._client = client or OpenAIStreamingClient()

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        usage: UsageSummary | None = None
        try:
            async for event in self._client.stream_chat_completion(
                api_key=self.api_key,
                model_name=self.model_name,
                messages=[
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
                base_url=self.base_url,
            ):
                usage_data = event.get("usage")
                if isinstance(usage_data, dict):
                    usage = UsageSummary(
                        prompt_tokens=int(usage_data.get("prompt_tokens", 0)),
                        completion_tokens=int(usage_data.get("completion_tokens", 0)),
                        total_tokens=int(usage_data.get("total_tokens", 0)),
                    )
                choices = event.get("choices")
                if not isinstance(choices, list) or not choices:
                    continue
                choice = choices[0]
                if not isinstance(choice, dict):
                    continue
                delta = choice.get("delta")
                if not isinstance(delta, dict):
                    continue
                content = delta.get("content")
                if isinstance(content, str) and content:
                    yield ModelChunk(delta=content)
        except httpx.HTTPError as exc:
            raise ModelProviderError(
                f"{self.provider_name} chat provider request failed"
            ) from exc
        if usage is not None:
            yield ModelChunk(delta="", usage=usage)


class GeminiStreamingClient:
    async def stream_generate_content(
        self,
        api_key: str,
        model_name: str,
        contents: list[dict[str, object]],
    ) -> AsyncIterator[dict[str, object]]:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                (
                    "https://generativelanguage.googleapis.com/v1beta/"
                    f"models/{model_name}:streamGenerateContent?alt=sse"
                ),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                },
                json={"contents": contents},
            ) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise ModelProviderError(
                        _provider_error("Gemini", response.status_code, detail)
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    yield json.loads(line.removeprefix("data: "))


class GeminiChatModel:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        client: GeminiClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client = client or GeminiStreamingClient()

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        usage: UsageSummary | None = None
        try:
            async for event in self._client.stream_generate_content(
                api_key=self.api_key,
                model_name=self.model_name,
                contents=_gemini_contents(request.messages),
            ):
                usage_data = event.get("usageMetadata")
                if isinstance(usage_data, dict):
                    usage = UsageSummary(
                        prompt_tokens=int(usage_data.get("promptTokenCount", 0)),
                        completion_tokens=int(usage_data.get("candidatesTokenCount", 0)),
                        total_tokens=int(usage_data.get("totalTokenCount", 0)),
                    )
                for text in _gemini_text_parts(event):
                    yield ModelChunk(delta=text)
        except httpx.HTTPError as exc:
            raise ModelProviderError("Gemini chat provider request failed") from exc
        if usage is not None:
            yield ModelChunk(delta="", usage=usage)


class OllamaStreamingClient:
    def __init__(self, timeout_seconds: float = 180.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def stream_chat(
        self,
        base_url: str,
        model_name: str,
        messages: list[dict[str, str]],
        think: bool,
    ) -> AsyncIterator[dict[str, object]]:
        normalized_base_url = base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{normalized_base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": True,
                    "think": think,
                },
            ) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise ModelProviderError(
                        _provider_error("Ollama", response.status_code, detail)
                    )
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    yield json.loads(line)


class OllamaChatModel:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        think: bool = False,
        client: OllamaClient | None = None,
    ) -> None:
        self.base_url = base_url
        self.model_name = model_name
        self.think = think
        self._client = client or OllamaStreamingClient()

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        usage: UsageSummary | None = None
        try:
            async for event in self._client.stream_chat(
                base_url=self.base_url,
                model_name=self.model_name,
                messages=[
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
                think=self.think,
            ):
                message = event.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content:
                        yield ModelChunk(delta=content)
                if event.get("done") is True:
                    prompt_tokens = _int_value(event.get("prompt_eval_count"))
                    completion_tokens = _int_value(event.get("eval_count"))
                    usage = UsageSummary(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                    )
        except httpx.HTTPError as exc:
            raise ModelProviderError("Ollama chat provider request failed") from exc
        if usage is not None:
            yield ModelChunk(delta="", usage=usage)


class FailingChatModel:
    model_name = "researchos-failing-chat"

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelChunk]:
        yield ModelChunk(delta="partial")
        raise ModelProviderError("Deterministic provider failure")


class DeterministicModelGateway:
    provider_name = "deterministic"

    def __init__(self, model_name: str = "researchos-deterministic-chat") -> None:
        self.model_name = model_name

    def chat_model(self) -> ChatModel:
        return DeterministicChatModel(model_name=self.model_name)


class OpenAIModelGateway:
    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def chat_model(self) -> ChatModel:
        return OpenAIChatModel(
            api_key=self.api_key,
            model_name=self.model_name,
            client=OpenAIStreamingClient(timeout_seconds=self.timeout_seconds),
        )


class OpenAICompatibleModelGateway:
    provider_name = "openai-compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        timeout_seconds: float = 60.0,
        client: OpenAIClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self._client = client

    def chat_model(self) -> ChatModel:
        return OpenAIChatModel(
            api_key=self.api_key,
            model_name=self.model_name,
            base_url=self.base_url,
            provider_name="OpenAI-compatible",
            client=self._client
            or OpenAIStreamingClient(timeout_seconds=self.timeout_seconds),
        )


class OllamaModelGateway:
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str,
        model_name: str,
        client: OllamaClient | None = None,
    ) -> None:
        self.base_url = base_url
        self.model_name = model_name
        self._client = client

    def chat_model(self) -> ChatModel:
        return OllamaChatModel(
            base_url=self.base_url,
            model_name=self.model_name,
            client=self._client,
        )


class GeminiModelGateway:
    provider_name = "gemini"

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.model_name = model_name

    def chat_model(self) -> ChatModel:
        return GeminiChatModel(api_key=self.api_key, model_name=self.model_name)


class FailingModelGateway:
    provider_name = "failing"
    model_name = FailingChatModel.model_name

    def chat_model(self) -> ChatModel:
        return FailingChatModel()


def _latest_user_content(messages: list[ChatMessageInput]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


def _count_tokens(text: str) -> int:
    tokens = text.split()
    return len(tokens)


def _int_value(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    return 0


def _local_researchos_response(user_content: str) -> str:
    normalized = user_content.strip().lower()
    if "uploaded file context:" in normalized:
        context = user_content.split("Uploaded file context:", maxsplit=1)[-1].strip()
        if "no extractable text was found" in context.lower():
            return (
                "I found the uploaded PDF, but this local extractor could not read text from it. "
                "It may be scanned or image-based, so full PDF vision/OCR analysis is needed."
            )
        excerpt = context[:900].strip()
        return (
            "According to the uploaded file, here is the most relevant extracted content I can "
            f"read now: {excerpt}"
        )
    if not normalized:
        return (
            "ResearchOS received the attached file. I can help inspect it once document "
            "analysis is available for this workspace."
        )
    if "pdf" in normalized or "paper" in normalized or "document" in normalized:
        return (
            "ResearchOS can work with the uploaded document metadata now. Structured PDF "
            "parsing, tables, figures, evidence packs, and citation validation are already "
            "implemented in the backend foundation."
        )
    if "dataset" in normalized or "csv" in normalized or "data" in normalized:
        return (
            "ResearchOS can profile CSV datasets with missingness, duplicates, statistics, "
            "correlations, leakage hints, and longitudinal visit summaries."
        )
    return (
        "ResearchOS is ready to help with this research task. The current local agent can "
        "summarize supported platform capabilities while the production LLM provider is "
        "kept behind the model gateway."
    )


def _gemini_contents(messages: list[ChatMessageInput]) -> list[dict[str, object]]:
    role_map = {"user": "user", "assistant": "model", "system": "user"}
    return [
        {
            "role": role_map[message.role],
            "parts": [{"text": message.content}],
        }
        for message in messages
    ]


def _gemini_text_parts(event: dict[str, object]) -> list[str]:
    candidates = event.get("candidates")
    if not isinstance(candidates, list):
        return []
    texts: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])
    return texts


def _provider_error(provider: str, status_code: int, content: bytes) -> str:
    try:
        body = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError:
        return f"{provider} chat provider request failed with HTTP {status_code}."
    error = body.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        return f"{provider} request failed: {error['message']}"
    return f"{provider} chat provider request failed with HTTP {status_code}."

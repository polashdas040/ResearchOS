from collections.abc import AsyncIterator
from typing import Literal, Protocol

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
        completion_tokens = prompt_tokens
        usage = UsageSummary(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

        yield ModelChunk(delta="Echo:")
        tokens = user_content.split()
        for index, token in enumerate(tokens):
            yield ModelChunk(delta=f" {token}", usage=usage if index == len(tokens) - 1 else None)


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

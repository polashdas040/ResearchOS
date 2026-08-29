import pytest

from apps.api.app.services.model_gateway import (
    ChatMessageInput,
    DeterministicChatModel,
    ModelRequest,
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

    assert [chunk.delta for chunk in chunks] == ["Echo:", " Hello", " world"]
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 4

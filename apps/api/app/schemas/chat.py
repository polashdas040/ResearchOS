from pydantic import BaseModel, Field


class ChatStreamRequest(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)

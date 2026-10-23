from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)


class ChatStreamRequest(BaseModel):
    content: str = Field(max_length=100_000)
    file_ids: list[UUID] = Field(default_factory=list, max_length=10)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=40)
    citation_style: Literal["IEEE", "APA 7", "Harvard", "MLA 9"] = "IEEE"
    reference_context: str = Field(default="", max_length=60_000)
    require_references: bool = False

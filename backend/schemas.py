from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatThread:
    user_id: str
    messages: list[ChatMessage] = field(default_factory=list)

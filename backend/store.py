import json
from pathlib import Path

from .schemas import ChatMessage, ChatThread


class ThreadStore:
    def __init__(self, path: Path):
        self.path = path
        self.threads: dict[str, ChatThread] = {}

    def load(self) -> None:
        if not self.path.exists():
            return

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.threads = {
            user_id: ChatThread(
                user_id=user_id,
                messages=[ChatMessage(**message) for message in messages],
            )
            for user_id, messages in data.items()
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            user_id: [message.__dict__ for message in thread.messages]
            for user_id, thread in self.threads.items()
        }
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def append_message(self, user_id: str, role: str, content: str) -> ChatThread:
        thread = self.get_thread(user_id)
        thread.messages.append(ChatMessage(role=role, content=content))
        self.save()
        return thread

    def get_thread(self, user_id: str) -> ChatThread:
        return self.threads.setdefault(user_id, ChatThread(user_id=user_id))

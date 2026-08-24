import sqlite3
from pathlib import Path

from .schemas import ChatMessage, ChatThread


class ThreadStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.threads: dict[str, ChatThread] = {}
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS threads (user_id TEXT PRIMARY KEY);
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL REFERENCES threads(user_id),
                        role TEXT NOT NULL,
                        content TEXT NOT NULL
                    );
                    """
                )
        finally:
            connection.close()

    def load(self) -> None:
        connection = self._connect()
        try:
            users = connection.execute("SELECT user_id FROM threads").fetchall()
            rows = connection.execute("SELECT user_id, role, content FROM messages ORDER BY id").fetchall()
        finally:
            connection.close()
        self.threads = {user_id: ChatThread(user_id) for (user_id,) in users}
        for user_id, role, content in rows:
            self.threads.setdefault(user_id, ChatThread(user_id)).messages.append(
                ChatMessage(role, content)
            )

    def save(self) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute("DELETE FROM messages")
                connection.execute("DELETE FROM threads")
                for thread in self.threads.values():
                    connection.execute("INSERT INTO threads (user_id) VALUES (?)", (thread.user_id,))
                    connection.executemany(
                        "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
                        [(thread.user_id, message.role, message.content) for message in thread.messages],
                    )
        finally:
            connection.close()

    def append_message(self, user_id: str, role: str, content: str) -> ChatThread:
        thread = self.get_thread(user_id)
        thread.messages.append(ChatMessage(role=role, content=content))
        connection = self._connect()
        try:
            with connection:
                connection.execute("INSERT OR IGNORE INTO threads (user_id) VALUES (?)", (user_id,))
                connection.execute(
                    "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
                    (user_id, role, content),
                )
        finally:
            connection.close()
        return thread

    def get_thread(self, user_id: str) -> ChatThread:
        return self.threads.setdefault(user_id, ChatThread(user_id=user_id))

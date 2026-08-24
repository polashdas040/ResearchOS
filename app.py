from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "chat_state.json"


class ChatRequest(BaseModel):
    user_id: str = Field(default="guest")
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    user_id: str
    reply: str
    history: list[dict[str, str]]


@dataclass
class ChatStore:
    path: Path
    state: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def load(self) -> None:
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_turn(self, user_id: str, role: str, content: str) -> list[dict[str, str]]:
        thread = self.state.setdefault(user_id, [])
        thread.append({"role": role, "content": content})
        self.save()
        return thread

    def get_history(self, user_id: str) -> list[dict[str, str]]:
        return self.state.get(user_id, [])


app = FastAPI(title="Research Agent Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = ChatStore(STATE_FILE)
store.load()

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def home() -> FileResponse:
    index = WEB_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend is missing")
    return FileResponse(index)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/history/{user_id}")
def history(user_id: str) -> dict[str, Any]:
    return {"user_id": user_id, "history": store.get_history(user_id)}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    store.add_turn(request.user_id, "user", request.message)

    reply = (
        "Research Agent Studio is ready. "
        "Next we will add the multi-agent planner, retrieval memory, login, credits, and document understanding."
    )

    history = store.add_turn(request.user_id, "assistant", reply)
    return ChatResponse(user_id=request.user_id, reply=reply, history=history)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

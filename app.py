from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.store import ThreadStore

load_dotenv()

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "chat_state.db"


class ChatRequest(BaseModel):
    user_id: str = Field(default="guest")
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    user_id: str
    reply: str
    history: list[dict[str, str]]


app = FastAPI(title="Research Agent Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = ThreadStore(STATE_FILE)
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
    thread = store.get_thread(user_id)
    return {"user_id": user_id, "history": [message.__dict__ for message in thread.messages]}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    store.append_message(request.user_id, "user", request.message)

    reply = (
        "Research Agent Studio is ready. "
        "Next we will add the multi-agent planner, retrieval memory, login, credits, and document understanding."
    )

    thread = store.append_message(request.user_id, "assistant", reply)
    history = [message.__dict__ for message in thread.messages]
    return ChatResponse(user_id=request.user_id, reply=reply, history=history)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

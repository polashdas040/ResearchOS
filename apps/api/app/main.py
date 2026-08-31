import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.api.routers.auth import router as auth_router
from apps.api.app.api.routers.chat import router as chat_router
from apps.api.app.api.routers.conversations import router as conversations_router
from apps.api.app.api.routers.files import router as files_router
from apps.api.app.api.routers.health import router as health_router
from apps.api.app.api.routers.projects import router as projects_router
from apps.api.app.api.routers.users import router as users_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ResearchOS API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(files_router)
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(users_router)

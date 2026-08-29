import logging

from fastapi import FastAPI

from apps.api.app.api.routers.auth import router as auth_router
from apps.api.app.api.routers.chat import router as chat_router
from apps.api.app.api.routers.conversations import router as conversations_router
from apps.api.app.api.routers.health import router as health_router
from apps.api.app.api.routers.projects import router as projects_router
from apps.api.app.api.routers.users import router as users_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ResearchOS API")
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(users_router)

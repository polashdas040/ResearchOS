import logging

from fastapi import FastAPI

from apps.api.app.api.routers.health import router as health_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ResearchOS API")
app.include_router(health_router)

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.api.app.services.readiness import ReadinessChecker, ReadinessReport, get_readiness_checker


class HealthResponse(BaseModel):
    status: Literal["ok"]


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessReport)
async def ready(
    checker: Annotated[ReadinessChecker, Depends(get_readiness_checker)],
) -> ReadinessReport | JSONResponse:
    report = await checker.check()
    if report.status == "ok":
        return report
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=report.model_dump(),
    )

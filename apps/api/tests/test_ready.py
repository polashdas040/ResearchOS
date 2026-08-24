from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.readiness import (
    DependencyStatus,
    ReadinessReport,
    get_readiness_checker,
)


class PassingChecker:
    async def check(self) -> ReadinessReport:
        return ReadinessReport(
            status="ok",
            dependencies={
                "postgres": DependencyStatus(status="ok"),
                "redis": DependencyStatus(status="ok"),
                "object_storage": DependencyStatus(status="ok"),
            },
        )


def test_ready_returns_ok_when_dependencies_pass() -> None:
    app.dependency_overrides[get_readiness_checker] = lambda: PassingChecker()
    try:
        response = TestClient(app).get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

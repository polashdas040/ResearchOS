import pytest

from apps.api.app.config import Settings


def test_settings_reads_environment_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RESEARCHOS_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "RESEARCHOS_DATABASE_URL",
        "postgresql+asyncpg://user:pass@db:5432/researchos",
    )

    settings = Settings()

    assert settings.environment == "test"
    assert str(settings.database_url).startswith("postgresql+asyncpg://")

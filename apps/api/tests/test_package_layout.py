from apps.api.app.main import app


def test_api_app_imports() -> None:
    assert app.title == "ResearchOS API"

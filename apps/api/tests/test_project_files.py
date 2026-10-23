from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_required_foundation_files_exist() -> None:
    required = [
        "docker-compose.yml",
        "Makefile",
        ".env.example",
        ".github/workflows/ci.yml",
        "README.md",
        "pyproject.toml",
        "package.json",
        "docs/api/health.md",
        "docs/adr/0001-monorepo-foundation.md",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]

    assert missing == []

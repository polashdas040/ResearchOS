from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_required_foundation_files_exist() -> None:
    required = [
        "docker-compose.yml",
        "Makefile",
        ".env.example",
        ".github/workflows/ci.yml",
        "README.md",
        "CODEX_MASTER_PROMPT.md",
        "docs/architecture/plan-00-foundation.md",
        "docs/api/health.md",
        "docs/adr/0001-monorepo-foundation.md",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]

    assert missing == []

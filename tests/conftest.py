from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
PYTEST_TEMP = Path("C:/Users/polas/.codex/visualizations/2026/08/24/01a03199-b311-7430-8a46-35cc1d2ab8d7/pytest-tmp/Multi-Agent AI Research")
PYTEST_TEMP.mkdir(parents=True, exist_ok=True)

for key in ("TMPDIR", "TEMP", "TMP"):
    os.environ[key] = str(PYTEST_TEMP)

tempfile.tempdir = str(PYTEST_TEMP)


@pytest.fixture
def tmp_path() -> Path:
    path = PYTEST_TEMP / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path

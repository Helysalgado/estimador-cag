from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def mock_engine_dispose(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main.dispose_engine", AsyncMock())


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

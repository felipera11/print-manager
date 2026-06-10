import pytest
from fastapi.testclient import TestClient

import models  # noqa: F401 - register models with Base.metadata
from database import Base, engine
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)

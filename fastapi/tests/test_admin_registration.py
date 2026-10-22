import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_first_admin_setup_is_one_time_and_regular_registration_remains_available(client):
    assert client.get("/api/auth/admin-registration").json() == {"available": True}

    regular = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert regular.status_code == 201
    assert regular.json()["user"]["is_superadmin"] is False

    admin = client.post(
        "/api/auth/admin-register",
        json={"email": "admin@example.com", "password": "password123"},
    )
    assert admin.status_code == 201
    assert admin.json()["user"]["is_superadmin"] is True
    assert client.get("/api/auth/admin-registration").json() == {"available": False}

    second_admin = client.post(
        "/api/auth/admin-register",
        json={"email": "another-admin@example.com", "password": "password123"},
    )
    assert second_admin.status_code == 409

    another_regular = client.post(
        "/api/auth/register",
        json={"email": "another-user@example.com", "password": "password123"},
    )
    assert another_regular.status_code == 201
    assert another_regular.json()["user"]["is_superadmin"] is False

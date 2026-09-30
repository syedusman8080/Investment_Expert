from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_local_configuration():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_rejects_unknown_document():
    response = TestClient(app).post(
        "/api/chat",
        json={"document_id": "missing", "question": "What is this?"},
    )
    assert response.status_code == 404

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "visites" in response.json()
    assert response.headers.get("x-visites-version") == "0.1.0"


def test_reset():
    response = client.post("/reset")
    assert response.status_code == 200
    assert response.json() == {"visites": 0}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

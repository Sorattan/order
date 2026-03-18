from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_should_return_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_should_return_404():
    response = client.get("/unknown")
    assert response.status_code == 404


def test_protected_route_without_token_should_return_401():
    response = client.get("/products")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing"
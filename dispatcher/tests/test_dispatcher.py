from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app
import httpx

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


@patch("app.main.httpx.post")
def test_auth_login_should_forward_request(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "fake-jwt-token",
        "token_type": "bearer",
        "role": "admin"
    }
    mock_post.return_value = mock_response

    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "1234"
    })

    assert response.status_code == 200
    assert response.json()["access_token"] == "fake-jwt-token"


@patch("app.main.httpx.post")
def test_auth_login_should_return_401_when_auth_service_rejects(mock_post):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.json.return_value = {
        "detail": "Invalid username or password"
    }
    mock_post.return_value = mock_response

    response = client.post("/auth/login", json={
        "username": "wrong",
        "password": "wrong"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

@patch("app.main.httpx.post")
def test_auth_login_should_return_503_when_auth_service_is_unavailable(mock_post):
    mock_post.side_effect = httpx.RequestError("Service unavailable")

    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "1234"
    })

    assert response.status_code == 503
    assert response.json()["detail"] == "Auth service unavailable"
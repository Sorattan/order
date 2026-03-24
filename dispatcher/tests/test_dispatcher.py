import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app

client = TestClient(app)

def test_health_should_return_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unknown_route_should_return_404():
    response = client.get("/unknown")
    assert response.status_code == 404

def test_products_without_token_should_return_401():
    response = client.get("/products")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing"

def test_products_with_invalid_token_should_return_401():
    response = client.get(
        "/products",
        headers={"Authorization": "Bearer wrong-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

@patch("app.main.httpx.post")
def test_auth_login_should_forward_admin_login(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "admin-token",
        "token_type": "bearer",
        "role": "admin"
    }
    mock_post.return_value = mock_response

    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "1234"
    })

    assert response.status_code == 200
    assert response.json()["access_token"] == "admin-token"

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

@patch("app.main.httpx.get")
def test_products_should_forward_request_when_token_exists(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": 1, "name": "Laptop", "price": 25000.0}
    ]
    mock_get.return_value = mock_response

    response = client.get(
        "/products",
        headers={"Authorization": "Bearer user-token"}
    )

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Laptop"

@patch("app.main.httpx.post")
def test_create_product_should_return_403_for_user_role(mock_post):
    response = client.post(
        "/products",
        headers={"Authorization": "Bearer user-token"},
        json={"name": "Keyboard", "price": 1200.0}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"

@patch("app.main.httpx.post")
def test_create_product_should_forward_request_for_admin_role(mock_post):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 3,
        "name": "Keyboard",
        "price": 1200.0
    }
    mock_post.return_value = mock_response

    response = client.post(
        "/products",
        headers={"Authorization": "Bearer admin-token"},
        json={"name": "Keyboard", "price": 1200.0}
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Keyboard"

@patch("app.main.httpx.post")
def test_create_product_should_return_503_when_product_service_is_unavailable(mock_post):
    mock_post.side_effect = httpx.RequestError("Service unavailable")

    response = client.post(
        "/products",
        headers={"Authorization": "Bearer admin-token"},
        json={"name": "Keyboard", "price": 1200.0}
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Product service unavailable"
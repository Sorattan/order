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

@patch("app.main.httpx.get")
def test_orders_should_return_only_user_orders_for_user_role(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": 1, "product_id": 1, "quantity": 2, "created_by": "user", "status": "created"},
        {"id": 2, "product_id": 2, "quantity": 1, "created_by": "admin", "status": "created"},
    ]
    mock_get.return_value = mock_response

    response = client.get(
        "/orders",
        headers={"Authorization": "Bearer user-token"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["created_by"] == "user"

@patch("app.main.httpx.get")
def test_orders_should_return_all_orders_for_admin_role(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": 1, "product_id": 1, "quantity": 2, "created_by": "user", "status": "created"},
        {"id": 2, "product_id": 2, "quantity": 1, "created_by": "admin", "status": "created"},
    ]
    mock_get.return_value = mock_response

    response = client.get(
        "/orders",
        headers={"Authorization": "Bearer admin-token"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

@patch("app.main.httpx.post")
def test_create_order_should_forward_request_for_user(mock_post):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 2,
        "product_id": 1,
        "quantity": 4,
        "created_by": "user",
        "status": "created",
    }
    mock_post.return_value = mock_response

    response = client.post(
        "/orders",
        headers={"Authorization": "Bearer user-token"},
        json={"product_id": 1, "quantity": 4}
    )

    assert response.status_code == 201
    assert response.json()["created_by"] == "user"

@patch("app.main.httpx.get")
def test_get_order_should_return_403_for_other_users_order(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 2,
        "product_id": 1,
        "quantity": 1,
        "created_by": "admin",
        "status": "created",
    }
    mock_get.return_value = mock_response

    response = client.get(
        "/orders/2",
        headers={"Authorization": "Bearer user-token"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to access this order"

@patch("app.main.httpx.put")
def test_update_product_should_return_403_for_user_role(mock_put):
    response = client.put(
        "/products/abc123",
        headers={"Authorization": "Bearer user-token"},
        json={"name": "Updated", "price": 1500.0}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"

@patch("app.main.httpx.put")
def test_update_product_should_forward_request_for_admin_role(mock_put):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "abc123",
        "name": "Updated Keyboard",
        "price": 1500.0
    }
    mock_put.return_value = mock_response

    response = client.put(
        "/products/abc123",
        headers={"Authorization": "Bearer admin-token"},
        json={"name": "Updated Keyboard", "price": 1500.0}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Keyboard"

@patch("app.main.httpx.delete")
def test_delete_product_should_return_403_for_user_role(mock_delete):
    response = client.delete(
        "/products/abc123",
        headers={"Authorization": "Bearer user-token"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"

@patch("app.main.httpx.delete")
def test_delete_product_should_forward_request_for_admin_role(mock_delete):
    mock_response = Mock()
    mock_response.status_code = 204
    mock_delete.return_value = mock_response

    response = client.delete(
        "/products/abc123",
        headers={"Authorization": "Bearer admin-token"}
    )

    assert response.status_code == 204

@patch("app.main.httpx.patch")
def test_update_order_status_should_return_403_for_user_role(mock_patch):
    response = client.patch(
        "/orders/abc123/status",
        headers={"Authorization": "Bearer user-token"},
        json={"status": "shipped"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"

@patch("app.main.httpx.patch")
def test_update_order_status_should_forward_request_for_admin_role(mock_patch):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "abc123",
        "product_id": 1,
        "quantity": 2,
        "created_by": "user",
        "status": "shipped"
    }
    mock_patch.return_value = mock_response

    response = client.patch(
        "/orders/abc123/status",
        headers={"Authorization": "Bearer admin-token"},
        json={"status": "shipped"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "shipped"

@patch("app.main.httpx.delete")
def test_delete_order_should_return_403_for_user_role(mock_delete):
    response = client.delete(
        "/orders/abc123",
        headers={"Authorization": "Bearer user-token"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"

@patch("app.main.httpx.delete")
def test_delete_order_should_forward_request_for_admin_role(mock_delete):
    mock_response = Mock()
    mock_response.status_code = 204
    mock_delete.return_value = mock_response

    response = client.delete(
        "/orders/abc123",
        headers={"Authorization": "Bearer admin-token"}
    )

    assert response.status_code == 204
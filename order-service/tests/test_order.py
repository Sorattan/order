from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_should_return_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_orders_should_return_200():
    response = client.get("/orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_existing_order_should_return_200():
    response = client.get("/orders/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_non_existing_order_should_return_404():
    response = client.get("/orders/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_create_order_should_return_201():
    response = client.post("/orders", json={
        "product_id": 2,
        "quantity": 3,
        "created_by": "user"
    })

    assert response.status_code == 201
    assert response.json()["product_id"] == 2
    assert response.json()["created_by"] == "user"
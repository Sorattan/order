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
    assert len(response.json()) >= 1

def test_get_existing_order_should_return_200():
    orders_response = client.get("/orders")
    order_id = orders_response.json()[0]["id"]

    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id

def test_get_non_existing_order_should_return_404():
    response = client.get("/orders/000000000000000000000000")
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

def test_update_order_status_should_return_200():
    create_response = client.post("/orders", json={
        "product_id": 1,
        "quantity": 2,
        "created_by": "user"
    })
    order_id = create_response.json()["id"]

    response = client.patch(f"/orders/{order_id}/status", json={
        "status": "shipped"
    })

    assert response.status_code == 200
    assert response.json()["status"] == "shipped"

def test_delete_order_should_return_204():
    create_response = client.post("/orders", json={
        "product_id": 1,
        "quantity": 1,
        "created_by": "user"
    })
    order_id = create_response.json()["id"]

    response = client.delete(f"/orders/{order_id}")
    assert response.status_code == 204

    get_response = client.get(f"/orders/{order_id}")
    assert get_response.status_code == 404
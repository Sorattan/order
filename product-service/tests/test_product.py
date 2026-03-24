from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_should_return_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_products_should_return_200():
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_existing_product_should_return_200():
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_non_existing_product_should_return_404():
    response = client.get("/products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_product_should_return_201():
    response = client.post("/products", json={
        "name": "Keyboard",
        "price": 1200.0
    })

    assert response.status_code == 201
    assert response.json()["name"] == "Keyboard"
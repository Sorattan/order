from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_should_return_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_login_should_return_admin_token():
    response = client.post("/login", json={
        "username": "admin",
        "password": "1234"
    })

    assert response.status_code == 200
    assert response.json()["access_token"] == "admin-token"
    assert response.json()["role"] == "admin"


def test_user_login_should_return_user_token():
    response = client.post("/login", json={
        "username": "user",
        "password": "1234"
    })

    assert response.status_code == 200
    assert response.json()["access_token"] == "user-token"
    assert response.json()["role"] == "user"


def test_login_should_return_401_for_invalid_credentials():
    response = client.post("/login", json={
        "username": "wrong",
        "password": "wrong"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
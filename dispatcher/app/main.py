import os
import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8003")

security = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    username: str
    password: str

class ProductCreateRequest(BaseModel):
    name: str
    price: float

class OrderCreateRequest(BaseModel):
    product_id: int
    quantity: int

def get_role_and_user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> tuple[str, str]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials

    if token == "admin-token":
        return "admin", "admin"

    if token == "user-token":
        return "user", "user"

    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/login")
def auth_login(data: LoginRequest):
    try:
        response = httpx.post(
            f"{AUTH_SERVICE_URL}/login",
            json=data.model_dump(),
            timeout=5.0,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

@app.get("/products")
def get_products(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    get_role_and_user_from_credentials(credentials)

    try:
        response = httpx.get(
            f"{PRODUCT_SERVICE_URL}/products",
            timeout=5.0,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Product service unavailable")

@app.post("/products")
def create_product(
    data: ProductCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    role, _ = get_role_and_user_from_credentials(credentials)

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        response = httpx.post(
            f"{PRODUCT_SERVICE_URL}/products",
            json=data.model_dump(),
            timeout=5.0,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Product service unavailable")

@app.get("/orders")
def get_orders(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    role, user_name = get_role_and_user_from_credentials(credentials)

    try:
        response = httpx.get(
            f"{ORDER_SERVICE_URL}/orders",
            timeout=5.0,
        )

        orders = response.json()

        if role == "admin":
            return JSONResponse(
                status_code=response.status_code,
                content=orders,
            )

        filtered_orders = [
            order for order in orders if order["created_by"] == user_name
        ]

        return JSONResponse(
            status_code=response.status_code,
            content=filtered_orders,
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Order service unavailable")

@app.get("/orders/{order_id}")
def get_order(
    order_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    role, user_name = get_role_and_user_from_credentials(credentials)

    try:
        response = httpx.get(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            timeout=5.0,
        )

        if response.status_code == 404:
            return JSONResponse(
                status_code=404,
                content=response.json(),
            )

        order = response.json()

        if role != "admin" and order["created_by"] != user_name:
            raise HTTPException(status_code=403, detail="Not allowed to access this order")

        return JSONResponse(
            status_code=response.status_code,
            content=order,
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Order service unavailable")

@app.post("/orders")
def create_order(
    data: OrderCreateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    _, user_name = get_role_and_user_from_credentials(credentials)

    payload = {
        "product_id": data.product_id,
        "quantity": data.quantity,
        "created_by": user_name,
    }

    try:
        response = httpx.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=payload,
            timeout=5.0,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Order service unavailable")
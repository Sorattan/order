import os
import json
import time
import httpx
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, HTTPException, Depends, Request, Response

app = FastAPI()

LOG_DIR = Path("/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "dispatcher.log"

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

class ProductUpdateRequest(BaseModel):
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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        write_dispatcher_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "dispatcher",
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_host": request.client.host if request.client else None,
        })

        return response

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        write_dispatcher_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "dispatcher",
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "status_code": 500,
            "duration_ms": duration_ms,
            "client_host": request.client.host if request.client else None,
            "error": str(exc),
        })
        raise

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

@app.put("/products/{product_id}")
def update_product(
    product_id: str,
    data: ProductUpdateRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    role, _ = get_role_and_user_from_credentials(credentials)

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        response = httpx.put(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            json=data.model_dump(),
            timeout=5.0,
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Product service unavailable")

@app.delete("/products/{product_id}")
def delete_product(
    product_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    role, _ = get_role_and_user_from_credentials(credentials)

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        response = httpx.delete(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=5.0,
        )

        if response.status_code == 204:
            return Response(status_code=204)

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
    
def write_dispatcher_log(record: dict) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
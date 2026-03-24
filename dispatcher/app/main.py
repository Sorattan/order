import os
import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8002")

class LoginRequest(BaseModel):
    username: str
    password: str

class ProductCreateRequest(BaseModel):
    name: str
    price: float

def get_role_from_authorization(authorization: str | None) -> str:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.split(" ", 1)[1].strip()

    if token == "admin-token":
        return "admin"

    if token == "user-token":
        return "user"

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
            timeout=5.0
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

@app.get("/products")
def get_products(authorization: str | None = Header(default=None)):
    get_role_from_authorization(authorization)

    try:
        response = httpx.get(
            f"{PRODUCT_SERVICE_URL}/products",
            timeout=5.0
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Product service unavailable")

@app.post("/products")
def create_product(
    data: ProductCreateRequest,
    authorization: str | None = Header(default=None)
):
    role = get_role_from_authorization(authorization)

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        response = httpx.post(
            f"{PRODUCT_SERVICE_URL}/products",
            json=data.model_dump(),
            timeout=5.0
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Product service unavailable")
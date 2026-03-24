import os
import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def get_products(authorization: str | None = Header(default=None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return {"message": "authorized request accepted"}


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
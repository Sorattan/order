from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "1234":
        return {
            "access_token": "admin-token",
            "token_type": "bearer",
            "role": "admin"
        }

    if data.username == "user" and data.password == "1234":
        return {
            "access_token": "user-token",
            "token_type": "bearer",
            "role": "user"
        }

    raise HTTPException(status_code=401, detail="Invalid username or password")
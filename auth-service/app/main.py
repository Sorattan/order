import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "auth_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
users_collection = db["users"]

class LoginRequest(BaseModel):
    username: str
    password: str

@app.on_event("startup")
def seed_users():
    if users_collection.count_documents({}) == 0:
        users_collection.insert_many([
            {
                "username": "admin",
                "password": "1234",
                "role": "admin",
                "access_token": "admin-token",
            },
            {
                "username": "user",
                "password": "1234",
                "role": "user",
                "access_token": "user-token",
            },
        ])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/login")
def login(data: LoginRequest):
    user = users_collection.find_one({
        "username": data.username,
        "password": data.password,
    })

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "access_token": user["access_token"],
        "token_type": "bearer",
        "role": user["role"],
    }
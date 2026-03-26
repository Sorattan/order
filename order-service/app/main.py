import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "order_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
orders_collection = db["orders"]

class OrderCreateRequest(BaseModel):
    product_id: int
    quantity: int
    created_by: str

def serialize_order(order) -> dict:
    return {
        "id": str(order["_id"]),
        "product_id": order["product_id"],
        "quantity": order["quantity"],
        "created_by": order["created_by"],
        "status": order["status"],
    }

@app.on_event("startup")
def seed_orders():
    if orders_collection.count_documents({}) == 0:
        orders_collection.insert_one({
            "product_id": 1,
            "quantity": 2,
            "created_by": "user",
            "status": "created",
        })

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/orders")
def get_orders():
    orders = orders_collection.find()
    return [serialize_order(order) for order in orders]

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    try:
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return serialize_order(order)

@app.post("/orders", status_code=201)
def create_order(data: OrderCreateRequest):
    result = orders_collection.insert_one({
        "product_id": data.product_id,
        "quantity": data.quantity,
        "created_by": data.created_by,
        "status": "created",
    })

    order = orders_collection.find_one({"_id": result.inserted_id})
    return serialize_order(order)
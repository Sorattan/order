import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "product_db")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
products_collection = db["products"]

class ProductCreateRequest(BaseModel):
    name: str
    price: float

def serialize_product(product) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "price": product["price"],
    }

@app.on_event("startup")
def seed_products():
    if products_collection.count_documents({}) == 0:
        products_collection.insert_many([
            {"name": "Laptop", "price": 25000.0},
            {"name": "Mouse", "price": 500.0},
        ])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products")
def get_products():
    products = products_collection.find()
    return [serialize_product(product) for product in products]

@app.get("/products/{product_id}")
def get_product(product_id: str):
    try:
        product = products_collection.find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return serialize_product(product)


@app.post("/products", status_code=201)
def create_product(data: ProductCreateRequest):
    result = products_collection.insert_one({
        "name": data.name,
        "price": data.price,
    })

    product = products_collection.find_one({"_id": result.inserted_id})
    return serialize_product(product)
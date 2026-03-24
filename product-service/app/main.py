from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class ProductCreateRequest(BaseModel):
    name: str
    price: float


products = [
    {"id": 1, "name": "Laptop", "price": 25000.0},
    {"id": 2, "name": "Mouse", "price": 500.0},
]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def get_products():
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")


@app.post("/products", status_code=201)
def create_product(data: ProductCreateRequest):
    new_id = max(product["id"] for product in products) + 1 if products else 1

    new_product = {
        "id": new_id,
        "name": data.name,
        "price": data.price
    }

    products.append(new_product)
    return new_product
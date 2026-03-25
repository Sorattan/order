from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class OrderCreateRequest(BaseModel):
    product_id: int
    quantity: int
    created_by: str

orders = [
    {
        "id": 1,
        "product_id": 1,
        "quantity": 2,
        "created_by": "user",
        "status": "created"
    }
]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/orders")
def get_orders():
    return orders

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["id"] == order_id:
            return order

    raise HTTPException(status_code=404, detail="Order not found")

@app.post("/orders", status_code=201)
def create_order(data: OrderCreateRequest):
    new_id = max(order["id"] for order in orders) + 1 if orders else 1

    new_order = {
        "id": new_id,
        "product_id": data.product_id,
        "quantity": data.quantity,
        "created_by": data.created_by,
        "status": "created"
    }

    orders.append(new_order)
    return new_order
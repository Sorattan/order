from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/products")
def get_products(authorization: str | None = Header(default=None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return {"message": "authorized request accepted"}
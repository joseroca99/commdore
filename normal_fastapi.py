from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="My First FastAPI")

# In-memory database
items_db = []


class Item(BaseModel):
    id: int
    name: str
    price: float


@app.get("/")
def read_root():
    return {"message": "API is running"}


@app.get("/items", response_model=List[Item])
def get_items():
    return items_db


@app.post("/items", response_model=Item)
def create_item(item: Item):
    # Check duplicate ID
    for existing in items_db:
        if existing.id == item.id:
            raise HTTPException(status_code=400, detail="Item ID already exists")

    items_db.append(item)
    return item


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(i)
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

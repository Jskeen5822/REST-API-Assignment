from typing import List

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Warehouse Operations API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InventoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., ge=0)
    price: float = Field(..., ge=0)


class InventoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    quantity: int | None = Field(None, ge=0)
    price: float | None = Field(None, ge=0)


class InventoryOut(InventoryCreate):
    id: int


class OrderCreate(BaseModel):
    customer: str = Field(..., min_length=1, max_length=100)
    items: List[int] = Field(default_factory=list, description="Inventory item identifiers")
    status: str = Field(default="pending", description="Current status of the order")


class OrderUpdate(BaseModel):
    customer: str | None = Field(None, min_length=1, max_length=100)
    items: List[int] | None = None
    status: str | None = None


class OrderOut(OrderCreate):
    id: int


def _reset_state() -> None:
    global inventory, orders, inventory_counter, order_counter
    inventory = {}
    orders = {}
    inventory_counter = 0
    order_counter = 0


_reset_state()


@app.get("/inventory", response_model=List[InventoryOut])
def list_inventory() -> List[InventoryOut]:
    return list(inventory.values())


@app.post("/inventory", response_model=InventoryOut, status_code=201)
def create_inventory(payload: InventoryCreate) -> InventoryOut:
    global inventory_counter
    inventory_counter += 1
    record = {"id": inventory_counter, **payload.model_dump()}
    inventory[inventory_counter] = record
    return record


@app.put("/inventory/{item_id}", response_model=InventoryOut)
def replace_inventory(item_id: int, payload: InventoryCreate) -> InventoryOut:
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    record = {"id": item_id, **payload.model_dump()}
    inventory[item_id] = record
    return record


@app.patch("/inventory/{item_id}", response_model=InventoryOut)
def patch_inventory(item_id: int, payload: InventoryUpdate) -> InventoryOut:
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    current = inventory[item_id].copy()
    updates = payload.model_dump(exclude_unset=True)
    current.update(updates)
    inventory[item_id] = current
    return current


@app.delete("/inventory/{item_id}", status_code=204)
def delete_inventory(item_id: int) -> Response:
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Clean up any order references to the deleted item.
    for order in orders.values():
        if item_id in order["items"]:
            order["items"] = [i for i in order["items"] if i != item_id]
    del inventory[item_id]
    return Response(status_code=204)


@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate) -> OrderOut:
    global order_counter
    _validate_order_items(payload.items)
    order_counter += 1
    record = {"id": order_counter, **payload.model_dump()}
    orders[order_counter] = record
    return record


@app.get("/orders/{order_id}", response_model=OrderOut)
def read_order(order_id: int) -> OrderOut:
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[order_id]


@app.put("/orders/{order_id}", response_model=OrderOut)
def replace_order(order_id: int, payload: OrderCreate) -> OrderOut:
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    _validate_order_items(payload.items)
    record = {"id": order_id, **payload.model_dump()}
    orders[order_id] = record
    return record


@app.patch("/orders/{order_id}", response_model=OrderOut)
def patch_order(order_id: int, payload: OrderUpdate) -> OrderOut:
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    updates = payload.model_dump(exclude_unset=True)
    if "items" in updates:
        _validate_order_items(updates["items"])
    current = orders[order_id].copy()
    current.update(updates)
    orders[order_id] = current
    return current


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int) -> Response:
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    del orders[order_id]
    return Response(status_code=204)


def _validate_order_items(item_ids: List[int]) -> None:
    missing = [item_id for item_id in item_ids if item_id not in inventory]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Items not found in inventory: {missing}",
        )


def reset_state() -> None:
    _reset_state()


__all__ = [
    "app",
    "reset_state",
]

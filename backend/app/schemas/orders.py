"""Pydantic schemas for orders and price quotes."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    """A single item the customer wants to order."""

    menu_item_id: int
    quantity: int = Field(ge=1, le=50, default=1)


class OrderCreate(BaseModel):
    """Payload for creating a new order."""

    table_number: int = Field(ge=1)
    items: list[OrderItemCreate]
    note: str = ""


class OrderItemResponse(BaseModel):
    """A single line-item in an order response."""

    id: int
    menu_item_id: int
    item_name: str
    item_price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Full order returned to clients."""

    id: int
    table_number: int
    status: str
    token: str
    note: str
    subtotal: float
    tax_amount: float
    service_charge_amount: float
    total: float
    items: list[OrderItemResponse]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """Payload for updating an order's status."""

    status: str


# ── Quote (price preview without creating an order) ───────────────────

class QuoteRequest(BaseModel):
    """Items to quote."""

    items: list[OrderItemCreate]


class QuoteItemDetail(BaseModel):
    """Single item inside a quote response."""

    menu_item_id: int
    name: str
    price: float
    quantity: int
    line_total: float


class QuoteResponse(BaseModel):
    """Price breakdown returned by /api/quote."""

    items: list[QuoteItemDetail]
    subtotal: float
    tax_percent: float
    tax_amount: float
    service_charge_percent: float
    service_charge_amount: float
    total: float

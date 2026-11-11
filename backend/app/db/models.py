"""SQLAlchemy ORM models for Brew Talk."""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def _utcnow() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


class MenuItem(Base):
    """A single item on the café menu."""

    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, default="")
    image_url = Column(String(500), default="")
    emoji = Column(String(10), default="☕")
    available = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<MenuItem {self.id}: {self.name}>"


class Order(Base):
    """A customer order."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_number = Column(Integer, nullable=False)
    status = Column(String(50), default="New")
    token = Column(String(100), nullable=False)
    note = Column(Text, default="")
    subtotal = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    service_charge_amount = Column(Float, default=0)
    total = Column(Float, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order {self.id} table={self.table_number} status={self.status}>"


class OrderItem(Base):
    """A single line-item within an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    item_name = Column(String(200), nullable=False)
    item_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")

    def __repr__(self) -> str:
        return f"<OrderItem {self.item_name} x{self.quantity}>"


class Setting(Base):
    """Key-value application settings."""

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)
    category = Column(String(50), default="general")
    description = Column(Text, default="")

    def __repr__(self) -> str:
        return f"<Setting {self.key}={self.value}>"

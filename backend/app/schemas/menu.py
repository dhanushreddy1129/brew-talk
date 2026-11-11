"""Pydantic schemas for menu items."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MenuItemBase(BaseModel):
    """Shared fields for menu item creation and responses."""

    name: str
    category: str
    price: float
    description: str = ""
    image_url: str = ""
    emoji: str = "☕"
    available: bool = True
    sort_order: int = 0


class MenuItemCreate(MenuItemBase):
    """Schema for creating a new menu item."""
    pass


class MenuItemUpdate(BaseModel):
    """Schema for partially updating a menu item. All fields optional."""

    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    emoji: Optional[str] = None
    available: Optional[bool] = None
    sort_order: Optional[int] = None


class MenuItemResponse(MenuItemBase):
    """Schema returned to clients. Includes id and timestamps."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

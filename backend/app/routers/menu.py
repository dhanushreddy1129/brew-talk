"""Public menu endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.database import get_db, get_menu_version
from app.db.models import MenuItem
from app.schemas.menu import MenuItemResponse

router = APIRouter(tags=["menu"])


@router.get("/api/menu/version")
async def menu_version(db: Session = Depends(get_db)) -> dict:
    """Lightweight polling endpoint — returns the current menu version hash."""
    return {"version": get_menu_version(db)}


@router.get("/api/menu", response_model=list[MenuItemResponse])
async def list_menu(
    response: Response,
    available: Optional[bool] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[MenuItem]:
    """List all menu items with optional filters."""
    query = db.query(MenuItem)

    if available is not None:
        query = query.filter(MenuItem.available == available)
    if category is not None:
        query = query.filter(MenuItem.category == category)

    items = query.order_by(MenuItem.sort_order, MenuItem.id).all()

    # Set the menu version header for ETag-style polling
    response.headers["X-Menu-Version"] = get_menu_version(db)

    return items


@router.get("/api/menu/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> MenuItem:
    """Get a single menu item by ID."""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

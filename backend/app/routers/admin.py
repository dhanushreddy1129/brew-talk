"""Admin endpoints — menu CRUD and statistics."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.database import get_db
from app.db.models import MenuItem, Order, OrderItem
from app.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from app.services.events import event_hub

router = APIRouter(tags=["admin"])


@router.post(
    "/api/admin/menu",
    response_model=MenuItemResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_menu_item(
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
) -> MenuItem:
    """Create a new menu item (admin only)."""
    item = MenuItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    await event_hub.broadcast("menu_changed", {"action": "created", "item_id": item.id}, channel="general")

    return item


@router.put(
    "/api/admin/menu/{item_id}",
    response_model=MenuItemResponse,
    dependencies=[Depends(require_admin)],
)
async def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
) -> MenuItem:
    """Update an existing menu item (admin only)."""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    await event_hub.broadcast("menu_changed", {"action": "updated", "item_id": item.id}, channel="general")

    return item


@router.delete(
    "/api/admin/menu/{item_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a menu item (admin only)."""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db.delete(item)
    db.commit()

    await event_hub.broadcast("menu_changed", {"action": "deleted", "item_id": item_id}, channel="general")

    return {"detail": "Menu item deleted"}


@router.get(
    "/api/admin/stats",
    dependencies=[Depends(require_admin)],
)
async def admin_stats(db: Session = Depends(get_db)) -> dict:
    """Get 24-hour dashboard statistics (admin only)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    # Total orders in the last 24 hours
    total_orders = (
        db.query(func.count(Order.id))
        .filter(Order.created_at >= cutoff)
        .scalar()
    ) or 0

    # Total revenue in the last 24 hours
    total_revenue = (
        db.query(func.sum(Order.total))
        .filter(Order.created_at >= cutoff)
        .scalar()
    ) or 0.0

    # Orders by status
    status_counts = (
        db.query(Order.status, func.count(Order.id))
        .filter(Order.created_at >= cutoff)
        .group_by(Order.status)
        .all()
    )
    orders_by_status = {status: count for status, count in status_counts}

    # Top 5 items by quantity ordered in the last 24 hours
    top_items_query = (
        db.query(
            OrderItem.item_name,
            func.sum(OrderItem.quantity).label("total_qty"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.created_at >= cutoff)
        .group_by(OrderItem.item_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    top_items = [{"name": name, "quantity": int(qty)} for name, qty in top_items_query]

    return {
        "total_orders": total_orders,
        "total_revenue": round(float(total_revenue), 2),
        "orders_by_status": orders_by_status,
        "top_items": top_items,
    }

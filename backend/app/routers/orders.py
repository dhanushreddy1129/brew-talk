"""Order endpoints — create, read, update status, delete, and price quoting."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.security import generate_order_token, verify_order_token, require_admin
from app.db.database import get_db
from app.db.models import MenuItem, Order, OrderItem, Setting
from app.schemas.orders import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    QuoteRequest,
    QuoteResponse,
)
from app.services.pricing import compute_quote
from app.services.events import event_hub

router = APIRouter(tags=["orders"])


def _get_pricing_settings(db: Session) -> tuple[float, float]:
    """Fetch tax_percent and service_charge_percent from settings."""
    tax_row = db.query(Setting).filter(Setting.key == "tax_percent").first()
    sc_row = db.query(Setting).filter(Setting.key == "service_charge_percent").first()
    tax_percent = float(tax_row.value) if tax_row else 5.0
    service_charge_percent = float(sc_row.value) if sc_row else 3.0
    return tax_percent, service_charge_percent


@router.post(
    "/api/orders",
    response_model=OrderResponse,
    status_code=201,
    dependencies=[Depends(rate_limit(max_calls=60, period=60))],
)
async def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> Order:
    """Create a new order. Validates all item IDs and uses DB prices."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    # Validate total_tables
    tables_row = db.query(Setting).filter(Setting.key == "total_tables").first()
    total_tables = int(tables_row.value) if tables_row else 12
    if payload.table_number > total_tables:
        raise HTTPException(status_code=400, detail=f"Table number must be between 1 and {total_tables}")

    # Fetch all requested menu items from DB
    item_ids = [i.menu_item_id for i in payload.items]
    db_items = db.query(MenuItem).filter(MenuItem.id.in_(item_ids)).all()
    db_items_map = {item.id: item for item in db_items}

    # Validate every requested item exists and is available
    for req_item in payload.items:
        if req_item.menu_item_id not in db_items_map:
            raise HTTPException(
                status_code=400,
                detail=f"Menu item with ID {req_item.menu_item_id} not found",
            )
        if not db_items_map[req_item.menu_item_id].available:
            name = db_items_map[req_item.menu_item_id].name
            raise HTTPException(
                status_code=400,
                detail=f"'{name}' is currently unavailable",
            )

    # Compute pricing
    tax_percent, service_charge_percent = _get_pricing_settings(db)
    items_for_pricing = [
        {
            "menu_item_id": ri.menu_item_id,
            "name": db_items_map[ri.menu_item_id].name,
            "price": db_items_map[ri.menu_item_id].price,
            "quantity": ri.quantity,
        }
        for ri in payload.items
    ]
    quote = compute_quote(items_for_pricing, tax_percent, service_charge_percent)

    # Create the order (token is a placeholder until we have the ID)
    order = Order(
        table_number=payload.table_number,
        note=payload.note,
        subtotal=quote["subtotal"],
        tax_amount=quote["tax_amount"],
        service_charge_amount=quote["service_charge_amount"],
        total=quote["total"],
        token="",  # will be set after flush
    )
    db.add(order)
    db.flush()  # get the order ID

    # Generate token based on order ID
    order.token = generate_order_token(order.id)

    # Create order items
    for ri in payload.items:
        db_menu_item = db_items_map[ri.menu_item_id]
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=ri.menu_item_id,
            item_name=db_menu_item.name,
            item_price=db_menu_item.price,
            quantity=ri.quantity,
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    # Broadcast event
    await event_hub.broadcast(
        "order_new",
        {
            "order_id": order.id,
            "table_number": order.table_number,
            "status": order.status,
            "total": order.total,
        },
        channel="kitchen",
    )

    return order


@router.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    token: str = "",
    db: Session = Depends(get_db),
) -> Order:
    """Get an order by ID. Customers must provide the correct token."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not token or not verify_order_token(order_id, token):
        raise HTTPException(status_code=403, detail="Invalid or missing order token")

    return order


@router.get(
    "/api/orders",
    response_model=list[OrderResponse],
    dependencies=[Depends(require_admin)],
)
async def list_orders(
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[Order]:
    """List all orders (admin only)."""
    query = db.query(Order).order_by(Order.created_at.desc())
    if status:
        query = query.filter(Order.status == status)
    return query.all()


@router.patch(
    "/api/orders/{order_id}/status",
    response_model=OrderResponse,
    dependencies=[Depends(require_admin)],
)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
) -> Order:
    """Update an order's status (admin only)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = payload.status
    db.commit()
    db.refresh(order)

    # Broadcast to kitchen and order-specific channel
    event_data = {
        "order_id": order.id,
        "table_number": order.table_number,
        "status": order.status,
        "total": order.total,
    }
    await event_hub.broadcast("order_update", event_data, channel="kitchen")
    await event_hub.broadcast("order_update", event_data, channel=f"orders_{order_id}")

    return order


@router.delete(
    "/api/orders/{order_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Cancel / delete an order (admin only)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    event_data = {
        "order_id": order.id,
        "table_number": order.table_number,
        "status": "Cancelled",
    }

    db.delete(order)
    db.commit()

    await event_hub.broadcast("order_update", event_data, channel="kitchen")
    await event_hub.broadcast("order_update", event_data, channel=f"orders_{order_id}")

    return {"detail": "Order deleted"}


@router.post("/api/quote", response_model=QuoteResponse)
async def quote_order(
    payload: QuoteRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Compute a price quote without creating an order."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="Quote must contain at least one item")

    item_ids = [i.menu_item_id for i in payload.items]
    db_items = db.query(MenuItem).filter(MenuItem.id.in_(item_ids)).all()
    db_items_map = {item.id: item for item in db_items}

    for req_item in payload.items:
        if req_item.menu_item_id not in db_items_map:
            raise HTTPException(
                status_code=400,
                detail=f"Menu item with ID {req_item.menu_item_id} not found",
            )

    tax_percent, service_charge_percent = _get_pricing_settings(db)

    items_for_pricing = [
        {
            "menu_item_id": ri.menu_item_id,
            "name": db_items_map[ri.menu_item_id].name,
            "price": db_items_map[ri.menu_item_id].price,
            "quantity": ri.quantity,
        }
        for ri in payload.items
    ]

    return compute_quote(items_for_pricing, tax_percent, service_charge_percent)

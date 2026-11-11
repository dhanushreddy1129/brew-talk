"""API tests for Brew Talk backend."""

import pytest
from app.db.models import MenuItem


# ── 1. Health ──────────────────────────────────────────────────────────

def test_health(client):
    """GET /api/health returns 200 with correct payload."""
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


# ── 2. Menu ────────────────────────────────────────────────────────────

def test_get_menu(client):
    """GET /api/menu returns all seeded items."""
    r = client.get("/api/menu")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 15
    # Verify some known items exist
    names = [i["name"] for i in items]
    assert "Filter Coffee" in names
    assert "Masala Dosa" in names
    assert "Ras Malai" in names


def test_menu_version(client):
    """GET /api/menu/version returns a version hash string."""
    r = client.get("/api/menu/version")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


# ── 3. Orders ─────────────────────────────────────────────────────────

def test_create_order(client, db):
    """POST /api/orders with valid items returns correct totals."""
    # Get two menu items from the DB
    item1 = db.query(MenuItem).filter(MenuItem.name == "Filter Coffee").first()
    item2 = db.query(MenuItem).filter(MenuItem.name == "Masala Dosa").first()
    assert item1 is not None and item2 is not None

    payload = {
        "table_number": 1,
        "items": [
            {"menu_item_id": item1.id, "quantity": 2},
            {"menu_item_id": item2.id, "quantity": 1},
        ],
        "note": "Extra sugar please",
    }
    r = client.post("/api/orders", json=payload)
    assert r.status_code == 201
    data = r.json()

    # Verify structure
    assert data["table_number"] == 1
    assert data["status"] == "New"
    assert data["note"] == "Extra sugar please"
    assert len(data["items"]) == 2
    assert data["token"] != ""

    # Verify pricing math
    # subtotal = 2*40 + 1*70 = 150
    expected_subtotal = item1.price * 2 + item2.price * 1
    assert data["subtotal"] == expected_subtotal
    expected_tax = round(expected_subtotal * 5 / 100, 2)
    assert data["tax_amount"] == expected_tax
    expected_sc = round(expected_subtotal * 3 / 100, 2)
    assert data["service_charge_amount"] == expected_sc
    expected_total = round(expected_subtotal + expected_tax + expected_sc, 2)
    assert data["total"] == expected_total


def test_create_order_invalid_item(client):
    """POST /api/orders with a non-existent item ID returns 400."""
    payload = {
        "table_number": 1,
        "items": [{"menu_item_id": 99999, "quantity": 1}],
    }
    r = client.post("/api/orders", json=payload)
    assert r.status_code == 400
    assert "99999" in r.json()["detail"]


def test_order_token_required(client, db):
    """GET /api/orders/{id} without a valid token returns 403."""
    # Create an order first
    item = db.query(MenuItem).first()
    payload = {
        "table_number": 1,
        "items": [{"menu_item_id": item.id, "quantity": 1}],
    }
    create_r = client.post("/api/orders", json=payload)
    order_id = create_r.json()["id"]

    # Try without token
    r = client.get(f"/api/orders/{order_id}")
    assert r.status_code == 403

    # Try with wrong token
    r = client.get(f"/api/orders/{order_id}?token=wrongtoken")
    assert r.status_code == 403

    # Try with correct token
    correct_token = create_r.json()["token"]
    r = client.get(f"/api/orders/{order_id}?token={correct_token}")
    assert r.status_code == 200


# ── 4. Admin Auth ──────────────────────────────────────────────────────

def test_admin_auth_required(client):
    """Admin endpoints without X-Admin-Key return 401 or 422."""
    # GET /api/orders (admin list) without header
    r = client.get("/api/orders")
    assert r.status_code in (401, 422)

    # GET /api/admin/stats without header
    r = client.get("/api/admin/stats")
    assert r.status_code in (401, 422)


# ── 5. Admin Menu CRUD ────────────────────────────────────────────────

def test_admin_create_menu_item(client, admin_headers):
    """POST /api/admin/menu creates a new item and it appears in the menu."""
    payload = {
        "name": "Test Latte",
        "category": "Beverages",
        "price": 99.0,
        "description": "A test latte",
        "emoji": "☕",
    }
    r = client.post("/api/admin/menu", json=payload, headers=admin_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Latte"
    assert data["price"] == 99.0
    assert data["id"] is not None

    # Verify it shows up in the menu
    menu_r = client.get("/api/menu")
    names = [i["name"] for i in menu_r.json()]
    assert "Test Latte" in names


def test_admin_update_menu_item(client, admin_headers, db):
    """PUT /api/admin/menu/{id} updates the price."""
    item = db.query(MenuItem).filter(MenuItem.name == "Masala Chai").first()
    assert item is not None

    r = client.put(
        f"/api/admin/menu/{item.id}",
        json={"price": 35.0},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["price"] == 35.0

    # Verify the change persists
    r2 = client.get(f"/api/menu/{item.id}")
    assert r2.json()["price"] == 35.0


# ── 6. Quote ──────────────────────────────────────────────────────────

def test_quote_endpoint(client, db):
    """POST /api/quote returns correct tax and service charge math."""
    item = db.query(MenuItem).filter(MenuItem.name == "Filter Coffee").first()
    assert item is not None

    payload = {"items": [{"menu_item_id": item.id, "quantity": 3}]}
    r = client.post("/api/quote", json=payload)
    assert r.status_code == 200
    data = r.json()

    expected_subtotal = item.price * 3
    assert data["subtotal"] == expected_subtotal
    assert data["tax_percent"] == 5.0
    assert data["tax_amount"] == round(expected_subtotal * 5 / 100, 2)
    assert data["service_charge_percent"] == 3.0
    assert data["service_charge_amount"] == round(expected_subtotal * 3 / 100, 2)
    expected_total = round(
        expected_subtotal + data["tax_amount"] + data["service_charge_amount"], 2
    )
    assert data["total"] == expected_total


def test_quote_price_tamper(client, db):
    """Ensure prices come from the DB, not the request (request has no price field)."""
    item = db.query(MenuItem).filter(MenuItem.name == "Thali Meals").first()
    assert item is not None

    # The OrderItemCreate schema only has menu_item_id and quantity — no price field.
    # So even if someone tries to inject a price, it's ignored.
    payload = {"items": [{"menu_item_id": item.id, "quantity": 1, "price": 1.0}]}
    r = client.post("/api/quote", json=payload)
    assert r.status_code == 200
    data = r.json()

    # The subtotal must use the DB price, not the injected 1.0
    assert data["subtotal"] == item.price
    assert data["items"][0]["price"] == item.price


# ── 7. Settings ───────────────────────────────────────────────────────

def test_settings(client):
    """GET /api/config returns all settings as a flat dict."""
    r = client.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    config = data["config"]
    assert config["cafe_name"] == "Brew Talk"
    assert config["tax_percent"] == "5"
    assert config["currency"] == "₹"


def test_admin_update_setting(client, admin_headers):
    """PUT /api/settings/{key} updates a setting via admin."""
    r = client.put(
        "/api/settings/cafe_tagline",
        json={"value": "New tagline!"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["value"] == "New tagline!"

    # Verify it's reflected in public config
    r2 = client.get("/api/config")
    assert r2.json()["config"]["cafe_tagline"] == "New tagline!"

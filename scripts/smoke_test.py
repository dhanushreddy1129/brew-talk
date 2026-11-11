"""
Smoke test for Brew Talk API.
Run: python scripts/smoke_test.py
Requires the server to be running on localhost:8000.
"""
import sys
import json
import urllib.request
import urllib.error

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8000"
ADMIN_KEY = "brewtalk2024"
PASS = 0
FAIL = 0


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  ✓ {name}")
        PASS += 1
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        FAIL += 1


def api_get(path, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()), resp.status


def api_post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()), resp.status


def api_patch(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=h, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()), resp.status


def api_put(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=h, method="PUT")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()), resp.status


def api_error(path, method="GET", body=None, headers=None):
    """Expect an HTTP error."""
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        urllib.request.urlopen(req)
        raise AssertionError("Expected HTTP error but got 2xx")
    except urllib.error.HTTPError as e:
        return e.code


print("\n☕ Brew Talk Smoke Tests")
print("=" * 40)


def run_tests():
    global PASS, FAIL

    # 1. Health
    def t_health():
        d, _ = api_get("/api/health")
        assert d["status"] == "ok", f"Got {d}"
    test("Health check", t_health)

    # 2. Menu
    def t_menu():
        items, _ = api_get("/api/menu")
        assert len(items) >= 13, f"Expected 13+ items, got {len(items)}"
    test("Menu has 13+ items", t_menu)

    # 3. Menu version
    def t_menu_version():
        d, _ = api_get("/api/menu/version")
        assert "version" in d, "No version field"
    test("Menu version endpoint", t_menu_version)

    # 4. Config
    def t_config():
        d, _ = api_get("/api/config")
        cfg = d.get("config", d)
        assert cfg.get("cafe_name") == "Brew Talk", f"Got {cfg.get('cafe_name')}"
        assert "tax_percent" in cfg
        assert "color_primary" in cfg
    test("Config returns settings", t_config)

    # 5. Config version
    def t_config_version():
        d, _ = api_get("/api/config/version")
        assert "version" in d
    test("Config version endpoint", t_config_version)

    # 6. Create order
    def t_create_order():
        items, _ = api_get("/api/menu")
        item = items[0]
        order, _ = api_post("/api/orders", {
            "table_number": 1,
            "items": [{"menu_item_id": item["id"], "quantity": 2}],
            "note": "Smoke test"
        })
        assert order["id"] > 0
        assert order["token"]
        assert order["total"] > 0
        assert order["subtotal"] == item["price"] * 2
        assert order["tax_amount"] > 0
        return order
    test("Create order", t_create_order)

    # 7. Order token required
    def t_order_token():
        items, _ = api_get("/api/menu")
        order, _ = api_post("/api/orders", {
            "table_number": 1,
            "items": [{"menu_item_id": items[0]["id"], "quantity": 1}],
        })
        code = api_error(f"/api/orders/{order['id']}")
        assert code in (401, 403, 422), f"Expected auth error, got {code}"
    test("Order requires token", t_order_token)

    # 8. Quote endpoint
    def t_quote():
        items, _ = api_get("/api/menu")
        item = items[0]
        quote, _ = api_post("/api/quote", {
            "items": [{"menu_item_id": item["id"], "quantity": 3}]
        })
        expected_subtotal = item["price"] * 3
        assert abs(quote["subtotal"] - expected_subtotal) < 0.01, \
            f"Subtotal {quote['subtotal']} != {expected_subtotal}"
        assert quote["tax_amount"] > 0
        assert quote["total"] > quote["subtotal"]
    test("Quote computes correct totals", t_quote)

    # 9. Admin auth required
    def t_admin_auth():
        code = api_error("/api/orders", method="GET")
        assert code in (401, 403, 422), f"Expected 401/403, got {code}"
    test("Admin auth required for orders list", t_admin_auth)

    # 10. Admin can list orders
    def t_admin_orders():
        orders, _ = api_get("/api/orders", headers={"X-Admin-Key": ADMIN_KEY})
        assert isinstance(orders, list)
    test("Admin can list orders", t_admin_orders)

    # 11. Admin update status
    def t_admin_status():
        items, _ = api_get("/api/menu")
        order, _ = api_post("/api/orders", {
            "table_number": 5,
            "items": [{"menu_item_id": items[0]["id"], "quantity": 1}],
        })
        updated, _ = api_patch(
            f"/api/orders/{order['id']}/status",
            {"status": "Preparing"},
            headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert updated["status"] == "Preparing"
    test("Admin can update order status", t_admin_status)

    # 12. Admin stats
    def t_stats():
        d, _ = api_get("/api/admin/stats", headers={"X-Admin-Key": ADMIN_KEY})
        assert "total_orders" in d
        assert "total_revenue" in d
    test("Admin stats endpoint", t_stats)

    # 13. Admin update setting
    def t_update_setting():
        api_put(
            "/api/settings/cafe_tagline",
            {"value": "Smoke test tagline"},
            headers={"X-Admin-Key": ADMIN_KEY}
        )
        d, _ = api_get("/api/config")
        cfg = d.get("config", d)
        assert cfg["cafe_tagline"] == "Smoke test tagline"
        # Restore
        api_put(
            "/api/settings/cafe_tagline",
            {"value": "Order with your voice, sip with joy"},
            headers={"X-Admin-Key": ADMIN_KEY}
        )
    test("Admin can update settings", t_update_setting)

    # 14. Invalid order (bad item ID)
    def t_invalid_item():
        code = api_error("/api/orders", method="POST", body={
            "table_number": 1,
            "items": [{"menu_item_id": 99999, "quantity": 1}]
        })
        assert code in (400, 404, 422), f"Expected 400/404/422, got {code}"
    test("Reject invalid menu item ID", t_invalid_item)


run_tests()

print(f"\n{'=' * 40}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL > 0:
    sys.exit(1)
else:
    print("All tests passed! ☕")
    sys.exit(0)

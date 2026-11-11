# Teacher Demo Scenarios

> This document walks through 7 live scenarios proving that backend changes reflect in the frontend instantly. Run each scenario while the server is running and a browser is open.

## Setup

1. Start the server: `scripts\run.bat` (Windows) or `./scripts/run.sh` (Linux/Mac)
2. Open these tabs:
   - **Customer**: http://localhost:8000/m/1
   - **Kitchen**: http://localhost:8000/kitchen (password: `brewtalk2024`)
   - **Admin**: http://localhost:8000/admin (password: `brewtalk2024`)
   - **Swagger**: http://localhost:8000/docs

---

## Scenario A: Change Item Price

**Goal**: Change a menu item's price and see it update on the customer page instantly.

### Via Admin Panel
1. Open **Admin** → **Menu** tab
2. Find "Filter Coffee" → click **Edit**
3. Change price from ₹40 to ₹60 → **Save**
4. Switch to the **Customer** tab → Filter Coffee now shows ₹60
5. Add it to cart → the cart total reflects the new price

### Via Swagger API
1. Open **Swagger** → `PUT /api/admin/menu/{id}`
2. Set `id = 1`, body: `{"price": 75}`
3. Header: `X-Admin-Key: brewtalk2024`
4. Execute → Customer page updates within 1 second

**Why it works**: The admin router broadcasts a `menu_changed` WebSocket event. The customer page listens and reloads the menu.

---

## Scenario B: Mark Item Unavailable

**Goal**: Mark an item as unavailable and watch it disappear from the customer menu.

1. Open **Admin** → **Menu** tab
2. Find "Masala Dosa" → click **Edit**
3. Uncheck **Available** → **Save**
4. Switch to **Customer** tab → Masala Dosa is gone from the menu
5. Re-enable it → it reappears

**Or via Swagger**: `PUT /api/admin/menu/{id}` with `{"available": false}`

---

## Scenario C: Change Brand Settings

**Goal**: Change the cafe name, tagline, or brand colour and see all pages update.

### Change Cafe Name
1. Open **Admin** → **Settings** tab
2. Find `cafe_name` → change to "Coffee House"
3. **Save** → All open pages show "Coffee House" in the header

### Change Brand Colour
1. Find `color_primary` → change to `#1B5E20` (forest green)
2. **Save** → The entire colour scheme updates across all pages
3. Change `color_accent` → accent elements (buttons, chips) update

### Change Tagline
1. Find `cafe_tagline` → change to "Fresh brews, happy you"
2. **Save** → Landing page and customer page update

**Why it works**: Settings changes broadcast `settings_changed` via WebSocket. Every page listens and re-applies CSS variables from `/api/config`.

---

## Scenario D: Change Tax Percentage

**Goal**: Change the tax rate and watch cart totals change.

1. Open **Customer** page (http://localhost:8000/m/1)
2. Add some items to cart → open the cart sheet → note the tax amount
3. Open **Admin** → **Settings** → change `tax_percent` from `5` to `18`
4. **Save** → Go back to the customer cart
5. The totals auto-update: GST is now 18% of the subtotal
6. Place an order → the receipt shows the new tax rate

**Why it works**: The cart calls `POST /api/quote` which reads `tax_percent` from the database. When settings change, the quote is recalculated.

---

## Scenario E: Change Order Status

**Goal**: Update an order status and watch the tracker and kitchen board update.

1. Place an order from the **Customer** page → note the order tracker
2. Open **Swagger** → `PATCH /api/orders/{id}/status`
3. Set the order ID, body: `{"status": "Preparing"}`, header: `X-Admin-Key: brewtalk2024`
4. Execute → Watch:
   - **Customer** tracker: status changes to "Preparing", coffee cup fills more
   - **Kitchen** board: order ticket moves from "New" to "Preparing" column

5. Change to "Ready" → both pages update again
6. Change to "Delivered" → tracker shows completed, ticket leaves the kitchen board

**Or from Kitchen**: Click the status button on the order ticket to advance it.

---

## Scenario F: Edit Database Directly

**Goal**: Edit `data/cafe.db` in an external tool and see the UI update within seconds.

1. Open `data/cafe.db` in **DB Browser for SQLite** (or any SQLite tool)
2. Go to the `menu_items` table
3. Change the price of "Masala Chai" from 30 to 50
4. Click **Write Changes** in DB Browser
5. Wait 3 seconds → the **Customer** page shows the new price (₹50)

### Also try:
- Change `cafe_name` in the `settings` table → all pages update within 3 seconds
- Set `available = 0` for an item → it disappears from the customer menu
- Add a new row to `menu_items` → it appears on the menu

**Why it works**: Every page polls `/api/menu/version` and `/api/config/version` every 3 seconds. These endpoints compute a hash of the database content. When the hash changes (because you edited the DB externally), the page reloads data from the API.

---

## Scenario G: Change Backend Code

**Goal**: Modify a pricing rule in Python, restart the server, and see the frontend reflect it.

1. Open `backend/app/services/pricing.py`
2. Find the `compute_quote` function
3. Add a discount rule, for example:
   ```python
   # 10% discount on orders above ₹200
   if subtotal > 200:
       discount = round(subtotal * 0.10, 2)
       subtotal = round(subtotal - discount, 2)
   ```
4. **Save** the file → the server auto-reloads (uvicorn --reload)
5. Go to the **Customer** page → add items totalling more than ₹200
6. Open the cart → the total now includes the 10% discount

### Also try:
- Change the service charge formula in `pricing.py`
- Add a new status to the default `order_statuses` in `seed.py` (requires reseed — delete `data/cafe.db` and restart)
- Change a validation rule in `routers/orders.py`

**Why it works**: The frontend never computes prices — it always calls `/api/quote` on the server. So changing the pricing logic in Python immediately affects what the frontend displays.

---

## Summary

| Scenario | What to Change | Where | Update Speed |
|----------|---------------|-------|-------------|
| A | Item price | Admin / Swagger | Instant (WebSocket) |
| B | Item availability | Admin / Swagger | Instant (WebSocket) |
| C | Cafe name / colours | Admin settings | Instant (WebSocket) |
| D | Tax percentage | Admin settings | Instant (WebSocket) |
| E | Order status | Swagger / Kitchen | Instant (WebSocket) |
| F | Database directly | DB Browser for SQLite | ~3 seconds (polling) |
| G | Python pricing code | Code editor | On server restart |

All scenarios demonstrate the same principle: **the frontend is a pure display layer**. All business logic, data, and configuration live on the backend, and the frontend fetches everything from the API.

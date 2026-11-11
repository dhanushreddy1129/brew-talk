# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Brew Talk System                      │
├──────────────────────┬──────────────────────────────────┤
│      Frontend        │           Backend                │
│  (Vanilla HTML/JS)   │     (FastAPI + SQLite)           │
│                      │                                  │
│  ┌─────────────┐     │  ┌──────────────┐               │
│  │  Landing     │────▶│  │  Pages Router │               │
│  │  /landing    │     │  │  (serves HTML)│               │
│  └─────────────┘     │  └──────────────┘               │
│                      │                                  │
│  ┌─────────────┐     │  ┌──────────────┐  ┌─────────┐ │
│  │  Customer    │────▶│  │  Menu Router  │──│ SQLite  │ │
│  │  /m/{table}  │     │  │  Order Router │  │ cafe.db │ │
│  └─────────────┘     │  │  AI Router    │  └─────────┘ │
│                      │  │  Quote Router │               │
│  ┌─────────────┐     │  └──────────────┘               │
│  │  Kitchen     │────▶│                                 │
│  │  /kitchen    │     │  ┌──────────────┐  ┌─────────┐ │
│  └─────────────┘     │  │  WebSocket    │──│EventHub │ │
│                      │  │  /ws/{channel}│  └─────────┘ │
│  ┌─────────────┐     │  └──────────────┘               │
│  │  Admin       │────▶│                                 │
│  │  /admin      │     │  ┌──────────────┐  ┌─────────┐ │
│  └─────────────┘     │  │  Admin Router │──│Settings │ │
│                      │  │  Settings API │  └─────────┘ │
│                      │  └──────────────┘               │
└──────────────────────┴──────────────────────────────────┘
```

## Folder Structure

```
brew-talk/
├── backend/
│   ├── app/
│   │   ├── main.py              # App creation, router registration, static mount
│   │   ├── core/
│   │   │   ├── config.py        # Environment settings (pydantic-settings)
│   │   │   ├── security.py      # Admin auth, order tokens
│   │   │   └── rate_limit.py    # In-memory rate limiting
│   │   ├── db/
│   │   │   ├── database.py      # Engine, session, version hashing
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   └── seed.py          # Initial data (13+ menu items, settings)
│   │   ├── schemas/
│   │   │   ├── menu.py          # Menu item pydantic models
│   │   │   ├── orders.py        # Order & quote pydantic models
│   │   │   ├── settings.py      # Settings pydantic models
│   │   │   └── ai.py            # Voice order request/response models
│   │   ├── routers/
│   │   │   ├── health.py        # GET /api/health
│   │   │   ├── menu.py          # GET /api/menu, /api/menu/version
│   │   │   ├── orders.py        # POST /api/orders, /api/quote, etc.
│   │   │   ├── ai.py            # POST /api/ai/voice-order
│   │   │   ├── admin.py         # Menu CRUD, stats (admin only)
│   │   │   ├── settings.py      # GET /api/config, PUT /api/settings
│   │   │   ├── ws.py            # WebSocket /ws/{channel}
│   │   │   └── pages.py         # HTML page serving
│   │   └── services/
│   │       ├── pricing.py       # Tax, service charge, quote computation
│   │       ├── ai_service.py    # Groq AI + keyword fallback
│   │       └── events.py        # WebSocket event hub (broadcast)
│   ├── tests/
│   │   ├── conftest.py          # Test fixtures
│   │   └── test_api.py          # API tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── shared/
│   │   ├── css/
│   │   │   ├── tokens.css       # CSS custom properties (design tokens)
│   │   │   └── base.css         # Reset, typography, utility classes
│   │   └── js/
│   │       ├── api.js           # Fetch wrapper (get, post, put, etc.)
│   │       ├── socket.js        # WebSocket manager with reconnect
│   │       ├── format.js        # Price formatting, time-ago, dates
│   │       └── theme.js         # Config loading, CSS variable application
│   ├── customer/                # Customer ordering page
│   ├── kitchen/                 # Kitchen display board
│   ├── admin/                   # Admin dashboard
│   ├── landing/                 # Landing / welcome page
│   └── assets/                  # Icons, sounds, images
├── data/
│   └── cafe.db                  # SQLite database (auto-created)
├── docs/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   └── TEACHER_DEMO.md
└── scripts/
    ├── run.bat                  # Windows launcher
    ├── run.sh                   # Unix launcher
    └── smoke_test.py            # End-to-end smoke tests
```

## Data Flow

### 1. Configuration Flow
Settings stored in the `settings` table drive ALL branding and behavior:
- Frontend loads `/api/config` → applies CSS variables
- Polls `/api/config/version` every 3 seconds for external DB changes
- WebSocket `settings_changed` event for admin-panel changes

### 2. Menu Flow
- Menu items stored in `menu_items` table
- Frontend loads `/api/menu` → renders cards
- Polls `/api/menu/version` every 3 seconds
- WebSocket `menu_changed` event on admin edits

### 3. Order Flow
1. Customer adds items to cart (client-side)
2. Cart changes trigger `POST /api/quote` → server computes totals
3. Customer places order → `POST /api/orders` → server validates, prices from DB
4. Server broadcasts `order_new` via WebSocket → kitchen gets it instantly
5. Kitchen updates status → `PATCH /api/orders/{id}/status` → broadcasts `order_update`
6. Customer's tracker updates via WebSocket channel `orders_{id}`

### 4. Voice Order Flow
1. Browser captures speech via Web Speech API
2. Transcript sent to `POST /api/ai/voice-order`
3. If Groq API key set: AI parses intent, returns cart actions
4. If no key: keyword matcher finds menu items in transcript
5. Cart actions applied client-side, prices always from DB

## Key Design Decisions

### Backend-Driven UI
Nothing is hard-coded in the frontend. Every label, color, price, and status name comes from the API. This means:
- Change `cafe_name` in settings → all pages update
- Change `color_primary` → theme updates live
- Change `tax_percent` → cart totals recalculate
- Change `order_statuses` → tracker and kitchen board adapt

### Server-Side Pricing Only
The frontend never computes totals. It calls `/api/quote` which uses `services/pricing.py`. This means changing the pricing formula in one Python file changes all totals everywhere.

### Dual Refresh Strategy
- **WebSocket**: instant updates for changes made through the app
- **ETag Polling**: catches changes made directly to the SQLite database (e.g., via DB Browser)

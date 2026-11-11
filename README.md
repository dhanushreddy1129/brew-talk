# Brew Talk ☕
> **Voice-Order QR Menu Web App for Artisan Cafes**  
> Conversational ordering with an AI barista where changes reflect live across Customer, Kitchen, and Admin screens in real time.

---

## 🌟 Highlights

- 🎙 **Voice Ordering** — English-first conversational ordering with real-time speech recognition and MediaRecorder + Groq Whisper AI fallback.
- 📱 **QR Menu Experience** — Unique URL and 3D tent QR card generator for every table (`/m/{table}`).
- 👨‍🍳 **Kitchen Display System (KDS)** — Live ticket rail with status progression (`New` → `Preparing` → `Ready` → `Delivered`) and sound chimes.
- ⚙️ **Admin Dashboard** — Instant menu CRUD, photo previews, live WebSocket event stream, 24h analytics, and runtime Groq API key manager.
- ⚡ **Zero-Build Architecture** — Pure FastAPI backend + Vanilla ES Modules and CSS custom properties on the frontend. No Node.js build step.
- 🔄 **Real-Time WebSockets** — Server-sent events instantly update menu items, prices, availability, and orders across all devices.
- 🍱 **30 Artisan Items Across 7 Categories** — Starters, Chinese, Rotis & Breads, Beverages, Breakfast, Meals, and Desserts.

---

## 🚀 Quick Start

### Windows
```bat
scripts\run.bat
```

### macOS / Linux
```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

The script will automatically:
1. Create a Python virtual environment (if not already created)
2. Install dependencies from `backend/requirements.txt`
3. Launch the server at **http://localhost:8000**

---

## 🌐 Application URLs

| Screen | URL | Description | Credentials |
|---|---|---|---|
| 🚪 **Landing / Door** | `http://localhost:8000/landing` | Camera QR scanner, 3D Table Stands gallery | Public |
| ☕ **Customer Menu** | `http://localhost:8000/m/1` | Voice order, touch tray, live SVG cup tracker | Public |
| 🍳 **Kitchen Board** | `http://localhost:8000/kitchen` | Live ticket rail with status controls | Password: `brewtalk2024` |
| 📊 **Admin Panel** | `http://localhost:8000/admin` | Menu CRUD, branding, QR generator, stats | Password: `brewtalk2024` |
| 📖 **API Docs** | `http://localhost:8000/docs` | Swagger UI documentation | Public |
| 🩺 **Health Check** | `http://localhost:8000/api/health` | Service and DB connectivity status | Public |

---

## 🤖 AI Setup (Groq)

Brew Talk features a dual-path voice engine:
1. **Intelligent Keyword & Multilingual NLP Matcher** — Built-in, zero configuration required.
2. **Groq Llama 3 & Whisper AI** — For natural language understanding:
   - Go to `http://localhost:8000/admin` → **Settings** tab
   - Paste your free Groq API key (get one from [console.groq.com](https://console.groq.com/keys))
   - Click **Save** — saved directly to DB, works immediately without server restart.

---

## 🛠 Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, SQLite, WebSockets, Pydantic v2
- **Frontend**: Vanilla HTML5, CSS3 Custom Properties (Design Tokens), Vanilla ES Modules
- **Voice**: Web Speech API + HTML5 MediaRecorder + Groq Whisper (`whisper-large-v3`)
- **Networking**: Uvicorn ASGI server, channel-based WebSocket hub

---

## 🧪 Testing

```bash
# Unit tests
cd backend
python -m pytest tests/ -v

# Automated smoke test (requires server running)
python scripts/smoke_test.py
```

---

## 📄 License

MIT License — free for educational and commercial use.

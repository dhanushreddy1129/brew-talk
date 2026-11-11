# Brew Talk ☕

> Voice-Order QR Menu for Cafes — ordering as a conversation with a friendly barista.

## Quick Start

### Windows
```bat
scripts\run.bat
```

### macOS / Linux
```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

The script will:
1. Create a Python virtual environment (if missing)
2. Install dependencies from `backend/requirements.txt`
3. Start the server on **http://localhost:8000**

### URLs

| Page | URL | Description |
|------|-----|-------------|
| Landing | http://localhost:8000/landing | Welcome page with table selector |
| Customer Menu | http://localhost:8000/m/1 | Order menu for Table 1 |
| Kitchen Board | http://localhost:8000/kitchen | Live order management |
| Admin Panel | http://localhost:8000/admin | Dashboard for managing everything |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| Health Check | http://localhost:8000/api/health | Server status |

### Default Admin Password
```
brewtalk2024
```

## Features

- **🎤 Voice Ordering** — Speak your order in English, Hindi, Kannada, Tamil, or Telugu
- **📱 QR Menu** — Each table gets a unique QR code linking to the order page
- **🔄 Real-time Updates** — WebSocket-powered live updates across all screens
- **🧾 Server-side Pricing** — Tax, service charge, and totals computed on the backend
- **🎨 Fully Configurable** — Change branding, colors, menu, and pricing from the admin panel
- **🌙 Dark Mode** — Toggle between light and dark themes
- **📊 Analytics** — 24-hour order stats and top items

## AI Setup (Optional)

Brew Talk can use Groq's AI to understand natural language voice orders. Without it, a keyword matcher handles basic orders.

1. Get a free API key from [groq.com](https://groq.com)
2. Edit `backend/.env`:
   ```
   GROQ_API_KEY=your_key_here
   GROQ_MODEL=openai/gpt-oss-120b
   ```
3. Restart the server

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLite, WebSockets
- **Frontend**: Vanilla HTML, CSS, JavaScript (ES Modules)
- **AI**: Groq (OpenAI-compatible) with keyword fallback
- **Database**: SQLite (file-based, zero config)

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed structure.

## Tests

```bash
# Unit tests
cd backend && python -m pytest tests/ -v

# Smoke tests (server must be running)
python scripts/smoke_test.py
```

## License

MIT

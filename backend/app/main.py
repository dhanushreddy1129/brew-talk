"""Brew Talk — Voice-Order QR Menu for Cafes"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine, Base, SessionLocal
from app.db.models import MenuItem, Order, OrderItem, Setting  # noqa: F401 — register models
from app.db.seed import seed_database
from app.routers import health, menu, orders, ai, admin, settings, ws, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed data on startup."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Brew Talk API",
    description="Voice-Order QR Menu for Cafes",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow everything during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(ai.router)
app.include_router(admin.router)
app.include_router(settings.router)
app.include_router(ws.router)
app.include_router(pages.router)

# Static files — mount AFTER routers so API routes take priority
frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

"""Serve frontend HTML pages."""

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter(tags=["pages"])

# Resolve paths relative to the project root (brew-talk/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


@router.get("/")
async def root() -> RedirectResponse:
    """Redirect root to the landing page."""
    return RedirectResponse(url="/landing")


@router.get("/landing")
async def landing_page() -> FileResponse:
    """Serve the landing page."""
    path = os.path.join(FRONTEND_DIR, "landing", "index.html")
    return FileResponse(path, media_type="text/html")


@router.get("/m/{table_number}")
async def customer_page(table_number: int) -> FileResponse:
    """Serve the customer menu page for a given table."""
    path = os.path.join(FRONTEND_DIR, "customer", "index.html")
    return FileResponse(path, media_type="text/html")


@router.get("/kitchen")
async def kitchen_page() -> FileResponse:
    """Serve the kitchen display page."""
    path = os.path.join(FRONTEND_DIR, "kitchen", "index.html")
    return FileResponse(path, media_type="text/html")


@router.get("/admin")
async def admin_page() -> FileResponse:
    """Serve the admin dashboard page."""
    path = os.path.join(FRONTEND_DIR, "admin", "index.html")
    return FileResponse(path, media_type="text/html")

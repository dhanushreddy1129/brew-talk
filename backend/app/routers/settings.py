"""Settings endpoints — public config and admin management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.database import get_db, get_settings_version
from app.db.models import Setting
from app.schemas.settings import SettingResponse, SettingUpdate, ConfigResponse
from app.services.events import event_hub

router = APIRouter(tags=["settings"])


@router.get("/api/config", response_model=ConfigResponse)
async def get_public_config(db: Session = Depends(get_db)) -> dict:
    """Return all settings as a flat key-value dict (public, no auth).
    Sensitive keys like groq_api_key are masked."""
    settings = db.query(Setting).all()
    config = {}
    for s in settings:
        # Mask sensitive keys so they never reach the frontend
        if s.key in ("groq_api_key",):
            config[s.key] = "***" if s.value else ""
        else:
            config[s.key] = s.value
    return {"config": config}


@router.get("/api/config/version")
async def config_version(db: Session = Depends(get_db)) -> dict:
    """Lightweight polling endpoint — returns the current settings version hash."""
    return {"version": get_settings_version(db)}


@router.get(
    "/api/settings",
    response_model=list[SettingResponse],
    dependencies=[Depends(require_admin)],
)
async def list_settings(db: Session = Depends(get_db)) -> list[Setting]:
    """List all settings with metadata (admin only)."""
    return db.query(Setting).order_by(Setting.category, Setting.key).all()


@router.put(
    "/api/settings/{key}",
    response_model=SettingResponse,
    dependencies=[Depends(require_admin)],
)
async def update_setting(
    key: str,
    payload: SettingUpdate,
    db: Session = Depends(get_db),
) -> Setting:
    """Update a setting value (admin only). Creates the setting if it doesn't exist."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        # Auto-create unknown settings (e.g. groq_api_key added after initial seed)
        category = "ai" if key in ("groq_api_key", "groq_model") else "general"
        setting = Setting(key=key, value=payload.value, category=category, description="")
        db.add(setting)
    else:
        setting.value = payload.value

    db.commit()
    db.refresh(setting)

    # Don't broadcast the actual API key value
    broadcast_value = "***" if key == "groq_api_key" and payload.value else payload.value
    await event_hub.broadcast(
        "settings_changed",
        {"key": key, "value": broadcast_value},
        channel="general",
    )

    return setting

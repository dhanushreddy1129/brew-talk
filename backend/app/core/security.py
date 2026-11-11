"""Security utilities: admin auth dependency, order token generation & verification."""

import hashlib
import hmac
from fastapi import Header, HTTPException, Depends

from app.core.config import get_settings


async def require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> str:
    """FastAPI dependency that checks the X-Admin-Key header against ADMIN_PASSWORD."""
    settings = get_settings()
    if not hmac.compare_digest(x_admin_key, settings.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key


def generate_order_token(order_id: int) -> str:
    """Generate a HMAC-based token for a given order ID."""
    settings = get_settings()
    key = settings.ADMIN_PASSWORD.encode("utf-8")
    message = f"order-{order_id}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_order_token(order_id: int, token: str) -> bool:
    """Verify that a token is valid for the given order ID."""
    expected = generate_order_token(order_id)
    return hmac.compare_digest(expected, token)

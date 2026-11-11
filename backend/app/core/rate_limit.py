"""Simple in-memory rate limiter using a dict of IP -> list of timestamps."""

import time
from typing import Callable

from fastapi import HTTPException, Request


# Global store: IP -> list of request timestamps
_rate_store: dict[str, list[float]] = {}


def rate_limit(max_calls: int = 60, period: int = 60) -> Callable:
    """
    Returns a FastAPI dependency that enforces rate limiting.

    Args:
        max_calls: Maximum number of calls allowed within the period.
        period: Time window in seconds.
    """

    async def _rate_limit_dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{max_calls}:{period}"
        now = time.time()

        # Get or create the timestamp list for this key
        if key not in _rate_store:
            _rate_store[key] = []

        # Prune timestamps outside the current window
        _rate_store[key] = [ts for ts in _rate_store[key] if now - ts < period]

        if len(_rate_store[key]) >= max_calls:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {max_calls} requests per {period}s.",
            )

        _rate_store[key].append(now)

    return _rate_limit_dependency

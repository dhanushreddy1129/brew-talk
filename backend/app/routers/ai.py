"""AI voice-order endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.database import get_db
from app.db.models import MenuItem
from app.schemas.ai import VoiceOrderRequest, AudioOrderRequest, VoiceOrderResponse
from app.services.ai_service import process_voice_order, process_audio_order

router = APIRouter(tags=["ai"])


@router.post(
    "/api/ai/voice-order",
    response_model=VoiceOrderResponse,
    dependencies=[Depends(rate_limit(max_calls=30, period=60))],
)
async def voice_order(
    payload: VoiceOrderRequest,
    db: Session = Depends(get_db),
) -> VoiceOrderResponse:
    """Process a voice transcript and return a reply with cart actions."""
    menu_items = db.query(MenuItem).order_by(MenuItem.sort_order).all()

    return await process_voice_order(
        transcript=payload.transcript,
        language=payload.language,
        menu_items=menu_items,
        db=db,
    )


@router.post(
    "/api/ai/audio-order",
    response_model=VoiceOrderResponse,
    dependencies=[Depends(rate_limit(max_calls=30, period=60))],
)
async def audio_order(
    payload: AudioOrderRequest,
    db: Session = Depends(get_db),
) -> VoiceOrderResponse:
    """Process raw recorded audio with Groq Whisper and return cart actions."""
    menu_items = db.query(MenuItem).order_by(MenuItem.sort_order).all()

    return await process_audio_order(
        audio_base64=payload.audio_base64,
        mime_type=payload.mime_type,
        language=payload.language,
        menu_items=menu_items,
        db=db,
    )

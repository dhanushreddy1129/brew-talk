"""Pydantic schemas for AI voice-ordering."""

from typing import Literal

from pydantic import BaseModel, Field


class CartAction(BaseModel):
    """A single add / remove / set action on the customer's cart."""

    action: Literal["add", "remove", "set"]
    menu_item_id: int
    item_name: str
    quantity: int
    price: float


class VoiceOrderRequest(BaseModel):
    """Incoming voice transcript from the customer."""

    transcript: str
    language: str = "en"
    table_number: int = Field(ge=1)


class AudioOrderRequest(BaseModel):
    """Audio base64 payload from browser MediaRecorder for Groq Whisper."""

    audio_base64: str
    mime_type: str = "audio/webm"
    language: str = "en"
    table_number: int = Field(ge=1)


class VoiceOrderResponse(BaseModel):
    """AI reply and cart actions returned to the frontend."""

    reply: str
    cart_actions: list[CartAction]
    language: str

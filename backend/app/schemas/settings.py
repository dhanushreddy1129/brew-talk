"""Pydantic schemas for application settings."""

from pydantic import BaseModel, ConfigDict


class SettingResponse(BaseModel):
    """A single setting with metadata."""

    key: str
    value: str
    category: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class SettingUpdate(BaseModel):
    """Payload for updating a setting value."""

    value: str


class ConfigResponse(BaseModel):
    """All settings returned as a flat key-value dict."""

    config: dict[str, str]

from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator


# ─── Request Bodies ───────────────────────────────────────────────────────────

class ShortenRequest(BaseModel):
    """What the client sends when creating a short URL."""
    long_url: str
    expires_at: datetime | None = None  # Optional expiry date

    @field_validator("long_url")
    @classmethod
    def must_be_valid_url(cls, v: str) -> str:
        """Reject URLs that don't start with http:// or https://"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if len(v) > 2048:
            raise ValueError("URL is too long (max 2048 characters)")
        return v


# ─── Response Bodies ──────────────────────────────────────────────────────────

class ShortenResponse(BaseModel):
    """What we return after creating a short URL."""
    short_code: str
    short_url: str       # full URL e.g. "http://localhost:8000/3xK9mP"
    long_url: str
    created_at: datetime
    expires_at: datetime | None


class URLStatsResponse(BaseModel):
    """Stats for a specific short URL."""
    short_code: str
    long_url: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None


class HealthResponse(BaseModel):
    """Health check response showing status of each service."""
    status: str
    database: str
    cache: str
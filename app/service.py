from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import URL, Click
from app.encoder import encode
from app.cache import cache_get, cache_set, cache_delete
from app.schemas import ShortenRequest


# ─── Create a Short URL ───────────────────────────────────────────────────────

def create_short_url(request: ShortenRequest, db: Session) -> URL:
    """
    Full flow for shortening a URL:
    1. Insert a new row into the DB (get auto-increment ID)
    2. Encode that ID to base62 → short_code
    3. Update the row with the short_code
    4. Cache the mapping in Redis
    5. Return the URL object
    """
    # Step 0: Check if this long_url was already shortened
    existing = db.query(URL).filter(URL.long_url == request.long_url).first()
    if existing:
        # Warm the cache in case it expired, then return the existing record
        cache_set(existing.short_code, existing.long_url)
        return existing
    # Step 1: Insert with a placeholder short_code first
    # We need the DB to generate the ID before we can encode it
    url_record = URL(
        short_code="PENDING",   # temporary value
        long_url=request.long_url,
        expires_at=request.expires_at,
    )
    db.add(url_record)
    db.flush()  # sends INSERT to DB and populates url_record.id (but doesn't commit yet)

    # Step 2: Now encode the real ID
    short_code = encode(url_record.id)

    # Step 3: Update with the real short_code
    url_record.short_code = short_code
    db.commit()
    db.refresh(url_record)

    # Step 4: Warm the cache immediately so first redirect is fast
    cache_set(short_code, request.long_url)

    return url_record


# ─── Redirect (the hot path) ──────────────────────────────────────────────────

def resolve_short_code(short_code: str, db: Session, request_info: dict) -> str | None:
    """
    Resolve a short code to a long URL.
    
    Cache-first strategy:
        1. Check Redis (fast: ~0.1ms)
        2. If miss, check MySQL (slower: ~5ms)
        3. If found in MySQL, backfill Redis
        4. Log the click asynchronously
    
    Returns the long_url string, or None if not found.
    """
    # ── Fast path: Redis cache hit ──
    long_url = cache_get(short_code)
    if long_url:
        _log_click(short_code, db, request_info)
        return long_url

    # ── Slow path: DB lookup ──
    url_record = (
        db.query(URL)
        .filter(URL.short_code == short_code)
        .first()
    )

    if not url_record:
        return None  # 404

    # Check if the link has expired
    if url_record.expires_at and url_record.expires_at < datetime.utcnow():
        return None  # treat expired links as 404

    # Backfill cache so next request is fast
    cache_set(short_code, url_record.long_url)

    # Log the click
    _log_click(short_code, db, request_info)

    # Increment click count in DB
    db.query(URL).filter(URL.short_code == short_code).update(
        {URL.click_count: URL.click_count + 1}
    )
    db.commit()

    return url_record.long_url


# ─── Get Stats ────────────────────────────────────────────────────────────────

def get_url_stats(short_code: str, db: Session) -> URL | None:
    """Return URL record with click count, or None if not found."""
    return db.query(URL).filter(URL.short_code == short_code).first()


# ─── Delete a URL ─────────────────────────────────────────────────────────────

def delete_short_url(short_code: str, db: Session) -> bool:
    """
    Delete a URL from DB and invalidate its cache entry.
    Returns True if deleted, False if not found.
    """
    url_record = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_record:
        return False

    db.delete(url_record)
    db.commit()
    cache_delete(short_code)  # remove from Redis too
    return True


# ─── Private helper ───────────────────────────────────────────────────────────

def _log_click(short_code: str, db: Session, request_info: dict):
    """Insert a row into the clicks table for analytics."""
    click = Click(
        short_code=short_code,
        user_agent=request_info.get("user_agent"),
        ip_address=request_info.get("ip_address"),
    )
    db.add(click)
    # Note: caller handles db.commit()
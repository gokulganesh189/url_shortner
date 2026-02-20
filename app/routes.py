from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ShortenRequest, ShortenResponse, URLStatsResponse, HealthResponse
from app.service import create_short_url, resolve_short_code, get_url_stats, delete_short_url
from app.cache import cache_ping
from app.config import settings

router = APIRouter()


# ─── Health Check ─────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """
    Check if the API, database, and Redis cache are all healthy.
    Run this after starting docker-compose to verify everything connected.
    """
    # Test DB connection
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Test Redis connection
    redis_status = "healthy" if cache_ping() else "unhealthy"

    overall = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    return HealthResponse(status=overall, database=db_status, cache=redis_status)


# ─── Shorten a URL ────────────────────────────────────────────────────────────

@router.post("/shorten", response_model=ShortenResponse, status_code=201, tags=["URLs"])
def shorten_url(request: ShortenRequest, db: Session = Depends(get_db)):
    """
    Create a short URL from a long one.
    
    Request body:
        {
            "long_url": "https://very-long-url.com/...",
            "expires_at": "2025-12-31T23:59:59"  (optional)
        }
    
    Returns the short URL like: http://localhost:8000/3xK9mP
    """
    url_record = create_short_url(request, db)

    return ShortenResponse(
        short_code=url_record.short_code,
        short_url=f"{settings.base_url}/{url_record.short_code}",
        long_url=url_record.long_url,
        created_at=url_record.created_at,
        expires_at=url_record.expires_at,
    )


# ─── Redirect ─────────────────────────────────────────────────────────────────

@router.get("/{short_code}", tags=["URLs"])
def redirect(short_code: str, request: Request, db: Session = Depends(get_db)):
    """
    The core endpoint. Visit http://localhost:8000/3xK9mP → redirected to original URL.
    
    Uses 302 (temporary redirect) so:
    - Browsers always hit our server (enabling click analytics)
    - We can update the destination URL later if needed
    
    Flow:
        1. Check Redis cache (fast path ~0.1ms)
        2. If miss, check MySQL (slow path ~5ms)  
        3. Log the click for analytics
        4. Redirect to long URL
    """
    request_info = {
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else None,
    }

    long_url = resolve_short_code(short_code, db, request_info)

    if not long_url:
        raise HTTPException(
            status_code=404,
            detail=f"Short code '{short_code}' not found or has expired"
        )

    # 302 = temporary redirect (browser won't cache it, we see every click)
    return RedirectResponse(url=long_url, status_code=302)


# ─── Get URL Stats ────────────────────────────────────────────────────────────

@router.get("/stats/{short_code}", response_model=URLStatsResponse, tags=["Analytics"])
def get_stats(short_code: str, db: Session = Depends(get_db)):
    """
    Get click stats for a short URL.
    
    Returns:
        - Original long URL
        - Total click count
        - Creation date
        - Expiry date (if set)
    """
    url_record = get_url_stats(short_code, db)

    if not url_record:
        raise HTTPException(status_code=404, detail="Short code not found")

    return URLStatsResponse(
        short_code=url_record.short_code,
        long_url=url_record.long_url,
        click_count=url_record.click_count,
        created_at=url_record.created_at,
        expires_at=url_record.expires_at,
    )


# ─── Delete a URL ─────────────────────────────────────────────────────────────

@router.delete("/{short_code}", status_code=204, tags=["URLs"])
def delete_url(short_code: str, db: Session = Depends(get_db)):
    """
    Delete a short URL. Removes from both MySQL and Redis cache.
    Returns 204 No Content on success, 404 if not found.
    """
    deleted = delete_short_url(short_code, db)

    if not deleted:
        raise HTTPException(status_code=404, detail="Short code not found")
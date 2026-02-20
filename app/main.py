from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Creates DB tables if they don't exist yet.
    (In production you'd use Alembic migrations instead)
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready")
    yield
    print("👋 Shutting down")


app = FastAPI(
    title="URL Shortener API",
    description="""
A production-style URL shortener built with:
- **FastAPI** — async Python web framework
- **MySQL** — persistent storage with full analytics
- **Redis** — high-speed caching layer (100x faster reads)

## How it works
1. `POST /shorten` → get a short URL
2. `GET /{short_code}` → redirected to original URL (checks Redis first, then MySQL)
3. `GET /stats/{short_code}` → see click analytics
4. `DELETE /{short_code}` → remove a URL
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # In production, replace * with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],        # Allow GET, POST, DELETE, etc.
    allow_headers=["*"],
)

app.include_router(router)
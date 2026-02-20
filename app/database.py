from datetime import datetime
from sqlalchemy import (
    BigInteger, Column, DateTime, Index, String, Text, create_engine
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings


# ─── Engine & Session ─────────────────────────────────────────────────────────
engine = create_engine(
    settings.mysql_url,
    pool_size=10,          # keep 10 connections open (connection pooling)
    max_overflow=20,       # allow 20 extra connections at peak
    pool_pre_ping=True,    # test connection health before using it
    echo=False,            # set True to log all SQL queries (useful for debugging)
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ─── Base class all models inherit from ──────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── URL Table ───────────────────────────────────────────────────────────────
class URL(Base):
    __tablename__ = "urls"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    short_code  = Column(String(20), unique=True, nullable=False, index=True)
    long_url    = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    expires_at  = Column(DateTime, nullable=True)
    click_count = Column(BigInteger, default=0)


# ─── Click Analytics Table ───────────────────────────────────────────────────
class Click(Base):
    __tablename__ = "clicks"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    short_code = Column(String(20), nullable=False, index=True)
    clicked_at = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)


# ─── Dependency for FastAPI routes ───────────────────────────────────────────
def get_db():
    """
    FastAPI dependency that provides a DB session per request.
    Automatically closes the session when the request finishes.
    
    Usage in route:
        def my_route(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
Tests for the URL Shortener.

Run with:  pytest tests/ -v

Note: These are unit tests using mocked DB and Redis.
For integration tests, run the full docker-compose stack first.
"""
import pytest
from app.encoder import encode, decode


# ─── Encoder Tests ────────────────────────────────────────────────────────────

def test_encode_returns_7_chars():
    assert len(encode(1)) == 7
    assert len(encode(999_999_999)) == 7


def test_encode_decode_roundtrip():
    """Encode then decode should return the original number."""
    for num in [1, 100, 99999, 3_521_614_606_207]:
        assert decode(encode(num)) == num


def test_different_ids_produce_different_codes():
    """No two IDs should produce the same short code."""
    codes = {encode(i) for i in range(1, 1000)}
    assert len(codes) == 999  # all unique


def test_encode_zero():
    result = encode(0)
    assert len(result) == 7
    assert all(c == "0" for c in result)


# ─── URL Validation Tests (via schemas) ───────────────────────────────────────

from app.schemas import ShortenRequest
from pydantic import ValidationError


def test_valid_url_accepted():
    req = ShortenRequest(long_url="https://example.com")
    assert req.long_url == "https://example.com"


def test_invalid_url_rejected():
    with pytest.raises(ValidationError):
        ShortenRequest(long_url="not-a-url")


def test_http_url_accepted():
    req = ShortenRequest(long_url="http://example.com")
    assert req.long_url == "http://example.com"


def test_url_too_long_rejected():
    with pytest.raises(ValidationError):
        ShortenRequest(long_url="https://" + "a" * 2050)
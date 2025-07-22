import json
from datetime import datetime, timedelta, timezone
import pytest
import builtins
from pathlib import Path

from offers_sdk.auth import AuthManager, TOKEN_CACHE_FILE
from offers_sdk.exceptions import (
    MissingTokenCacheKeysError,
    TokenCacheError,
)


@pytest.fixture(autouse=True)
def cleanup_cache_file():
    if TOKEN_CACHE_FILE.exists():
        TOKEN_CACHE_FILE.unlink()
    yield
    if TOKEN_CACHE_FILE.exists():
        TOKEN_CACHE_FILE.unlink()


def test_load_cached_token_success():
    token_data = {
        "access_token": "cached-token",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    }
    TOKEN_CACHE_FILE.write_text(json.dumps(token_data))

    auth = AuthManager("refresh", "https://example.com")
    auth._load_cached_token()

    assert auth.access_token == "cached-token"
    assert isinstance(auth.expires_at, datetime)


def test_load_cached_token_missing_keys():
    TOKEN_CACHE_FILE.write_text(json.dumps({"access_token": "incomplete"}))

    auth = AuthManager("x", "https://example.com")

    with pytest.raises(TokenCacheError):
        auth._load_cached_token()


def test_load_cached_token_invalid_json():
    TOKEN_CACHE_FILE.write_text("not-a-json-string")

    auth = AuthManager("x", "https://example.com")

    with pytest.raises(TokenCacheError):
        auth._load_cached_token()


def test_save_token_to_file_failure(monkeypatch):
    auth = AuthManager("x", "https://example.com")
    auth.access_token = "abc"
    auth.expires_at = datetime.now(timezone.utc)

    def mock_write_text(*args, **kwargs):
        raise OSError("Simulated write failure")

    monkeypatch.setattr(Path, "write_text", mock_write_text)

    with pytest.raises(TokenCacheError) as exc:
        auth._save_token_to_file()

    assert "Failed to write access token to cache" in str(exc.value)
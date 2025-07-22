import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx
from httpx import Response

from offers_sdk.auth import AuthManager, TOKEN_CACHE_FILE
from offers_sdk.exceptions import (
    TokenRefreshError,
    UnexpectedAPIResponseError,
    MissingTokenCacheKeysError,
    TokenCacheError,
)


# Make all tests in file async
pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def cleanup_cache_file():
    """Ensure no token cache interferes with tests."""
    if TOKEN_CACHE_FILE.exists():
        TOKEN_CACHE_FILE.unlink()
    yield
    if TOKEN_CACHE_FILE.exists():
        TOKEN_CACHE_FILE.unlink()


@respx.mock
async def test_get_access_token_success():
    dummy_token = "fake-access-token"

    # Mock the auth endpoint
    respx.post("https://example.com/auth").mock(
        return_value=Response(201, json={"access_token": dummy_token})
    )

    auth = AuthManager(refresh_token="dummy-refresh", base_url="https://example.com")
    token = await auth.get_access_token()

    assert token == dummy_token
    assert auth.access_token == dummy_token
    assert auth.expires_at > datetime.now(timezone.utc)

    # Verify token was saved to file
    with open(TOKEN_CACHE_FILE, "r") as f:
        saved = json.load(f)
    assert saved["access_token"] == dummy_token


@respx.mock
async def test_get_access_token_failure(monkeypatch):
    monkeypatch.setattr(AuthManager, "_load_cached_token", lambda self: None)

    respx.post("https://example.com/auth").mock(
        return_value=Response(400, json={"error": "invalid token"})
    )

    auth = AuthManager(refresh_token="bad-token", base_url="https://example.com")

    with pytest.raises(TokenRefreshError) as exc:
        await auth.get_access_token()

    assert "Bad request" in str(exc.value)


@respx.mock
async def test_token_is_reused_if_not_expired():
    auth = AuthManager(refresh_token="x", base_url="https://example.com")
    auth.access_token = "cached-token"
    auth.expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)

    token = await auth.get_access_token()

    assert token == "cached-token"


@respx.mock
async def test_network_error_raises_token_refresh_error(monkeypatch):
    monkeypatch.setattr(AuthManager, "_load_cached_token", lambda self: None)

    respx.post("https://example.com/auth").mock(
        side_effect=httpx.ConnectTimeout("Simulated timeout")
    )

    auth = AuthManager("dummy-refresh", "https://example.com")

    with pytest.raises(TokenRefreshError) as exc:
        await auth.get_access_token()

    assert "Network error" in str(exc.value)


@respx.mock
async def test_get_access_token_unauthorized(monkeypatch):
    monkeypatch.setattr(AuthManager, "_load_cached_token", lambda self: None)

    respx.post("https://example.com/auth").mock(
        return_value=Response(401, json={"detail": "Invalid token"})
    )

    auth = AuthManager(refresh_token="invalid-token", base_url="https://example.com")

    with pytest.raises(TokenRefreshError) as exc:
        await auth.get_access_token()

    assert "Authentication failed" in str(exc.value)


@respx.mock
async def test_get_access_token_validation_error(monkeypatch):
    monkeypatch.setattr(AuthManager, "_load_cached_token", lambda self: None)

    respx.post("https://example.com/auth").mock(
        return_value=Response(422, json={"detail": "Missing fields"})
    )

    auth = AuthManager(refresh_token="bad-data", base_url="https://example.com")

    with pytest.raises(TokenRefreshError) as exc:
        await auth.get_access_token()

    assert "Validation error" in str(exc.value)


@respx.mock
async def test_get_access_token_unexpected_status(monkeypatch):
    monkeypatch.setattr(AuthManager, "_load_cached_token", lambda self: None)

    respx.post("https://example.com/auth").mock(
        return_value=Response(500, text="Internal Server Error")
    )

    auth = AuthManager(refresh_token="x", base_url="https://example.com")

    with pytest.raises(UnexpectedAPIResponseError) as exc:
        await auth.get_access_token()

    assert "Failed to refresh access token: 500" in str(exc.value)


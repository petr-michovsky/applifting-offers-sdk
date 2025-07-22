from datetime import datetime, timedelta, timezone
from typing import Optional
import json

import httpx
from pathlib import Path

from offers_sdk.exceptions import (
    TokenRefreshError,
    UnexpectedAPIResponseError,
    TokenCacheError,
    MissingTokenCacheKeysError
)


TOKEN_CACHE_FILE = Path(".access_token.json")


class AuthManager:
    """
    Manages authentication for the Offers API using a long-lived refresh token.

    This class transparently handles short-lived access tokens (valid for 5 minutes)
    by caching them in memory and on disk. It refreshes tokens automatically if:
        - No token has been retrieved yet
        - The cached token has expired
        - The cache file does not exist or is incomplete

    Access tokens are stored locally in a JSON file (`.access_token.json`) and
    reloaded on future calls to reduce unnecessary API requests.

    Attributes:
        refresh_token (str): Long-lived refresh token provided by the user.
        base_url (str): Base URL of the Offers API.
        access_token (Optional[str]): Cached short-lived access token.
        expires_at (Optional[datetime]): UTC time when the token becomes invalid.

    Raises:
        TokenRefreshError:
            - On network errors during the refresh request
            - If the API responds with 400, 401, or 422 status codes
        UnexpectedAPIResponseError:
            - If the API returns an unhandled HTTP status code
        TokenCacheError:
            - If reading or writing the cache file fails
        MissingTokenCacheKeysError:
            - If the cache file is missing required keys
    """
    def __init__(self, refresh_token: str, base_url: str):
        self.refresh_token = refresh_token
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None


    async def get_access_token(self) -> str:
        """
        Returns a valid access token, refreshing it if expired or missing.

        Loads the token from disk if not already cached in memory. If the token
        is expired or missing, sends a refresh request to the API and updates
        the local cache file.

        Returns:
            str: A valid access token.

        Raises:
            TokenRefreshError: If the refresh request fails.
            UnexpectedAPIResponseError: If an unrecognized status is returned.
            TokenCacheError: If loading the token from disk fails.
            MissingTokenCacheKeysError: If the cache file is malformed.
        """
        now = datetime.now(timezone.utc)

        if not self.access_token or not self.expires_at:
            self._load_cached_token()

        if not self.access_token or not self.expires_at or now  >= self.expires_at:
            await self._refresh_access_token()

        return self.access_token


    def _save_token_to_file(self):
        """
        Saves the current access token and expiration time to `.access_token.json`.

        Raises:
            TokenCacheError: If writing to disk fails.
        """
        try:
            TOKEN_CACHE_FILE.write_text(json.dumps({
                "access_token": self.access_token,
                "expires_at": self.expires_at.isoformat()
            }))
        except Exception as e:
            raise TokenCacheError(f"Failed to write access token to cache: {e}") from e


    def _load_cached_token(self):
        """
        Attempts to load the cached token from `.access_token.json`.

        If the file exists and contains valid data, populates `access_token`
        and `expires_at`. Otherwise, raises appropriate exceptions.

        Raises:
            TokenCacheError: If the file cannot be read or parsed.
            MissingTokenCacheKeysError: If required keys are missing from the file.
        """
        if TOKEN_CACHE_FILE.exists():
            try:
                with open(TOKEN_CACHE_FILE, "r") as f:
                    data = json.load(f)

                    token = data.get("access_token")
                    expires = data.get("expires_at")

                    if not token or not expires:
                        raise MissingTokenCacheKeysError("Cached token file is missing 'access_token' or 'expires_at'")

                    self.access_token = token
                    self.expires_at = datetime.fromisoformat(expires)

            except Exception as e:
                raise TokenCacheError(f"Failed to load cached access token: {e}") from e


    async def _refresh_access_token(self):
        """
        Performs an HTTP POST request to /auth using the refresh token.

        On 201 success, updates `access_token` and `expires_at`.
        On error, raises a specific exception based on the status code.

        Raises:
            TokenRefreshError: On status 400, 401, 422, or network issues.
            UnexpectedAPIResponseError: On any other unexpected status code.
        """
        headers = {
            "Bearer": self.refresh_token,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/auth", headers=headers)

        except httpx.RequestError as e:
            raise TokenRefreshError(f"Network error while refreshing access token: {str(e)}") from e

        if response.status_code == 201:
            data = response.json()
            self.access_token = data['access_token']
            self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            self._save_token_to_file()

        elif response.status_code == 400:
            raise TokenRefreshError("Bad request while refreshing access token. The request was malformed.")

        elif response.status_code == 401:
            raise TokenRefreshError("Authentication failed. The refresh token is invalid.")

        elif response.status_code == 422:
            raise TokenRefreshError("Validation error: the request data did not meet schema requirements.")

        else:
            raise UnexpectedAPIResponseError(f"Failed to refresh access token: {response.status_code} {response.text}")

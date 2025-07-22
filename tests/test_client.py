import pytest

from offers_sdk.client import OffersAPIClient
from offers_sdk.exceptions import MissingConfigurationError


def test_client_from_env(monkeypatch):
    monkeypatch.setenv("REFRESH_TOKEN", "dummy-refresh")
    monkeypatch.setenv("BASE_URL", "https://example.com")

    client = OffersAPIClient.from_env()
    assert isinstance(client, OffersAPIClient)
    assert client.auth.refresh_token == "dummy-refresh"
    assert client.client.base_url.host == "example.com"


def test_client_from_env_missing_env(monkeypatch):
    monkeypatch.delenv("REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)

    with pytest.raises(MissingConfigurationError, match="Missing REFRESH_TOKEN or BASE_URL"):
        OffersAPIClient.from_env()
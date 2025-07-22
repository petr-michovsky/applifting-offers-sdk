from uuid import uuid4

import pytest
import respx
from httpx import Response

from offers_sdk.client import OffersAPIClient
from offers_sdk.exceptions import (
    InvalidProductDataError,
    ProductAlreadyRegisteredError,
    ProductNotFoundError,
    TokenRefreshError,
    UnexpectedAPIResponseError,
)
from offers_sdk.models import Product


pytestmark = pytest.mark.asyncio


@respx.mock
async def test_register_product_token_fetch_failure(monkeypatch):
    async def raise_token_error(_self):
        raise Exception("auth fail")

    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", raise_token_error)

    client = OffersAPIClient("invalid", "https://example.com")
    product = Product(id=uuid4(), name="Fail", description="auth fail", offers=[])

    with pytest.raises(TokenRefreshError, match="Failed to get access token: auth fail"):
        await client.register_product(product)


@respx.mock
async def test_register_product_success(monkeypatch):
    # Dummy product
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Test Product",
        description="A test product",
        offers=[]
    )

    async def mock_get_access_token(_self):
        return "fake-token"

    # Mock token fetch
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_get_access_token)

    # Mock /products/register response
    respx.post("https://example.com/products/register").mock(
        return_value=Response(201, json={
            "id": str(product_id),
            "name": "Test Product",
            "description": "A test product",
            "offers": []
        })
    )

    client = OffersAPIClient("dummy-refresh", "https://example.com")
    result = await client.register_product(product)

    assert result.id == product.id
    assert result.name == product.name


@respx.mock
async def test_register_product_unauthorized_then_retries(monkeypatch):
    product_id = uuid4()
    product = Product(id=product_id, name="Retry Product", description="Should retry", offers=[])

    async def mock_get_access_token(_self):
        return "fake-token"

    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_get_access_token)

    # First POST returns 401 Unauthorized
    respx.post("https://example.com/products/register").mock(
        return_value=Response(401)
    )

    # Then retry via GET offers
    respx.get(f"https://example.com/products/{product_id}/offers").mock(
        return_value=Response(200, json={
            "id": str(product_id),
            "name": "Retry Product",
            "description": "Should retry",
            "offers": []
        })
    )

    client = OffersAPIClient("dummy-refresh", "https://example.com")
    with pytest.raises(TokenRefreshError, match="Unauthorized: access token is invalid or expired."):
        await client.register_product(product)


@respx.mock
async def test_register_product_fails_with_error(monkeypatch):
    product = Product(id=uuid4(), name="Fail Product", description="Bad", offers=[])

    async def mock_get_access_token(_self):
        return "fake-token"

    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_get_access_token)

    respx.post("https://example.com/products/register").mock(
        return_value=Response(500, json={"detail": "Server error"})
    )

    client = OffersAPIClient("dummy-refresh", "https://example.com")

    with pytest.raises(UnexpectedAPIResponseError, match="500"):
        await client.register_product(product)

@respx.mock
async def test_register_product_retry_fails(monkeypatch):
    product_id = uuid4()
    product = Product(id=product_id, name="Retry Fails", description="Still bad", offers=[])

    async def mock_get_access_token(_self):
        return "fake-token"
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_get_access_token)

    respx.post("https://example.com/products/register").mock(
        return_value=Response(401)
    )
    respx.get(f"https://example.com/products/{product_id}/offers").mock(
        return_value=Response(500)
    )

    client = OffersAPIClient("dummy-refresh", "https://example.com")

    with pytest.raises(TokenRefreshError):
        await client.register_product(product)


@respx.mock
async def test_register_product_invalid_data(monkeypatch):
    async def mock_token(_self): return "token"
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_token)

    respx.post("https://example.com/products/register").mock(
        return_value=Response(422, json={"detail": "invalid payload"})
    )

    product = Product(
        id=uuid4(),
        name="ValidNameButAPIRejects",
        description="Valid description",
        offers=[]
    )

    client = OffersAPIClient("token", "https://example.com")

    with pytest.raises(InvalidProductDataError, match="invalid payload"):
        await client.register_product(product)


@respx.mock
async def test_register_product_already_registered(monkeypatch):
    async def mock_token(_self): return "token"
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_token)

    respx.post("https://example.com/products/register").mock(
        return_value=Response(409)
    )

    client = OffersAPIClient("token", "https://example.com")
    product = Product(id=uuid4(), name="Duplicate", description="Already exists", offers=[])

    with pytest.raises(ProductAlreadyRegisteredError):
        await client.register_product(product)


@respx.mock
async def test_get_product_with_offers_retries(monkeypatch):
    product_id = uuid4()

    async def mock_token(_self):
        return "valid-token"
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_token)

    # Mock 401 followed by 200 with offers (as expected by the SDK)
    respx.get(f"https://example.com/products/{product_id}/offers").mock(side_effect=[
        Response(401),
        Response(200, json=[
            {
                "id": str(uuid4()),
                "price": 1234,
                "items_in_stock": 99
            },
            {
                "id": str(uuid4()),
                "price": 2345,
                "items_in_stock": 50
            }
        ])
    ])

    client = OffersAPIClient("dummy", "https://example.com")
    result = await client.get_product_with_offers(product_id)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].price == 1234
    assert result[1].items_in_stock == 50


@respx.mock
async def test_get_product_with_offers_retry_fails(monkeypatch):
    product_id = uuid4()

    async def mock_token(_self):
        return "token"
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_token)

    # Both attempts fail
    respx.get(f"https://example.com/products/{product_id}/offers").mock(
        return_value=Response(500, json={"detail": "internal error"})
    )

    client = OffersAPIClient("dummy", "https://example.com")

    with pytest.raises(UnexpectedAPIResponseError, match="500"):
        await client.get_product_with_offers(product_id)


@respx.mock
async def test_get_product_with_offers_404(monkeypatch):
    product_id = uuid4()
    async def mock_token(_self): return "token"
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_token)

    respx.get(f"https://example.com/products/{product_id}/offers").mock(
        return_value=Response(404)
    )

    client = OffersAPIClient("token", "https://example.com")

    with pytest.raises(ProductNotFoundError):
        await client.get_product_with_offers(product_id)


@respx.mock
async def test_get_product_with_offers_invalid_data(monkeypatch):
    product_id = uuid4()
    async def mock_token(_self): return "token"
    monkeypatch.setattr("offers_sdk.auth.AuthManager.get_access_token", mock_token)

    respx.get(f"https://example.com/products/{product_id}/offers").mock(
        return_value=Response(422)
    )

    client = OffersAPIClient("token", "https://example.com")

    with pytest.raises(InvalidProductDataError):
        await client.get_product_with_offers(product_id)

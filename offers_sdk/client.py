import os
from uuid import UUID

import httpx

from offers_sdk.auth import AuthManager
from offers_sdk.models import Product, Offer
from offers_sdk.exceptions import (
    TokenRefreshError,
    MissingConfigurationError,
    InvalidProductDataError,
    InvalidOfferDataError,
    ProductAlreadyRegisteredError,
    ProductNotFoundError,
    UnexpectedAPIResponseError,
)



class OffersAPIClient:
    """
    Async SDK client for interacting with the Offers microservice API.

    Responsibilities:
    - Handles OAuth2-style access token refresh using a provided refresh token.
    - Registers new products with the API.
    - Retrieves offers associated with a registered product.
    - Transparently retries once on 401 Unauthorized responses.

    Usage:
        client = OffersAPIClient(refresh_token="your_token", base_url="https://python.exercise.applifting.cz/api/v1")
        await client.register_product(product)
        offers = await client.get_product_with_offers(product.id)
    """
    def __init__(self, refresh_token: str, base_url: str):
        self.auth = AuthManager(refresh_token, base_url)
        self.client = httpx.AsyncClient(base_url=base_url)

    @classmethod
    def from_env(cls):
        """
        Create a client using REFRESH_TOKEN and BASE_URL environment variables.

        Raises MissingConfigurationError if either is missing.
        """
        refresh_token: str = os.getenv("REFRESH_TOKEN")
        base_url: str = os.getenv("BASE_URL")
        if not refresh_token or not base_url:
            raise MissingConfigurationError(
                "Missing REFRESH_TOKEN or BASE_URL in environment variables. "
                "Set them in your .env file or system environment."
            )
        return cls(refresh_token=refresh_token, base_url=base_url)


    async def register_product(self, product: Product, retry: bool = True) -> Product:
        """
        Register a product with the API.

        Automatically retries once on 401 Unauthorized by refreshing the access token.

        Args:
            product (Product): The product to register.
            retry (bool): Internal flag to retry once on 401 Unauthorized.

        Returns:
            Product: The registered product returned by the API.

        Raises:
            TokenRefreshError: If token refresh or auth fails, or unauthorized after retry.
            ProductAlreadyRegisteredError: If the product was already registered (409).
            InvalidProductDataError: If product data is invalid (422).
            UnexpectedAPIResponseError: For any other unhandled status codes.
        """
        try:
            access_token = await self.auth.get_access_token()
        except Exception as e:
            raise TokenRefreshError(f"Failed to get access token: {str(e)}")

        headers = {
            "Bearer": access_token,
            "Content-Type": "application/json",
        }

        product_data = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
        }

        response = await self.client.post("/products/register", headers=headers, json=product_data)

        # Debug prints
        # if response.content:
            # print("Register response JSON:", response.json())
        # else:
            # print(f"Register response returned {response.status_code} with no content")

        if response.status_code == 201:
            data = response.json()

            return Product(
                id=UUID(data["id"]),
                name=product.name,
                description=product.description,
                offers=product.offers
            )

        elif response.status_code == 401:
            if retry:
                self.auth.access_token = None
                return await self.register_product(product, retry=False)
            raise TokenRefreshError("Unauthorized: access token is invalid or expired.")

        elif response.status_code == 409:
            raise ProductAlreadyRegisteredError("Product already registered.")

        elif response.status_code == 422:
            raise InvalidProductDataError(f"Invalid product data: {response.text}")

        else:
            raise UnexpectedAPIResponseError(f"{response.status_code}, {response.text}")


    async def get_product_with_offers(self, product_id: UUID, retry: bool = True) -> list[Offer]:
        """
        Retrieve a product and its offers by ID.

        Automatically retries once on 401 Unauthorized by refreshing the access token.

        Args:
            product_id (UUID): ID of the product to retrieve.
            retry (bool): Internal flag to retry once on 401 Unauthorized.

        Returns:
            list[Offer]: Parsed list of offers for the specified product.

        Raises:
            TokenRefreshError: If token refresh or auth fails, or unauthorized after retry.
            ProductNotFoundError: If product is not registered (404).
            InvalidProductDataError: If product ID is malformed or invalid (422).
            InvalidOfferDataError: If response data cannot be parsed into Offer objects.
            UnexpectedAPIResponseError: For any other unhandled status codes.
        """
        try:
            access_token = await self.auth.get_access_token()
        except Exception as e:
            raise TokenRefreshError(f"Failed to get access token: {str(e)}")

        headers = {
            "Bearer": access_token,
            "Content-Type": "application/json",
        }

        response = await self.client.get(f"/products/{product_id}/offers", headers=headers)

        if response.status_code == 200:
            offers_data = response.json()

            try:
                offers = [Offer.from_dict(o) for o in offers_data]
                return offers
            except Exception as e:
                raise InvalidOfferDataError(f"Error parsing offers: {e}")

        elif response.status_code == 401:
            if retry:
                self.auth.access_token = None
                return await self.get_product_with_offers(product_id, retry=False)
            raise TokenRefreshError("Unauthorized: access token is invalid or expired.")

        elif response.status_code == 404:
            raise ProductNotFoundError(f"Product {product_id} not found or not registered.")

        elif response.status_code == 422:
            raise InvalidProductDataError(f"Invalid product ID: {response.text}")

        else:
            raise UnexpectedAPIResponseError(f"{response.status_code}, {response.text}")
import asyncio
import os
from dotenv import load_dotenv
from uuid import uuid4
from offers_sdk.models import Product
from offers_sdk.client import OffersAPIClient

load_dotenv()
refresh_token = os.getenv("REFRESH_TOKEN")
base_url = os.getenv("BASE_URL")

async def main():
    # Create a product using the Product model from offers_sdk.models
    product = Product(
        id=uuid4(),
        name="Test Product",
        description="A demo product",
        offers=[]
    )

    # Initialize the client using async with
    async with OffersAPIClient(refresh_token, base_url) as client:
        # Use the register_product method of the client and pass in the product as a parameter
        registered = await client.register_product(product)

        print("Registered product:")
        print(registered)

        print("")

        # Use the get_product_with_offers method of the client and pass in the id of the product
        offers = await client.get_product_with_offers(registered.id)

        print(f"Offers for product with id: {product.id}")
        print(offers)
        # Returns a list of Offers - a model from offers_sdk.models


if __name__ == "__main__":
    asyncio.run(main())
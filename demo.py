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
    client = OffersAPIClient(refresh_token=refresh_token, base_url=base_url)

    # Create a product
    product = Product(
        id=uuid4(),
        name="Test Product",
        description="A demo product",
        offers=[]
    )

    # Use the register_product method of the client
    registered = await client.register_product(product)
    print("Registered product:")
    print(registered)

    print("")

    # Use the get_product_with_offers method of the client
    offers = await client.get_product_with_offers(registered.id)
    print(f"Offers for product with id: {product.id}")
    print(offers)


if __name__ == "__main__":
    asyncio.run(main())
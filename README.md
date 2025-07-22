# Applifting Offers SDK (Async Python Client)

A fully async SDK client for interacting with the Applifting Offers microservice API.

This client handles:
- Access token authentication with automatic refresh and local caching
- Registering products
- Fetching associated offers for a product
- Clear exception handling using custom exception classes

---

## ⚙️ Environment Setup

Before using the SDK, create a `.env` file in the project root:

```env
REFRESH_TOKEN=your_refresh_token_here
BASE_URL=https://python.exercise.applifting.cz/api/v1
```

---

## ✅ Example Usage

To get started using the SDK, you can follow this example script (which you can also run yourself in demo.py):

```python
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

    # Create a product using the Product model from offers_sdk.models
    product = Product(
        id=uuid4(),
        name="Test Product",
        description="A demo product",
        offers=[]
    )

    # Use the register_product method of the client and pass in the product as a parameter
    registered = await client.register_product(product)
    print("Registered product:")
    print(registered)

    print("")

    # Use the get_product_with_offers method of the client and pass in the id of the product
    offers = await client.get_product_with_offers(registered.id)
    print(f"Offers for product with id: {product.id}")
    print(offers)
    # Return a list of Offers - a model from offers_sdk.models

if __name__ == "__main__":
    asyncio.run(main())
```

> Make sure your `.env` file is properly configured with `REFRESH_TOKEN` and `BASE_URL`.

---

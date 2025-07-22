from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from offers_sdk.exceptions import InvalidOfferDataError, InvalidProductDataError


@dataclass
class Offer:
    """
    Represents an offer for a product.

    Attributes:
        id: Unique identifier of the offer (UUID).
        price: Price of the offer (must be an integer).
        items_in_stock: Number of items currently in stock (must be an integer).
        product_id: Optional UUID of the associated product. Absent in API responses.

    Methods:
        from_dict(data): Parses and validates an Offer from a dictionary, raising
                         InvalidOfferDataError on malformed input.
    """
    id: UUID
    price: int
    items_in_stock: int
    product_id: Optional[UUID] = None # Not returned from the API

    @staticmethod
    def from_dict(data: dict) -> "Offer":
        """
        Creates an Offer instance from a dictionary with validation.

        Raises:
            InvalidOfferDataError: If required fields are missing, of the wrong type,
                                   or contain invalid UUIDs.
        """
        try:
            id_ = UUID(data["id"])
            price = data["price"]
            items_in_stock = data["items_in_stock"]

            if not isinstance(price, int):
                raise InvalidOfferDataError("Offer price must be an integer.")

            if not isinstance(items_in_stock, int):
                raise InvalidOfferDataError("Items in stock must be an integer.")

            product_id = UUID(data["product_id"]) if "product_id" in data and data["product_id"] else None

            return Offer(
                id=id_,
                price=price,
                items_in_stock=items_in_stock,
                product_id=product_id
            )
        except KeyError as e:
            raise InvalidOfferDataError(f"Missing required offer field: {e}") from e
        except ValueError as e:
            raise InvalidOfferDataError(f"Invalid value in offer data: {e}") from e


@dataclass
class Product:
    """
    Represents a product with its associated offers.

    Attributes:
        id: Unique identifier of the product (UUID).
        name: Name of the product (must be a non-empty string).
        description: Description of the product (must be a non-empty string).
        offers: List of associated Offer objects.

    Methods:
        from_dict(data): Parses and validates a Product from a dictionary, including nested offers.
    """
    id: UUID
    name: str
    description: str
    offers: List[Offer]

    @staticmethod
    def from_dict(data: dict) -> "Product":
        """
        Creates a Product instance from a dictionary with validation.

        Validates the nested offers using Offer.from_dict.

        Raises:
            InvalidProductDataError: If product fields are invalid.
            InvalidOfferDataError: If any nested offer data is malformed.
        """
        return Product(
            id=UUID(data["id"]),
            name=data["name"],
            description=data["description"],
            offers=[Offer.from_dict(offer) for offer in data.get("offers", [])]
        )

    def __post_init__(self):
        """
        Validates the Product instance after initialization.

        Raises:
            InvalidProductDataError: If `id` is not a UUID, or name/description are empty or invalid.
        """
        if not isinstance(self.id, UUID):
            raise InvalidProductDataError("Product ID must be a UUID.")

        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidProductDataError("Product name must be a non-empty string.")

        if not isinstance(self.description, str) or not self.description.strip():
            raise InvalidProductDataError("Product description must be a non-empty string.")

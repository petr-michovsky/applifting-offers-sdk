from uuid import UUID, uuid4

import pytest

from offers_sdk.exceptions import InvalidOfferDataError, InvalidProductDataError
from offers_sdk.models import Offer, Product


def test_product_invalid_id_type():
    with pytest.raises(InvalidProductDataError):
        Product(
            id="not-a-uuid",  # type: ignore
            name="Valid",
            description="Valid",
            offers=[]
        )


def test_product_empty_name():
    with pytest.raises(InvalidProductDataError):
        Product(
            id=uuid4(),
            name="",
            description="Valid",
            offers=[]
        )


def test_product_empty_description():
    with pytest.raises(InvalidProductDataError):
        Product(
            id=uuid4(),
            name="Valid",
            description="",
            offers=[]
        )


def test_product_from_dict_with_nested_offers():
    raw_product = {
        "id": str(uuid4()),
        "name": "Test Product",
        "description": "A product for testing",
        "offers": [
            {
                "id": str(uuid4()),
                "price": 120,
                "items_in_stock": 10
            },
            {
                "id": str(uuid4()),
                "price": 90,
                "items_in_stock": 5
            }
        ]
    }

    product = Product.from_dict(raw_product)

    assert product.name == "Test Product"
    assert len(product.offers) == 2
    for offer in product.offers:
        assert isinstance(offer, Offer)
        assert isinstance(offer.id, UUID)


def test_product_from_dict_with_invalid_nested_offer():
    raw_product = {
        "id": str(uuid4()),
        "name": "Broken Product",
        "description": "This one has bad offers",
        "offers": [
            {
                "id": str(uuid4()),
                "price": "free",
                "items_in_stock": 10
            }
        ]
    }

    with pytest.raises(InvalidOfferDataError):
        Product.from_dict(raw_product)



def test_parse_offers_api_response():
    from offers_sdk.models import Offer
    raw_offers = [
        {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "price": 0,
            "items_in_stock": 0
        }
    ]

    offers = [Offer.from_dict(offer) for offer in raw_offers]

    assert len(offers) == 1
    assert offers[0].id == UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
    assert offers[0].price == 0
    assert offers[0].items_in_stock == 0
    assert offers[0].product_id is None  # API does not return this


def test_offer_missing_required_field():
    incomplete_offer = {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        # "price" is missing
        "items_in_stock": 5
    }

    with pytest.raises(InvalidOfferDataError, match="Missing required offer field"):
        Offer.from_dict(incomplete_offer)


def test_offer_invalid_uuid():
    raw_offer = {
        "id": "invalid-uuid",
        "price": 100,
        "items_in_stock": 10
    }

    with pytest.raises(InvalidOfferDataError, match="Invalid value in offer data"):
        Offer.from_dict(raw_offer)


def test_offer_invalid_price_type():
    raw_offer = {
        "id": str(uuid4()),
        "price": "free",  # invalid type
        "items_in_stock": 10
    }

    with pytest.raises(InvalidOfferDataError, match="price must be an integer"):
        Offer.from_dict(raw_offer)


def test_offer_with_product_id():
    raw_offer = {
        "id": str(uuid4()),
        "price": 150,
        "items_in_stock": 20,
        "product_id": str(uuid4())
    }

    offer = Offer.from_dict(raw_offer)

    assert isinstance(offer.id, UUID)
    assert isinstance(offer.product_id, UUID)
    assert offer.price == 150
    assert offer.items_in_stock == 20


def test_offer_invalid_items_in_stock_type():
    raw_offer = {
        "id": str(uuid4()),
        "price": 100,
        "items_in_stock": "a lot"
    }

    with pytest.raises(InvalidOfferDataError, match="Items in stock must be an integer"):
        Offer.from_dict(raw_offer)


def test_offer_invalid_product_id():
    raw_offer = {
        "id": str(uuid4()),
        "price": 99,
        "items_in_stock": 5,
        "product_id": "not-a-uuid"
    }

    with pytest.raises(InvalidOfferDataError, match="Invalid value in offer data"):
        Offer.from_dict(raw_offer)

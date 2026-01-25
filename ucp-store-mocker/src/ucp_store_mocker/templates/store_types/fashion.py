"""Fashion store template."""

from dataclasses import dataclass, field
from typing import Any

from ucp_store_mocker.templates.base import BaseTemplate


@dataclass
class FashionTemplate(BaseTemplate):
    """Template for fashion/apparel stores."""

    name: str = "fashion"
    description: str = "Fashion and apparel store"

    default_categories: list[dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Mens Clothing", "count": 15, "price_range": [1999, 14999]},
        {"name": "Womens Clothing", "count": 15, "price_range": [1999, 19999]},
        {"name": "Shoes", "count": 12, "price_range": [4999, 24999]},
        {"name": "Accessories", "count": 10, "price_range": [999, 9999]},
        {"name": "Activewear", "count": 8, "price_range": [2999, 12999]},
        {"name": "Outerwear", "count": 6, "price_range": [7999, 39999]},
    ])

    default_variations: dict[str, list[dict]] = field(default_factory=lambda: {
        "Mens Clothing": [
            {"type": "size", "options": ["XS", "S", "M", "L", "XL", "XXL"],
             "affects_price": False},
            {"type": "color", "options": ["Black", "White", "Navy", "Gray", "Olive"],
             "affects_price": False},
        ],
        "Womens Clothing": [
            {"type": "size", "options": ["XS", "S", "M", "L", "XL"],
             "affects_price": False},
            {"type": "color", "options": ["Black", "White", "Red", "Navy", "Blush", "Sage"],
             "affects_price": False},
        ],
        "Shoes": [
            {"type": "size", "options": ["6", "7", "8", "9", "10", "11", "12"],
             "affects_price": False},
            {"type": "color", "options": ["Black", "Brown", "White", "Tan"],
             "affects_price": False},
        ],
        "Activewear": [
            {"type": "size", "options": ["XS", "S", "M", "L", "XL"],
             "affects_price": False},
            {"type": "color", "options": ["Black", "Navy", "Gray", "Neon"],
             "affects_price": False},
        ],
    })

    default_fulfillment: list[dict[str, Any]] = field(default_factory=lambda: [
        {
            "type": "shipping",
            "options": [
                {"id": "standard", "title": "Standard Shipping", "price": 599, "delivery_days": [5, 7]},
                {"id": "express", "title": "Express Shipping", "price": 1299, "delivery_days": [2, 3]},
            ],
        },
    ])

    sample_products: list[dict[str, Any]] = field(default_factory=lambda: [
        {"title": "Classic Cotton T-Shirt", "category": "Mens Clothing", "price": 2999, "brand": "StyleCo"},
        {"title": "Slim Fit Jeans", "category": "Mens Clothing", "price": 7999, "brand": "DenimWorks"},
        {"title": "Floral Summer Dress", "category": "Womens Clothing", "price": 8999, "brand": "Elegance"},
        {"title": "Leather Ankle Boots", "category": "Shoes", "price": 15999, "brand": "FootStyle"},
        {"title": "Crossbody Bag", "category": "Accessories", "price": 4999, "brand": "BagCraft"},
    ])

    def get_product_descriptors(self) -> dict[str, list[str]]:
        """Get product name descriptors for Faker generation."""
        return {
            "Mens Clothing": {
                "prefixes": ["Classic", "Modern", "Slim Fit", "Relaxed", "Premium"],
                "items": ["T-Shirt", "Polo", "Button-Down", "Jeans", "Chinos", "Shorts",
                         "Sweater", "Hoodie", "Blazer"],
                "brands": ["StyleCo", "MensWear", "UrbanStyle", "ClassicMan"],
            },
            "Womens Clothing": {
                "prefixes": ["Elegant", "Casual", "Boho", "Classic", "Modern"],
                "items": ["Dress", "Blouse", "Skirt", "Pants", "Top", "Cardigan",
                         "Jumpsuit", "Romper"],
                "brands": ["Elegance", "ChicStyle", "FemmeWear", "GlamourCo"],
            },
            "Shoes": {
                "prefixes": ["Classic", "Premium", "Comfort", "Designer", "Sport"],
                "items": ["Sneakers", "Boots", "Heels", "Loafers", "Sandals", "Oxfords"],
                "brands": ["FootStyle", "StepUp", "SoleMate", "WalkRight"],
            },
            "Accessories": {
                "prefixes": ["Designer", "Classic", "Modern", "Handcrafted"],
                "items": ["Belt", "Watch", "Sunglasses", "Scarf", "Hat", "Wallet", "Bag"],
                "brands": ["BagCraft", "AccessoryCo", "StylePlus"],
            },
        }

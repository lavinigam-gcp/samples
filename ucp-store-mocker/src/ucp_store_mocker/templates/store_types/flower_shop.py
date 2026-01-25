"""Flower shop template."""

from dataclasses import dataclass, field
from typing import Any

from ucp_store_mocker.templates.base import BaseTemplate


@dataclass
class FlowerShopTemplate(BaseTemplate):
    """Template for flower shop stores."""

    name: str = "flower_shop"
    description: str = "Flower shop and gifting"

    default_categories: list[dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Bouquets", "count": 15, "price_range": [2999, 12999]},
        {"name": "Arrangements", "count": 10, "price_range": [4999, 19999]},
        {"name": "Plants", "count": 10, "price_range": [1999, 7999]},
        {"name": "Gifts", "count": 8, "price_range": [999, 4999]},
        {"name": "Occasions", "count": 6, "price_range": [3999, 14999]},
    ])

    default_variations: dict[str, list[dict]] = field(default_factory=lambda: {
        "Bouquets": [
            {"type": "size", "options": ["Standard", "Deluxe", "Premium"],
             "price_multipliers": [1.0, 1.5, 2.0]},
        ],
        "Arrangements": [
            {"type": "size", "options": ["Small", "Medium", "Large"],
             "price_multipliers": [1.0, 1.5, 2.0]},
            {"type": "vase", "options": ["Standard", "Premium Glass", "Ceramic"],
             "price_adjustments": [0, 1500, 2500]},
        ],
        "Plants": [
            {"type": "pot", "options": ["Plastic", "Terracotta", "Ceramic"],
             "price_adjustments": [0, 500, 1200]},
        ],
    })

    default_fulfillment: list[dict[str, Any]] = field(default_factory=lambda: [
        {
            "type": "shipping",
            "options": [
                {"id": "standard", "title": "Standard Delivery", "price": 999, "delivery_days": [2, 3]},
                {"id": "same_day", "title": "Same Day Delivery", "price": 1999, "delivery_days": [0, 0]},
            ],
        },
        {
            "type": "pickup",
            "options": [
                {"id": "pickup", "title": "Store Pickup", "price": 0},
            ],
        },
    ])

    sample_products: list[dict[str, Any]] = field(default_factory=lambda: [
        {"title": "Rose Romance Bouquet", "category": "Bouquets", "price": 5999,
         "description": "A dozen red roses with baby's breath"},
        {"title": "Spring Garden Arrangement", "category": "Arrangements", "price": 8999,
         "description": "Mixed seasonal flowers in a glass vase"},
        {"title": "Monstera Deliciosa", "category": "Plants", "price": 3999,
         "description": "Tropical statement plant in ceramic pot"},
        {"title": "Chocolate Truffles Box", "category": "Gifts", "price": 2499,
         "description": "Assorted premium chocolates"},
        {"title": "Birthday Celebration", "category": "Occasions", "price": 7999,
         "description": "Festive arrangement with balloons"},
    ])

    def get_product_descriptors(self) -> dict[str, list[str]]:
        """Get product name descriptors for Faker generation."""
        return {
            "Bouquets": {
                "prefixes": ["Classic", "Romantic", "Elegant", "Wild", "Garden"],
                "flowers": ["Rose", "Tulip", "Lily", "Sunflower", "Peony", "Orchid",
                           "Daisy", "Carnation", "Hydrangea"],
                "suffixes": ["Bouquet", "Bundle", "Collection", "Arrangement"],
            },
            "Arrangements": {
                "prefixes": ["Spring", "Summer", "Autumn", "Winter", "Tropical", "Modern"],
                "styles": ["Garden", "Cascade", "Centerpiece", "Statement", "Minimalist"],
            },
            "Plants": {
                "types": ["Monstera", "Fiddle Leaf Fig", "Snake Plant", "Pothos",
                         "Peace Lily", "Succulent", "Orchid", "Fern", "Philodendron"],
            },
            "Gifts": {
                "items": ["Chocolates", "Candles", "Vase", "Teddy Bear", "Wine",
                         "Gift Card", "Greeting Card", "Balloon"],
            },
            "Occasions": {
                "events": ["Birthday", "Anniversary", "Valentine's Day", "Mother's Day",
                          "Sympathy", "Get Well", "Congratulations", "Thank You"],
            },
        }

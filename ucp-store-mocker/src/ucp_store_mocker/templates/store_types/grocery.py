"""Grocery store template."""

from dataclasses import dataclass, field
from typing import Any

from ucp_store_mocker.templates.base import BaseTemplate


@dataclass
class GroceryTemplate(BaseTemplate):
    """Template for grocery/supermarket stores."""

    name: str = "grocery"
    description: str = "Grocery/Supermarket store"

    default_categories: list[dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Fresh Produce", "count": 15, "price_range": [99, 999]},
        {"name": "Dairy & Eggs", "count": 10, "price_range": [199, 899]},
        {"name": "Bakery", "count": 8, "price_range": [299, 1299]},
        {"name": "Snacks", "count": 12, "price_range": [199, 799]},
        {"name": "Beverages", "count": 10, "price_range": [149, 599]},
        {"name": "Frozen Foods", "count": 8, "price_range": [299, 1499]},
        {"name": "Pantry", "count": 10, "price_range": [199, 999]},
    ])

    default_variations: dict[str, list[dict]] = field(default_factory=lambda: {
        "Fresh Produce": [
            {"type": "weight", "options": ["1 lb", "2 lb", "5 lb"], "price_multipliers": [1.0, 1.9, 4.5]},
        ],
        "Beverages": [
            {"type": "size", "options": ["12 oz", "20 oz", "2 L"], "price_multipliers": [1.0, 1.4, 2.5]},
        ],
    })

    default_fulfillment: list[dict[str, Any]] = field(default_factory=lambda: [
        {
            "type": "shipping",
            "options": [
                {"id": "standard", "title": "Standard Delivery", "price": 599, "delivery_days": [3, 5]},
                {"id": "express", "title": "Express Delivery", "price": 999, "delivery_days": [1, 2]},
            ],
        },
        {
            "type": "pickup",
            "options": [
                {"id": "curbside", "title": "Curbside Pickup", "price": 0},
                {"id": "instore", "title": "In-Store Pickup", "price": 0},
            ],
        },
    ])

    sample_products: list[dict[str, Any]] = field(default_factory=lambda: [
        {"title": "Organic Bananas", "category": "Fresh Produce", "price": 199, "unit": "lb"},
        {"title": "Whole Milk", "category": "Dairy & Eggs", "price": 449, "unit": "gallon"},
        {"title": "Sourdough Bread", "category": "Bakery", "price": 599, "unit": "loaf"},
        {"title": "Tortilla Chips", "category": "Snacks", "price": 399, "unit": "bag"},
        {"title": "Orange Juice", "category": "Beverages", "price": 549, "unit": "64 oz"},
    ])

    def get_product_descriptors(self) -> dict[str, list[str]]:
        """Get product name descriptors for Faker generation."""
        return {
            "Fresh Produce": {
                "prefixes": ["Organic", "Fresh", "Local", "Premium", "Farm-Fresh"],
                "items": ["Apples", "Oranges", "Bananas", "Strawberries", "Grapes", "Avocados",
                         "Lettuce", "Tomatoes", "Carrots", "Broccoli", "Spinach", "Onions"],
            },
            "Dairy & Eggs": {
                "prefixes": ["Organic", "Free-Range", "Grass-Fed", "Premium"],
                "items": ["Milk", "Eggs", "Butter", "Cheese", "Yogurt", "Cream Cheese",
                         "Sour Cream", "Heavy Cream", "Cottage Cheese"],
            },
            "Bakery": {
                "prefixes": ["Artisan", "Fresh-Baked", "Homestyle", "Classic"],
                "items": ["Bread", "Croissants", "Muffins", "Bagels", "Rolls", "Cookies",
                         "Cake", "Pie", "Danish"],
            },
            "Snacks": {
                "prefixes": ["Crunchy", "Original", "Family Size", "Party Size"],
                "items": ["Chips", "Pretzels", "Crackers", "Popcorn", "Nuts", "Trail Mix",
                         "Granola Bars", "Fruit Snacks"],
            },
            "Beverages": {
                "prefixes": ["Refreshing", "Natural", "Premium", "Sparkling"],
                "items": ["Water", "Juice", "Soda", "Tea", "Coffee", "Energy Drink",
                         "Lemonade", "Iced Tea"],
            },
        }

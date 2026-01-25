"""Restaurant template."""

from dataclasses import dataclass, field
from typing import Any

from ucp_store_mocker.templates.base import BaseTemplate


@dataclass
class RestaurantTemplate(BaseTemplate):
    """Template for restaurant/food delivery stores."""

    name: str = "restaurant"
    description: str = "Restaurant and food delivery"

    default_categories: list[dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Appetizers", "count": 8, "price_range": [599, 1299]},
        {"name": "Entrees", "count": 15, "price_range": [1199, 2999]},
        {"name": "Sides", "count": 8, "price_range": [299, 799]},
        {"name": "Desserts", "count": 6, "price_range": [499, 999]},
        {"name": "Drinks", "count": 10, "price_range": [199, 599]},
        {"name": "Combos", "count": 5, "price_range": [1499, 2499]},
    ])

    default_variations: dict[str, list[dict]] = field(default_factory=lambda: {
        "Entrees": [
            {"type": "size", "options": ["Regular", "Large"],
             "price_adjustments": [0, 400]},
            {"type": "protein", "options": ["Chicken", "Beef", "Tofu", "Shrimp"],
             "price_adjustments": [0, 200, 0, 400]},
        ],
        "Drinks": [
            {"type": "size", "options": ["Small", "Medium", "Large"],
             "price_adjustments": [0, 100, 200]},
        ],
        "Combos": [
            {"type": "size", "options": ["Regular", "Large", "Family"],
             "price_adjustments": [0, 500, 1200]},
        ],
    })

    default_fulfillment: list[dict[str, Any]] = field(default_factory=lambda: [
        {
            "type": "shipping",
            "options": [
                {"id": "delivery", "title": "Delivery", "price": 399, "delivery_days": [0, 0]},
            ],
        },
        {
            "type": "pickup",
            "options": [
                {"id": "pickup", "title": "Pickup", "price": 0},
            ],
        },
    ])

    sample_products: list[dict[str, Any]] = field(default_factory=lambda: [
        {"title": "Spring Rolls", "category": "Appetizers", "price": 799, "description": "Crispy vegetable spring rolls with dipping sauce"},
        {"title": "Grilled Salmon", "category": "Entrees", "price": 2499, "description": "Atlantic salmon with seasonal vegetables"},
        {"title": "French Fries", "category": "Sides", "price": 399, "description": "Crispy golden fries with sea salt"},
        {"title": "Chocolate Cake", "category": "Desserts", "price": 699, "description": "Rich chocolate layer cake"},
        {"title": "Fresh Lemonade", "category": "Drinks", "price": 349, "description": "Freshly squeezed lemonade"},
    ])

    def get_product_descriptors(self) -> dict[str, list[str]]:
        """Get product name descriptors for Faker generation."""
        return {
            "Appetizers": {
                "prefixes": ["Crispy", "Fresh", "Spicy", "Savory", "Classic"],
                "items": ["Spring Rolls", "Wings", "Nachos", "Bruschetta", "Soup",
                         "Calamari", "Mozzarella Sticks", "Dumplings"],
            },
            "Entrees": {
                "prefixes": ["Grilled", "Pan-Seared", "Roasted", "Braised", "Classic"],
                "items": ["Salmon", "Steak", "Chicken", "Pasta", "Burger", "Tacos",
                         "Pizza", "Stir Fry", "Curry", "Risotto"],
            },
            "Sides": {
                "prefixes": ["Crispy", "Seasoned", "Creamy", "Fresh", "Roasted"],
                "items": ["Fries", "Salad", "Rice", "Vegetables", "Coleslaw",
                         "Mashed Potatoes", "Onion Rings"],
            },
            "Desserts": {
                "prefixes": ["Decadent", "Classic", "Homemade", "Fresh"],
                "items": ["Cake", "Pie", "Ice Cream", "Cheesecake", "Brownie",
                         "Tiramisu", "Creme Brulee"],
            },
            "Drinks": {
                "prefixes": ["Fresh", "Iced", "Hot", "Sparkling", "Classic"],
                "items": ["Lemonade", "Iced Tea", "Soda", "Coffee", "Juice",
                         "Smoothie", "Milkshake"],
            },
        }

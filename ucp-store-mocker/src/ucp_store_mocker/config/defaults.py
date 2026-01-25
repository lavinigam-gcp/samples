"""Default configurations for different store types."""

from typing import Any


def get_store_defaults(
    store_type: str,
    name: str,
    with_a2a: bool = True,
    with_images: bool = False,
) -> dict[str, Any]:
    """Get default configuration for a store type."""

    # Base configuration
    config = {
        "store": {
            "name": name,
            "type": store_type,
            "location": {
                "address": {
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "postal_code": "94102",
                    "country": "US",
                },
                "coordinates": {
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                },
            },
        },
        "server": {
            "port": 8080,
            "transport": {
                "rest": True,
                "a2a": with_a2a,
            },
        },
        "capabilities": {
            "checkout": {"enabled": True},
            "order": {
                "enabled": True,
                "webhooks": {"enabled": True},
            },
            "fulfillment": {
                "enabled": True,
                "methods": [],
                "free_shipping": {"enabled": True, "threshold": 3500},
            },
            "discount": {
                "enabled": True,
                "codes": [
                    {"code": "SAVE10", "type": "percentage", "value": 10},
                    {"code": "WELCOME", "type": "percentage", "value": 15},
                ],
            },
            "buyer_consent": {"enabled": True},
        },
        "payment": {
            "handlers": [
                {"id": "mock_payment", "name": "dev.ucp.mock_payment", "enabled": True},
            ],
        },
        "catalog": {
            "generation": {
                "strategy": "hybrid",
                "count": 50,
                "seed": 42,
            },
            "images": {
                "generate": with_images,
                "model": "gemini-2.5-flash-image",
                "style": "product-photography",
                "resolution": "1024x1024",
            },
            "variations": {"enabled": True, "category_variations": {}},
            "categories": [],
        },
        "inventory": {
            "strategy": "realistic",
            "default_quantity": 100,
            "variance": 0.3,
            "low_stock_percentage": 10,
            "out_of_stock_percentage": 5,
        },
        "a2a": {
            "enabled": with_a2a,
            "agent_card": {
                "name": f"{name} Agent",
                "skills": [
                    {"id": "product_search"},
                    {"id": "checkout"},
                ],
            },
        },
    }

    # Apply store-type specific defaults
    type_defaults = _get_type_specific_defaults(store_type)
    _deep_merge(config, type_defaults)

    return config


def _get_type_specific_defaults(store_type: str) -> dict[str, Any]:
    """Get store type specific default overrides."""

    if store_type == "grocery":
        return {
            "capabilities": {
                "fulfillment": {
                    "methods": [
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
                    ],
                },
            },
            "catalog": {
                "categories": [
                    {"name": "Fresh Produce", "count": 15, "price_range": [99, 999]},
                    {"name": "Dairy & Eggs", "count": 10, "price_range": [199, 899]},
                    {"name": "Bakery", "count": 8, "price_range": [299, 1299]},
                    {"name": "Snacks", "count": 12, "price_range": [199, 799]},
                    {"name": "Beverages", "count": 10, "price_range": [149, 599]},
                ],
                "variations": {
                    "category_variations": {
                        "Fresh Produce": [
                            {"type": "weight", "options": ["1 lb", "2 lb", "5 lb"], "price_multipliers": [1.0, 1.9, 4.5]},
                        ],
                    },
                },
            },
            "inventory": {
                "category_overrides": {
                    "Fresh Produce": {"default_quantity": 50, "variance": 0.5},
                },
            },
        }

    elif store_type == "electronics":
        return {
            "capabilities": {
                "fulfillment": {
                    "methods": [
                        {
                            "type": "shipping",
                            "options": [
                                {"id": "standard", "title": "Standard Shipping", "price": 0, "delivery_days": [5, 7]},
                                {"id": "express", "title": "Express Shipping", "price": 1499, "delivery_days": [2, 3]},
                            ],
                        },
                    ],
                    "free_shipping": {"enabled": True, "threshold": 5000},
                },
                "returns": {"enabled": True, "return_window_days": 30},
            },
            "catalog": {
                "categories": [
                    {"name": "Smartphones", "count": 10, "price_range": [29900, 129900]},
                    {"name": "Laptops", "count": 8, "price_range": [49900, 249900]},
                    {"name": "Accessories", "count": 15, "price_range": [999, 9999]},
                    {"name": "Gaming", "count": 10, "price_range": [1999, 59900]},
                    {"name": "Audio", "count": 8, "price_range": [2999, 34900]},
                ],
                "variations": {
                    "category_variations": {
                        "Smartphones": [
                            {"type": "storage", "options": ["64GB", "128GB", "256GB", "512GB"], "price_adjustments": [0, 10000, 20000, 40000]},
                            {"type": "color", "options": ["Space Gray", "Silver", "Gold"], "affects_price": False},
                        ],
                        "Laptops": [
                            {"type": "storage", "options": ["256GB", "512GB", "1TB"], "price_adjustments": [0, 20000, 50000]},
                            {"type": "ram", "options": ["8GB", "16GB", "32GB"], "price_adjustments": [0, 20000, 50000]},
                        ],
                    },
                },
            },
            "inventory": {
                "default_quantity": 25,
            },
        }

    elif store_type == "fashion":
        return {
            "capabilities": {
                "fulfillment": {
                    "methods": [
                        {
                            "type": "shipping",
                            "options": [
                                {"id": "standard", "title": "Standard Shipping", "price": 599, "delivery_days": [5, 7]},
                                {"id": "express", "title": "Express Shipping", "price": 1299, "delivery_days": [2, 3]},
                            ],
                        },
                    ],
                    "free_shipping": {"enabled": True, "threshold": 7500},
                },
                "returns": {"enabled": True, "return_window_days": 60},
                "wishlist": {"enabled": True},
            },
            "catalog": {
                "categories": [
                    {"name": "Mens Clothing", "count": 15, "price_range": [1999, 14999]},
                    {"name": "Womens Clothing", "count": 15, "price_range": [1999, 19999]},
                    {"name": "Shoes", "count": 12, "price_range": [4999, 24999]},
                    {"name": "Accessories", "count": 10, "price_range": [999, 9999]},
                ],
                "variations": {
                    "category_variations": {
                        "Mens Clothing": [
                            {"type": "size", "options": ["XS", "S", "M", "L", "XL", "XXL"], "affects_price": False},
                            {"type": "color", "options": ["Black", "White", "Navy", "Gray"], "affects_price": False},
                        ],
                        "Womens Clothing": [
                            {"type": "size", "options": ["XS", "S", "M", "L", "XL"], "affects_price": False},
                            {"type": "color", "options": ["Black", "White", "Red", "Navy", "Blush"], "affects_price": False},
                        ],
                        "Shoes": [
                            {"type": "size", "options": ["6", "7", "8", "9", "10", "11", "12"], "affects_price": False},
                            {"type": "color", "options": ["Black", "Brown", "White"], "affects_price": False},
                        ],
                    },
                },
            },
        }

    elif store_type == "restaurant":
        return {
            "capabilities": {
                "fulfillment": {
                    "methods": [
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
                    ],
                    "free_shipping": {"enabled": True, "threshold": 2500},
                },
            },
            "catalog": {
                "categories": [
                    {"name": "Appetizers", "count": 8, "price_range": [599, 1299]},
                    {"name": "Entrees", "count": 15, "price_range": [1199, 2999]},
                    {"name": "Sides", "count": 8, "price_range": [299, 799]},
                    {"name": "Desserts", "count": 6, "price_range": [499, 999]},
                    {"name": "Drinks", "count": 10, "price_range": [199, 599]},
                ],
                "variations": {
                    "category_variations": {
                        "Entrees": [
                            {"type": "size", "options": ["Regular", "Large"], "price_adjustments": [0, 400]},
                        ],
                        "Drinks": [
                            {"type": "size", "options": ["Small", "Medium", "Large"], "price_adjustments": [0, 100, 200]},
                        ],
                    },
                },
            },
            "inventory": {
                "strategy": "unlimited",
            },
        }

    elif store_type == "subscription":
        return {
            "capabilities": {
                "fulfillment": {"enabled": False},
                "subscriptions": {"enabled": True},
            },
            "catalog": {
                "generation": {"count": 10},
                "categories": [
                    {"name": "Basic Plans", "count": 3, "price_range": [499, 999]},
                    {"name": "Premium Plans", "count": 3, "price_range": [1499, 2999]},
                    {"name": "Enterprise Plans", "count": 2, "price_range": [4999, 9999]},
                    {"name": "Add-ons", "count": 5, "price_range": [199, 999]},
                ],
                "variations": {"enabled": False},
            },
            "inventory": {
                "strategy": "unlimited",
            },
        }

    elif store_type == "flower_shop":
        return {
            "capabilities": {
                "fulfillment": {
                    "methods": [
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
                    ],
                    "free_shipping": {"enabled": True, "threshold": 7500},
                },
                "gift_cards": {"enabled": True, "denominations": [2500, 5000, 7500, 10000]},
            },
            "catalog": {
                "categories": [
                    {"name": "Bouquets", "count": 15, "price_range": [2999, 12999]},
                    {"name": "Arrangements", "count": 10, "price_range": [4999, 19999]},
                    {"name": "Plants", "count": 10, "price_range": [1999, 7999]},
                    {"name": "Gifts", "count": 8, "price_range": [999, 4999]},
                ],
                "variations": {
                    "category_variations": {
                        "Bouquets": [
                            {"type": "size", "options": ["Standard", "Deluxe", "Premium"], "price_multipliers": [1.0, 1.5, 2.0]},
                        ],
                    },
                },
            },
            "inventory": {
                "default_quantity": 30,
                "variance": 0.4,
            },
        }

    return {}


def _deep_merge(base: dict, override: dict) -> None:
    """Deep merge override into base dict in place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value

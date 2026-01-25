"""Electronics store template."""

from dataclasses import dataclass, field
from typing import Any

from ucp_store_mocker.templates.base import BaseTemplate


@dataclass
class ElectronicsTemplate(BaseTemplate):
    """Template for electronics stores."""

    name: str = "electronics"
    description: str = "Electronics and technology store"

    default_categories: list[dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Smartphones", "count": 10, "price_range": [29900, 129900]},
        {"name": "Laptops", "count": 8, "price_range": [49900, 249900]},
        {"name": "Tablets", "count": 6, "price_range": [19900, 129900]},
        {"name": "Accessories", "count": 15, "price_range": [999, 9999]},
        {"name": "Gaming", "count": 10, "price_range": [1999, 59900]},
        {"name": "Audio", "count": 8, "price_range": [2999, 34900]},
        {"name": "Wearables", "count": 6, "price_range": [9900, 49900]},
    ])

    default_variations: dict[str, list[dict]] = field(default_factory=lambda: {
        "Smartphones": [
            {"type": "storage", "options": ["64GB", "128GB", "256GB", "512GB"],
             "price_adjustments": [0, 10000, 20000, 40000]},
            {"type": "color", "options": ["Space Gray", "Silver", "Gold", "Blue"],
             "affects_price": False},
        ],
        "Laptops": [
            {"type": "storage", "options": ["256GB", "512GB", "1TB"],
             "price_adjustments": [0, 20000, 50000]},
            {"type": "ram", "options": ["8GB", "16GB", "32GB"],
             "price_adjustments": [0, 20000, 50000]},
        ],
        "Tablets": [
            {"type": "storage", "options": ["64GB", "128GB", "256GB"],
             "price_adjustments": [0, 10000, 20000]},
            {"type": "connectivity", "options": ["WiFi", "WiFi + Cellular"],
             "price_adjustments": [0, 15000]},
        ],
    })

    default_fulfillment: list[dict[str, Any]] = field(default_factory=lambda: [
        {
            "type": "shipping",
            "options": [
                {"id": "standard", "title": "Standard Shipping", "price": 0, "delivery_days": [5, 7]},
                {"id": "express", "title": "Express Shipping", "price": 1499, "delivery_days": [2, 3]},
                {"id": "overnight", "title": "Overnight", "price": 2999, "delivery_days": [1, 1]},
            ],
        },
    ])

    sample_products: list[dict[str, Any]] = field(default_factory=lambda: [
        {"title": "Galaxy Pro Max", "category": "Smartphones", "price": 99900, "brand": "TechCorp"},
        {"title": "UltraBook Pro 15", "category": "Laptops", "price": 149900, "brand": "CompuMax"},
        {"title": "Wireless Earbuds Pro", "category": "Audio", "price": 19900, "brand": "SoundWave"},
        {"title": "Gaming Controller Elite", "category": "Gaming", "price": 6999, "brand": "GamePro"},
        {"title": "Smart Watch Series 5", "category": "Wearables", "price": 39900, "brand": "TechCorp"},
    ])

    def get_product_descriptors(self) -> dict[str, list[str]]:
        """Get product name descriptors for Faker generation."""
        return {
            "Smartphones": {
                "prefixes": ["Galaxy", "Pixel", "Nova", "Ultra", "Pro"],
                "suffixes": ["Max", "Plus", "Pro", "SE", "Lite"],
                "brands": ["TechCorp", "PhoneMaster", "MobileX", "SmartTech"],
            },
            "Laptops": {
                "prefixes": ["UltraBook", "ThinkPad", "ProBook", "ZenBook", "MacStyle"],
                "suffixes": ["Pro", "Air", "Elite", "X1", "360"],
                "brands": ["CompuMax", "TechBook", "LaptopPro", "NoteMaster"],
            },
            "Audio": {
                "prefixes": ["Wireless", "Premium", "Studio", "Pro", "Elite"],
                "items": ["Earbuds", "Headphones", "Speaker", "Soundbar", "Microphone"],
                "brands": ["SoundWave", "AudioMax", "BeatsPro", "SonicElite"],
            },
            "Gaming": {
                "prefixes": ["Pro", "Elite", "Ultimate", "Gaming", "RGB"],
                "items": ["Controller", "Headset", "Keyboard", "Mouse", "Monitor", "Chair"],
                "brands": ["GamePro", "RazerX", "LogiGame", "SteelMax"],
            },
            "Accessories": {
                "prefixes": ["Premium", "Universal", "Fast", "Wireless", "Portable"],
                "items": ["Charger", "Cable", "Case", "Screen Protector", "Stand", "Adapter"],
            },
        }

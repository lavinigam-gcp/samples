"""Subscription service template."""

from dataclasses import dataclass, field
from typing import Any

from ucp_store_mocker.templates.base import BaseTemplate


@dataclass
class SubscriptionTemplate(BaseTemplate):
    """Template for subscription-based services."""

    name: str = "subscription"
    description: str = "Subscription service"

    default_categories: list[dict[str, Any]] = field(default_factory=lambda: [
        {"name": "Basic Plans", "count": 3, "price_range": [499, 999]},
        {"name": "Premium Plans", "count": 3, "price_range": [1499, 2999]},
        {"name": "Enterprise Plans", "count": 2, "price_range": [4999, 9999]},
        {"name": "Add-ons", "count": 5, "price_range": [199, 999]},
    ])

    default_variations: dict[str, list[dict]] = field(default_factory=lambda: {
        "Basic Plans": [
            {"type": "billing", "options": ["Monthly", "Yearly"],
             "price_multipliers": [1.0, 10.0]},  # Yearly is 10x monthly (2 months free)
        ],
        "Premium Plans": [
            {"type": "billing", "options": ["Monthly", "Yearly"],
             "price_multipliers": [1.0, 10.0]},
        ],
        "Enterprise Plans": [
            {"type": "billing", "options": ["Monthly", "Yearly"],
             "price_multipliers": [1.0, 10.0]},
        ],
    })

    default_fulfillment: list[dict[str, Any]] = field(default_factory=lambda: [])  # No fulfillment for digital subscriptions

    sample_products: list[dict[str, Any]] = field(default_factory=lambda: [
        {"title": "Starter Plan", "category": "Basic Plans", "price": 499,
         "description": "Perfect for individuals", "features": ["5 projects", "Basic support"]},
        {"title": "Pro Plan", "category": "Premium Plans", "price": 1999,
         "description": "For growing teams", "features": ["Unlimited projects", "Priority support", "Advanced analytics"]},
        {"title": "Enterprise Plan", "category": "Enterprise Plans", "price": 7999,
         "description": "For large organizations", "features": ["Custom integrations", "Dedicated support", "SLA"]},
        {"title": "Extra Storage", "category": "Add-ons", "price": 499,
         "description": "50GB additional storage"},
        {"title": "API Access", "category": "Add-ons", "price": 999,
         "description": "Full API access for integrations"},
    ])

    def get_product_descriptors(self) -> dict[str, list[str]]:
        """Get product name descriptors for Faker generation."""
        return {
            "Basic Plans": {
                "names": ["Starter", "Basic", "Personal", "Lite", "Free Trial"],
                "features": ["Limited projects", "Email support", "Basic features"],
            },
            "Premium Plans": {
                "names": ["Pro", "Professional", "Team", "Business", "Growth"],
                "features": ["Unlimited projects", "Priority support", "Advanced analytics", "Team collaboration"],
            },
            "Enterprise Plans": {
                "names": ["Enterprise", "Corporate", "Ultimate", "Scale"],
                "features": ["Custom integrations", "Dedicated support", "SLA", "Custom contracts", "On-premise option"],
            },
            "Add-ons": {
                "names": ["Extra Storage", "API Access", "Custom Domain", "Priority Queue", "Backup Service"],
            },
        }

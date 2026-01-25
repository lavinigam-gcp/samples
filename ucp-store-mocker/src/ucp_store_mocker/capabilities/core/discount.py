"""Discount capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class DiscountCapability:
    """UCP Discount capability."""

    id: str = "dev.ucp.shopping.discount"
    name: str = "Discount"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return []  # Integrated into checkout routes

    def get_services(self) -> list[str]:
        """Get service templates needed for this capability."""
        return []

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "apply_discount",
                "type": "dev.ucp.action.apply_discount",
                "description": "Apply a discount code to checkout",
            },
            {
                "id": "remove_discount",
                "type": "dev.ucp.action.remove_discount",
                "description": "Remove a discount from checkout",
            },
        ]

    def get_discount_types(self) -> list[str]:
        """Get supported discount types."""
        return ["percentage", "fixed"]

    def get_models(self) -> list[str]:
        """Get model imports needed for this capability."""
        return [
            "Discount",
            "DiscountType",
        ]

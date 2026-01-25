"""Fulfillment capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class FulfillmentCapability:
    """UCP Fulfillment capability."""

    id: str = "dev.ucp.shopping.fulfillment"
    name: str = "Fulfillment"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return []  # Integrated into checkout routes

    def get_services(self) -> list[str]:
        """Get service templates needed for this capability."""
        return ["services/fulfillment_service.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "get_fulfillment_options",
                "type": "dev.ucp.action.get_fulfillment_options",
                "description": "Get available fulfillment options",
            },
            {
                "id": "set_fulfillment",
                "type": "dev.ucp.action.set_fulfillment",
                "description": "Set fulfillment method on checkout",
            },
        ]

    def get_fulfillment_types(self) -> list[str]:
        """Get supported fulfillment types."""
        return ["shipping", "pickup"]

    def get_models(self) -> list[str]:
        """Get model imports needed for this capability."""
        return [
            "FulfillmentOption",
            "FulfillmentMethod",
            "ShippingAddress",
        ]

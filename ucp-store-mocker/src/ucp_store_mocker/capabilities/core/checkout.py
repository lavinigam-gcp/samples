"""Checkout capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class CheckoutCapability:
    """UCP Checkout capability - always enabled."""

    id: str = "dev.ucp.shopping.checkout"
    name: str = "Checkout"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["routes/checkout.py.j2"]

    def get_services(self) -> list[str]:
        """Get service templates needed for this capability."""
        return ["services/checkout_service.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "create_checkout",
                "type": "dev.ucp.action.create_checkout",
                "description": "Create a new checkout session",
            },
            {
                "id": "get_checkout",
                "type": "dev.ucp.action.get_checkout",
                "description": "Get checkout by ID",
            },
            {
                "id": "update_checkout",
                "type": "dev.ucp.action.update_checkout",
                "description": "Update checkout with items, fulfillment, or payment",
            },
            {
                "id": "complete_checkout",
                "type": "dev.ucp.action.complete_checkout",
                "description": "Complete checkout and create order",
            },
            {
                "id": "cancel_checkout",
                "type": "dev.ucp.action.cancel_checkout",
                "description": "Cancel an active checkout",
            },
        ]

    def get_models(self) -> list[str]:
        """Get model imports needed for this capability."""
        return [
            "Checkout",
            "CheckoutLineItem",
            "CheckoutStatus",
        ]

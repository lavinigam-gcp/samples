"""Order capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class OrderCapability:
    """UCP Order capability."""

    id: str = "dev.ucp.shopping.order"
    name: str = "Order"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["routes/order.py.j2"]

    def get_services(self) -> list[str]:
        """Get service templates needed for this capability."""
        return []

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "get_order",
                "type": "dev.ucp.action.get_order",
                "description": "Get order by ID",
            },
            {
                "id": "list_orders",
                "type": "dev.ucp.action.list_orders",
                "description": "List orders for a buyer",
            },
            {
                "id": "cancel_order",
                "type": "dev.ucp.action.cancel_order",
                "description": "Cancel an order",
            },
        ]

    def get_webhook_events(self) -> list[str]:
        """Get webhook event types for this capability."""
        return [
            "order.created",
            "order.updated",
            "order.completed",
            "order.cancelled",
            "order.refunded",
        ]

    def get_models(self) -> list[str]:
        """Get model imports needed for this capability."""
        return [
            "Order",
            "OrderLineItem",
            "OrderStatus",
        ]

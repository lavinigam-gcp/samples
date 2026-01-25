"""Returns extended capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ReturnsCapability:
    """Extended capability for returns and refunds."""

    id: str = "dev.ucp.shopping.returns"
    name: str = "Returns"
    extends: str = "dev.ucp.shopping.order"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["capabilities/returns.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "create_return_request",
                "type": "dev.ucp.action.create_return_request",
                "description": "Request a return for order items",
            },
            {
                "id": "get_return_request",
                "type": "dev.ucp.action.get_return_request",
                "description": "Get return request details",
            },
            {
                "id": "get_return_eligibility",
                "type": "dev.ucp.action.get_return_eligibility",
                "description": "Check if items are eligible for return",
            },
            {
                "id": "cancel_return_request",
                "type": "dev.ucp.action.cancel_return_request",
                "description": "Cancel a pending return request",
            },
        ]

    def get_database_tables(self) -> list[dict[str, Any]]:
        """Get database table definitions for this capability."""
        return [
            {
                "name": "return_requests",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "order_id", "type": "TEXT", "index": True},
                    {"name": "buyer_id", "type": "TEXT", "index": True},
                    {"name": "status", "type": "TEXT"},  # pending, approved, rejected, completed
                    {"name": "reason", "type": "TEXT"},
                    {"name": "refund_amount", "type": "INTEGER"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                    {"name": "resolved_at", "type": "TIMESTAMP", "nullable": True},
                ],
            },
            {
                "name": "return_items",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "return_request_id", "type": "TEXT", "foreign_key": "return_requests.id"},
                    {"name": "order_line_item_id", "type": "TEXT"},
                    {"name": "quantity", "type": "INTEGER"},
                    {"name": "reason", "type": "TEXT", "nullable": True},
                ],
            },
        ]

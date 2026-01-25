"""Subscriptions extended capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class SubscriptionsCapability:
    """Extended capability for subscription management."""

    id: str = "dev.ucp.shopping.subscriptions"
    name: str = "Subscriptions"
    extends: str = "dev.ucp.shopping.order"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["capabilities/subscriptions.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "create_subscription",
                "type": "dev.ucp.action.create_subscription",
                "description": "Create a new subscription",
            },
            {
                "id": "get_subscription",
                "type": "dev.ucp.action.get_subscription",
                "description": "Get subscription details",
            },
            {
                "id": "update_subscription",
                "type": "dev.ucp.action.update_subscription",
                "description": "Update subscription (change plan, quantity)",
            },
            {
                "id": "pause_subscription",
                "type": "dev.ucp.action.pause_subscription",
                "description": "Pause a subscription",
            },
            {
                "id": "resume_subscription",
                "type": "dev.ucp.action.resume_subscription",
                "description": "Resume a paused subscription",
            },
            {
                "id": "cancel_subscription",
                "type": "dev.ucp.action.cancel_subscription",
                "description": "Cancel a subscription",
            },
        ]

    def get_database_tables(self) -> list[dict[str, Any]]:
        """Get database table definitions for this capability."""
        return [
            {
                "name": "subscriptions",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "buyer_id", "type": "TEXT", "index": True},
                    {"name": "product_id", "type": "TEXT"},
                    {"name": "status", "type": "TEXT"},  # active, paused, cancelled
                    {"name": "billing_cycle", "type": "TEXT"},  # monthly, yearly
                    {"name": "current_period_start", "type": "TIMESTAMP"},
                    {"name": "current_period_end", "type": "TIMESTAMP"},
                    {"name": "next_billing_date", "type": "TIMESTAMP"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                    {"name": "cancelled_at", "type": "TIMESTAMP", "nullable": True},
                ],
            },
            {
                "name": "subscription_invoices",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "subscription_id", "type": "TEXT", "foreign_key": "subscriptions.id"},
                    {"name": "amount", "type": "INTEGER"},
                    {"name": "status", "type": "TEXT"},  # pending, paid, failed
                    {"name": "period_start", "type": "TIMESTAMP"},
                    {"name": "period_end", "type": "TIMESTAMP"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                    {"name": "paid_at", "type": "TIMESTAMP", "nullable": True},
                ],
            },
        ]

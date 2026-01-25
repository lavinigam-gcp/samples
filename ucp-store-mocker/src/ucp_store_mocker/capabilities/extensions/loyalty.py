"""Loyalty extended capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class LoyaltyCapability:
    """Extended capability for loyalty points and tiers."""

    id: str = "dev.ucp.shopping.loyalty"
    name: str = "Loyalty"
    extends: str = "dev.ucp.shopping.checkout"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["capabilities/loyalty.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "get_loyalty_balance",
                "type": "dev.ucp.action.get_loyalty_balance",
                "description": "Get buyer's loyalty points balance",
            },
            {
                "id": "get_loyalty_tier",
                "type": "dev.ucp.action.get_loyalty_tier",
                "description": "Get buyer's current loyalty tier",
            },
            {
                "id": "redeem_points",
                "type": "dev.ucp.action.redeem_points",
                "description": "Redeem loyalty points on checkout",
            },
            {
                "id": "get_loyalty_history",
                "type": "dev.ucp.action.get_loyalty_history",
                "description": "Get points transaction history",
            },
        ]

    def get_database_tables(self) -> list[dict[str, Any]]:
        """Get database table definitions for this capability."""
        return [
            {
                "name": "loyalty_accounts",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "buyer_id", "type": "TEXT", "unique": True},
                    {"name": "points_balance", "type": "INTEGER", "default": 0},
                    {"name": "lifetime_points", "type": "INTEGER", "default": 0},
                    {"name": "tier", "type": "TEXT", "default": "'Bronze'"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
            },
            {
                "name": "loyalty_transactions",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "account_id", "type": "TEXT", "foreign_key": "loyalty_accounts.id"},
                    {"name": "points", "type": "INTEGER"},
                    {"name": "type", "type": "TEXT"},  # earned, redeemed, expired
                    {"name": "order_id", "type": "TEXT", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
            },
        ]

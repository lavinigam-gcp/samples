"""Gift cards extended capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class GiftCardsCapability:
    """Extended capability for gift cards."""

    id: str = "dev.ucp.shopping.gift_cards"
    name: str = "Gift Cards"
    extends: str = "dev.ucp.shopping.checkout"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["capabilities/gift_cards.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "purchase_gift_card",
                "type": "dev.ucp.action.purchase_gift_card",
                "description": "Purchase a new gift card",
            },
            {
                "id": "get_gift_card_balance",
                "type": "dev.ucp.action.get_gift_card_balance",
                "description": "Check gift card balance",
            },
            {
                "id": "redeem_gift_card",
                "type": "dev.ucp.action.redeem_gift_card",
                "description": "Apply gift card to checkout",
            },
        ]

    def get_database_tables(self) -> list[dict[str, Any]]:
        """Get database table definitions for this capability."""
        return [
            {
                "name": "gift_cards",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "code", "type": "TEXT", "unique": True},
                    {"name": "initial_balance", "type": "INTEGER"},
                    {"name": "current_balance", "type": "INTEGER"},
                    {"name": "purchaser_email", "type": "TEXT", "nullable": True},
                    {"name": "recipient_email", "type": "TEXT", "nullable": True},
                    {"name": "is_active", "type": "BOOLEAN", "default": True},
                    {"name": "created_at", "type": "TIMESTAMP"},
                    {"name": "expires_at", "type": "TIMESTAMP", "nullable": True},
                ],
            },
            {
                "name": "gift_card_transactions",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "gift_card_id", "type": "TEXT", "foreign_key": "gift_cards.id"},
                    {"name": "amount", "type": "INTEGER"},
                    {"name": "type", "type": "TEXT"},  # purchase, redemption
                    {"name": "order_id", "type": "TEXT", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
            },
        ]

"""Wishlist extended capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class WishlistCapability:
    """Extended capability for wishlist functionality."""

    id: str = "dev.ucp.shopping.wishlist"
    name: str = "Wishlist"
    extends: str = "dev.ucp.shopping.checkout"

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["capabilities/wishlist.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "add_to_wishlist",
                "type": "dev.ucp.action.add_to_wishlist",
                "description": "Add item to wishlist",
            },
            {
                "id": "remove_from_wishlist",
                "type": "dev.ucp.action.remove_from_wishlist",
                "description": "Remove item from wishlist",
            },
            {
                "id": "get_wishlist",
                "type": "dev.ucp.action.get_wishlist",
                "description": "Get buyer's wishlist",
            },
            {
                "id": "move_to_cart",
                "type": "dev.ucp.action.move_to_cart",
                "description": "Move wishlist item to checkout",
            },
        ]

    def get_database_tables(self) -> list[dict[str, Any]]:
        """Get database table definitions for this capability."""
        return [
            {
                "name": "wishlists",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "buyer_id", "type": "TEXT", "index": True},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
            },
            {
                "name": "wishlist_items",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "wishlist_id", "type": "TEXT", "foreign_key": "wishlists.id"},
                    {"name": "product_id", "type": "TEXT"},
                    {"name": "variant_id", "type": "TEXT", "nullable": True},
                    {"name": "added_at", "type": "TIMESTAMP"},
                ],
            },
        ]

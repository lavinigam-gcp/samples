"""Reviews extended capability definition."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ReviewsCapability:
    """Extended capability for product reviews."""

    id: str = "dev.ucp.shopping.reviews"
    name: str = "Reviews"
    extends: str = None

    def get_routes(self) -> list[str]:
        """Get route templates needed for this capability."""
        return ["capabilities/reviews.py.j2"]

    def get_discovery_actions(self) -> list[dict[str, Any]]:
        """Get UCP discovery profile actions for this capability."""
        return [
            {
                "id": "create_review",
                "type": "dev.ucp.action.create_review",
                "description": "Create a product review",
            },
            {
                "id": "get_reviews",
                "type": "dev.ucp.action.get_reviews",
                "description": "Get reviews for a product",
            },
            {
                "id": "get_review_summary",
                "type": "dev.ucp.action.get_review_summary",
                "description": "Get aggregate review statistics for a product",
            },
        ]

    def get_database_tables(self) -> list[dict[str, Any]]:
        """Get database table definitions for this capability."""
        return [
            {
                "name": "reviews",
                "columns": [
                    {"name": "id", "type": "TEXT", "primary_key": True},
                    {"name": "product_id", "type": "TEXT", "index": True},
                    {"name": "buyer_id", "type": "TEXT", "nullable": True},
                    {"name": "rating", "type": "INTEGER"},
                    {"name": "title", "type": "TEXT", "nullable": True},
                    {"name": "body", "type": "TEXT", "nullable": True},
                    {"name": "verified_purchase", "type": "BOOLEAN", "default": False},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ],
            },
        ]

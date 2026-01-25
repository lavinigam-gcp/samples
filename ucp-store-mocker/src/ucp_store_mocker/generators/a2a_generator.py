"""A2A (Agent-to-Agent) code generator."""

import json
from pathlib import Path
from typing import Any

from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.utils.file_utils import ensure_dir, write_file


class A2AGenerator:
    """Generate A2A agent card and handler code."""

    def __init__(self, config: StoreConfig):
        self.config = config

    def generate(self, output_path: Path) -> list[str]:
        """Generate A2A files and return list of created paths."""
        files = []

        a2a_dir = ensure_dir(output_path / "src" / "server" / "a2a")

        # Generate agent card
        agent_card = self._generate_agent_card()
        path = write_file(a2a_dir / "agent_card.json", json.dumps(agent_card, indent=2))
        files.append(str(path))

        # Generate agent handler
        agent_code = self._generate_agent_handler()
        path = write_file(a2a_dir / "agent.py", agent_code)
        files.append(str(path))

        # Generate __init__.py
        path = write_file(a2a_dir / "__init__.py", "")
        files.append(str(path))

        return files

    def _generate_agent_card(self) -> dict[str, Any]:
        """Generate A2A agent card JSON."""
        store_name = self.config.store.name
        agent_name = self.config.a2a.agent_card.name or f"{store_name} Agent"

        # Build skills list
        skills = []
        for skill_config in self.config.a2a.agent_card.skills:
            skill = {
                "id": skill_config.id,
                "name": skill_config.id.replace("_", " ").title(),
            }
            if skill_config.description:
                skill["description"] = skill_config.description
            else:
                skill["description"] = self._get_default_skill_description(skill_config.id)
            skills.append(skill)

        # Default skills if none configured
        if not skills:
            skills = [
                {
                    "id": "product_search",
                    "name": "Product Search",
                    "description": "Search for products in the catalog",
                },
                {
                    "id": "checkout",
                    "name": "Checkout",
                    "description": "Manage checkout sessions and complete purchases",
                },
            ]

        agent_card = {
            "name": agent_name,
            "description": self.config.a2a.agent_card.description or f"Shopping agent for {store_name}",
            "url": f"http://localhost:{self.config.server.port}",
            "version": "0.1.0",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
            },
            "skills": skills,
            "authentication": {
                "schemes": ["none"],
            },
        }

        return agent_card

    def _get_default_skill_description(self, skill_id: str) -> str:
        """Get default description for a skill."""
        descriptions = {
            "product_search": "Search for products by name, category, or attributes",
            "checkout": "Create and manage checkout sessions",
            "order_status": "Check order status and history",
            "inventory": "Check product availability and stock levels",
            "recommendations": "Get product recommendations",
        }
        return descriptions.get(skill_id, f"Perform {skill_id.replace('_', ' ')} operations")

    def _generate_agent_handler(self) -> str:
        """Generate A2A agent handler code."""
        store_name = self.config.store.name

        return f'''"""A2A Agent handler for {store_name}."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

from server.db import query_db, query_one
from server.services.checkout_service import CheckoutService


router = APIRouter()


class AgentMessage(BaseModel):
    """Incoming agent message."""
    type: str
    content: Any
    context: Optional[dict] = None


class AgentResponse(BaseModel):
    """Agent response."""
    type: str
    content: Any
    metadata: Optional[dict] = None


@router.get("/.well-known/agent.json")
async def get_agent_card():
    """Return the A2A agent card."""
    card_path = Path(__file__).parent / "agent_card.json"
    if card_path.exists():
        with open(card_path) as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Agent card not found")


@router.post("/agent/message")
async def handle_message(message: AgentMessage) -> AgentResponse:
    """Handle incoming agent messages."""
    handler = MessageHandler()
    return handler.handle(message)


class MessageHandler:
    """Handle different types of agent messages."""

    def __init__(self):
        self.checkout_service = CheckoutService()

    def handle(self, message: AgentMessage) -> AgentResponse:
        """Route message to appropriate handler."""
        handlers = {{
            "product_search": self._handle_product_search,
            "product_details": self._handle_product_details,
            "create_checkout": self._handle_create_checkout,
            "add_to_cart": self._handle_add_to_cart,
            "get_checkout": self._handle_get_checkout,
            "complete_checkout": self._handle_complete_checkout,
        }}

        handler = handlers.get(message.type)
        if not handler:
            return AgentResponse(
                type="error",
                content={{"message": f"Unknown message type: {{message.type}}"}},
            )

        try:
            result = handler(message.content)
            return AgentResponse(type=message.type + "_response", content=result)
        except Exception as e:
            return AgentResponse(
                type="error",
                content={{"message": str(e)}},
            )

    def _handle_product_search(self, content: dict) -> dict:
        """Search for products."""
        query = content.get("query", "")
        category = content.get("category")
        limit = content.get("limit", 10)

        sql = "SELECT * FROM products WHERE 1=1"
        params = []

        if query:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{{query}}%", f"%{{query}}%"])

        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " LIMIT ?"
        params.append(limit)

        products = query_db(sql, tuple(params))
        return {{"products": products, "total": len(products)}}

    def _handle_product_details(self, content: dict) -> dict:
        """Get product details."""
        product_id = content.get("product_id")
        if not product_id:
            raise ValueError("product_id is required")

        product = query_one("SELECT * FROM products WHERE id = ?", (product_id,))
        if not product:
            raise ValueError(f"Product not found: {{product_id}}")

        # Get inventory
        inventory = query_one("SELECT * FROM inventory WHERE product_id = ?", (product_id,))
        if inventory:
            product["inventory"] = {{
                "quantity": inventory["quantity"],
                "available": inventory["quantity"] > 0,
            }}

        return product

    def _handle_create_checkout(self, content: dict) -> dict:
        """Create a new checkout."""
        buyer_id = content.get("buyer_id")
        checkout = self.checkout_service.create_checkout(buyer_id)
        return checkout

    def _handle_add_to_cart(self, content: dict) -> dict:
        """Add item to checkout."""
        checkout_id = content.get("checkout_id")
        product_id = content.get("product_id")
        quantity = content.get("quantity", 1)

        if not checkout_id or not product_id:
            raise ValueError("checkout_id and product_id are required")

        checkout = self.checkout_service.add_line_item(
            checkout_id, product_id, None, quantity
        )
        if not checkout:
            raise ValueError("Failed to add item to checkout")

        return checkout

    def _handle_get_checkout(self, content: dict) -> dict:
        """Get checkout details."""
        checkout_id = content.get("checkout_id")
        if not checkout_id:
            raise ValueError("checkout_id is required")

        checkout = self.checkout_service.get_checkout(checkout_id)
        if not checkout:
            raise ValueError(f"Checkout not found: {{checkout_id}}")

        return checkout

    def _handle_complete_checkout(self, content: dict) -> dict:
        """Complete a checkout."""
        checkout_id = content.get("checkout_id")
        if not checkout_id:
            raise ValueError("checkout_id is required")

        result = self.checkout_service.complete_checkout(checkout_id)
        if not result:
            raise ValueError("Failed to complete checkout")

        return result
'''

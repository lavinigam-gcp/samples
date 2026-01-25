"""Server code generator - generates FastAPI server code."""

from pathlib import Path

from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.utils.file_utils import ensure_dir, write_file


class ServerGenerator:
    """Generates FastAPI server code for the mock store."""

    def __init__(self, config: StoreConfig):
        self.config = config

    def generate(self, output_path: Path) -> list[str]:
        """Generate all server files and return list of created paths."""
        files = []

        # Create server package structure
        server_dir = ensure_dir(output_path / "src" / "server")
        routes_dir = ensure_dir(server_dir / "routes")
        services_dir = ensure_dir(server_dir / "services")

        # Generate main files
        files.append(str(write_file(server_dir / "__init__.py", "")))
        files.append(str(write_file(server_dir / "__main__.py", self._render_main())))
        files.append(str(write_file(server_dir / "server.py", self._render_server())))
        files.append(str(write_file(server_dir / "config.py", self._render_config())))
        files.append(str(write_file(server_dir / "db.py", self._render_db())))

        # Generate routes
        files.append(str(write_file(routes_dir / "__init__.py", "")))
        files.append(str(write_file(routes_dir / "discovery.py", self._render_discovery_routes())))
        files.append(str(write_file(routes_dir / "checkout.py", self._render_checkout_routes())))

        if self.config.capabilities.order.enabled:
            files.append(str(write_file(routes_dir / "order.py", self._render_order_routes())))

        # Generate services
        files.append(str(write_file(services_dir / "__init__.py", "")))
        files.append(str(write_file(services_dir / "checkout_service.py", self._render_checkout_service())))

        if self.config.capabilities.fulfillment.enabled:
            files.append(str(write_file(services_dir / "fulfillment_service.py", self._render_fulfillment_service())))

        files.append(str(write_file(services_dir / "inventory_service.py", self._render_inventory_service())))

        # Generate extended capability routes if enabled
        if self.config.capabilities.wishlist and self.config.capabilities.wishlist.enabled:
            cap_dir = ensure_dir(server_dir / "capabilities")
            files.append(str(write_file(cap_dir / "__init__.py", "")))
            files.append(str(write_file(cap_dir / "wishlist.py", self._render_wishlist_capability())))

        return files

    def _render_main(self) -> str:
        """Render __main__.py entry point."""
        return '''"""Entry point for running the server."""

import argparse
import uvicorn

from server.config import settings


def main():
    parser = argparse.ArgumentParser(description="Run the UCP mock store server")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to run on")
    parser.add_argument("--host", type=str, default=settings.host, help="Host to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    uvicorn.run(
        "server.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
'''

    def _render_server(self) -> str:
        """Render main FastAPI server."""
        store_name = self.config.store.name

        routes_imports = [
            "from server.routes.discovery import router as discovery_router",
            "from server.routes.checkout import router as checkout_router",
        ]

        routes_includes = [
            'app.include_router(discovery_router, tags=["Discovery"])',
            'app.include_router(checkout_router, prefix="/checkout", tags=["Checkout"])',
        ]

        if self.config.capabilities.order.enabled:
            routes_imports.append("from server.routes.order import router as order_router")
            routes_includes.append('app.include_router(order_router, prefix="/orders", tags=["Orders"])')

        imports_str = "\n".join(routes_imports)
        includes_str = "\n    ".join(routes_includes)

        return f'''"""FastAPI server for {store_name}."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from server.config import settings
from server.db import init_db
{imports_str}


app = FastAPI(
    title="{store_name}",
    description="UCP-compliant mock store",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for product images
static_path = Path(__file__).parent.parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
{includes_str}


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "store": "{store_name}"}}
'''

    def _render_config(self) -> str:
        """Render configuration module."""
        return f'''"""Configuration settings for the server."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration."""

    # Server
    host: str = "0.0.0.0"
    port: int = {self.config.server.port}

    # Store info
    store_name: str = "{self.config.store.name}"
    store_type: str = "{self.config.store.type}"

    # Database
    database_path: str = str(Path(__file__).parent.parent.parent / "databases" / "store.db")

    # Data paths
    data_path: str = str(Path(__file__).parent.parent.parent / "data")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
'''

    def _render_db(self) -> str:
        """Render database module."""
        return '''"""Database connection and initialization."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

from server.config import settings


def get_db_path() -> Path:
    """Get database path, creating parent directory if needed."""
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_db():
    """Initialize the database with schema."""
    db_path = get_db_path()

    # Check if init.sql exists
    init_sql_path = db_path.parent / "init.sql"
    if init_sql_path.exists():
        with open(init_sql_path) as f:
            init_sql = f.read()

        conn = sqlite3.connect(db_path)
        conn.executescript(init_sql)
        conn.commit()
        conn.close()


@contextmanager
def get_db():
    """Get database connection context manager."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def query_db(sql: str, params: tuple = ()):
    """Execute a query and return all results."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def query_one(sql: str, params: tuple = ()):
    """Execute a query and return one result."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def execute_db(sql: str, params: tuple = ()):
    """Execute a write operation."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
'''

    def _render_discovery_routes(self) -> str:
        """Render UCP discovery routes."""
        return '''"""UCP discovery endpoint routes."""

import json
from pathlib import Path
from fastapi import APIRouter

from server.config import settings


router = APIRouter()


@router.get("/.well-known/ucp")
async def get_ucp_discovery():
    """Return UCP discovery profile."""
    profile_path = Path(__file__).parent / "discovery_profile.json"

    if profile_path.exists():
        with open(profile_path) as f:
            return json.load(f)

    # Fallback minimal profile
    return {
        "profile_version": "0.1.0",
        "name": settings.store_name,
        "capabilities": ["dev.ucp.shopping.checkout"],
    }
'''

    def _render_checkout_routes(self) -> str:
        """Render checkout routes."""
        return '''"""Checkout routes for UCP shopping."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from server.services.checkout_service import CheckoutService


router = APIRouter()
checkout_service = CheckoutService()


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout."""
    buyer_id: Optional[str] = None


class AddLineItemRequest(BaseModel):
    """Request to add a line item."""
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1


class UpdateLineItemRequest(BaseModel):
    """Request to update a line item quantity."""
    quantity: int


class ApplyDiscountRequest(BaseModel):
    """Request to apply a discount code."""
    code: str


class SetFulfillmentRequest(BaseModel):
    """Request to set fulfillment method."""
    method_id: str
    address: Optional[dict] = None


@router.post("")
async def create_checkout(request: CreateCheckoutRequest):
    """Create a new checkout session."""
    checkout = checkout_service.create_checkout(request.buyer_id)
    return checkout


@router.get("/{checkout_id}")
async def get_checkout(checkout_id: str):
    """Get checkout by ID."""
    checkout = checkout_service.get_checkout(checkout_id)
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    return checkout


@router.post("/{checkout_id}/line-items")
async def add_line_item(checkout_id: str, request: AddLineItemRequest):
    """Add a line item to checkout."""
    checkout = checkout_service.add_line_item(
        checkout_id,
        request.product_id,
        request.variant_id,
        request.quantity
    )
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    return checkout


@router.patch("/{checkout_id}/line-items/{line_item_id}")
async def update_line_item(checkout_id: str, line_item_id: str, request: UpdateLineItemRequest):
    """Update a line item quantity."""
    checkout = checkout_service.update_line_item(checkout_id, line_item_id, request.quantity)
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout or line item not found")
    return checkout


@router.delete("/{checkout_id}/line-items/{line_item_id}")
async def remove_line_item(checkout_id: str, line_item_id: str):
    """Remove a line item from checkout."""
    checkout = checkout_service.remove_line_item(checkout_id, line_item_id)
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout or line item not found")
    return checkout


@router.post("/{checkout_id}/discounts")
async def apply_discount(checkout_id: str, request: ApplyDiscountRequest):
    """Apply a discount code to checkout."""
    checkout = checkout_service.apply_discount(checkout_id, request.code)
    if not checkout:
        raise HTTPException(status_code=400, detail="Invalid discount code")
    return checkout


@router.post("/{checkout_id}/fulfillment")
async def set_fulfillment(checkout_id: str, request: SetFulfillmentRequest):
    """Set fulfillment method on checkout."""
    checkout = checkout_service.set_fulfillment(checkout_id, request.method_id, request.address)
    if not checkout:
        raise HTTPException(status_code=400, detail="Invalid fulfillment method")
    return checkout


@router.post("/{checkout_id}/complete")
async def complete_checkout(checkout_id: str):
    """Complete checkout and create order."""
    result = checkout_service.complete_checkout(checkout_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot complete checkout")
    return result


@router.post("/{checkout_id}/cancel")
async def cancel_checkout(checkout_id: str):
    """Cancel an active checkout."""
    success = checkout_service.cancel_checkout(checkout_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel checkout")
    return {"status": "cancelled", "checkout_id": checkout_id}
'''

    def _render_order_routes(self) -> str:
        """Render order routes."""
        return '''"""Order routes for UCP shopping."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from server.db import query_db, query_one


router = APIRouter()


@router.get("/{order_id}")
async def get_order(order_id: str):
    """Get order by ID."""
    order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get line items
    items = query_db("SELECT * FROM order_line_items WHERE order_id = ?", (order_id,))
    order["line_items"] = items

    return order


@router.get("")
async def list_orders(buyer_id: Optional[str] = None, limit: int = 20, offset: int = 0):
    """List orders, optionally filtered by buyer."""
    if buyer_id:
        orders = query_db(
            "SELECT * FROM orders WHERE buyer_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (buyer_id, limit, offset)
        )
    else:
        orders = query_db(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )

    return {"orders": orders, "total": len(orders)}


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancel an order."""
    order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] not in ["pending", "confirmed"]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    from server.db import execute_db
    execute_db("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))

    return {"status": "cancelled", "order_id": order_id}
'''

    def _render_checkout_service(self) -> str:
        """Render checkout service."""
        return '''"""Checkout service for managing checkout sessions."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from server.db import query_db, query_one, execute_db


class CheckoutService:
    """Service for managing checkout sessions."""

    def create_checkout(self, buyer_id: Optional[str] = None) -> dict:
        """Create a new checkout session."""
        checkout_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        execute_db(
            """INSERT INTO checkouts (id, buyer_id, status, subtotal, total, currency, created_at, updated_at)
               VALUES (?, ?, 'active', 0, 0, 'USD', ?, ?)""",
            (checkout_id, buyer_id, now, now)
        )

        return self.get_checkout(checkout_id)

    def get_checkout(self, checkout_id: str) -> Optional[dict]:
        """Get a checkout by ID."""
        checkout = query_one("SELECT * FROM checkouts WHERE id = ?", (checkout_id,))
        if not checkout:
            return None

        # Get line items
        items = query_db("SELECT * FROM checkout_line_items WHERE checkout_id = ?", (checkout_id,))
        checkout["line_items"] = items

        # Get applied discounts
        discounts = query_db("SELECT * FROM checkout_discounts WHERE checkout_id = ?", (checkout_id,))
        checkout["discounts"] = discounts

        return checkout

    def add_line_item(self, checkout_id: str, product_id: str, variant_id: Optional[str], quantity: int) -> Optional[dict]:
        """Add a line item to checkout."""
        checkout = query_one("SELECT * FROM checkouts WHERE id = ? AND status = 'active'", (checkout_id,))
        if not checkout:
            return None

        # Get product info
        product = query_one("SELECT * FROM products WHERE id = ?", (product_id,))
        if not product:
            return None

        # Check if item already exists
        existing = query_one(
            "SELECT * FROM checkout_line_items WHERE checkout_id = ? AND product_id = ? AND variant_id IS ?",
            (checkout_id, product_id, variant_id)
        )

        if existing:
            # Update quantity
            new_quantity = existing["quantity"] + quantity
            execute_db(
                "UPDATE checkout_line_items SET quantity = ? WHERE id = ?",
                (new_quantity, existing["id"])
            )
        else:
            # Add new item
            item_id = str(uuid.uuid4())
            execute_db(
                """INSERT INTO checkout_line_items (id, checkout_id, product_id, variant_id, title, price, quantity)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (item_id, checkout_id, product_id, variant_id, product["title"], product["price"], quantity)
            )

        self._recalculate_totals(checkout_id)
        return self.get_checkout(checkout_id)

    def update_line_item(self, checkout_id: str, line_item_id: str, quantity: int) -> Optional[dict]:
        """Update line item quantity."""
        if quantity <= 0:
            return self.remove_line_item(checkout_id, line_item_id)

        execute_db(
            "UPDATE checkout_line_items SET quantity = ? WHERE id = ? AND checkout_id = ?",
            (quantity, line_item_id, checkout_id)
        )
        self._recalculate_totals(checkout_id)
        return self.get_checkout(checkout_id)

    def remove_line_item(self, checkout_id: str, line_item_id: str) -> Optional[dict]:
        """Remove a line item from checkout."""
        execute_db(
            "DELETE FROM checkout_line_items WHERE id = ? AND checkout_id = ?",
            (line_item_id, checkout_id)
        )
        self._recalculate_totals(checkout_id)
        return self.get_checkout(checkout_id)

    def apply_discount(self, checkout_id: str, code: str) -> Optional[dict]:
        """Apply a discount code."""
        # Check discount exists and is active
        discount = query_one("SELECT * FROM discounts WHERE code = ? AND active = 1", (code,))
        if not discount:
            return None

        # Add to checkout discounts
        discount_id = str(uuid.uuid4())
        execute_db(
            "INSERT OR REPLACE INTO checkout_discounts (id, checkout_id, code, type, value) VALUES (?, ?, ?, ?, ?)",
            (discount_id, checkout_id, code, discount["type"], discount["value"])
        )

        self._recalculate_totals(checkout_id)
        return self.get_checkout(checkout_id)

    def set_fulfillment(self, checkout_id: str, method_id: str, address: Optional[dict]) -> Optional[dict]:
        """Set fulfillment method."""
        # Get shipping rate
        rate = query_one("SELECT * FROM shipping_rates WHERE id = ?", (method_id,))
        if not rate:
            return None

        execute_db(
            "UPDATE checkouts SET fulfillment_method = ?, fulfillment_price = ? WHERE id = ?",
            (method_id, rate["price"], checkout_id)
        )

        self._recalculate_totals(checkout_id)
        return self.get_checkout(checkout_id)

    def complete_checkout(self, checkout_id: str) -> Optional[dict]:
        """Complete checkout and create order."""
        checkout = self.get_checkout(checkout_id)
        if not checkout or checkout["status"] != "active":
            return None

        if not checkout["line_items"]:
            return None

        # Create order
        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        execute_db(
            """INSERT INTO orders (id, checkout_id, buyer_id, status, subtotal, total, currency, created_at)
               VALUES (?, ?, ?, 'confirmed', ?, ?, ?, ?)""",
            (order_id, checkout_id, checkout["buyer_id"], checkout["subtotal"], checkout["total"], checkout["currency"], now)
        )

        # Copy line items to order
        for item in checkout["line_items"]:
            item_id = str(uuid.uuid4())
            execute_db(
                """INSERT INTO order_line_items (id, order_id, product_id, variant_id, title, price, quantity)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (item_id, order_id, item["product_id"], item.get("variant_id"), item["title"], item["price"], item["quantity"])
            )

        # Mark checkout as completed
        execute_db("UPDATE checkouts SET status = 'completed' WHERE id = ?", (checkout_id,))

        return {"order_id": order_id, "checkout_id": checkout_id, "status": "confirmed"}

    def cancel_checkout(self, checkout_id: str) -> bool:
        """Cancel an active checkout."""
        checkout = query_one("SELECT * FROM checkouts WHERE id = ? AND status = 'active'", (checkout_id,))
        if not checkout:
            return False

        execute_db("UPDATE checkouts SET status = 'cancelled' WHERE id = ?", (checkout_id,))
        return True

    def _recalculate_totals(self, checkout_id: str):
        """Recalculate checkout totals."""
        checkout = query_one("SELECT * FROM checkouts WHERE id = ?", (checkout_id,))
        if not checkout:
            return

        # Calculate subtotal from line items
        items = query_db("SELECT * FROM checkout_line_items WHERE checkout_id = ?", (checkout_id,))
        subtotal = sum(item["price"] * item["quantity"] for item in items)

        # Apply discounts
        discounts = query_db("SELECT * FROM checkout_discounts WHERE checkout_id = ?", (checkout_id,))
        discount_amount = 0
        for discount in discounts:
            if discount["type"] == "percentage":
                discount_amount += int(subtotal * discount["value"] / 100)
            else:
                discount_amount += discount["value"]

        # Add fulfillment cost
        fulfillment_price = checkout.get("fulfillment_price") or 0

        total = max(0, subtotal - discount_amount + fulfillment_price)

        execute_db(
            "UPDATE checkouts SET subtotal = ?, total = ?, updated_at = ? WHERE id = ?",
            (subtotal, total, datetime.now(timezone.utc).isoformat(), checkout_id)
        )
'''

    def _render_fulfillment_service(self) -> str:
        """Render fulfillment service."""
        return '''"""Fulfillment service for managing shipping and pickup."""

from server.db import query_db


class FulfillmentService:
    """Service for fulfillment options and calculations."""

    def get_available_options(self, checkout_id: str = None) -> list:
        """Get available fulfillment options."""
        rates = query_db("SELECT * FROM shipping_rates")
        return rates

    def calculate_shipping(self, method_id: str, subtotal: int) -> int:
        """Calculate shipping cost, applying free shipping threshold if applicable."""
        from server.db import query_one
        rate = query_one("SELECT * FROM shipping_rates WHERE id = ?", (method_id,))
        if not rate:
            return 0

        # Check for free shipping threshold (configurable)
        FREE_SHIPPING_THRESHOLD = 3500  # $35.00

        if rate["type"] == "shipping" and subtotal >= FREE_SHIPPING_THRESHOLD:
            return 0

        return rate["price"]
'''

    def _render_inventory_service(self) -> str:
        """Render inventory service."""
        return '''"""Inventory service for stock management."""

from server.db import query_one, execute_db


class InventoryService:
    """Service for inventory management."""

    def check_availability(self, product_id: str, quantity: int = 1) -> bool:
        """Check if product has sufficient inventory."""
        inventory = query_one("SELECT * FROM inventory WHERE product_id = ?", (product_id,))
        if not inventory:
            return False
        return inventory["quantity"] >= quantity

    def get_inventory(self, product_id: str) -> dict:
        """Get inventory for a product."""
        inventory = query_one("SELECT * FROM inventory WHERE product_id = ?", (product_id,))
        if not inventory:
            return {"product_id": product_id, "quantity": 0, "available": False}

        return {
            "product_id": product_id,
            "quantity": inventory["quantity"],
            "available": inventory["quantity"] > 0,
            "low_stock": inventory["quantity"] <= inventory.get("low_stock_threshold", 10),
        }

    def reserve_inventory(self, product_id: str, quantity: int) -> bool:
        """Reserve inventory for a checkout."""
        if not self.check_availability(product_id, quantity):
            return False

        execute_db(
            "UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?",
            (quantity, product_id)
        )
        return True

    def release_inventory(self, product_id: str, quantity: int):
        """Release reserved inventory (e.g., on checkout cancellation)."""
        execute_db(
            "UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?",
            (quantity, product_id)
        )
'''

    def _render_wishlist_capability(self) -> str:
        """Render wishlist capability routes."""
        return '''"""Wishlist capability routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone

from server.db import query_db, query_one, execute_db


router = APIRouter()


class AddToWishlistRequest(BaseModel):
    """Request to add item to wishlist."""
    product_id: str
    variant_id: Optional[str] = None


@router.get("/wishlists/{buyer_id}")
async def get_wishlist(buyer_id: str):
    """Get buyer's wishlist."""
    wishlist = query_one("SELECT * FROM wishlists WHERE buyer_id = ?", (buyer_id,))

    if not wishlist:
        # Create new wishlist
        wishlist_id = str(uuid.uuid4())
        execute_db(
            "INSERT INTO wishlists (id, buyer_id, created_at) VALUES (?, ?, ?)",
            (wishlist_id, buyer_id, datetime.now(timezone.utc).isoformat())
        )
        wishlist = {"id": wishlist_id, "buyer_id": buyer_id, "items": []}
    else:
        items = query_db("SELECT * FROM wishlist_items WHERE wishlist_id = ?", (wishlist["id"],))
        wishlist["items"] = items

    return wishlist


@router.post("/wishlists/{buyer_id}/items")
async def add_to_wishlist(buyer_id: str, request: AddToWishlistRequest):
    """Add item to wishlist."""
    wishlist = query_one("SELECT * FROM wishlists WHERE buyer_id = ?", (buyer_id,))

    if not wishlist:
        wishlist_id = str(uuid.uuid4())
        execute_db(
            "INSERT INTO wishlists (id, buyer_id, created_at) VALUES (?, ?, ?)",
            (wishlist_id, buyer_id, datetime.now(timezone.utc).isoformat())
        )
    else:
        wishlist_id = wishlist["id"]

    # Check if already in wishlist
    existing = query_one(
        "SELECT * FROM wishlist_items WHERE wishlist_id = ? AND product_id = ? AND variant_id IS ?",
        (wishlist_id, request.product_id, request.variant_id)
    )

    if not existing:
        item_id = str(uuid.uuid4())
        execute_db(
            "INSERT INTO wishlist_items (id, wishlist_id, product_id, variant_id, added_at) VALUES (?, ?, ?, ?, ?)",
            (item_id, wishlist_id, request.product_id, request.variant_id, datetime.now(timezone.utc).isoformat())
        )

    return await get_wishlist(buyer_id)


@router.delete("/wishlists/{buyer_id}/items/{item_id}")
async def remove_from_wishlist(buyer_id: str, item_id: str):
    """Remove item from wishlist."""
    execute_db("DELETE FROM wishlist_items WHERE id = ?", (item_id,))
    return await get_wishlist(buyer_id)
'''

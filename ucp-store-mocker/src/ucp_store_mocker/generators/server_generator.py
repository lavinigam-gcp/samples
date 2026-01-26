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

        # Add testing routes for webhook simulation
        files.append(str(write_file(routes_dir / "testing.py", self._render_testing_routes())))

        # Generate services
        files.append(str(write_file(services_dir / "__init__.py", "")))
        files.append(str(write_file(services_dir / "checkout_service.py", self._render_checkout_service())))

        if self.config.capabilities.fulfillment.enabled:
            files.append(str(write_file(services_dir / "fulfillment_service.py", self._render_fulfillment_service())))

        files.append(str(write_file(services_dir / "inventory_service.py", self._render_inventory_service())))
        files.append(str(write_file(services_dir / "webhook_service.py", self._render_webhook_service())))

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
            "from server.routes.testing import router as testing_router",
        ]

        routes_includes = [
            'app.include_router(discovery_router, tags=["Discovery"])',
            'app.include_router(checkout_router, tags=["Checkout"])',
            'app.include_router(testing_router, prefix="/testing", tags=["Testing"])',
        ]

        if self.config.capabilities.order.enabled:
            routes_imports.append("from server.routes.order import router as order_router")
            routes_includes.append('app.include_router(order_router, prefix="/orders", tags=["Orders"])')

        imports_str = "\n".join(routes_imports)
        includes_str = "\n".join(routes_includes)

        return f'''"""FastAPI server for {store_name}."""

import re
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path

from server.config import settings
from server.db import init_db
{imports_str}


# UCP Protocol version supported by this server
SUPPORTED_VERSIONS = ["2026-01-11"]


class UCPVersionMiddleware(BaseHTTPMiddleware):
    """Middleware to validate UCP-Agent header version."""

    async def dispatch(self, request: Request, call_next):
        # Only validate on mutation requests (POST, PUT, PATCH)
        if request.method in ("POST", "PUT", "PATCH"):
            ucp_agent = request.headers.get("UCP-Agent", "")
            # Parse version from UCP-Agent header (format: 'agent="name" version="X.X.X"')
            version_match = re.search(r'version="([^"]+)"', ucp_agent)
            if version_match:
                version = version_match.group(1)
                if version not in SUPPORTED_VERSIONS:
                    return JSONResponse(
                        status_code=400,
                        content={{"error": "unsupported_version", "message": f"Version {{version}} is not supported"}}
                    )
        return await call_next(request)


app = FastAPI(
    title="{store_name}",
    description="UCP-compliant mock store",
    version="0.1.0",
)

# Add UCP version validation middleware
app.add_middleware(UCPVersionMiddleware)

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
    """Initialize database and import data on startup."""
    from server.db import query_one
    init_db()

    # Auto-import CSV data if database is empty
    result = query_one("SELECT COUNT(*) as count FROM products", ())
    if result and result["count"] == 0:
        import subprocess
        import sys
        from pathlib import Path
        script_path = Path(__file__).parent / "scripts" / "import_csv.py"
        if script_path.exists():
            subprocess.run([sys.executable, str(script_path)], check=True)


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
from fastapi import APIRouter, Request


router = APIRouter()

PROFILE_PATH = Path(__file__).parent / "discovery_profile.json"


@router.get("/.well-known/ucp")
async def get_ucp_discovery(request: Request):
    """Return UCP discovery profile."""
    if not PROFILE_PATH.exists():
        return {"error": "Discovery profile not found"}

    with open(PROFILE_PATH) as f:
        template = f.read()

    # Replace endpoint placeholder with actual request URL
    endpoint = str(request.base_url).rstrip("/")
    profile_json = template.replace("{{ENDPOINT}}", endpoint)

    return json.loads(profile_json)
'''

    def _render_checkout_routes(self) -> str:
        """Render checkout routes with UCP-compliant paths and response format."""
        return '''"""Checkout routes for UCP shopping.

Routes use /checkout-sessions path as per UCP specification.
Responses follow UCP SDK Checkout model schema.
"""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional, Any
import json
import hashlib
from pathlib import Path

from server.services.checkout_service import CheckoutService, PaymentFailureError, FulfillmentRequiredError


router = APIRouter()
checkout_service = CheckoutService()

# Idempotency cache: key -> (request_hash, response_json, status_code)
_idempotency_cache: dict[str, tuple[str, dict, int]] = {}


def _hash_request(data: Any) -> str:
    """Create a hash of the request data for idempotency comparison."""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _check_idempotency(key: str, request_data: Any) -> tuple[bool, Optional[tuple[dict, int]]]:
    """Check idempotency key and return cached response if valid.

    Returns:
        (is_conflict, cached_response_or_none)
        - (False, None): New key, proceed with request
        - (False, (response, status)): Same request, return cached response
        - (True, None): Different request with same key, return 409
    """
    if not key:
        return False, None

    request_hash = _hash_request(request_data)

    if key in _idempotency_cache:
        cached_hash, cached_response, cached_status = _idempotency_cache[key]
        if cached_hash == request_hash:
            return False, (cached_response, cached_status)
        else:
            return True, None

    return False, None


def _store_idempotency(key: str, request_data: Any, response: dict, status_code: int):
    """Store response for idempotency key."""
    if key:
        request_hash = _hash_request(request_data)
        _idempotency_cache[key] = (request_hash, response, status_code)

# UCP Protocol version
UCP_VERSION = "2026-01-11"

# Load discovery profile for payment handlers
PROFILE_PATH = Path(__file__).parent / "discovery_profile.json"

# Status mapping from internal to UCP spec
STATUS_MAP = {
    "incomplete": "incomplete",
    "in_progress": "incomplete",  # Map legacy status
    "active": "incomplete",  # Map legacy status
    "requires_escalation": "requires_escalation",
    "ready_for_complete": "ready_for_complete",
    "complete_in_progress": "complete_in_progress",
    "completed": "completed",
    "cancelled": "canceled",
    "canceled": "canceled",
}


def _get_payment_handlers() -> list[dict]:
    """Load payment handlers from discovery profile."""
    if PROFILE_PATH.exists():
        with open(PROFILE_PATH) as f:
            profile = json.load(f)
        return profile.get("payment", {}).get("handlers", [])
    # Default fallback with all required fields
    return [{
        "id": "mock_payment_handler",
        "name": "dev.ucp.mock_payment",
        "version": UCP_VERSION,
        "spec": "https://ucp.dev/handlers/mock-payment",
        "config_schema": "https://ucp.dev/handlers/mock-payment/config.json",
        "instrument_schemas": ["https://ucp.dev/handlers/mock-payment/instrument.json"],
        "config": {"auto_approve": True},
    }]


def _build_totals(checkout: dict) -> list[dict]:
    """Build UCP-compliant totals array from checkout data."""
    totals = []

    subtotal = checkout.get("subtotal", 0)
    if subtotal > 0:
        totals.append({
            "type": "subtotal",
            "display_text": "Subtotal",
            "amount": subtotal,
        })

    # Calculate discount from applied discounts (sequential application)
    # For percentage discounts, calculate new total first then derive discount amount
    running_total = subtotal
    discount_amount = 0
    for discount in checkout.get("discounts", []):
        if discount.get("type") == "percentage":
            # Calculate new total first, then derive discount amount to avoid rounding errors
            new_running_total = int(running_total * (100 - discount.get("value", 0)) / 100)
            disc = running_total - new_running_total
            discount_amount += disc
            running_total = new_running_total
        else:
            disc = discount.get("value", 0)
            discount_amount += disc
            running_total = max(0, running_total - disc)

    if discount_amount > 0:
        totals.append({
            "type": "discount",
            "display_text": "Discount",
            "amount": discount_amount,
        })

    # Fulfillment/shipping
    fulfillment_price = checkout.get("fulfillment_price", 0)
    if fulfillment_price > 0:
        totals.append({
            "type": "fulfillment",
            "display_text": "Shipping",
            "amount": fulfillment_price,
        })

    # Total
    total = checkout.get("total", 0)
    totals.append({
        "type": "total",
        "display_text": "Total",
        "amount": max(0, total),
    })

    return totals


def _build_discounts(checkout: dict) -> dict:
    """Build UCP-compliant discounts object with applied discounts."""
    discounts_list = checkout.get("discounts", [])
    if not discounts_list:
        return None

    subtotal = checkout.get("subtotal", 0)
    running_total = subtotal
    applied = []
    codes = []

    for discount in discounts_list:
        code = discount.get("code", "")
        discount_type = discount.get("type", "percentage")
        value = discount.get("value", 0)

        if code:
            codes.append(code)

        # Calculate the actual discount amount (sequential application)
        # For percentage discounts, calculate new total first then derive discount amount
        if discount_type == "percentage":
            new_running_total = int(running_total * (100 - value) / 100)
            amount = running_total - new_running_total
            title = f"{value}% Off"
            running_total = new_running_total
        else:
            amount = value
            title = f"${value / 100:.2f} Off"
            running_total = max(0, running_total - amount)

        applied.append({
            "code": code,
            "title": title,
            "amount": amount,
        })

    return {
        "codes": codes,
        "applied": applied,
    }


def _build_line_items(raw_items: list) -> list[dict]:
    """Build UCP-compliant line items from database items."""
    line_items = []
    for item in raw_items:
        price = item.get("price", 0)
        quantity = item.get("quantity", 1)
        line_total = price * quantity

        line_items.append({
            "id": item.get("id"),
            "item": {
                "id": item.get("product_id"),
                "title": item.get("title", "Unknown Item"),
                "price": price,
            },
            "quantity": quantity,
            "totals": [
                {
                    "type": "subtotal",
                    "display_text": "Subtotal",
                    "amount": line_total,
                },
                {
                    "type": "total",
                    "display_text": "Total",
                    "amount": line_total,
                },
            ],
        })
    return line_items


def _build_links(base_url: str = "") -> list[dict]:
    """Build required legal links."""
    return [
        {
            "type": "privacy_policy",
            "url": f"{base_url}/legal/privacy" if base_url else "https://example.com/privacy",
            "title": "Privacy Policy",
        },
        {
            "type": "terms_of_service",
            "url": f"{base_url}/legal/terms" if base_url else "https://example.com/terms",
            "title": "Terms of Service",
        },
    ]


def _build_fulfillment(checkout: dict) -> dict:
    """Build UCP-compliant fulfillment structure with all required fields.

    Dynamically calculates fulfillment options based on the selected destination's
    country code. This matches the reference implementation behavior.
    """
    from server.services.fulfillment_service import FulfillmentService

    fulfillment_data = checkout.get("_fulfillment_data", {})
    line_items = checkout.get("line_items", [])
    line_item_ids = [li.get("id", str(i)) for i, li in enumerate(line_items)]

    # Get product IDs for free shipping eligibility check
    product_ids = [li.get("product_id", li.get("item", {}).get("id", "")) for li in line_items]

    # Get subtotal for free shipping threshold
    subtotal = checkout.get("subtotal", 0)

    # Default method structure (empty until destination selected)
    default_method = {
        "id": "shipping_method_0",
        "type": "shipping",
        "line_item_ids": line_item_ids,
        "destinations": [],
        "groups": [],
    }

    # If we have fulfillment data stored, use and enhance it
    if fulfillment_data and fulfillment_data.get("methods"):
        fulfillment_service = FulfillmentService()

        for i, method in enumerate(fulfillment_data.get("methods", [])):
            # Ensure method has required fields
            if "id" not in method:
                method["id"] = f"shipping_method_{i}"
            if "type" not in method:
                method["type"] = "shipping"
            if "line_item_ids" not in method:
                method["line_item_ids"] = line_item_ids

            # Check if destination is selected - if so, calculate options
            selected_dest_id = method.get("selected_destination_id")
            destinations = method.get("destinations", [])

            if selected_dest_id and destinations:
                # Find selected destination
                selected_dest = next(
                    (d for d in destinations if d.get("id") == selected_dest_id),
                    None
                )

                if selected_dest:
                    # Get country code from destination
                    country_code = selected_dest.get("address_country", "US")

                    # Calculate options based on country with free shipping check
                    options = fulfillment_service.calculate_options_for_country(
                        country_code, product_ids, subtotal
                    )

                    # Generate or update groups with options
                    if not method.get("groups"):
                        # Create new group with calculated options
                        method["groups"] = [{
                            "id": f"group_{i}_0",
                            "line_item_ids": method.get("line_item_ids", line_item_ids),
                            "options": options,
                            "selected_option_id": None,
                        }]
                    else:
                        # Update existing groups with new options
                        for j, group in enumerate(method["groups"]):
                            if "id" not in group:
                                group["id"] = f"group_{i}_{j}"
                            if "line_item_ids" not in group:
                                group["line_item_ids"] = method.get("line_item_ids", line_item_ids)
                            # Refresh options based on current destination
                            group["options"] = options

        return fulfillment_data

    return {"methods": [default_method]}


def _format_checkout_response(checkout: dict, base_url: str = "") -> dict:
    """Transform internal checkout to UCP-compliant response format."""
    if not checkout:
        return checkout

    handlers = _get_payment_handlers()

    # Map internal status to UCP status
    internal_status = checkout.get("status", "incomplete")
    ucp_status = STATUS_MAP.get(internal_status, "incomplete")

    # Build line items in UCP format
    raw_items = checkout.get("line_items", [])
    line_items = _build_line_items(raw_items)

    # Build totals
    totals = _build_totals(checkout)

    # Build UCP response
    response = {
        "id": checkout.get("id"),
        "status": ucp_status,
        "currency": checkout.get("currency", "USD"),
        "line_items": line_items,
        "totals": totals,
        "links": _build_links(base_url),
        "fulfillment": _build_fulfillment(checkout),
        "ucp": {
            "version": UCP_VERSION,
            "capabilities": [
                {"name": "dev.ucp.shopping.checkout", "version": UCP_VERSION}
            ],
        },
        "payment": {
            "handlers": handlers,
            "instruments": [],  # ALWAYS empty array, NEVER None - required for idempotency test
            "selected_instrument_id": checkout.get("payment_instrument_id"),
        },
    }

    # Add optional buyer info if present (prefer full buyer object over just id)
    buyer = checkout.get("_buyer")
    if buyer:
        response["buyer"] = buyer
    elif checkout.get("buyer_id"):
        response["buyer"] = {"id": checkout["buyer_id"]}

    # Add timestamps if present
    if checkout.get("created_at"):
        response["created_at"] = checkout["created_at"]
    if checkout.get("updated_at"):
        response["updated_at"] = checkout["updated_at"]

    # Add discounts field if any discounts are applied
    discounts = _build_discounts(checkout)
    if discounts:
        response["discounts"] = discounts

    return response


class ItemRequest(BaseModel):
    """Item details in line item."""
    id: str
    title: Optional[str] = None
    unit_price: Optional[int] = None


class LineItemRequest(BaseModel):
    """Line item in checkout request."""
    item: ItemRequest
    quantity: int = 1


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout - supports UCP checkout creation format."""
    currency: Optional[str] = "USD"
    buyer: Optional[dict] = None
    line_items: Optional[list[LineItemRequest]] = None
    payment: Optional[dict] = None
    fulfillment: Optional[dict] = None

    class Config:
        extra = "allow"  # Allow additional fields


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


class SetPaymentRequest(BaseModel):
    """Request to set payment on checkout."""
    handler_id: str
    instrument: Optional[dict] = None


@router.post("/checkout-sessions", status_code=201)
async def create_checkout(request: CreateCheckoutRequest, req: Request):
    """Create a new checkout session with optional line items."""
    # Check idempotency
    idem_key = req.headers.get("Idempotency-Key")
    request_data = request.model_dump(mode="json", exclude_none=True)
    is_conflict, cached = _check_idempotency(idem_key, request_data)
    if is_conflict:
        raise HTTPException(status_code=409, detail="Conflict: Different request with same idempotency key")
    if cached:
        return cached[0]

    buyer = request.buyer
    try:
        checkout = checkout_service.create_checkout(
            buyer=buyer,
            currency=request.currency,
            line_items=request.line_items,
            payment=request.payment,
            fulfillment=request.fulfillment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    base_url = str(req.base_url).rstrip("/")
    response = _format_checkout_response(checkout, base_url)
    _store_idempotency(idem_key, request_data, response, 201)
    return response


@router.get("/checkout-sessions/{checkout_id}")
async def get_checkout(checkout_id: str, req: Request):
    """Get checkout by ID."""
    checkout = checkout_service.get_checkout(checkout_id)
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    base_url = str(req.base_url).rstrip("/")
    return _format_checkout_response(checkout, base_url)


@router.put("/checkout-sessions/{checkout_id}")
async def update_checkout(checkout_id: str, request: dict, req: Request):
    """Update checkout session (general update endpoint)."""
    # Check idempotency
    idem_key = req.headers.get("Idempotency-Key")
    request_data = {"checkout_id": checkout_id, **request}
    is_conflict, cached = _check_idempotency(idem_key, request_data)
    if is_conflict:
        raise HTTPException(status_code=409, detail="Conflict: Different request with same idempotency key")
    if cached:
        return cached[0]

    try:
        checkout = checkout_service.update_checkout(checkout_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    base_url = str(req.base_url).rstrip("/")
    response = _format_checkout_response(checkout, base_url)
    _store_idempotency(idem_key, request_data, response, 200)
    return response


@router.post("/checkout-sessions/{checkout_id}/line-items")
async def add_line_item(checkout_id: str, request: AddLineItemRequest, req: Request):
    """Add a line item to checkout."""
    checkout = checkout_service.add_line_item(
        checkout_id,
        request.product_id,
        request.variant_id,
        request.quantity
    )
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    base_url = str(req.base_url).rstrip("/")
    return _format_checkout_response(checkout, base_url)


@router.patch("/checkout-sessions/{checkout_id}/line-items/{line_item_id}")
async def update_line_item(checkout_id: str, line_item_id: str, request: UpdateLineItemRequest, req: Request):
    """Update a line item quantity."""
    checkout = checkout_service.update_line_item(checkout_id, line_item_id, request.quantity)
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout or line item not found")
    base_url = str(req.base_url).rstrip("/")
    return _format_checkout_response(checkout, base_url)


@router.delete("/checkout-sessions/{checkout_id}/line-items/{line_item_id}")
async def remove_line_item(checkout_id: str, line_item_id: str, req: Request):
    """Remove a line item from checkout."""
    checkout = checkout_service.remove_line_item(checkout_id, line_item_id)
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout or line item not found")
    base_url = str(req.base_url).rstrip("/")
    return _format_checkout_response(checkout, base_url)


@router.post("/checkout-sessions/{checkout_id}/discounts")
async def apply_discount(checkout_id: str, request: ApplyDiscountRequest, req: Request):
    """Apply a discount code to checkout."""
    checkout = checkout_service.apply_discount(checkout_id, request.code)
    if not checkout:
        raise HTTPException(status_code=400, detail="Invalid discount code")
    base_url = str(req.base_url).rstrip("/")
    return _format_checkout_response(checkout, base_url)


@router.post("/checkout-sessions/{checkout_id}/fulfillment")
async def set_fulfillment(checkout_id: str, request: SetFulfillmentRequest, req: Request):
    """Set fulfillment method on checkout."""
    checkout = checkout_service.set_fulfillment(checkout_id, request.method_id, request.address)
    if not checkout:
        raise HTTPException(status_code=400, detail="Invalid fulfillment method")
    base_url = str(req.base_url).rstrip("/")
    return _format_checkout_response(checkout, base_url)


@router.post("/checkout-sessions/{checkout_id}/payment")
async def set_payment(checkout_id: str, request: SetPaymentRequest, req: Request):
    """Set payment handler and instrument on checkout."""
    checkout = checkout_service.set_payment(checkout_id, request.handler_id, request.instrument)
    if not checkout:
        raise HTTPException(status_code=400, detail="Invalid payment configuration")
    base_url = str(req.base_url).rstrip("/")
    return _format_checkout_response(checkout, base_url)


@router.post("/checkout-sessions/{checkout_id}/complete")
async def complete_checkout(checkout_id: str, req: Request):
    """Complete checkout and create order."""
    # Parse optional body for payment info
    try:
        body = await req.json()
    except:
        body = None

    # Check idempotency
    idem_key = req.headers.get("Idempotency-Key")
    request_data = {"checkout_id": checkout_id, "body": body}
    is_conflict, cached = _check_idempotency(idem_key, request_data)
    if is_conflict:
        raise HTTPException(status_code=409, detail="Conflict: Different request with same idempotency key")
    if cached:
        return cached[0]

    try:
        result = checkout_service.complete_checkout(checkout_id, body)
    except PaymentFailureError:
        raise HTTPException(status_code=402, detail="Payment failed")
    except FulfillmentRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=400, detail="Cannot complete checkout")
    base_url = str(req.base_url).rstrip("/")
    # Return the completed checkout in UCP format with order
    checkout = checkout_service.get_checkout(checkout_id)
    response = _format_checkout_response(checkout, base_url)
    # Add order object from completion result
    if result.get("order_id"):
        order_id = result["order_id"]
        response["order"] = {
            "id": order_id,
            "status": result.get("status", "confirmed"),
            "permalink_url": f"{base_url}/orders/{order_id}",
        }

        # Send order_placed webhook - get URL from agent profile via UCP-Agent header
        ucp_agent_header = req.headers.get("UCP-Agent", "")
        if ucp_agent_header:
            from server.services.webhook_service import get_webhook_service
            from server.db import query_one as db_query_one
            import asyncio

            async def send_order_placed_webhook():
                webhook_service = get_webhook_service()
                # Fetch webhook URL from agent profile
                webhook_url = await webhook_service.get_webhook_url_from_ucp_agent(ucp_agent_header)
                if not webhook_url:
                    return

                # Get full order data for webhook
                order = db_query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
                if order:
                    order_response = {
                        "id": order_id,
                        "checkout_id": checkout_id,
                        "status": result.get("status", "confirmed"),
                        "fulfillment": {"expectations": [], "events": []},
                    }
                    # Parse fulfillment data
                    if order.get("fulfillment_data"):
                        try:
                            order_response["fulfillment"] = json.loads(order["fulfillment_data"])
                        except json.JSONDecodeError:
                            pass
                    # Send webhook
                    await webhook_service.send_webhook(
                        webhook_url,
                        "order_placed",
                        order_response,
                        checkout_id
                    )

            # Send webhook asynchronously
            asyncio.create_task(send_order_placed_webhook())

    _store_idempotency(idem_key, request_data, response, 200)
    return response


@router.post("/checkout-sessions/{checkout_id}/cancel")
async def cancel_checkout(checkout_id: str, req: Request):
    """Cancel an active checkout."""
    # Check idempotency
    idem_key = req.headers.get("Idempotency-Key")
    request_data = {"checkout_id": checkout_id, "action": "cancel"}
    is_conflict, cached = _check_idempotency(idem_key, request_data)
    if is_conflict:
        raise HTTPException(status_code=409, detail="Conflict: Different request with same idempotency key")
    if cached:
        return cached[0]

    checkout = checkout_service.cancel_checkout(checkout_id)
    if not checkout:
        raise HTTPException(status_code=400, detail="Cannot cancel checkout")
    base_url = str(req.base_url).rstrip("/")
    response = _format_checkout_response(checkout, base_url)
    _store_idempotency(idem_key, request_data, response, 200)
    return response
'''

    def _render_order_routes(self) -> str:
        """Render order routes."""
        return '''"""Order routes for UCP shopping."""

from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import json
from datetime import datetime, timezone

from server.db import query_db, query_one, execute_db


router = APIRouter()


def _format_order_response(order: dict, base_url: str = "") -> dict:
    """Transform internal order to UCP-compliant Order response format.

    Required fields per Order schema:
    - ucp: ResponseOrder (version, capabilities)
    - id: order ID
    - checkout_id: associated checkout ID
    - permalink_url: URL to order on merchant site
    - line_items: list of OrderLineItem
    - fulfillment: expectations and events
    - totals: list of TotalResponse
    """
    order_id = order.get("id", "")
    checkout_id = order.get("checkout_id", "")

    # Get line items from database
    db_items = query_db("SELECT * FROM order_line_items WHERE order_id = ?", (order_id,))

    # Build OrderLineItem format
    line_items = []
    for li in db_items:
        quantity_total = li.get("quantity", 1)
        unit_price = li.get("price", 0)
        line_total = unit_price * quantity_total

        line_items.append({
            "id": li.get("id", ""),
            "item": {
                "id": li.get("product_id", ""),
                "title": li.get("title", ""),
                "price": unit_price,
            },
            "quantity": {
                "total": quantity_total,
                "fulfilled": 0,  # Initially nothing fulfilled
            },
            "totals": [
                {"type": "subtotal", "amount": line_total},
                {"type": "total", "amount": line_total},
            ],
            "status": "processing",  # Default status
        })

    # Build totals
    subtotal = order.get("subtotal", 0)
    total = order.get("total", 0)
    fulfillment_cost = total - subtotal if total > subtotal else 0

    totals = [
        {"type": "subtotal", "amount": subtotal},
    ]
    if fulfillment_cost > 0:
        totals.append({"type": "fulfillment", "amount": fulfillment_cost})
    totals.append({"type": "total", "amount": total})

    # Build fulfillment with expectations and events
    fulfillment = {
        "expectations": [],
        "events": [],
    }

    # Parse stored fulfillment_data for expectations
    fulfillment_data_str = order.get("fulfillment_data")
    if fulfillment_data_str:
        try:
            fulfillment_data = json.loads(fulfillment_data_str)
            expectations = fulfillment_data.get("expectations", [])
            events = fulfillment_data.get("events", [])

            if expectations:
                fulfillment["expectations"] = expectations
            if events:
                fulfillment["events"] = events
        except json.JSONDecodeError:
            pass

    # Fallback: create basic expectation if we have fulfillment_method but no stored expectations
    # Note: This fallback may not have all required fields, but stored expectations should
    if not fulfillment["expectations"] and order.get("fulfillment_method") and line_items:
        fulfillment["expectations"] = [{
            "id": "exp_1",
            "line_items": [
                {"id": li["id"], "quantity": li["quantity"]["total"]}
                for li in line_items
            ],
            "method_type": "shipping",
            "destination": {
                "street_address": "",
                "address_locality": "",
                "address_region": "",
                "postal_code": "",
                "address_country": "US",
            },
        }]

    # Build response
    response = {
        "ucp": {
            "version": "2026-01-11",
            "capabilities": [
                {
                    "name": "dev.ucp.shopping.order",
                    "version": "2026-01-11",
                }
            ],
        },
        "id": order_id,
        "checkout_id": checkout_id,
        "permalink_url": f"{base_url}/orders/{order_id}",
        "line_items": line_items,
        "fulfillment": fulfillment,
        "totals": totals,
    }

    # Add adjustments if present
    adjustments_str = order.get("adjustments")
    if adjustments_str:
        try:
            adjustments = json.loads(adjustments_str)
            if adjustments:
                response["adjustments"] = adjustments
        except json.JSONDecodeError:
            pass

    return response


@router.get("/{order_id}")
async def get_order(order_id: str, request: Request):
    """Get order by ID."""
    order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Determine base URL from request
    base_url = str(request.base_url).rstrip("/")

    return _format_order_response(order, base_url)


@router.put("/{order_id}")
async def update_order(order_id: str, updates: dict, request: Request):
    """Update an existing order.

    Supports updating:
    - fulfillment.events (e.g., shipment tracking)
    - adjustments (e.g., refunds)
    """
    order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    set_clauses = []
    values = []

    # Handle fulfillment updates (events)
    if "fulfillment" in updates:
        fulfillment_update = updates["fulfillment"]

        # Load existing fulfillment data
        existing_data = {}
        if order.get("fulfillment_data"):
            try:
                existing_data = json.loads(order["fulfillment_data"])
            except json.JSONDecodeError:
                pass

        # Merge events
        if "events" in fulfillment_update:
            existing_data["events"] = fulfillment_update["events"]

        # Preserve expectations from updates if provided
        if "expectations" in fulfillment_update:
            existing_data["expectations"] = fulfillment_update["expectations"]

        set_clauses.append("fulfillment_data = ?")
        values.append(json.dumps(existing_data))

    # Handle adjustments updates
    if "adjustments" in updates:
        set_clauses.append("adjustments = ?")
        values.append(json.dumps(updates["adjustments"]))

    # Handle status updates
    if "status" in updates:
        set_clauses.append("status = ?")
        values.append(updates["status"])

    if set_clauses:
        set_clauses.append("updated_at = ?")
        values.append(datetime.now(timezone.utc).isoformat())
        values.append(order_id)

        execute_db(
            f"UPDATE orders SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(values)
        )

    # Return updated order
    updated_order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    base_url = str(request.base_url).rstrip("/")
    return _format_order_response(updated_order, base_url)


@router.get("")
async def list_orders(request: Request, buyer_id: Optional[str] = None, limit: int = 20, offset: int = 0):
    """List orders, optionally filtered by buyer."""
    base_url = str(request.base_url).rstrip("/")

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

    formatted_orders = [_format_order_response(o, base_url) for o in orders]
    return {"orders": formatted_orders, "total": len(formatted_orders)}


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, request: Request):
    """Cancel an order."""
    order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] not in ["pending", "confirmed"]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    execute_db("UPDATE orders SET status = 'canceled' WHERE id = ?", (order_id,))

    base_url = str(request.base_url).rstrip("/")
    order["status"] = "canceled"
    return _format_order_response(order, base_url)
'''

    def _render_checkout_service(self) -> str:
        """Render checkout service."""
        return '''"""Checkout service for managing checkout sessions."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any

from server.db import query_db, query_one, execute_db


class PaymentFailureError(Exception):
    """Raised when payment processing fails."""
    pass


class FulfillmentRequiredError(Exception):
    """Raised when fulfillment details are missing."""
    pass


class CheckoutService:
    """Service for managing checkout sessions."""

    def create_checkout(self, buyer: Optional[dict] = None, currency: str = "USD",
                        line_items: Optional[list] = None, payment: Optional[dict] = None,
                        fulfillment: Optional[dict] = None) -> dict:
        """Create a new checkout session with optional line items.

        Raises:
            ValueError: If product not found or insufficient stock.
        """
        import json as json_lib
        checkout_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Validate line items before creating checkout
        if line_items:
            for li in line_items:
                item = li.item if hasattr(li, 'item') else li.get('item', {})
                item_id = item.id if hasattr(item, 'id') else item.get('id')
                quantity = li.quantity if hasattr(li, 'quantity') else li.get('quantity', 1)

                # Check product exists
                product = query_one("SELECT * FROM products WHERE id = ?", (item_id,))
                if not product:
                    raise ValueError(f"Product not found: {item_id}")

                # Check inventory
                inventory = query_one("SELECT * FROM inventory WHERE product_id = ?", (item_id,))
                available = inventory["quantity"] if inventory else 0
                if available < quantity:
                    raise ValueError(f"Insufficient stock for {item_id}: requested {quantity}, available {available}")

        # Extract buyer_id and store full buyer data
        buyer_id = buyer.get("id") if buyer else None
        buyer_json = json_lib.dumps(buyer) if buyer else None

        # Store fulfillment data if provided
        fulfillment_json = json_lib.dumps(fulfillment) if fulfillment else None

        execute_db(
            """INSERT INTO checkouts (id, buyer_id, status, subtotal, total, currency, fulfillment_data, buyer_data, created_at, updated_at)
               VALUES (?, ?, 'incomplete', 0, 0, ?, ?, ?, ?, ?)""",
            (checkout_id, buyer_id, currency, fulfillment_json, buyer_json, now, now)
        )

        # Add line items if provided (already validated above)
        if line_items:
            for li in line_items:
                item = li.item if hasattr(li, 'item') else li.get('item', {})
                item_id = item.id if hasattr(item, 'id') else item.get('id', str(uuid.uuid4()))
                quantity = li.quantity if hasattr(li, 'quantity') else li.get('quantity', 1)

                # Look up product from database to get authoritative price/title
                product = query_one("SELECT * FROM products WHERE id = ?", (item_id,))
                title = product["title"]
                price = product["price"]

                line_item_id = str(uuid.uuid4())
                execute_db(
                    """INSERT INTO checkout_line_items (id, checkout_id, product_id, title, price, quantity)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (line_item_id, checkout_id, item_id, title, price or 0, quantity)
                )

        self._recalculate_totals(checkout_id)
        return self.get_checkout(checkout_id)

    def get_checkout(self, checkout_id: str) -> Optional[dict]:
        """Get a checkout by ID."""
        import json as json_lib
        checkout = query_one("SELECT * FROM checkouts WHERE id = ?", (checkout_id,))
        if not checkout:
            return None

        # Get line items
        items = query_db("SELECT * FROM checkout_line_items WHERE checkout_id = ?", (checkout_id,))
        checkout["line_items"] = items

        # Get applied discounts
        discounts = query_db("SELECT * FROM checkout_discounts WHERE checkout_id = ?", (checkout_id,))
        checkout["discounts"] = discounts

        # Parse fulfillment data if present
        if checkout.get("fulfillment_data"):
            try:
                checkout["_fulfillment_data"] = json_lib.loads(checkout["fulfillment_data"])
            except json_lib.JSONDecodeError:
                checkout["_fulfillment_data"] = {}

        # Parse buyer data if present
        if checkout.get("buyer_data"):
            try:
                checkout["_buyer"] = json_lib.loads(checkout["buyer_data"])
            except json_lib.JSONDecodeError:
                checkout["_buyer"] = None

        return checkout

    def add_line_item(self, checkout_id: str, product_id: str, variant_id: Optional[str], quantity: int) -> Optional[dict]:
        """Add a line item to checkout."""
        checkout = query_one("SELECT * FROM checkouts WHERE id = ? AND status = 'incomplete'", (checkout_id,))
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

    def complete_checkout(self, checkout_id: str, body: Optional[dict] = None) -> Optional[dict]:
        """Complete checkout and create order.

        Raises:
            FulfillmentRequiredError: If fulfillment destination or option not selected.
            PaymentFailureError: If payment instrument is 'instr_fail'.
        """
        import json as json_lib
        checkout = self.get_checkout(checkout_id)
        if not checkout:
            return None

        # Can only complete from incomplete status
        if checkout["status"] != "incomplete":
            return None

        if not checkout["line_items"]:
            return None

        # Check for payment failure simulation
        if body:
            # Check both possible locations for instrument ID
            payment_data = body.get("payment_data", {})
            instrument_id = payment_data.get("id")
            # Also check nested payment structure
            if not instrument_id:
                payment = body.get("payment", {})
                instrument_id = payment.get("selected_instrument_id")
            if instrument_id == "instr_fail":
                raise PaymentFailureError("Payment processing failed")

        # Validate fulfillment requirements
        fulfillment_data = checkout.get("_fulfillment_data", {})
        has_destination = False
        has_option = False

        if fulfillment_data:
            for method in fulfillment_data.get("methods", []):
                if method.get("selected_destination_id"):
                    has_destination = True
                for group in method.get("groups", []):
                    if group.get("selected_option_id"):
                        has_option = True

        if not (has_destination and has_option):
            raise FulfillmentRequiredError("Fulfillment address and option must be selected")

        # Create order
        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Build fulfillment data for order from checkout fulfillment
        order_fulfillment_data = None
        order_line_item_ids = []
        fulfillment_data = checkout.get("_fulfillment_data", {})
        if fulfillment_data:
            # Build expectations from selected fulfillment option
            expectations = []

            # First, generate order line item IDs
            for i, item in enumerate(checkout["line_items"]):
                order_line_item_ids.append(str(uuid.uuid4()))

            # Find selected option, destination, and method type
            selected_option_title = None
            selected_destination = None
            method_type = "shipping"  # Default

            for method in fulfillment_data.get("methods", []):
                method_type = method.get("type", "shipping")

                # Get selected destination
                selected_dest_id = method.get("selected_destination_id")
                if selected_dest_id and method.get("destinations"):
                    for dest in method["destinations"]:
                        if dest.get("id") == selected_dest_id:
                            selected_destination = {
                                "street_address": dest.get("street_address", ""),
                                "address_locality": dest.get("address_locality", ""),
                                "address_region": dest.get("address_region", ""),
                                "postal_code": dest.get("postal_code", ""),
                                "address_country": dest.get("address_country", "US"),
                            }
                            if dest.get("full_name"):
                                selected_destination["full_name"] = dest["full_name"]
                            break

                # Get selected option title - prefer stored _selected_option_title for exact match
                for group in method.get("groups", []):
                    selected_id = group.get("selected_option_id")
                    if selected_id:
                        # First check for stored title (set during update_checkout)
                        # This captures exact title including "(Free)" suffix
                        if group.get("_selected_option_title"):
                            selected_option_title = group["_selected_option_title"]
                        else:
                            # Look up option in the group options
                            for opt in group.get("options", []):
                                if opt.get("id") == selected_id:
                                    selected_option_title = opt.get("title")
                                    break
                            # If not in group options, try to look up from shipping rates
                            if not selected_option_title:
                                rate = query_one("SELECT * FROM shipping_rates WHERE id = ?", (selected_id,))
                                if rate:
                                    selected_option_title = rate.get("title")

            if order_line_item_ids and selected_destination:
                expectation = {
                    "id": "exp_1",
                    "line_items": [
                        {"id": lid, "quantity": checkout["line_items"][i]["quantity"]}
                        for i, lid in enumerate(order_line_item_ids)
                    ],
                    "method_type": method_type,
                    "destination": selected_destination,
                }
                # Add description from selected option
                if selected_option_title:
                    expectation["description"] = selected_option_title
                expectations.append(expectation)

            order_fulfillment_data = json_lib.dumps({
                "expectations": expectations,
                "events": [],
            })

        execute_db(
            """INSERT INTO orders (id, checkout_id, buyer_id, status, subtotal, total, currency, fulfillment_data, created_at)
               VALUES (?, ?, ?, 'confirmed', ?, ?, ?, ?, ?)""",
            (order_id, checkout_id, checkout["buyer_id"], checkout["subtotal"], checkout["total"], checkout["currency"], order_fulfillment_data, now)
        )

        # Copy line items to order (using pre-generated IDs for consistency with expectations)
        for i, item in enumerate(checkout["line_items"]):
            if order_fulfillment_data and i < len(order_line_item_ids):
                item_id = order_line_item_ids[i]
            else:
                item_id = str(uuid.uuid4())
            execute_db(
                """INSERT INTO order_line_items (id, order_id, product_id, variant_id, title, price, quantity)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (item_id, order_id, item["product_id"], item.get("variant_id"), item["title"], item["price"], item["quantity"])
            )

        # Mark checkout as completed
        execute_db("UPDATE checkouts SET status = 'completed' WHERE id = ?", (checkout_id,))

        return {"order_id": order_id, "checkout_id": checkout_id, "status": "confirmed"}

    def update_checkout(self, checkout_id: str, updates: dict) -> Optional[dict]:
        """Update checkout with arbitrary fields including fulfillment."""
        import json as json_lib
        checkout = query_one("SELECT * FROM checkouts WHERE id = ? AND status = 'incomplete'", (checkout_id,))
        if not checkout:
            return None

        # Handle simple update fields
        allowed_fields = ["currency"]
        set_clauses = []
        values = []
        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field} = ?")
                values.append(updates[field])

        # Handle buyer updates - store full buyer object as JSON
        if "buyer" in updates:
            buyer = updates["buyer"]
            buyer_id = buyer.get("id") if buyer else None
            set_clauses.append("buyer_id = ?")
            values.append(buyer_id)
            set_clauses.append("buyer_data = ?")
            values.append(json_lib.dumps(buyer) if buyer else None)

        # Handle line_items updates (quantity changes)
        if "line_items" in updates:
            for li in updates["line_items"]:
                line_item_id = li.get("id")
                quantity = li.get("quantity")
                if line_item_id and quantity is not None:
                    if quantity <= 0:
                        # Remove the line item
                        execute_db(
                            "DELETE FROM checkout_line_items WHERE id = ? AND checkout_id = ?",
                            (line_item_id, checkout_id)
                        )
                    else:
                        # Validate inventory before updating
                        existing_item = query_one(
                            "SELECT product_id FROM checkout_line_items WHERE id = ? AND checkout_id = ?",
                            (line_item_id, checkout_id)
                        )
                        if existing_item:
                            product_id = existing_item["product_id"]
                            inventory = query_one("SELECT * FROM inventory WHERE product_id = ?", (product_id,))
                            available = inventory["quantity"] if inventory else 0
                            if available < quantity:
                                raise ValueError(f"Insufficient stock for {product_id}: requested {quantity}, available {available}")
                        # Update quantity
                        execute_db(
                            "UPDATE checkout_line_items SET quantity = ? WHERE id = ? AND checkout_id = ?",
                            (quantity, line_item_id, checkout_id)
                        )

        # Handle fulfillment updates - store as JSON and update fulfillment_price
        if "fulfillment" in updates:
            from server.services.fulfillment_service import FulfillmentService
            fulfillment_service = FulfillmentService()

            fulfillment = updates["fulfillment"]
            fulfillment_price = 0

            # Get buyer email from checkout for address lookup
            buyer_data = checkout.get("buyer_data")
            buyer_email = None
            if buyer_data:
                try:
                    buyer = json_lib.loads(buyer_data)
                    buyer_email = buyer.get("email")
                except json_lib.JSONDecodeError:
                    pass

            # Helper to get known customer addresses
            def get_customer_addresses(email):
                if not email:
                    return []
                customer = query_one("SELECT id FROM customers WHERE email = ?", (email,))
                if not customer:
                    return []
                return query_db(
                    "SELECT * FROM customer_addresses WHERE customer_id = ?",
                    (customer["id"],)
                )

            # Helper to match address content (handles both column naming conventions)
            def addresses_match(addr1, addr2):
                # Get values with fallback for different column names
                def get_val(addr, key, alt_key=None):
                    val = addr.get(key) or (addr.get(alt_key) if alt_key else "")
                    return (val or "").lower()

                if get_val(addr1, "street_address") != get_val(addr2, "street_address"):
                    return False
                if get_val(addr1, "postal_code") != get_val(addr2, "postal_code"):
                    return False
                if get_val(addr1, "address_country", "country") != get_val(addr2, "address_country", "country"):
                    return False
                return True

            # Merge with existing fulfillment data if present
            existing_data = checkout.get("fulfillment_data")
            if existing_data:
                try:
                    existing = json_lib.loads(existing_data)
                    # Merge methods
                    if "methods" in fulfillment and "methods" in existing:
                        for new_method in fulfillment["methods"]:
                            # Find existing method by id or type and update
                            found = False
                            for i, existing_method in enumerate(existing["methods"]):
                                if existing_method.get("id") == new_method.get("id") or \
                                   existing_method.get("type") == new_method.get("type"):
                                    # Deep merge: preserve destinations if not in new_method
                                    if "destinations" not in new_method and "destinations" in existing_method:
                                        new_method["destinations"] = existing_method["destinations"]
                                    if "selected_destination_id" not in new_method and "selected_destination_id" in existing_method:
                                        new_method["selected_destination_id"] = existing_method["selected_destination_id"]
                                    existing["methods"][i] = {**existing_method, **new_method}
                                    found = True
                                    break
                            if not found:
                                existing["methods"].append(new_method)
                        fulfillment = existing
                except json_lib.JSONDecodeError:
                    pass

            # Check if client provided destinations in the original update
            client_provided_destinations = False
            for method in updates["fulfillment"].get("methods", []):
                if method.get("destinations"):
                    client_provided_destinations = True
                    break

            # Inject known customer addresses ONLY if buyer is known AND no destinations provided
            stored_addresses = get_customer_addresses(buyer_email)
            if stored_addresses and not client_provided_destinations:
                for method in fulfillment.get("methods", []):
                    existing_dests = method.get("destinations") or []
                    existing_ids = {d.get("id") for d in existing_dests if d.get("id")}

                    # Add stored addresses that aren't already present
                    for addr in stored_addresses:
                        if addr["id"] not in existing_ids:
                            # Handle both column naming conventions (UCP vs CSV)
                            existing_dests.append({
                                "id": addr["id"],
                                "street_address": addr.get("street_address", ""),
                                "address_locality": addr.get("address_locality") or addr.get("city", ""),
                                "address_region": addr.get("address_region") or addr.get("state", ""),
                                "postal_code": addr.get("postal_code", ""),
                                "address_country": addr.get("address_country") or addr.get("country", "US"),
                            })
                    if existing_dests:
                        method["destinations"] = existing_dests

            # Process destinations: match to existing or generate new IDs
            # Also persist new addresses for the customer
            for method in fulfillment.get("methods", []):
                if "destinations" in method:
                    for dest in method["destinations"]:
                        if not dest.get("id"):
                            # Check if matches a stored address
                            matched = False
                            for stored in stored_addresses:
                                if addresses_match(dest, stored):
                                    dest["id"] = stored["id"]
                                    matched = True
                                    break
                            if not matched:
                                # Generate new ID
                                new_id = f"dest_{str(uuid.uuid4())[:8]}"
                                dest["id"] = new_id

                                # Persist new address for buyer if email is known
                                if buyer_email:
                                    # Get or create customer
                                    customer = query_one("SELECT id FROM customers WHERE email = ?", (buyer_email,))
                                    if not customer:
                                        # Create new customer
                                        customer_id = f"cust_{str(uuid.uuid4())[:8]}"
                                        execute_db(
                                            "INSERT INTO customers (id, email) VALUES (?, ?)",
                                            (customer_id, buyer_email)
                                        )
                                    else:
                                        customer_id = customer["id"]

                                    # Save the new address
                                    execute_db(
                                        """INSERT INTO customer_addresses
                                           (id, customer_id, street_address, address_locality, address_region, postal_code, address_country)
                                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                        (new_id, customer_id,
                                         dest.get("street_address", ""),
                                         dest.get("address_locality", ""),
                                         dest.get("address_region", ""),
                                         dest.get("postal_code", ""),
                                         dest.get("address_country", "US"))
                                    )

            # Calculate fulfillment price from selected option and store exact title
            for method in fulfillment.get("methods", []):
                for group in method.get("groups", []):
                    selected_id = group.get("selected_option_id")
                    if selected_id:
                        option_found = False
                        # Find option in group options - capture exact title for order expectations
                        for opt in group.get("options", []):
                            if opt.get("id") == selected_id:
                                # Store the exact title as shown in options (includes "(Free)" suffix if applicable)
                                group["_selected_option_title"] = opt.get("title")
                                option_found = True
                                # Get total from option
                                for total in opt.get("totals", []):
                                    if total.get("type") == "total":
                                        fulfillment_price += total.get("amount", 0)
                                        break
                                break
                        # If options not in group yet, look up from shipping rates
                        if not option_found:
                            rate = query_one("SELECT * FROM shipping_rates WHERE id = ?", (selected_id,))
                            if rate:
                                rate_price = rate.get("price", 0)
                                rate_title = rate.get("title", "")
                                # Apply free shipping logic for standard level
                                if rate.get("service_level") == "standard":
                                    # Get subtotal and product_ids from checkout
                                    subtotal = checkout.get("subtotal", 0)
                                    line_items = query_db(
                                        "SELECT product_id FROM checkout_line_items WHERE checkout_id = ?",
                                        (checkout_id,)
                                    )
                                    product_ids = [li.get("product_id", "") for li in line_items]

                                    # Check promotions for free shipping
                                    is_free_shipping = False
                                    promotions = query_db("SELECT * FROM promotions WHERE active = 1 AND type = 'free_shipping'")
                                    for promo in promotions:
                                        min_subtotal = promo.get("min_subtotal")
                                        if min_subtotal and subtotal >= min_subtotal:
                                            is_free_shipping = True
                                            break
                                        eligible_ids_str = promo.get("eligible_item_ids")
                                        if eligible_ids_str:
                                            try:
                                                eligible_ids = json_lib.loads(eligible_ids_str)
                                                if any(pid in eligible_ids for pid in product_ids):
                                                    is_free_shipping = True
                                                    break
                                            except (json_lib.JSONDecodeError, TypeError):
                                                pass

                                    if is_free_shipping:
                                        rate_price = 0
                                        rate_title = rate_title + " (Free)"

                                fulfillment_price += rate_price
                                # Store the title with potential "(Free)" suffix
                                group["_selected_option_title"] = rate_title

            set_clauses.append("fulfillment_data = ?")
            values.append(json_lib.dumps(fulfillment))
            set_clauses.append("fulfillment_price = ?")
            values.append(fulfillment_price)

        # Handle discount code updates
        if "discounts" in updates:
            discounts_data = updates["discounts"]
            codes = discounts_data.get("codes", [])
            for code in codes:
                # Check discount exists and is active
                discount = query_one("SELECT * FROM discounts WHERE code = ? AND active = 1", (code,))
                if discount:
                    # Add to checkout discounts
                    discount_id = str(uuid.uuid4())
                    execute_db(
                        "INSERT OR REPLACE INTO checkout_discounts (id, checkout_id, code, type, value) VALUES (?, ?, ?, ?, ?)",
                        (discount_id, checkout_id, code, discount["type"], discount["value"])
                    )

        if set_clauses:
            set_clauses.append("updated_at = ?")
            values.append(datetime.now(timezone.utc).isoformat())
            values.append(checkout_id)
            execute_db(
                f"UPDATE checkouts SET {', '.join(set_clauses)} WHERE id = ?",
                tuple(values)
            )

        # Always recalculate totals after any update (handles discounts, line item changes, etc.)
        self._recalculate_totals(checkout_id)

        return self.get_checkout(checkout_id)

    def set_payment(self, checkout_id: str, handler_id: str, instrument: Optional[dict] = None) -> Optional[dict]:
        """Set payment handler and instrument on checkout."""
        import json as json_lib
        checkout = query_one("SELECT * FROM checkouts WHERE id = ? AND status = 'incomplete'", (checkout_id,))
        if not checkout:
            return None

        instrument_json = json_lib.dumps(instrument) if instrument else None
        execute_db(
            "UPDATE checkouts SET payment_handler_id = ?, payment_instrument = ?, updated_at = ? WHERE id = ?",
            (handler_id, instrument_json, datetime.now(timezone.utc).isoformat(), checkout_id)
        )

        return self.get_checkout(checkout_id)

    def cancel_checkout(self, checkout_id: str) -> Optional[dict]:
        """Cancel an active checkout."""
        checkout = query_one("SELECT * FROM checkouts WHERE id = ? AND status = 'incomplete'", (checkout_id,))
        if not checkout:
            return None

        execute_db("UPDATE checkouts SET status = 'canceled', updated_at = ? WHERE id = ?",
                   (datetime.now(timezone.utc).isoformat(), checkout_id))
        return self.get_checkout(checkout_id)

    def _recalculate_totals(self, checkout_id: str):
        """Recalculate checkout totals."""
        checkout = query_one("SELECT * FROM checkouts WHERE id = ?", (checkout_id,))
        if not checkout:
            return

        # Calculate subtotal from line items
        items = query_db("SELECT * FROM checkout_line_items WHERE checkout_id = ?", (checkout_id,))
        subtotal = sum(item["price"] * item["quantity"] for item in items)

        # Apply discounts sequentially (each discount applies to the running total, not original subtotal)
        # For percentage discounts, calculate new total first then derive discount amount
        discounts = query_db("SELECT * FROM checkout_discounts WHERE checkout_id = ?", (checkout_id,))
        running_total = subtotal
        discount_amount = 0
        for discount in discounts:
            if discount["type"] == "percentage":
                # Calculate new total first, then derive discount amount to avoid rounding errors
                new_running_total = int(running_total * (100 - discount["value"]) / 100)
                disc = running_total - new_running_total
                discount_amount += disc
                running_total = new_running_total
            else:
                disc = discount["value"]
                discount_amount += disc
                running_total = max(0, running_total - disc)

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

from server.db import query_db, query_one


class FulfillmentService:
    """Service for fulfillment options and calculations."""

    def get_available_options(self, checkout_id: str = None) -> list:
        """Get available fulfillment options."""
        rates = query_db("SELECT * FROM shipping_rates WHERE active = 1")
        return rates

    def calculate_options_for_country(self, country_code: str, product_ids: list = None, subtotal: int = 0) -> list:
        """Calculate available fulfillment options based on destination country.

        Logic mirrors reference implementation:
        - Fetch rates matching the country or 'default'
        - For each service_level, prefer country-specific rate over default
        - Check promotions for free shipping eligibility
        - Return sorted by price
        """
        import json as json_lib

        if not country_code:
            return []

        product_ids = product_ids or []

        # Check for free shipping promotions
        is_free_shipping = False
        promotions = query_db("SELECT * FROM promotions WHERE active = 1 AND type = 'free_shipping'")
        for promo in promotions:
            # Check threshold-based free shipping
            min_subtotal = promo.get("min_subtotal")
            if min_subtotal and subtotal >= min_subtotal:
                is_free_shipping = True
                break

            # Check product eligibility-based free shipping
            eligible_ids_str = promo.get("eligible_item_ids")
            if eligible_ids_str:
                try:
                    eligible_ids = json_lib.loads(eligible_ids_str)
                    if any(pid in eligible_ids for pid in product_ids):
                        is_free_shipping = True
                        break
                except (json_lib.JSONDecodeError, TypeError):
                    pass

        # Fetch rates for specific country and default
        rates = query_db(
            "SELECT * FROM shipping_rates WHERE active = 1 AND (country_code = ? OR country_code = 'default')",
            (country_code,)
        )

        # Group by service_level, preferring country-specific over default
        rates_by_level = {}
        for rate in rates:
            level = rate.get("service_level", "standard")
            if level not in rates_by_level:
                rates_by_level[level] = rate
            else:
                existing = rates_by_level[level]
                # Prefer specific country over default
                if existing.get("country_code") == "default" and rate.get("country_code") != "default":
                    rates_by_level[level] = rate

        # Build options sorted by price
        sorted_rates = sorted(rates_by_level.values(), key=lambda r: r.get("price", 0))

        options = []
        for rate in sorted_rates:
            price = rate["price"]
            title = rate["title"]

            # Apply free shipping for standard level
            if is_free_shipping and rate.get("service_level") == "standard":
                price = 0
                title = title + " (Free)"

            options.append({
                "id": rate["id"],
                "title": title,
                "totals": [
                    {"type": "subtotal", "amount": price},
                    {"type": "total", "amount": price},
                ],
            })

        return options

    def calculate_shipping(self, method_id: str, subtotal: int) -> int:
        """Calculate shipping cost, applying free shipping threshold if applicable."""
        rate = query_one("SELECT * FROM shipping_rates WHERE id = ?", (method_id,))
        if not rate:
            return 0

        # Check for free shipping threshold from promotions
        promotions = query_db("SELECT * FROM promotions WHERE active = 1 AND type = 'free_shipping'")
        for promo in promotions:
            min_subtotal = promo.get("min_subtotal")
            if min_subtotal and subtotal >= min_subtotal and rate.get("service_level") == "standard":
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

    def _render_webhook_service(self) -> str:
        """Render webhook service for sending UCP events."""
        return '''"""Webhook service for sending UCP events to agent endpoints."""

import re
import httpx
import json
import logging
from typing import Optional
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook events to UCP agents."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self._profile_cache: dict[str, dict] = {}

    async def get_webhook_url_from_ucp_agent(self, ucp_agent_header: str) -> Optional[str]:
        """Extract webhook URL from agent profile referenced in UCP-Agent header.

        The UCP-Agent header contains a profile URL like:
        profile="http://localhost:9000/profiles/shopping-agent.json"

        We fetch that profile and look for the webhook_url in the
        dev.ucp.shopping.order capability config.
        """
        if not ucp_agent_header:
            return None

        # Parse profile URL from header
        profile_match = re.search(r'profile="([^"]+)"', ucp_agent_header)
        if not profile_match:
            logger.debug("No profile URL found in UCP-Agent header")
            return None

        profile_url = profile_match.group(1)

        # Check cache first
        if profile_url in self._profile_cache:
            profile = self._profile_cache[profile_url]
        else:
            # Fetch the agent profile
            try:
                response = await self.client.get(profile_url)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch agent profile from {profile_url}: {response.status_code}")
                    return None
                profile = response.json()
                self._profile_cache[profile_url] = profile
            except Exception as e:
                logger.error(f"Error fetching agent profile from {profile_url}: {e}")
                return None

        # Look for webhook_url in capabilities
        capabilities = profile.get("ucp", {}).get("capabilities", [])
        for cap in capabilities:
            if cap.get("name") == "dev.ucp.shopping.order":
                webhook_url = cap.get("config", {}).get("webhook_url")
                if webhook_url:
                    logger.debug(f"Found webhook URL: {webhook_url}")
                    return webhook_url

        logger.debug("No webhook_url found in agent profile capabilities")
        return None

    async def send_webhook(self, webhook_url: str, event_type: str, order: dict, checkout_id: str):
        """Send a webhook event to the agent.

        Args:
            webhook_url: The URL to POST the webhook to
            event_type: Event type (e.g., 'order_placed', 'order_shipped')
            order: The order data to include in the payload
            checkout_id: The checkout ID associated with this order
        """
        if not webhook_url:
            logger.warning("No webhook URL configured, skipping webhook")
            return

        # Send the payload directly - the webhook server wraps it in {"partner_id": ..., "payload": ...}
        payload = {
            "event_type": event_type,
            "checkout_id": checkout_id,
            "order": order,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            response = await self.client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            logger.info(f"Webhook sent to {webhook_url}: {response.status_code}")
            return response.status_code
        except Exception as e:
            logger.error(f"Failed to send webhook to {webhook_url}: {e}")
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global webhook service instance
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """Get or create the webhook service singleton."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
'''

    def _render_testing_routes(self) -> str:
        """Render testing routes for webhook simulation."""
        return '''"""Testing routes for simulating fulfillment events.

These endpoints are used by conformance tests to trigger webhook events.
"""

import os
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional

from server.db import query_one, execute_db
from server.services.webhook_service import get_webhook_service


router = APIRouter()

# Get simulation secret from environment
SIMULATION_SECRET = os.environ.get("SIMULATION_SECRET", "")


def _validate_simulation_secret(simulation_secret: Optional[str]):
    """Validate the Simulation-Secret header."""
    if not SIMULATION_SECRET:
        # If no secret configured, skip validation
        return

    if not simulation_secret or simulation_secret != SIMULATION_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing Simulation-Secret header"
        )


def _get_order_response(order: dict, base_url: str = "") -> dict:
    """Format order for webhook response."""
    order_id = order.get("id", "")
    checkout_id = order.get("checkout_id", "")

    # Parse fulfillment data
    fulfillment = {"expectations": [], "events": []}
    fulfillment_data_str = order.get("fulfillment_data")
    if fulfillment_data_str:
        try:
            fulfillment = json.loads(fulfillment_data_str)
        except json.JSONDecodeError:
            pass

    return {
        "id": order_id,
        "checkout_id": checkout_id,
        "status": order.get("status", "confirmed"),
        "fulfillment": fulfillment,
    }


@router.post("/simulate-shipping/{order_id}")
async def simulate_shipping(
    order_id: str,
    request: Request,
    simulation_secret: Optional[str] = Header(None, alias="Simulation-Secret")
):
    """Simulate shipping an order - triggers order_shipped webhook.

    Requires Simulation-Secret header if SIMULATION_SECRET env var is set.
    """
    # Validate simulation secret
    _validate_simulation_secret(simulation_secret)

    # Get the order
    order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Load existing fulfillment data
    fulfillment_data = {}
    if order.get("fulfillment_data"):
        try:
            fulfillment_data = json.loads(order["fulfillment_data"])
        except json.JSONDecodeError:
            fulfillment_data = {"expectations": [], "events": []}

    # Add shipped event
    shipped_event = {
        "id": f"event_{order_id}_shipped",
        "type": "shipped",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tracking": {
            "carrier": "Mock Carrier",
            "tracking_number": f"MOCK{order_id[:8].upper()}",
            "tracking_url": f"https://example.com/track/MOCK{order_id[:8].upper()}",
        }
    }

    if "events" not in fulfillment_data:
        fulfillment_data["events"] = []
    fulfillment_data["events"].append(shipped_event)

    # Update order with new fulfillment data and status
    execute_db(
        "UPDATE orders SET fulfillment_data = ?, status = 'shipped', updated_at = ? WHERE id = ?",
        (json.dumps(fulfillment_data), datetime.now(timezone.utc).isoformat(), order_id)
    )

    # Get updated order
    updated_order = query_one("SELECT * FROM orders WHERE id = ?", (order_id,))

    # Send webhook - get URL from agent profile via UCP-Agent header
    ucp_agent_header = request.headers.get("UCP-Agent", "")
    webhook_service = get_webhook_service()

    webhook_url = await webhook_service.get_webhook_url_from_ucp_agent(ucp_agent_header)

    if webhook_url:
        base_url = str(request.base_url).rstrip("/")
        order_response = _get_order_response(updated_order, base_url)
        await webhook_service.send_webhook(
            webhook_url,
            "order_shipped",
            order_response,
            updated_order.get("checkout_id", "")
        )

    return {
        "success": True,
        "order_id": order_id,
        "status": "shipped",
        "event": shipped_event,
    }
'''

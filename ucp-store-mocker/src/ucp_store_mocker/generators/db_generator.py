"""Database schema and initialization generator."""

from typing import Any

from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.capabilities.registry import CapabilityRegistry


class DatabaseGenerator:
    """Generate database schema and import scripts."""

    def __init__(self, config: StoreConfig):
        self.config = config
        self.registry = CapabilityRegistry()

    def generate_init_sql(self) -> str:
        """Generate SQL initialization script."""
        tables = []

        # Core tables
        tables.append(self._products_table())
        tables.append(self._inventory_table())
        tables.append(self._checkouts_table())
        tables.append(self._checkout_line_items_table())
        tables.append(self._checkout_discounts_table())

        if self.config.capabilities.discount.enabled:
            tables.append(self._discounts_table())

        if self.config.capabilities.fulfillment.enabled:
            tables.append(self._shipping_rates_table())
            tables.append(self._customers_table())
            tables.append(self._customer_addresses_table())
            tables.append(self._promotions_table())

        if self.config.capabilities.order.enabled:
            tables.append(self._orders_table())
            tables.append(self._order_line_items_table())

        # Extended capability tables
        if self.config.capabilities.wishlist and self.config.capabilities.wishlist.enabled:
            tables.extend(self._wishlist_tables())

        if self.config.capabilities.reviews and self.config.capabilities.reviews.enabled:
            tables.append(self._reviews_table())

        if self.config.capabilities.loyalty and self.config.capabilities.loyalty.enabled:
            tables.extend(self._loyalty_tables())

        if self.config.capabilities.gift_cards and self.config.capabilities.gift_cards.enabled:
            tables.extend(self._gift_cards_tables())

        if self.config.capabilities.subscriptions and self.config.capabilities.subscriptions.enabled:
            tables.extend(self._subscriptions_tables())

        if self.config.capabilities.returns and self.config.capabilities.returns.enabled:
            tables.extend(self._returns_tables())

        return "\n\n".join(tables)

    def _products_table(self) -> str:
        """Generate products table."""
        return """-- Products table
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    price INTEGER NOT NULL,
    currency TEXT DEFAULT 'USD',
    image_url TEXT,
    sku TEXT,
    parent_id TEXT,
    variations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_parent_id ON products(parent_id);"""

    def _inventory_table(self) -> str:
        """Generate inventory table."""
        return """-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    product_id TEXT PRIMARY KEY,
    quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);"""

    def _checkouts_table(self) -> str:
        """Generate checkouts table."""
        return """-- Checkouts table
CREATE TABLE IF NOT EXISTS checkouts (
    id TEXT PRIMARY KEY,
    buyer_id TEXT,
    buyer_data TEXT,
    status TEXT DEFAULT 'incomplete',
    subtotal INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    fulfillment_method TEXT,
    fulfillment_price INTEGER DEFAULT 0,
    fulfillment_address TEXT,
    payment_handler_id TEXT,
    payment_instrument TEXT,
    fulfillment_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_checkouts_buyer_id ON checkouts(buyer_id);
CREATE INDEX IF NOT EXISTS idx_checkouts_status ON checkouts(status);"""

    def _checkout_line_items_table(self) -> str:
        """Generate checkout line items table."""
        return """-- Checkout Line Items table
CREATE TABLE IF NOT EXISTS checkout_line_items (
    id TEXT PRIMARY KEY,
    checkout_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    variant_id TEXT,
    title TEXT NOT NULL,
    price INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY (checkout_id) REFERENCES checkouts(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_checkout_items_checkout ON checkout_line_items(checkout_id);"""

    def _checkout_discounts_table(self) -> str:
        """Generate checkout discounts table."""
        return """-- Checkout Discounts table
CREATE TABLE IF NOT EXISTS checkout_discounts (
    id TEXT PRIMARY KEY,
    checkout_id TEXT NOT NULL,
    code TEXT NOT NULL,
    type TEXT NOT NULL,
    value INTEGER NOT NULL,
    FOREIGN KEY (checkout_id) REFERENCES checkouts(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_checkout_discounts_unique ON checkout_discounts(checkout_id, code);"""

    def _discounts_table(self) -> str:
        """Generate discounts table."""
        return """-- Discounts table
CREATE TABLE IF NOT EXISTS discounts (
    code TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    value INTEGER NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT 1,
    min_purchase INTEGER DEFAULT 0,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    expires_at TIMESTAMP
);"""

    def _shipping_rates_table(self) -> str:
        """Generate shipping rates table."""
        return """-- Shipping Rates table
CREATE TABLE IF NOT EXISTS shipping_rates (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT DEFAULT 'shipping',
    price INTEGER NOT NULL,
    country_code TEXT DEFAULT 'default',
    service_level TEXT DEFAULT 'standard',
    delivery_days_min INTEGER DEFAULT 0,
    delivery_days_max INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_shipping_rates_country ON shipping_rates(country_code);"""

    def _promotions_table(self) -> str:
        """Generate promotions table for free shipping rules."""
        return """-- Promotions table
CREATE TABLE IF NOT EXISTS promotions (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    min_subtotal INTEGER,
    eligible_item_ids TEXT,
    description TEXT,
    active BOOLEAN DEFAULT 1
);"""

    def _customers_table(self) -> str:
        """Generate customers table for known customer lookup."""
        return """-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);"""

    def _customer_addresses_table(self) -> str:
        """Generate customer addresses table for address injection."""
        return """-- Customer Addresses table
CREATE TABLE IF NOT EXISTS customer_addresses (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    street_address TEXT,
    address_locality TEXT,
    city TEXT,
    address_region TEXT,
    state TEXT,
    postal_code TEXT,
    address_country TEXT DEFAULT 'US',
    country TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE INDEX IF NOT EXISTS idx_customer_addresses_customer ON customer_addresses(customer_id);"""

    def _orders_table(self) -> str:
        """Generate orders table."""
        return """-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    checkout_id TEXT,
    buyer_id TEXT,
    status TEXT DEFAULT 'pending',
    subtotal INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    fulfillment_method TEXT,
    fulfillment_status TEXT DEFAULT 'pending',
    fulfillment_data TEXT,
    adjustments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (checkout_id) REFERENCES checkouts(id)
);

CREATE INDEX IF NOT EXISTS idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);"""

    def _order_line_items_table(self) -> str:
        """Generate order line items table."""
        return """-- Order Line Items table
CREATE TABLE IF NOT EXISTS order_line_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    variant_id TEXT,
    title TEXT NOT NULL,
    price INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_line_items(order_id);"""

    def _wishlist_tables(self) -> list[str]:
        """Generate wishlist tables."""
        return [
            """-- Wishlists table
CREATE TABLE IF NOT EXISTS wishlists (
    id TEXT PRIMARY KEY,
    buyer_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wishlists_buyer ON wishlists(buyer_id);""",
            """-- Wishlist Items table
CREATE TABLE IF NOT EXISTS wishlist_items (
    id TEXT PRIMARY KEY,
    wishlist_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    variant_id TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wishlist_id) REFERENCES wishlists(id)
);

CREATE INDEX IF NOT EXISTS idx_wishlist_items_wishlist ON wishlist_items(wishlist_id);""",
        ]

    def _reviews_table(self) -> str:
        """Generate reviews table."""
        return """-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    buyer_id TEXT,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title TEXT,
    body TEXT,
    verified_purchase BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);"""

    def _loyalty_tables(self) -> list[str]:
        """Generate loyalty tables."""
        return [
            """-- Loyalty Accounts table
CREATE TABLE IF NOT EXISTS loyalty_accounts (
    id TEXT PRIMARY KEY,
    buyer_id TEXT NOT NULL UNIQUE,
    points_balance INTEGER DEFAULT 0,
    lifetime_points INTEGER DEFAULT 0,
    tier TEXT DEFAULT 'Bronze',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loyalty_buyer ON loyalty_accounts(buyer_id);""",
            """-- Loyalty Transactions table
CREATE TABLE IF NOT EXISTS loyalty_transactions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    points INTEGER NOT NULL,
    type TEXT NOT NULL,
    order_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES loyalty_accounts(id)
);

CREATE INDEX IF NOT EXISTS idx_loyalty_tx_account ON loyalty_transactions(account_id);""",
        ]

    def _gift_cards_tables(self) -> list[str]:
        """Generate gift card tables."""
        return [
            """-- Gift Cards table
CREATE TABLE IF NOT EXISTS gift_cards (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    initial_balance INTEGER NOT NULL,
    current_balance INTEGER NOT NULL,
    purchaser_email TEXT,
    recipient_email TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gift_cards_code ON gift_cards(code);""",
            """-- Gift Card Transactions table
CREATE TABLE IF NOT EXISTS gift_card_transactions (
    id TEXT PRIMARY KEY,
    gift_card_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    type TEXT NOT NULL,
    order_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gift_card_id) REFERENCES gift_cards(id)
);""",
        ]

    def _subscriptions_tables(self) -> list[str]:
        """Generate subscription tables."""
        return [
            """-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    buyer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    billing_cycle TEXT DEFAULT 'monthly',
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    next_billing_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_buyer ON subscriptions(buyer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);""",
            """-- Subscription Invoices table
CREATE TABLE IF NOT EXISTS subscription_invoices (
    id TEXT PRIMARY KEY,
    subscription_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);""",
        ]

    def _returns_tables(self) -> list[str]:
        """Generate returns tables."""
        return [
            """-- Return Requests table
CREATE TABLE IF NOT EXISTS return_requests (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    buyer_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    reason TEXT,
    refund_amount INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_returns_order ON return_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_returns_buyer ON return_requests(buyer_id);""",
            """-- Return Items table
CREATE TABLE IF NOT EXISTS return_items (
    id TEXT PRIMARY KEY,
    return_request_id TEXT NOT NULL,
    order_line_item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    reason TEXT,
    FOREIGN KEY (return_request_id) REFERENCES return_requests(id)
);""",
        ]

    def generate_import_script(self) -> str:
        """Generate Python script to import CSV data."""
        return '''"""Import CSV data into SQLite database."""

import csv
import sqlite3
from pathlib import Path


def import_csv_to_table(db_path: Path, csv_path: Path, table_name: str):
    """Import a CSV file into a database table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames

        for row in reader:
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            values = [row[col] for col in columns]

            cursor.execute(
                f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})",
                values
            )

    conn.commit()
    conn.close()


def main():
    """Import all CSV files."""
    # Initialize database first (creates tables)
    from server.db import init_db
    init_db()

    project_root = Path(__file__).parent.parent.parent.parent
    db_path = project_root / "databases" / "store.db"
    data_path = project_root / "data"

    # Import mappings
    mappings = [
        ("products.csv", "products"),
        ("inventory.csv", "inventory"),
        ("discounts.csv", "discounts"),
        ("shipping_rates.csv", "shipping_rates"),
        ("customers.csv", "customers"),
        ("addresses.csv", "customer_addresses"),
        ("promotions.csv", "promotions"),
    ]

    for csv_file, table_name in mappings:
        csv_path = data_path / csv_file
        if csv_path.exists():
            print(f"Importing {csv_file} -> {table_name}")
            import_csv_to_table(db_path, csv_path, table_name)
        else:
            print(f"Skipping {csv_file} (not found)")

    print("Import complete!")


if __name__ == "__main__":
    main()
'''

"""Pre-defined product data and catalogs."""

from pathlib import Path
import json

DATA_DIR = Path(__file__).parent

def load_product_catalog(store_type: str) -> dict:
    """Load the product catalog for a store type."""
    catalog_path = DATA_DIR / "product_catalogs" / f"{store_type}.json"
    if catalog_path.exists():
        with open(catalog_path) as f:
            return json.load(f)
    return {"categories": [], "products": []}

def load_brand_names() -> list:
    """Load brand name data."""
    path = DATA_DIR / "brand_names.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []

def load_product_descriptors() -> dict:
    """Load product descriptor data."""
    path = DATA_DIR / "product_descriptors.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

__all__ = ["load_product_catalog", "load_brand_names", "load_product_descriptors", "DATA_DIR"]

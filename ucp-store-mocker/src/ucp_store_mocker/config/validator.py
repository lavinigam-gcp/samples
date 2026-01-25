"""Configuration validation for store configs."""

from typing import Optional
from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.templates.store_types import STORE_TEMPLATES


def validate_config(config: StoreConfig) -> list[str]:
    """Validate a store configuration and return a list of errors.

    Returns an empty list if the configuration is valid.
    """
    errors = []

    # Validate store type
    if config.store.type not in STORE_TEMPLATES:
        errors.append(
            f"Unknown store type: '{config.store.type}'. "
            f"Valid types: {', '.join(STORE_TEMPLATES.keys())}"
        )

    # Validate server port
    if not (1 <= config.server.port <= 65535):
        errors.append(f"Invalid port number: {config.server.port}")

    # Validate catalog
    if config.catalog.generation.count < 1:
        errors.append("Catalog count must be at least 1")

    if config.catalog.generation.strategy not in ("template", "faker", "hybrid"):
        errors.append(
            f"Invalid catalog generation strategy: '{config.catalog.generation.strategy}'. "
            "Valid strategies: template, faker, hybrid"
        )

    # Validate inventory
    if config.inventory.strategy not in ("realistic", "unlimited", "scarce"):
        errors.append(
            f"Invalid inventory strategy: '{config.inventory.strategy}'. "
            "Valid strategies: realistic, unlimited, scarce"
        )

    if not (0 <= config.inventory.variance <= 1):
        errors.append("Inventory variance must be between 0 and 1")

    if not (0 <= config.inventory.out_of_stock_percentage <= 100):
        errors.append("Out of stock percentage must be between 0 and 100")

    if not (0 <= config.inventory.low_stock_percentage <= 100):
        errors.append("Low stock percentage must be between 0 and 100")

    # Validate image generation
    if config.catalog.images.generate:
        valid_models = ["gemini-2.5-flash-image", "gemini-3-pro-image-preview"]
        if config.catalog.images.model not in valid_models:
            errors.append(
                f"Invalid image generation model: '{config.catalog.images.model}'. "
                f"Valid models: {', '.join(valid_models)}"
            )

    # Validate discount codes
    for i, code in enumerate(config.capabilities.discount.codes):
        if code.type not in ("percentage", "fixed"):
            errors.append(
                f"Discount code {i}: Invalid type '{code.type}'. "
                "Valid types: percentage, fixed"
            )
        if code.type == "percentage" and not (0 <= code.value <= 100):
            errors.append(f"Discount code {i}: Percentage must be between 0 and 100")

    # Validate categories have valid price ranges
    for cat in config.catalog.categories:
        if len(cat.price_range) != 2:
            errors.append(f"Category '{cat.name}': price_range must have exactly 2 values")
        elif cat.price_range[0] > cat.price_range[1]:
            errors.append(
                f"Category '{cat.name}': price_range min ({cat.price_range[0]}) "
                f"is greater than max ({cat.price_range[1]})"
            )

    # Validate fulfillment methods
    for method in config.capabilities.fulfillment.methods:
        if method.type not in ("shipping", "pickup"):
            errors.append(
                f"Invalid fulfillment method type: '{method.type}'. "
                "Valid types: shipping, pickup"
            )

    # Validate payment handlers
    for handler in config.payment.handlers:
        if not handler.name:
            errors.append(f"Payment handler '{handler.id}': name is required")

    return errors


def validate_multi_store_config(config: dict) -> list[str]:
    """Validate a multi-store orchestration configuration."""
    errors = []

    if "stores" not in config:
        errors.append("Multi-store config must have a 'stores' key")
        return errors

    if not isinstance(config["stores"], list):
        errors.append("'stores' must be a list")
        return errors

    store_names = set()
    store_ports = set()

    for i, store in enumerate(config["stores"]):
        if "name" not in store:
            errors.append(f"Store {i}: missing 'name'")
        else:
            if store["name"] in store_names:
                errors.append(f"Duplicate store name: '{store['name']}'")
            store_names.add(store["name"])

        if "config" not in store and "config_file" not in store:
            errors.append(f"Store {i}: must have either 'config' or 'config_file'")

        if "port" in store:
            if store["port"] in store_ports:
                errors.append(f"Duplicate port: {store['port']}")
            store_ports.add(store["port"])

    return errors

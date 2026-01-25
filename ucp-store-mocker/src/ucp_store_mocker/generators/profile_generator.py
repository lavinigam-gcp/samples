"""UCP Discovery Profile generator."""

import json
from typing import Any

from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.capabilities.registry import CapabilityRegistry


class ProfileGenerator:
    """Generate UCP discovery profile JSON."""

    def __init__(self, config: StoreConfig):
        self.config = config
        self.registry = CapabilityRegistry()

    def generate(self) -> str:
        """Generate the UCP discovery profile as JSON string."""
        profile = self._build_profile()
        return json.dumps(profile, indent=2)

    def _build_profile(self) -> dict[str, Any]:
        """Build the complete discovery profile."""
        enabled_caps = self.registry.get_enabled_capabilities(self.config)

        profile = {
            "profile_version": "0.1.0",
            "name": self.config.store.name,
            "description": f"UCP Mock Store - {self.config.store.type.title()}",
            "provider": {
                "name": "UCP Store Mocker",
                "url": "https://github.com/anthropics/ucp",
            },
            "capabilities": [cap.id for cap in enabled_caps],
            "actions": self._build_actions(enabled_caps),
            "payment_methods": self._build_payment_methods(),
        }

        # Add fulfillment options if enabled
        if self.config.capabilities.fulfillment.enabled:
            profile["fulfillment"] = self._build_fulfillment()

        # Add location if configured
        if self.config.store.location:
            profile["location"] = self._build_location()

        return profile

    def _build_actions(self, enabled_caps: list) -> list[dict[str, Any]]:
        """Build the actions list from enabled capabilities."""
        actions = []

        for cap in enabled_caps:
            cap_instance = self._get_capability_instance(cap.id)
            if cap_instance and hasattr(cap_instance, 'get_discovery_actions'):
                cap_actions = cap_instance.get_discovery_actions()
                actions.extend(cap_actions)

        return actions

    def _get_capability_instance(self, cap_id: str):
        """Get a capability instance by ID."""
        from ucp_store_mocker.capabilities.core import CORE_CAPABILITIES
        from ucp_store_mocker.capabilities.extensions import EXTENDED_CAPABILITIES

        all_caps = {**CORE_CAPABILITIES, **EXTENDED_CAPABILITIES}
        cap_class = all_caps.get(cap_id)
        if cap_class:
            return cap_class()
        return None

    def _build_payment_methods(self) -> list[dict[str, Any]]:
        """Build payment methods list."""
        methods = []

        for handler in self.config.payment.handlers:
            if handler.enabled:
                methods.append({
                    "id": handler.id,
                    "name": handler.name,
                    "type": "mock" if "mock" in handler.id.lower() else "external",
                })

        # Add default mock payment if none configured
        if not methods:
            methods.append({
                "id": "mock_payment",
                "name": "dev.ucp.mock_payment",
                "type": "mock",
            })

        return methods

    def _build_fulfillment(self) -> dict[str, Any]:
        """Build fulfillment configuration."""
        fulfillment = {
            "methods": [],
        }

        for method in self.config.capabilities.fulfillment.methods:
            method_config = {
                "type": method.type,
                "options": [],
            }

            for option in method.options:
                opt = {
                    "id": option.get("id"),
                    "title": option.get("title"),
                    "price": option.get("price", 0),
                }

                if "delivery_days" in option:
                    opt["delivery_days"] = {
                        "min": option["delivery_days"][0],
                        "max": option["delivery_days"][1] if len(option["delivery_days"]) > 1 else option["delivery_days"][0],
                    }

                method_config["options"].append(opt)

            fulfillment["methods"].append(method_config)

        # Add free shipping threshold if enabled
        if self.config.capabilities.fulfillment.free_shipping.enabled:
            fulfillment["free_shipping_threshold"] = self.config.capabilities.fulfillment.free_shipping.threshold

        return fulfillment

    def _build_location(self) -> dict[str, Any]:
        """Build location information."""
        loc = self.config.store.location
        return {
            "address": {
                "street": loc.address.street,
                "city": loc.address.city,
                "state": loc.address.state,
                "postal_code": loc.address.postal_code,
                "country": loc.address.country,
            },
            "coordinates": {
                "latitude": loc.coordinates.latitude,
                "longitude": loc.coordinates.longitude,
            },
        }

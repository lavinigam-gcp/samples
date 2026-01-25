"""Capability registry for managing UCP capabilities."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CapabilityInfo:
    """Information about a UCP capability."""
    id: str
    name: str
    description: str
    configurable: bool = True
    extends: Optional[str] = None
    is_core: bool = True


class CapabilityRegistry:
    """Registry for UCP capabilities."""

    # Core UCP capabilities from the specification
    CORE_CAPABILITIES = [
        CapabilityInfo(
            id="dev.ucp.shopping.checkout",
            name="Checkout",
            description="Create, get, update, complete, and cancel checkouts",
            configurable=False,  # Always enabled
            is_core=True,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.order",
            name="Order",
            description="Order management with lifecycle webhooks",
            is_core=True,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.fulfillment",
            name="Fulfillment",
            description="Shipping and pickup with multi-destination support",
            is_core=True,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.discount",
            name="Discount",
            description="Percentage and fixed discounts, auto-discounts",
            is_core=True,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.buyer_consent",
            name="Buyer Consent",
            description="GDPR consent flags for buyer information",
            is_core=True,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.ap2_mandate",
            name="AP2 Mandate",
            description="Cryptographic mandates for agent authorization",
            is_core=True,
        ),
    ]

    # Extended capabilities (custom implementations)
    EXTENDED_CAPABILITIES = [
        CapabilityInfo(
            id="dev.ucp.shopping.wishlist",
            name="Wishlist",
            description="Save items for later, move to cart",
            extends="dev.ucp.shopping.checkout",
            is_core=False,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.reviews",
            name="Reviews",
            description="Product ratings and reviews",
            extends=None,
            is_core=False,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.loyalty",
            name="Loyalty",
            description="Points, tiers, rewards redemption",
            extends="dev.ucp.shopping.checkout",
            is_core=False,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.gift_cards",
            name="Gift Cards",
            description="Purchase, redeem, balance check",
            extends="dev.ucp.shopping.checkout",
            is_core=False,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.subscriptions",
            name="Subscriptions",
            description="Recurring orders, subscription management",
            extends="dev.ucp.shopping.order",
            is_core=False,
        ),
        CapabilityInfo(
            id="dev.ucp.shopping.returns",
            name="Returns",
            description="Return requests, refund processing",
            extends="dev.ucp.shopping.order",
            is_core=False,
        ),
    ]

    def __init__(self):
        self._capabilities = {}
        for cap in self.CORE_CAPABILITIES + self.EXTENDED_CAPABILITIES:
            self._capabilities[cap.id] = cap

    def get(self, capability_id: str) -> Optional[CapabilityInfo]:
        """Get a capability by ID."""
        return self._capabilities.get(capability_id)

    def get_core_capabilities(self) -> list[CapabilityInfo]:
        """Get all core UCP capabilities."""
        return [c for c in self._capabilities.values() if c.is_core]

    def get_extended_capabilities(self) -> list[CapabilityInfo]:
        """Get all extended capabilities."""
        return [c for c in self._capabilities.values() if not c.is_core]

    def get_all(self) -> list[CapabilityInfo]:
        """Get all capabilities."""
        return list(self._capabilities.values())

    def get_enabled_capabilities(self, config) -> list[CapabilityInfo]:
        """Get capabilities enabled in a config."""
        enabled = []
        caps = config.capabilities

        # Core capabilities
        if caps.checkout.enabled:
            enabled.append(self.get("dev.ucp.shopping.checkout"))
        if caps.order.enabled:
            enabled.append(self.get("dev.ucp.shopping.order"))
        if caps.fulfillment.enabled:
            enabled.append(self.get("dev.ucp.shopping.fulfillment"))
        if caps.discount.enabled:
            enabled.append(self.get("dev.ucp.shopping.discount"))
        if caps.buyer_consent.enabled:
            enabled.append(self.get("dev.ucp.shopping.buyer_consent"))
        if caps.ap2_mandate.enabled:
            enabled.append(self.get("dev.ucp.shopping.ap2_mandate"))

        # Extended capabilities
        if caps.wishlist and caps.wishlist.enabled:
            enabled.append(self.get("dev.ucp.shopping.wishlist"))
        if caps.reviews and caps.reviews.enabled:
            enabled.append(self.get("dev.ucp.shopping.reviews"))
        if caps.loyalty and caps.loyalty.enabled:
            enabled.append(self.get("dev.ucp.shopping.loyalty"))
        if caps.gift_cards and caps.gift_cards.enabled:
            enabled.append(self.get("dev.ucp.shopping.gift_cards"))
        if caps.subscriptions and caps.subscriptions.enabled:
            enabled.append(self.get("dev.ucp.shopping.subscriptions"))
        if caps.returns and caps.returns.enabled:
            enabled.append(self.get("dev.ucp.shopping.returns"))

        return [c for c in enabled if c is not None]

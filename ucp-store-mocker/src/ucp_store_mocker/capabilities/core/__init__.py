"""Core UCP capabilities from the specification."""

from ucp_store_mocker.capabilities.core.checkout import CheckoutCapability
from ucp_store_mocker.capabilities.core.order import OrderCapability
from ucp_store_mocker.capabilities.core.fulfillment import FulfillmentCapability
from ucp_store_mocker.capabilities.core.discount import DiscountCapability
from ucp_store_mocker.capabilities.core.buyer_consent import BuyerConsentCapability

CORE_CAPABILITIES = {
    "dev.ucp.shopping.checkout": CheckoutCapability,
    "dev.ucp.shopping.order": OrderCapability,
    "dev.ucp.shopping.fulfillment": FulfillmentCapability,
    "dev.ucp.shopping.discount": DiscountCapability,
    "dev.ucp.shopping.buyer_consent": BuyerConsentCapability,
}

__all__ = [
    "CORE_CAPABILITIES",
    "CheckoutCapability",
    "OrderCapability",
    "FulfillmentCapability",
    "DiscountCapability",
    "BuyerConsentCapability",
]

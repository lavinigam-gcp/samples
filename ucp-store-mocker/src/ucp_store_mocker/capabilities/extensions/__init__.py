"""Extended capabilities beyond the core UCP specification."""

from ucp_store_mocker.capabilities.extensions.wishlist import WishlistCapability
from ucp_store_mocker.capabilities.extensions.reviews import ReviewsCapability
from ucp_store_mocker.capabilities.extensions.loyalty import LoyaltyCapability
from ucp_store_mocker.capabilities.extensions.gift_cards import GiftCardsCapability
from ucp_store_mocker.capabilities.extensions.subscriptions import SubscriptionsCapability
from ucp_store_mocker.capabilities.extensions.returns import ReturnsCapability

EXTENDED_CAPABILITIES = {
    "dev.ucp.shopping.wishlist": WishlistCapability,
    "dev.ucp.shopping.reviews": ReviewsCapability,
    "dev.ucp.shopping.loyalty": LoyaltyCapability,
    "dev.ucp.shopping.gift_cards": GiftCardsCapability,
    "dev.ucp.shopping.subscriptions": SubscriptionsCapability,
    "dev.ucp.shopping.returns": ReturnsCapability,
}

__all__ = [
    "EXTENDED_CAPABILITIES",
    "WishlistCapability",
    "ReviewsCapability",
    "LoyaltyCapability",
    "GiftCardsCapability",
    "SubscriptionsCapability",
    "ReturnsCapability",
]

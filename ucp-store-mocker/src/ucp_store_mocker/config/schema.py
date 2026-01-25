"""Pydantic models for store configuration YAML schema."""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Location Models
# ─────────────────────────────────────────────────────────────────────────────

class Address(BaseModel):
    """Physical address configuration."""
    street: str = "123 Main St"
    city: str = "San Francisco"
    state: str = "CA"
    postal_code: str = "94102"
    country: str = "US"


class Coordinates(BaseModel):
    """Geographic coordinates."""
    latitude: float = 37.7749
    longitude: float = -122.4194


class Location(BaseModel):
    """Store location configuration."""
    address: Address = Field(default_factory=Address)
    coordinates: Coordinates = Field(default_factory=Coordinates)


# ─────────────────────────────────────────────────────────────────────────────
# Store Configuration
# ─────────────────────────────────────────────────────────────────────────────

class StoreInfo(BaseModel):
    """Basic store information."""
    name: str = "My UCP Store"
    type: str = "grocery"
    location: Location = Field(default_factory=Location)


# ─────────────────────────────────────────────────────────────────────────────
# Server Configuration
# ─────────────────────────────────────────────────────────────────────────────

class TransportConfig(BaseModel):
    """Transport protocol configuration."""
    rest: bool = True
    a2a: bool = True


class ServerConfig(BaseModel):
    """Server configuration."""
    port: int = 8080
    transport: TransportConfig = Field(default_factory=TransportConfig)


# ─────────────────────────────────────────────────────────────────────────────
# Capability Configurations
# ─────────────────────────────────────────────────────────────────────────────

class CheckoutConfig(BaseModel):
    """Checkout capability configuration."""
    enabled: bool = True


class WebhookConfig(BaseModel):
    """Webhook configuration for order events."""
    enabled: bool = True
    url: Optional[str] = None


class OrderConfig(BaseModel):
    """Order capability configuration."""
    enabled: bool = True
    webhooks: WebhookConfig = Field(default_factory=WebhookConfig)


class ShippingOption(BaseModel):
    """Shipping option configuration."""
    id: str
    title: str
    price: int  # cents
    delivery_days: list[int] = Field(default_factory=lambda: [3, 5])


class PickupOption(BaseModel):
    """Pickup option configuration."""
    id: str
    title: str
    price: int = 0


class FulfillmentMethod(BaseModel):
    """Fulfillment method configuration."""
    type: str  # "shipping" or "pickup"
    options: list[dict] = Field(default_factory=list)


class FreeShippingConfig(BaseModel):
    """Free shipping threshold configuration."""
    enabled: bool = True
    threshold: int = 3500  # cents


class FulfillmentConfig(BaseModel):
    """Fulfillment capability configuration."""
    enabled: bool = True
    methods: list[FulfillmentMethod] = Field(default_factory=list)
    free_shipping: FreeShippingConfig = Field(default_factory=FreeShippingConfig)


class DiscountCode(BaseModel):
    """Discount code configuration."""
    code: str
    type: str = "percentage"  # percentage or fixed
    value: int = 10  # percentage or cents


class DiscountConfig(BaseModel):
    """Discount capability configuration."""
    enabled: bool = True
    codes: list[DiscountCode] = Field(default_factory=list)
    auto_discounts: list[dict] = Field(default_factory=list)


class BuyerConsentConfig(BaseModel):
    """Buyer consent capability configuration."""
    enabled: bool = True


class AP2MandateConfig(BaseModel):
    """AP2 mandate capability configuration."""
    enabled: bool = False


# Extended Capabilities

class WishlistConfig(BaseModel):
    """Wishlist extended capability configuration."""
    enabled: bool = False


class ReviewsConfig(BaseModel):
    """Reviews extended capability configuration."""
    enabled: bool = False
    allow_anonymous: bool = False


class LoyaltyConfig(BaseModel):
    """Loyalty extended capability configuration."""
    enabled: bool = False
    points_per_dollar: int = 10
    tiers: list[str] = Field(default_factory=lambda: ["Bronze", "Silver", "Gold", "Platinum"])


class GiftCardsConfig(BaseModel):
    """Gift cards extended capability configuration."""
    enabled: bool = False
    denominations: list[int] = Field(default_factory=lambda: [1000, 2500, 5000, 10000])


class SubscriptionsConfig(BaseModel):
    """Subscriptions extended capability configuration."""
    enabled: bool = False


class ReturnsConfig(BaseModel):
    """Returns extended capability configuration."""
    enabled: bool = False
    return_window_days: int = 30


class CapabilitiesConfig(BaseModel):
    """All capabilities configuration."""
    # Core capabilities
    checkout: CheckoutConfig = Field(default_factory=CheckoutConfig)
    order: OrderConfig = Field(default_factory=OrderConfig)
    fulfillment: FulfillmentConfig = Field(default_factory=FulfillmentConfig)
    discount: DiscountConfig = Field(default_factory=DiscountConfig)
    buyer_consent: BuyerConsentConfig = Field(default_factory=BuyerConsentConfig)
    ap2_mandate: AP2MandateConfig = Field(default_factory=AP2MandateConfig)

    # Extended capabilities
    wishlist: Optional[WishlistConfig] = None
    reviews: Optional[ReviewsConfig] = None
    loyalty: Optional[LoyaltyConfig] = None
    gift_cards: Optional[GiftCardsConfig] = None
    subscriptions: Optional[SubscriptionsConfig] = None
    returns: Optional[ReturnsConfig] = None


# ─────────────────────────────────────────────────────────────────────────────
# Payment Configuration
# ─────────────────────────────────────────────────────────────────────────────

class PaymentHandler(BaseModel):
    """Payment handler configuration."""
    id: str
    name: str
    enabled: bool = True


class PaymentConfig(BaseModel):
    """Payment configuration."""
    handlers: list[PaymentHandler] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Catalog Configuration
# ─────────────────────────────────────────────────────────────────────────────

class CatalogGenerationConfig(BaseModel):
    """Product catalog generation settings."""
    strategy: str = "hybrid"  # template, faker, or hybrid
    count: int = 50
    seed: int = 42


class ImageGenerationConfig(BaseModel):
    """Image generation settings."""
    generate: bool = False
    model: str = "gemini-2.5-flash-image"
    style: str = "product-photography"
    background: str = "white"
    resolution: str = "1024x1024"
    batch_size: int = 10
    cache_dir: str = "./generated_images"


class VariationRule(BaseModel):
    """Product variation rule."""
    type: str  # size, color, storage, weight, etc.
    options: list[str]
    affects_price: bool = False
    price_adjustments: Optional[list[int]] = None
    price_multipliers: Optional[list[float]] = None


class VariationsConfig(BaseModel):
    """Product variations configuration."""
    enabled: bool = True
    category_variations: dict[str, list[VariationRule]] = Field(default_factory=dict)


class CategoryConfig(BaseModel):
    """Product category configuration."""
    name: str
    count: int = 10
    price_range: list[int] = Field(default_factory=lambda: [100, 1000])


class CatalogConfig(BaseModel):
    """Catalog configuration."""
    generation: CatalogGenerationConfig = Field(default_factory=CatalogGenerationConfig)
    images: ImageGenerationConfig = Field(default_factory=ImageGenerationConfig)
    variations: VariationsConfig = Field(default_factory=VariationsConfig)
    categories: list[CategoryConfig] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Inventory Configuration
# ─────────────────────────────────────────────────────────────────────────────

class CategoryInventoryOverride(BaseModel):
    """Category-specific inventory settings."""
    default_quantity: int = 100
    variance: float = 0.3


class InventoryConfig(BaseModel):
    """Inventory configuration."""
    strategy: str = "realistic"  # realistic, unlimited, scarce
    default_quantity: int = 100
    variance: float = 0.3
    low_stock_percentage: int = 10
    out_of_stock_percentage: int = 5
    restock_simulation: bool = False
    category_overrides: dict[str, CategoryInventoryOverride] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# A2A Configuration
# ─────────────────────────────────────────────────────────────────────────────

class AgentSkill(BaseModel):
    """A2A agent skill configuration."""
    id: str
    description: Optional[str] = None


class AgentCardConfig(BaseModel):
    """A2A agent card configuration."""
    name: Optional[str] = None  # Defaults to "{store.name} Agent"
    description: Optional[str] = None
    skills: list[AgentSkill] = Field(default_factory=list)


class A2AConfig(BaseModel):
    """A2A (Agent-to-Agent) configuration."""
    enabled: bool = True
    agent_card: AgentCardConfig = Field(default_factory=AgentCardConfig)


# ─────────────────────────────────────────────────────────────────────────────
# Root Configuration
# ─────────────────────────────────────────────────────────────────────────────

class StoreConfig(BaseModel):
    """Root store configuration model."""
    store: StoreInfo = Field(default_factory=StoreInfo)
    server: ServerConfig = Field(default_factory=ServerConfig)
    capabilities: CapabilitiesConfig = Field(default_factory=CapabilitiesConfig)
    payment: PaymentConfig = Field(default_factory=PaymentConfig)
    catalog: CatalogConfig = Field(default_factory=CatalogConfig)
    inventory: InventoryConfig = Field(default_factory=InventoryConfig)
    a2a: A2AConfig = Field(default_factory=A2AConfig)


def load_config(path: Path) -> StoreConfig:
    """Load and parse a store configuration from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)

    return StoreConfig(**data)

"""Base template class for store types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseTemplate(ABC):
    """Base class for store type templates."""

    name: str
    description: str
    default_categories: list[dict[str, Any]] = field(default_factory=list)
    default_variations: dict[str, list[dict]] = field(default_factory=dict)
    default_fulfillment: list[dict[str, Any]] = field(default_factory=list)
    sample_products: list[dict[str, Any]] = field(default_factory=list)

    @abstractmethod
    def get_product_descriptors(self) -> dict[str, list[str]]:
        """Get product name descriptors for Faker generation."""
        pass

    def get_category_names(self) -> list[str]:
        """Get list of category names."""
        return [cat["name"] for cat in self.default_categories]

    def get_default_config(self) -> dict[str, Any]:
        """Get default configuration for this store type."""
        return {
            "categories": self.default_categories,
            "variations": {"category_variations": self.default_variations},
            "fulfillment": {"methods": self.default_fulfillment},
        }

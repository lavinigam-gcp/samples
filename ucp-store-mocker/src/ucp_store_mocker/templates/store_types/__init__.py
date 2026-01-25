"""Store type templates with pre-configured defaults."""

from ucp_store_mocker.templates.store_types.grocery import GroceryTemplate
from ucp_store_mocker.templates.store_types.electronics import ElectronicsTemplate
from ucp_store_mocker.templates.store_types.fashion import FashionTemplate
from ucp_store_mocker.templates.store_types.restaurant import RestaurantTemplate
from ucp_store_mocker.templates.store_types.subscription import SubscriptionTemplate
from ucp_store_mocker.templates.store_types.flower_shop import FlowerShopTemplate

STORE_TEMPLATES = {
    "grocery": GroceryTemplate,
    "electronics": ElectronicsTemplate,
    "fashion": FashionTemplate,
    "restaurant": RestaurantTemplate,
    "subscription": SubscriptionTemplate,
    "flower_shop": FlowerShopTemplate,
}

__all__ = [
    "STORE_TEMPLATES",
    "GroceryTemplate",
    "ElectronicsTemplate",
    "FashionTemplate",
    "RestaurantTemplate",
    "SubscriptionTemplate",
    "FlowerShopTemplate",
]

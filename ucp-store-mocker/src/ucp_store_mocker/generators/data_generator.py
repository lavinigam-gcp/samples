"""Data generator for products, inventory, and variations."""

import random
import uuid
from typing import Any, Optional
from itertools import product as cartesian_product

from faker import Faker

from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.templates.store_types import STORE_TEMPLATES


class DataGenerator:
    """Generate product catalog data."""

    def __init__(self, config: StoreConfig, seed: Optional[int] = None):
        self.config = config
        self.seed = seed or config.catalog.generation.seed
        self.random = random.Random(self.seed)
        self.faker = Faker()
        Faker.seed(self.seed)

        # Get template for store type
        template_class = STORE_TEMPLATES.get(config.store.type)
        self.template = template_class() if template_class else None

    def generate_products(self) -> list[dict[str, Any]]:
        """Generate product catalog."""
        products = []
        target_count = self.config.catalog.generation.count

        # Use categories from config or template defaults
        categories = self.config.catalog.categories
        if not categories and self.template:
            categories = [
                type("cat", (), {"name": c["name"], "count": c["count"], "price_range": c["price_range"]})()
                for c in self.template.default_categories
            ]

        if not categories:
            # Fallback to generating generic products
            return self._generate_generic_products(target_count)

        # Calculate products per category
        total_specified = sum(cat.count for cat in categories)
        if total_specified < target_count:
            # Distribute extra products
            extra = target_count - total_specified
            extra_per_cat = extra // len(categories)
        else:
            extra_per_cat = 0

        for category in categories:
            count = category.count + extra_per_cat
            cat_products = self._generate_category_products(
                category.name,
                count,
                category.price_range
            )
            products.extend(cat_products)

        return products[:target_count]

    def _generate_category_products(
        self,
        category: str,
        count: int,
        price_range: list[int]
    ) -> list[dict[str, Any]]:
        """Generate products for a specific category."""
        products = []
        descriptors = self._get_descriptors_for_category(category)

        for i in range(count):
            product_id = f"{category.lower().replace(' ', '-')}-{i+1:03d}"
            title = self._generate_product_title(category, descriptors)
            price = self.random.randint(price_range[0], price_range[1])

            products.append({
                "id": product_id,
                "title": title,
                "description": self._generate_description(title, category),
                "category": category,
                "price": price,
                "currency": "USD",
                "image_url": f"/static/images/{product_id}.png",
                "sku": self._generate_sku(product_id),
            })

        return products

    def _generate_product_title(self, category: str, descriptors: dict) -> str:
        """Generate a product title using descriptors."""
        if not descriptors:
            return f"{category} Item {self.random.randint(1, 100)}"

        parts = []

        # Add prefix if available
        if "prefixes" in descriptors:
            parts.append(self.random.choice(descriptors["prefixes"]))

        # Add main item name
        if "items" in descriptors:
            parts.append(self.random.choice(descriptors["items"]))
        elif "names" in descriptors:
            parts.append(self.random.choice(descriptors["names"]))
        elif "flowers" in descriptors:
            parts.append(self.random.choice(descriptors["flowers"]))
        elif "types" in descriptors:
            parts.append(self.random.choice(descriptors["types"]))
        else:
            parts.append(f"{category} Item")

        # Add suffix if available
        if "suffixes" in descriptors:
            parts.append(self.random.choice(descriptors["suffixes"]))

        return " ".join(parts)

    def _generate_description(self, title: str, category: str) -> str:
        """Generate a product description."""
        templates = [
            f"High-quality {title.lower()} from our {category} collection.",
            f"Premium {title.lower()} - perfect for any occasion.",
            f"Our popular {title.lower()} from the {category} department.",
            f"Discover our {title.lower()} - customer favorite.",
        ]
        return self.random.choice(templates)

    def _generate_sku(self, product_id: str) -> str:
        """Generate a SKU from product ID."""
        return product_id.upper().replace("-", "")[:12]

    def _get_descriptors_for_category(self, category: str) -> dict:
        """Get product descriptors for a category."""
        if not self.template:
            return {}

        all_descriptors = self.template.get_product_descriptors()
        return all_descriptors.get(category, {})

    def _generate_generic_products(self, count: int) -> list[dict[str, Any]]:
        """Generate generic products when no template is available."""
        products = []
        for i in range(count):
            product_id = f"product-{i+1:03d}"
            products.append({
                "id": product_id,
                "title": f"Product {i+1}",
                "description": f"Generic product #{i+1}",
                "category": "General",
                "price": self.random.randint(100, 10000),
                "currency": "USD",
                "image_url": f"/static/images/{product_id}.png",
                "sku": f"PROD{i+1:04d}",
            })
        return products

    def generate_variants(self, products: list[dict]) -> list[dict[str, Any]]:
        """Generate product variants based on variation rules."""
        if not self.config.catalog.variations.enabled:
            return []

        variation_gen = ProductVariationGenerator(self.config, self.seed)
        all_variants = []

        for product in products:
            variants = variation_gen.generate_variations(product)
            if len(variants) > 1:  # Only include if there are actual variants
                all_variants.extend(variants[1:])  # Skip the first (base product)

        return all_variants

    def generate_inventory(self, products: list[dict]) -> list[dict[str, Any]]:
        """Generate inventory for products."""
        inventory_gen = InventoryGenerator(self.config, self.seed)
        return inventory_gen.generate_inventory(products)


class ProductVariationGenerator:
    """Generate product variations based on category rules."""

    def __init__(self, config: StoreConfig, seed: int = 42):
        self.config = config.catalog.variations
        self.random = random.Random(seed)

    def generate_variations(self, product: dict) -> list[dict[str, Any]]:
        """Generate all variations for a product."""
        category = product.get("category", "")
        variation_rules = self._get_variation_rules(category)

        if not variation_rules:
            return [product]  # No variations, return as-is

        # Generate all combinations
        combinations = self._get_all_combinations(variation_rules)
        if not combinations:
            return [product]

        variations = [product]  # Include base product

        for combo in combinations[:10]:  # Limit to 10 variants per product
            variant = self._create_variant(product, combo, variation_rules)
            variations.append(variant)

        return variations

    def _get_variation_rules(self, category: str) -> list[dict]:
        """Get variation rules for a category."""
        cat_variations = self.config.category_variations
        if category in cat_variations:
            return [v.model_dump() if hasattr(v, 'model_dump') else v for v in cat_variations[category]]
        return []

    def _create_variant(self, base_product: dict, combo: dict, rules: list) -> dict:
        """Create a single variant from a combination."""
        variant = base_product.copy()

        # Build variant ID and title
        variant_suffix = "-".join(str(v).lower().replace(" ", "") for v in combo.values())
        variant["id"] = f"{base_product['id']}-{variant_suffix}"
        variant["parent_id"] = base_product["id"]
        variant["variations"] = combo

        # Calculate price adjustments
        price = base_product["price"]
        for rule in rules:
            var_type = rule["type"]
            var_value = combo.get(var_type)
            if not var_value:
                continue

            options = rule.get("options", [])
            if var_value not in options:
                continue

            idx = options.index(var_value)

            if "price_adjustments" in rule and rule["price_adjustments"]:
                adjustments = rule["price_adjustments"]
                if idx < len(adjustments):
                    price += adjustments[idx]
            elif "price_multipliers" in rule and rule["price_multipliers"]:
                multipliers = rule["price_multipliers"]
                if idx < len(multipliers):
                    price = int(base_product["price"] * multipliers[idx])

        variant["price"] = price

        # Update title to include variations
        variation_str = ", ".join(str(v) for v in combo.values())
        variant["title"] = f"{base_product['title']} - {variation_str}"

        # Update SKU
        variant["sku"] = f"{base_product.get('sku', '')}-{variant_suffix.upper()}"[:16]

        return variant

    def _get_all_combinations(self, rules: list) -> list[dict]:
        """Generate all possible variation combinations."""
        if not rules:
            return []

        options_per_type = [(rule["type"], rule.get("options", [])) for rule in rules]
        options_per_type = [(t, o) for t, o in options_per_type if o]

        if not options_per_type:
            return []

        combinations = []
        for combo in cartesian_product(*[opts for _, opts in options_per_type]):
            combinations.append({
                options_per_type[i][0]: combo[i]
                for i in range(len(combo))
            })

        return combinations


class InventoryGenerator:
    """Generate realistic inventory levels."""

    def __init__(self, config: StoreConfig, seed: int = 42):
        self.config = config.inventory
        self.random = random.Random(seed)

    def generate_inventory(self, products: list[dict]) -> list[dict[str, Any]]:
        """Generate inventory for all products."""
        if self.config.strategy == "unlimited":
            return self._generate_unlimited(products)
        elif self.config.strategy == "scarce":
            return self._generate_scarce(products)
        else:
            return self._generate_realistic(products)

    def _generate_realistic(self, products: list[dict]) -> list[dict[str, Any]]:
        """Generate realistic inventory with variance."""
        inventory = []
        product_count = len(products)

        # Determine which products are low stock or OOS
        oos_count = int(product_count * self.config.out_of_stock_percentage / 100)
        low_stock_count = int(product_count * self.config.low_stock_percentage / 100)

        indices = list(range(product_count))
        self.random.shuffle(indices)

        oos_products = set(indices[:oos_count])
        low_stock_products = set(indices[oos_count:oos_count + low_stock_count])

        for i, product in enumerate(products):
            if i in oos_products:
                quantity = 0
            elif i in low_stock_products:
                quantity = self.random.randint(1, 5)
            else:
                base = self._get_base_quantity(product)
                variance = int(base * self.config.variance)
                quantity = self.random.randint(max(1, base - variance), base + variance)

            inventory.append({
                "product_id": product["id"],
                "quantity": quantity,
                "low_stock_threshold": 10,
            })

        return inventory

    def _generate_unlimited(self, products: list[dict]) -> list[dict[str, Any]]:
        """Generate unlimited inventory."""
        return [
            {
                "product_id": product["id"],
                "quantity": 9999,
                "low_stock_threshold": 10,
            }
            for product in products
        ]

    def _generate_scarce(self, products: list[dict]) -> list[dict[str, Any]]:
        """Generate scarce inventory for testing."""
        inventory = []
        for product in products:
            # 20% chance of OOS
            if self.random.random() < 0.2:
                quantity = 0
            else:
                quantity = self.random.randint(1, 5)

            inventory.append({
                "product_id": product["id"],
                "quantity": quantity,
                "low_stock_threshold": 3,
            })
        return inventory

    def _get_base_quantity(self, product: dict) -> int:
        """Get base quantity considering category overrides."""
        category = product.get("category", "")
        overrides = self.config.category_overrides

        if category in overrides:
            override = overrides[category]
            if hasattr(override, 'default_quantity'):
                return override.default_quantity
            elif isinstance(override, dict):
                return override.get("default_quantity", self.config.default_quantity)

        return self.config.default_quantity

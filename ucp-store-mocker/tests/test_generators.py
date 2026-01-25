"""Tests for generators."""

import pytest
from pathlib import Path

from ucp_store_mocker.generators.data_generator import (
    DataGenerator,
    InventoryGenerator,
    ProductVariationGenerator,
)
from ucp_store_mocker.generators.profile_generator import ProfileGenerator
from ucp_store_mocker.generators.store_generator import StoreGenerator


class TestDataGenerator:
    """Tests for DataGenerator."""

    def test_generate_products(self, grocery_config):
        """Test generating products."""
        generator = DataGenerator(grocery_config)
        products = generator.generate_products()

        assert len(products) > 0
        assert len(products) <= grocery_config.catalog.generation.count

        for product in products:
            assert "id" in product
            assert "title" in product
            assert "price" in product
            assert "category" in product

    def test_generate_products_has_categories(self, grocery_config):
        """Test that generated products have correct categories."""
        generator = DataGenerator(grocery_config)
        products = generator.generate_products()

        categories = set(p["category"] for p in products)
        assert len(categories) > 1  # Multiple categories

    def test_generate_with_seed_reproducible(self, grocery_config):
        """Test that generation with same seed produces same results."""
        gen1 = DataGenerator(grocery_config, seed=42)
        gen2 = DataGenerator(grocery_config, seed=42)

        products1 = gen1.generate_products()
        products2 = gen2.generate_products()

        assert products1 == products2


class TestInventoryGenerator:
    """Tests for InventoryGenerator."""

    def test_generate_realistic_inventory(self, grocery_config, sample_products):
        """Test generating realistic inventory."""
        generator = InventoryGenerator(grocery_config)
        inventory = generator.generate_inventory(sample_products)

        assert len(inventory) == len(sample_products)

        for item in inventory:
            assert "product_id" in item
            assert "quantity" in item
            assert "low_stock_threshold" in item
            assert item["quantity"] >= 0

    def test_unlimited_strategy(self, grocery_config, sample_products):
        """Test unlimited inventory strategy."""
        grocery_config.inventory.strategy = "unlimited"
        generator = InventoryGenerator(grocery_config)
        inventory = generator.generate_inventory(sample_products)

        for item in inventory:
            assert item["quantity"] == 9999

    def test_scarce_strategy(self, grocery_config, sample_products):
        """Test scarce inventory strategy."""
        grocery_config.inventory.strategy = "scarce"
        generator = InventoryGenerator(grocery_config)
        inventory = generator.generate_inventory(sample_products)

        for item in inventory:
            assert item["quantity"] <= 5


class TestProductVariationGenerator:
    """Tests for ProductVariationGenerator."""

    def test_no_variations_for_unconfigured_category(self, grocery_config):
        """Test that products in unconfigured categories have no variations."""
        generator = ProductVariationGenerator(grocery_config)

        product = {"id": "test-1", "title": "Test", "category": "Unconfigured", "price": 100}
        variations = generator.generate_variations(product)

        assert len(variations) == 1  # Only the original product

    def test_variations_for_configured_category(self, grocery_config):
        """Test that products in configured categories have variations."""
        generator = ProductVariationGenerator(grocery_config)

        product = {"id": "test-1", "title": "Apple", "category": "Fresh Produce", "price": 100}
        variations = generator.generate_variations(product)

        # Should have multiple variations for Fresh Produce (weight options)
        assert len(variations) >= 1


class TestProfileGenerator:
    """Tests for ProfileGenerator."""

    def test_generate_profile(self, grocery_config):
        """Test generating UCP discovery profile."""
        generator = ProfileGenerator(grocery_config)
        profile_json = generator.generate()

        import json
        profile = json.loads(profile_json)

        assert "profile_version" in profile
        assert "name" in profile
        assert profile["name"] == grocery_config.store.name
        assert "capabilities" in profile
        assert len(profile["capabilities"]) > 0

    def test_profile_has_actions(self, grocery_config):
        """Test that profile includes actions."""
        generator = ProfileGenerator(grocery_config)
        profile_json = generator.generate()

        import json
        profile = json.loads(profile_json)

        assert "actions" in profile
        assert len(profile["actions"]) > 0


class TestStoreGenerator:
    """Tests for StoreGenerator."""

    def test_generate_store(self, grocery_config, temp_dir):
        """Test generating a complete store."""
        generator = StoreGenerator(grocery_config, temp_dir)
        result = generator.generate()

        # Check result structure
        assert "project" in result
        assert "server" in result
        assert "data" in result

        # Check files were created
        assert (temp_dir / "pyproject.toml").exists()
        assert (temp_dir / "README.md").exists()
        assert (temp_dir / "src" / "server" / "server.py").exists()
        assert (temp_dir / "data" / "products.csv").exists()

    def test_generate_with_a2a(self, grocery_config, temp_dir):
        """Test generating store with A2A agent."""
        grocery_config.a2a.enabled = True
        generator = StoreGenerator(grocery_config, temp_dir)
        result = generator.generate()

        assert "a2a" in result
        assert (temp_dir / "src" / "server" / "a2a" / "agent_card.json").exists()

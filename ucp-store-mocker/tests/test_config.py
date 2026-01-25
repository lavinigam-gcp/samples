"""Tests for configuration handling."""

import pytest
from pathlib import Path
import tempfile
import yaml

from ucp_store_mocker.config.schema import StoreConfig, load_config
from ucp_store_mocker.config.validator import validate_config
from ucp_store_mocker.config.defaults import get_store_defaults


class TestStoreConfig:
    """Tests for StoreConfig model."""

    def test_minimal_config(self):
        """Test creating minimal config."""
        config = StoreConfig()

        assert config.store.name == "My UCP Store"
        assert config.store.type == "grocery"
        assert config.server.port == 8080

    def test_custom_config(self):
        """Test creating custom config."""
        config = StoreConfig(
            store={"name": "Custom Store", "type": "electronics"},
            server={"port": 9000},
        )

        assert config.store.name == "Custom Store"
        assert config.store.type == "electronics"
        assert config.server.port == 9000

    def test_capabilities_default(self):
        """Test default capabilities."""
        config = StoreConfig()

        assert config.capabilities.checkout.enabled is True
        assert config.capabilities.order.enabled is True


class TestLoadConfig:
    """Tests for loading config from file."""

    def test_load_valid_yaml(self):
        """Test loading valid YAML config."""
        config_data = {
            "store": {"name": "Test Store", "type": "grocery"},
            "server": {"port": 8080},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = load_config(Path(f.name))

            assert config.store.name == "Test Store"
            assert config.store.type == "grocery"


class TestValidateConfig:
    """Tests for config validation."""

    def test_valid_config(self, grocery_config):
        """Test validating a valid config."""
        errors = validate_config(grocery_config)
        assert len(errors) == 0

    def test_invalid_store_type(self):
        """Test validation catches invalid store type."""
        config = StoreConfig(store={"name": "Test", "type": "invalid_type"})
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("store type" in e.lower() for e in errors)

    def test_invalid_port(self):
        """Test validation catches invalid port."""
        config = StoreConfig(server={"port": 99999})
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("port" in e.lower() for e in errors)

    def test_invalid_inventory_strategy(self):
        """Test validation catches invalid inventory strategy."""
        config = StoreConfig(inventory={"strategy": "invalid"})
        errors = validate_config(config)

        assert len(errors) > 0

    def test_invalid_discount_type(self):
        """Test validation catches invalid discount type."""
        config = StoreConfig(
            capabilities={
                "discount": {
                    "enabled": True,
                    "codes": [{"code": "TEST", "type": "invalid", "value": 10}],
                }
            }
        )
        errors = validate_config(config)

        assert len(errors) > 0


class TestGetStoreDefaults:
    """Tests for getting store type defaults."""

    def test_grocery_defaults(self):
        """Test grocery store defaults."""
        defaults = get_store_defaults("grocery", "Test Grocery")

        assert defaults["store"]["name"] == "Test Grocery"
        assert defaults["store"]["type"] == "grocery"
        assert len(defaults["catalog"]["categories"]) > 0

    def test_electronics_defaults(self):
        """Test electronics store defaults."""
        defaults = get_store_defaults("electronics", "Test Electronics")

        assert defaults["store"]["type"] == "electronics"
        # Electronics should have higher default prices
        categories = defaults["catalog"]["categories"]
        assert any(c["price_range"][1] > 10000 for c in categories)

    def test_with_a2a_flag(self):
        """Test defaults with A2A enabled."""
        defaults = get_store_defaults("grocery", "Test", with_a2a=True)
        assert defaults["a2a"]["enabled"] is True

    def test_without_a2a_flag(self):
        """Test defaults with A2A disabled."""
        defaults = get_store_defaults("grocery", "Test", with_a2a=False)
        assert defaults["a2a"]["enabled"] is False

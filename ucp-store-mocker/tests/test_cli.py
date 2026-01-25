"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from ucp_store_mocker.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestInitCommand:
    """Tests for the init command."""

    def test_init_grocery(self, runner, temp_dir):
        """Test initializing a grocery store config."""
        output_file = temp_dir / "grocery.yaml"
        result = runner.invoke(cli, [
            "init", "grocery",
            "--name", "Test Grocery",
            "-o", str(output_file),
        ])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Created configuration file" in result.output

    def test_init_electronics(self, runner, temp_dir):
        """Test initializing an electronics store config."""
        output_file = temp_dir / "electronics.yaml"
        result = runner.invoke(cli, [
            "init", "electronics",
            "--name", "Test Electronics",
            "-o", str(output_file),
        ])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_init_invalid_type(self, runner):
        """Test initializing with invalid store type."""
        result = runner.invoke(cli, [
            "init", "invalid_type",
            "--name", "Test Store",
        ])

        assert result.exit_code != 0


class TestListTemplates:
    """Tests for list-templates command."""

    def test_list_templates(self, runner):
        """Test listing available templates."""
        result = runner.invoke(cli, ["list-templates"])

        assert result.exit_code == 0
        assert "grocery" in result.output
        assert "electronics" in result.output
        assert "fashion" in result.output


class TestListCapabilities:
    """Tests for list-capabilities command."""

    def test_list_capabilities(self, runner):
        """Test listing capabilities."""
        result = runner.invoke(cli, ["list-capabilities"])

        assert result.exit_code == 0
        assert "Checkout" in result.output
        assert "Order" in result.output
        assert "Fulfillment" in result.output

    def test_list_core_only(self, runner):
        """Test listing core capabilities only."""
        result = runner.invoke(cli, ["list-capabilities", "--core-only"])

        assert result.exit_code == 0
        assert "Checkout" in result.output


class TestValidateCommand:
    """Tests for validate command."""

    def test_validate_valid_config(self, runner, temp_dir):
        """Test validating a valid config."""
        # First create a config
        config_file = temp_dir / "config.yaml"
        runner.invoke(cli, [
            "init", "grocery",
            "--name", "Test",
            "-o", str(config_file),
        ])

        # Then validate it
        result = runner.invoke(cli, ["validate", str(config_file)])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_nonexistent_file(self, runner):
        """Test validating a nonexistent file."""
        result = runner.invoke(cli, ["validate", "/nonexistent/file.yaml"])

        assert result.exit_code != 0

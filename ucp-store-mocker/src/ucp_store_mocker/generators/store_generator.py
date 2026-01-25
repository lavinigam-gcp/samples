"""Main store generator - orchestrates all generation."""

from pathlib import Path
from typing import Any

from rich.console import Console

from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.generators.server_generator import ServerGenerator
from ucp_store_mocker.generators.data_generator import DataGenerator
from ucp_store_mocker.generators.image_generator import ProductImageGenerator
from ucp_store_mocker.generators.profile_generator import ProfileGenerator
from ucp_store_mocker.generators.a2a_generator import A2AGenerator
from ucp_store_mocker.generators.db_generator import DatabaseGenerator
from ucp_store_mocker.utils.file_utils import ensure_dir, clean_directory, write_file

console = Console()


class StoreGenerator:
    """Main generator that orchestrates all store generation."""

    def __init__(self, config: StoreConfig, output_path: Path, generate_images: bool = False):
        self.config = config
        self.output_path = Path(output_path)
        self.generate_images = generate_images

        # Initialize sub-generators
        self.server_gen = ServerGenerator(config)
        self.data_gen = DataGenerator(config)
        self.profile_gen = ProfileGenerator(config)
        self.db_gen = DatabaseGenerator(config)

        if config.a2a.enabled:
            self.a2a_gen = A2AGenerator(config)
        else:
            self.a2a_gen = None

        if generate_images and config.catalog.images.generate:
            self.image_gen = ProductImageGenerator(config)
        else:
            self.image_gen = None

    def generate(self) -> dict[str, list[str]]:
        """Generate the complete store and return summary of generated files."""
        result = {
            "project": [],
            "server": [],
            "data": [],
            "database": [],
            "a2a": [],
            "images": [],
        }

        # Clean and create output directory
        clean_directory(self.output_path)

        # Generate project files
        result["project"] = self._generate_project_files()

        # Generate data first (products, inventory, etc.)
        console.print("  Generating product catalog...")
        result["data"] = self._generate_data_files()

        # Generate images if enabled
        if self.image_gen:
            console.print("  Generating product images...")
            result["images"] = self._generate_images()

        # Generate server code
        console.print("  Generating server code...")
        result["server"] = self._generate_server_files()

        # Generate database initialization
        console.print("  Generating database...")
        result["database"] = self._generate_database()

        # Generate A2A agent if enabled
        if self.a2a_gen:
            console.print("  Generating A2A agent...")
            result["a2a"] = self._generate_a2a_files()

        return result

    def _generate_project_files(self) -> list[str]:
        """Generate project-level files."""
        files = []

        # pyproject.toml
        pyproject = self._render_pyproject()
        path = write_file(self.output_path / "pyproject.toml", pyproject)
        files.append(str(path))

        # README.md
        readme = self._render_readme()
        path = write_file(self.output_path / "README.md", readme)
        files.append(str(path))

        # .env.example
        env_example = self._render_env_example()
        path = write_file(self.output_path / ".env.example", env_example)
        files.append(str(path))

        # .gitignore
        gitignore = self._render_gitignore()
        path = write_file(self.output_path / ".gitignore", gitignore)
        files.append(str(path))

        return files

    def _generate_data_files(self) -> list[str]:
        """Generate data files (products, inventory, etc.)."""
        files = []
        data_dir = ensure_dir(self.output_path / "data")

        # Generate products
        products = self.data_gen.generate_products()
        products_csv = self._to_csv(products, ["id", "title", "description", "category", "price", "currency", "image_url", "sku"])
        path = write_file(data_dir / "products.csv", products_csv)
        files.append(str(path))

        # Generate variants if variations are enabled
        if self.config.catalog.variations.enabled:
            variants = self.data_gen.generate_variants(products)
            if variants:
                variants_csv = self._to_csv(variants, ["id", "parent_id", "title", "price", "variations", "sku"])
                path = write_file(data_dir / "product_variants.csv", variants_csv)
                files.append(str(path))

        # Generate inventory
        inventory = self.data_gen.generate_inventory(products)
        inventory_csv = self._to_csv(inventory, ["product_id", "quantity", "low_stock_threshold"])
        path = write_file(data_dir / "inventory.csv", inventory_csv)
        files.append(str(path))

        # Generate discount codes
        if self.config.capabilities.discount.enabled:
            discounts = self._generate_discounts()
            discounts_csv = self._to_csv(discounts, ["code", "type", "value", "active"])
            path = write_file(data_dir / "discounts.csv", discounts_csv)
            files.append(str(path))

        # Generate shipping rates if fulfillment enabled
        if self.config.capabilities.fulfillment.enabled:
            shipping = self._generate_shipping_rates()
            shipping_csv = self._to_csv(shipping, ["id", "title", "type", "price", "delivery_days_min", "delivery_days_max"])
            path = write_file(data_dir / "shipping_rates.csv", shipping_csv)
            files.append(str(path))

        # Store products for image generation
        self._products = products

        return files

    def _generate_images(self) -> list[str]:
        """Generate product images using Gemini."""
        if not self.image_gen or not hasattr(self, "_products"):
            return []

        files = []
        images_dir = ensure_dir(self.output_path / "static" / "images")

        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        image_paths = loop.run_until_complete(
            self.image_gen.generate_batch(self._products, images_dir)
        )

        files.extend(image_paths.values())
        return files

    def _generate_server_files(self) -> list[str]:
        """Generate server code files."""
        files = []

        # Generate server package
        server_files = self.server_gen.generate(self.output_path)
        files.extend(server_files)

        # Generate UCP discovery profile
        profile_json = self.profile_gen.generate()
        routes_dir = ensure_dir(self.output_path / "src" / "server" / "routes")
        path = write_file(routes_dir / "discovery_profile.json", profile_json)
        files.append(str(path))

        return files

    def _generate_database(self) -> list[str]:
        """Generate database files."""
        files = []
        db_dir = ensure_dir(self.output_path / "databases")

        # Generate SQLite database initialization script
        init_sql = self.db_gen.generate_init_sql()
        path = write_file(db_dir / "init.sql", init_sql)
        files.append(str(path))

        # Generate import script
        import_script = self.db_gen.generate_import_script()
        scripts_dir = ensure_dir(self.output_path / "src" / "server" / "scripts")
        path = write_file(scripts_dir / "import_csv.py", import_script)
        files.append(str(path))

        return files

    def _generate_a2a_files(self) -> list[str]:
        """Generate A2A agent files."""
        if not self.a2a_gen:
            return []

        files = []
        a2a_files = self.a2a_gen.generate(self.output_path)
        files.extend(a2a_files)
        return files

    def _generate_discounts(self) -> list[dict]:
        """Generate discount code data."""
        discounts = []
        for code_config in self.config.capabilities.discount.codes:
            discounts.append({
                "code": code_config.code,
                "type": code_config.type,
                "value": code_config.value,
                "active": True,
            })
        return discounts

    def _generate_shipping_rates(self) -> list[dict]:
        """Generate shipping rate data."""
        rates = []
        for method in self.config.capabilities.fulfillment.methods:
            for option in method.options:
                delivery_days = option.get("delivery_days", [3, 5])
                rates.append({
                    "id": option["id"],
                    "title": option["title"],
                    "type": method.type,
                    "price": option["price"],
                    "delivery_days_min": delivery_days[0] if delivery_days else 0,
                    "delivery_days_max": delivery_days[1] if len(delivery_days) > 1 else delivery_days[0],
                })
        return rates

    def _render_pyproject(self) -> str:
        """Render pyproject.toml for generated store."""
        store_name = self.config.store.name.lower().replace(" ", "-")
        return f'''[project]
name = "{store_name}"
version = "0.1.0"
description = "UCP Mock Store - {self.config.store.name}"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/server"]
'''

    def _render_readme(self) -> str:
        """Render README.md for generated store."""
        return f'''# {self.config.store.name}

A UCP-compliant mock store generated by ucp-store-mocker.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the server
uv run python -m server
```

## Endpoints

- **UCP Discovery:** `http://localhost:{self.config.server.port}/.well-known/ucp`
- **Health Check:** `http://localhost:{self.config.server.port}/health`

## Configuration

Copy `.env.example` to `.env` and configure as needed.

## Store Type

- **Type:** {self.config.store.type}
- **Port:** {self.config.server.port}

## Generated by

[ucp-store-mocker](https://github.com/anthropics/ucp/tree/main/samples/ucp-store-mocker)
'''

    def _render_env_example(self) -> str:
        """Render .env.example file."""
        lines = [
            "# Server Configuration",
            f"PORT={self.config.server.port}",
            "HOST=0.0.0.0",
            "",
            "# Database",
            "DATABASE_PATH=./databases/store.db",
            "",
        ]

        if self.config.catalog.images.generate:
            lines.extend([
                "# Gemini API (for image generation)",
                "GEMINI_API_KEY=your-api-key-here",
                "",
            ])

        return "\n".join(lines)

    def _render_gitignore(self) -> str:
        """Render .gitignore for generated store."""
        return '''# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Environment
.env

# Databases
*.db
*.sqlite

# IDE
.idea/
.vscode/
'''

    def _to_csv(self, data: list[dict], columns: list[str]) -> str:
        """Convert list of dicts to CSV string."""
        import csv
        import io
        import json

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for row in data:
            # Convert complex types to JSON strings
            processed_row = {}
            for col in columns:
                value = row.get(col, "")
                if isinstance(value, (dict, list)):
                    processed_row[col] = json.dumps(value)
                else:
                    processed_row[col] = value
            writer.writerow(processed_row)

        return output.getvalue()

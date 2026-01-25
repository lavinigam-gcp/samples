"""Multi-store orchestration for running multiple mock stores."""

import yaml
from pathlib import Path
from typing import Any

from ucp_store_mocker.config.schema import StoreConfig, load_config
from ucp_store_mocker.config.validator import validate_multi_store_config
from ucp_store_mocker.generators.store_generator import StoreGenerator


class MultiStoreOrchestrator:
    """Orchestrate generation of multiple stores."""

    def __init__(self, config_path: Path, output_base: Path):
        self.config_path = Path(config_path)
        self.output_base = Path(output_base)
        self.stores: list[dict[str, Any]] = []

        self._load_config()

    def _load_config(self):
        """Load multi-store configuration."""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        errors = validate_multi_store_config(config)
        if errors:
            raise ValueError(f"Invalid multi-store config: {errors}")

        self.stores = config.get("stores", [])
        self.registry_port = config.get("registry", {}).get("port", 9000)

    def generate_all(self) -> dict[str, Path]:
        """Generate all stores and return mapping of names to paths."""
        results = {}

        for i, store_config in enumerate(self.stores):
            name = store_config.get("name", f"store-{i+1}")
            port = store_config.get("port", 8080 + i)

            # Load or build store config
            if "config_file" in store_config:
                config = load_config(Path(store_config["config_file"]))
            else:
                config = StoreConfig(**store_config.get("config", {}))

            # Override port
            config.server.port = port

            # Generate store
            output_path = self.output_base / name
            generator = StoreGenerator(config, output_path)
            generator.generate()

            results[name] = output_path

        # Generate registry if multiple stores
        if len(results) > 1:
            self._generate_registry(results)

        return results

    def _generate_registry(self, stores: dict[str, Path]):
        """Generate a store registry for discovery."""
        registry_path = self.output_base / "registry"
        registry_path.mkdir(parents=True, exist_ok=True)

        # Build registry data
        registry_data = {
            "stores": [
                {
                    "name": name,
                    "url": f"http://localhost:{8080 + i}",
                    "path": str(path),
                }
                for i, (name, path) in enumerate(stores.items())
            ],
        }

        # Write registry JSON
        import json
        registry_file = registry_path / "stores.json"
        with open(registry_file, "w") as f:
            json.dump(registry_data, f, indent=2)

        # Write docker-compose for running all stores
        self._generate_docker_compose(stores, registry_path)

    def _generate_docker_compose(self, stores: dict[str, Path], output_path: Path):
        """Generate docker-compose.yml for all stores."""
        services = {}

        for i, (name, path) in enumerate(stores.items()):
            port = 8080 + i
            services[name] = {
                "build": str(path),
                "ports": [f"{port}:{port}"],
                "environment": [f"PORT={port}"],
            }

        compose = {
            "version": "3.8",
            "services": services,
        }

        compose_file = output_path / "docker-compose.yml"
        with open(compose_file, "w") as f:
            yaml.dump(compose, f, default_flow_style=False)

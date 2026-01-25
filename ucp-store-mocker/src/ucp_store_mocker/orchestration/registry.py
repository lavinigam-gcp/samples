"""Store registry for discovering and managing multiple stores."""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class StoreEntry:
    """Entry in the store registry."""
    name: str
    url: str
    store_type: str
    port: int
    path: Optional[str] = None
    status: str = "unknown"


class StoreRegistry:
    """Registry for managing multiple UCP stores."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.stores: dict[str, StoreEntry] = {}
        self.registry_path = registry_path

        if registry_path and registry_path.exists():
            self._load_registry()

    def _load_registry(self):
        """Load registry from file."""
        registry_file = self.registry_path / "stores.json"
        if registry_file.exists():
            with open(registry_file) as f:
                data = json.load(f)

            for store_data in data.get("stores", []):
                entry = StoreEntry(
                    name=store_data["name"],
                    url=store_data["url"],
                    store_type=store_data.get("type", "unknown"),
                    port=store_data.get("port", 8080),
                    path=store_data.get("path"),
                )
                self.stores[entry.name] = entry

    def register(self, entry: StoreEntry):
        """Register a store."""
        self.stores[entry.name] = entry

    def unregister(self, name: str):
        """Unregister a store."""
        if name in self.stores:
            del self.stores[name]

    def get(self, name: str) -> Optional[StoreEntry]:
        """Get a store by name."""
        return self.stores.get(name)

    def list_stores(self) -> list[StoreEntry]:
        """List all registered stores."""
        return list(self.stores.values())

    def save(self):
        """Save registry to file."""
        if not self.registry_path:
            return

        self.registry_path.mkdir(parents=True, exist_ok=True)
        registry_file = self.registry_path / "stores.json"

        data = {
            "stores": [
                {
                    "name": entry.name,
                    "url": entry.url,
                    "type": entry.store_type,
                    "port": entry.port,
                    "path": entry.path,
                }
                for entry in self.stores.values()
            ]
        }

        with open(registry_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_discovery_urls(self) -> list[str]:
        """Get UCP discovery URLs for all stores."""
        return [f"{entry.url}/.well-known/ucp" for entry in self.stores.values()]

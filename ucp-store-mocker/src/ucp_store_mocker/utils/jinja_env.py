"""Jinja2 environment configuration."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_jinja_env() -> Environment:
    """Create a configured Jinja2 environment for code templates."""
    templates_dir = Path(__file__).parent.parent / "templates" / "code"

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Add custom filters
    env.filters["to_snake_case"] = _to_snake_case
    env.filters["to_camel_case"] = _to_camel_case
    env.filters["to_pascal_case"] = _to_pascal_case
    env.filters["cents_to_dollars"] = _cents_to_dollars

    return env


def _to_snake_case(s: str) -> str:
    """Convert string to snake_case."""
    import re
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.replace("-", "_").replace(" ", "_").lower()


def _to_camel_case(s: str) -> str:
    """Convert string to camelCase."""
    parts = _to_snake_case(s).split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _to_pascal_case(s: str) -> str:
    """Convert string to PascalCase."""
    return "".join(p.capitalize() for p in _to_snake_case(s).split("_"))


def _cents_to_dollars(cents: int) -> str:
    """Convert cents to formatted dollar string."""
    return f"${cents / 100:.2f}"

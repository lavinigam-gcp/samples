"""CLI commands for UCP Store Mocker."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from ucp_store_mocker import __version__
from ucp_store_mocker.config import load_config, validate_config, get_store_defaults
from ucp_store_mocker.generators import StoreGenerator
from ucp_store_mocker.templates.store_types import STORE_TEMPLATES
from ucp_store_mocker.capabilities.registry import CapabilityRegistry
from ucp_store_mocker.orchestration import MultiStoreOrchestrator

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="ucp-store-mocker")
def cli():
    """UCP Store Mocker - Generate UCP-compliant mock stores for developer enablement."""
    pass


@cli.command()
@click.argument("store_type", type=click.Choice(list(STORE_TEMPLATES.keys())))
@click.option("--name", "-n", required=True, help="Name of the store")
@click.option("--output", "-o", default="store_config.yaml", help="Output config file path")
@click.option("--with-a2a/--no-a2a", default=True, help="Include A2A agent configuration")
@click.option("--with-images/--no-images", default=False, help="Configure image generation")
def init(store_type: str, name: str, output: str, with_a2a: bool, with_images: bool):
    """Initialize a new store configuration file.

    STORE_TYPE: Type of store (grocery, electronics, fashion, restaurant, subscription, flower_shop)
    """
    console.print(f"[bold blue]Initializing {store_type} store configuration...[/bold blue]")

    # Get defaults for the store type
    defaults = get_store_defaults(store_type, name, with_a2a=with_a2a, with_images=with_images)

    # Write config file
    output_path = Path(output)
    import yaml
    with open(output_path, "w") as f:
        yaml.dump(defaults, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    console.print(f"[green]✓[/green] Created configuration file: [bold]{output_path}[/bold]")
    console.print("\nNext steps:")
    console.print(f"  1. Edit [bold]{output_path}[/bold] to customize your store")
    console.print(f"  2. Run: [bold]ucp-store-mocker generate-store {output_path}[/bold]")


@cli.command("generate-store")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="./generated-store", help="Output directory for generated store")
@click.option("--generate-images/--no-images", default=False, help="Generate product images with Gemini")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing output directory")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without writing files")
def generate_store(config_file: str, output: str, generate_images: bool, force: bool, dry_run: bool):
    """Generate a UCP-compliant mock store from configuration.

    CONFIG_FILE: Path to the store configuration YAML file
    """
    config_path = Path(config_file)
    output_path = Path(output)

    console.print(Panel.fit(
        f"[bold]Generating UCP Mock Store[/bold]\n"
        f"Config: {config_path}\n"
        f"Output: {output_path}",
        title="UCP Store Mocker"
    ))

    # Load and validate config
    with console.status("[bold green]Loading configuration..."):
        config = load_config(config_path)
        errors = validate_config(config)
        if errors:
            console.print("[red]Configuration errors:[/red]")
            for error in errors:
                console.print(f"  [red]✗[/red] {error}")
            raise click.Abort()

    console.print(f"[green]✓[/green] Configuration loaded: [bold]{config.store.name}[/bold] ({config.store.type})")

    # Check output directory
    if output_path.exists() and not force:
        if not click.confirm(f"Output directory {output_path} exists. Overwrite?"):
            raise click.Abort()

    if dry_run:
        console.print("\n[yellow]Dry run mode - no files will be written[/yellow]")
        _show_generation_plan(config)
        return

    # Generate store
    generator = StoreGenerator(config, output_path, generate_images=generate_images)

    with console.status("[bold green]Generating store..."):
        result = generator.generate()

    # Show results
    console.print("\n[bold green]✓ Store generated successfully![/bold green]\n")

    table = Table(title="Generated Files")
    table.add_column("Category", style="cyan")
    table.add_column("Files", style="green")

    for category, files in result.items():
        table.add_row(category, str(len(files)))

    console.print(table)

    console.print(f"\n[bold]To run your store:[/bold]")
    console.print(f"  cd {output_path}")
    console.print(f"  uv sync")
    console.print(f"  uv run python -m server")


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate(config_file: str):
    """Validate a store configuration file.

    CONFIG_FILE: Path to the store configuration YAML file
    """
    config_path = Path(config_file)

    console.print(f"[bold]Validating configuration:[/bold] {config_path}")

    try:
        config = load_config(config_path)
        errors = validate_config(config)

        if errors:
            console.print("\n[red]Validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]✗[/red] {error}")
            raise click.Abort()

        console.print("\n[green]✓ Configuration is valid![/green]")
        _show_config_summary(config)

    except Exception as e:
        console.print(f"\n[red]Error loading configuration:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("store_dir", type=click.Path(exists=True))
@click.option("--port", "-p", default=8080, help="Port to run the store on")
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
def run(store_dir: str, port: int, host: str):
    """Run a generated mock store.

    STORE_DIR: Path to the generated store directory
    """
    import subprocess
    import sys

    store_path = Path(store_dir)

    console.print(f"[bold]Starting mock store:[/bold] {store_path}")
    console.print(f"Server will be available at: http://{host}:{port}")
    console.print(f"UCP Discovery: http://{host}:{port}/.well-known/ucp\n")

    # Run the store
    try:
        subprocess.run(
            [sys.executable, "-m", "server", "--port", str(port), "--host", host],
            cwd=store_path,
            check=True
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Store stopped[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running store:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="./stores", help="Base output directory")
def orchestrate(config_file: str, output: str):
    """Orchestrate multiple stores from a multi-store configuration.

    CONFIG_FILE: Path to the multi-store configuration YAML file
    """
    config_path = Path(config_file)
    output_path = Path(output)

    console.print(Panel.fit(
        f"[bold]Multi-Store Orchestration[/bold]\n"
        f"Config: {config_path}\n"
        f"Output: {output_path}",
        title="UCP Store Mocker"
    ))

    orchestrator = MultiStoreOrchestrator(config_path, output_path)

    with console.status("[bold green]Generating stores..."):
        results = orchestrator.generate_all()

    console.print(f"\n[bold green]✓ Generated {len(results)} stores![/bold green]")

    for store_name, store_path in results.items():
        console.print(f"  • {store_name}: {store_path}")


@cli.command("list-templates")
def list_templates():
    """List available store type templates."""
    console.print("[bold]Available Store Templates[/bold]\n")

    table = Table()
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Description")
    table.add_column("Default Categories")

    templates_info = {
        "grocery": ("Grocery/Supermarket", "Produce, Dairy, Bakery, Snacks, Beverages"),
        "electronics": ("Electronics Store", "Phones, Laptops, Accessories, Gaming"),
        "fashion": ("Fashion/Apparel", "Mens, Womens, Shoes, Accessories"),
        "restaurant": ("Restaurant/Food Delivery", "Appetizers, Entrees, Desserts, Drinks"),
        "subscription": ("Subscription Service", "Plans, Add-ons"),
        "flower_shop": ("Flower Shop", "Bouquets, Plants, Gifts"),
    }

    for type_name, (desc, categories) in templates_info.items():
        table.add_row(type_name, desc, categories)

    console.print(table)

    console.print("\n[bold]Usage:[/bold]")
    console.print("  ucp-store-mocker init <type> --name 'My Store' -o config.yaml")


@cli.command("list-capabilities")
@click.option("--extended/--core-only", default=True, help="Include extended capabilities")
def list_capabilities(extended: bool):
    """List available UCP capabilities."""
    registry = CapabilityRegistry()

    console.print("[bold]Core UCP Capabilities[/bold]\n")

    core_table = Table()
    core_table.add_column("Capability", style="cyan")
    core_table.add_column("Description")
    core_table.add_column("Configurable")

    for cap in registry.get_core_capabilities():
        core_table.add_row(cap.id, cap.description, "Yes" if cap.configurable else "Always On")

    console.print(core_table)

    if extended:
        console.print("\n[bold]Extended Capabilities[/bold] (Custom implementations)\n")

        ext_table = Table()
        ext_table.add_column("Capability", style="yellow")
        ext_table.add_column("Description")
        ext_table.add_column("Extends")

        for cap in registry.get_extended_capabilities():
            ext_table.add_row(cap.id, cap.description, cap.extends or "-")

        console.print(ext_table)


def _show_generation_plan(config):
    """Show what would be generated without writing files."""
    console.print("\n[bold]Generation Plan:[/bold]")

    console.print(f"\n  Store: {config.store.name}")
    console.print(f"  Type: {config.store.type}")

    console.print("\n  [bold]Capabilities:[/bold]")
    if config.capabilities.checkout.enabled:
        console.print("    • Checkout (Core)")
    if config.capabilities.order.enabled:
        console.print("    • Order Management")
    if config.capabilities.fulfillment.enabled:
        console.print("    • Fulfillment")
    if config.capabilities.discount.enabled:
        console.print("    • Discounts")
    if config.capabilities.wishlist and config.capabilities.wishlist.enabled:
        console.print("    • Wishlist (Extended)")
    if config.capabilities.loyalty and config.capabilities.loyalty.enabled:
        console.print("    • Loyalty (Extended)")

    console.print("\n  [bold]Catalog:[/bold]")
    console.print(f"    • Products: ~{config.catalog.generation.count}")
    if config.catalog.images.generate:
        console.print(f"    • Image generation: {config.catalog.images.model}")

    console.print("\n  [bold]Files to generate:[/bold]")
    console.print("    • pyproject.toml")
    console.print("    • src/server/ (FastAPI server)")
    console.print("    • data/ (CSV data files)")
    console.print("    • databases/ (SQLite)")
    if config.a2a.enabled:
        console.print("    • A2A agent card and handler")


def _show_config_summary(config):
    """Show a summary of the loaded configuration."""
    console.print(f"\n  Store: [bold]{config.store.name}[/bold]")
    console.print(f"  Type: {config.store.type}")
    console.print(f"  Port: {config.server.port}")

    enabled_caps = []
    if config.capabilities.checkout.enabled:
        enabled_caps.append("checkout")
    if config.capabilities.order.enabled:
        enabled_caps.append("order")
    if config.capabilities.fulfillment.enabled:
        enabled_caps.append("fulfillment")
    if config.capabilities.discount.enabled:
        enabled_caps.append("discount")

    console.print(f"  Capabilities: {', '.join(enabled_caps)}")


if __name__ == "__main__":
    cli()

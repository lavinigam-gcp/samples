# UCP Store Mocker

A CLI tool for generating UCP-compliant mock stores for developer enablement. Quickly spin up realistic commerce stores for testing UCP integrations with ADK, A2A, and AP2.

## Quick Start

```bash
# Initialize a grocery store configuration
uvx ucp-store-mocker init grocery --name "My Grocery" -o config.yaml

# Generate the store
uvx ucp-store-mocker generate-store config.yaml -o ./my-store

# Run the store
cd my-store
uv sync
uv run python -m server
```

## Installation

```bash
# Install with pip
pip install ucp-store-mocker

# Or run directly with uvx
uvx ucp-store-mocker --help
```

## Commands

### Initialize Configuration

Create a new store configuration file with sensible defaults:

```bash
ucp-store-mocker init <store-type> --name "Store Name" -o config.yaml
```

**Store Types:**
- `grocery` - Supermarket/grocery store
- `electronics` - Electronics and technology
- `fashion` - Apparel and accessories
- `restaurant` - Food delivery/restaurant
- `subscription` - SaaS subscription service
- `flower_shop` - Flower shop and gifting

### Generate Store

Generate a complete UCP-compliant mock store:

```bash
ucp-store-mocker generate-store config.yaml -o ./output-dir

# With AI-generated product images
ucp-store-mocker generate-store config.yaml -o ./output-dir --generate-images
```

### Validate Configuration

Check a configuration file for errors:

```bash
ucp-store-mocker validate config.yaml
```

### Run Store

Start a generated store server:

```bash
ucp-store-mocker run ./my-store --port 8080
```

### Multi-Store Orchestration

Generate and manage multiple stores:

```bash
ucp-store-mocker orchestrate multi_store.yaml -o ./stores
```

### List Available Resources

```bash
# List store templates
ucp-store-mocker list-templates

# List UCP capabilities
ucp-store-mocker list-capabilities
```

## Configuration Reference

### Basic Structure

```yaml
store:
  name: "My Store"
  type: grocery
  location:
    address:
      street: "123 Main St"
      city: "San Francisco"
      state: "CA"
      postal_code: "94102"
      country: "US"

server:
  port: 8080
  transport:
    rest: true
    a2a: true

capabilities:
  checkout:
    enabled: true
  order:
    enabled: true
  fulfillment:
    enabled: true
    methods:
      - type: shipping
        options:
          - id: standard
            title: "Standard Shipping"
            price: 599
            delivery_days: [3, 5]
      - type: pickup
        options:
          - id: curbside
            title: "Curbside Pickup"
            price: 0
    free_shipping:
      enabled: true
      threshold: 3500
  discount:
    enabled: true
    codes:
      - code: "SAVE10"
        type: percentage
        value: 10

catalog:
  generation:
    strategy: hybrid  # template, faker, or hybrid
    count: 50
    seed: 42
  variations:
    enabled: true
  categories:
    - name: "Fresh Produce"
      count: 15
      price_range: [99, 999]

inventory:
  strategy: realistic  # realistic, unlimited, scarce
  default_quantity: 100
  variance: 0.3

a2a:
  enabled: true
  agent_card:
    name: "Store Agent"
    skills:
      - id: product_search
      - id: checkout
```

## UCP Capabilities

### Core Capabilities

| Capability | Description |
|------------|-------------|
| `dev.ucp.shopping.checkout` | Create, update, complete checkouts |
| `dev.ucp.shopping.order` | Order management with webhooks |
| `dev.ucp.shopping.fulfillment` | Shipping and pickup options |
| `dev.ucp.shopping.discount` | Discount codes and promotions |
| `dev.ucp.shopping.buyer_consent` | GDPR consent management |

### Extended Capabilities

| Capability | Description |
|------------|-------------|
| `dev.ucp.shopping.wishlist` | Save items for later |
| `dev.ucp.shopping.reviews` | Product ratings and reviews |
| `dev.ucp.shopping.loyalty` | Points and rewards |
| `dev.ucp.shopping.gift_cards` | Gift card purchase and redemption |
| `dev.ucp.shopping.subscriptions` | Recurring billing |
| `dev.ucp.shopping.returns` | Return requests and refunds |

## Generated Store Structure

```
my-store/
├── pyproject.toml
├── README.md
├── .env.example
├── databases/
│   └── init.sql
├── data/
│   ├── products.csv
│   ├── inventory.csv
│   └── discounts.csv
├── static/
│   └── images/
├── src/server/
│   ├── __main__.py
│   ├── server.py
│   ├── config.py
│   ├── db.py
│   ├── routes/
│   │   ├── discovery.py
│   │   ├── checkout.py
│   │   └── order.py
│   ├── services/
│   │   ├── checkout_service.py
│   │   └── fulfillment_service.py
│   └── a2a/
│       ├── agent_card.json
│       └── agent.py
└── tests/
```

## Image Generation

Generate product images using Google's Gemini API:

```yaml
catalog:
  images:
    generate: true
    model: "gemini-2.5-flash-image"
    style: "product-photography"
    resolution: "1024x1024"
```

Set your API key:
```bash
export GEMINI_API_KEY="your-api-key"
```

## Product Variations

Configure variations by category:

```yaml
catalog:
  variations:
    enabled: true
    category_variations:
      "Electronics":
        - type: storage
          options: ["64GB", "128GB", "256GB"]
          price_adjustments: [0, 10000, 20000]
        - type: color
          options: ["Black", "Silver"]
          affects_price: false
```

## Testing Your Store

### Verify UCP Discovery

```bash
curl http://localhost:8080/.well-known/ucp | jq .
```

### Create a Checkout

```bash
curl -X POST http://localhost:8080/checkout \
  -H "Content-Type: application/json" \
  -d '{"buyer_id": "test-buyer"}'
```

### Run Conformance Tests

```bash
cd ../conformance
uv run checkout_lifecycle_test.py --server_url=http://localhost:8080
```

## Examples

See the `examples/` directory for complete configuration examples:

- `grocery_store.yaml` - Full-featured grocery store
- `electronics_store.yaml` - Electronics with variations
- `fashion_store.yaml` - Fashion with wishlist
- `restaurant.yaml` - Restaurant/food delivery
- `subscription_service.yaml` - SaaS subscriptions
- `multi_store.yaml` - Multi-store orchestration

## Development

```bash
# Clone and install
git clone https://github.com/anthropics/ucp.git
cd samples/ucp-store-mocker
uv sync

# Run tests
uv run pytest

# Run locally
uv run ucp-store-mocker --help
```

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

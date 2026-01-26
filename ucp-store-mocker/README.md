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

The UCP conformance test suite validates protocol compliance. Run all tests:

```bash
cd /path/to/ucp-work/conformance

# Run individual test suites
uv run checkout_lifecycle_test.py --server_url=http://localhost:8080
uv run business_logic_test.py --server_url=http://localhost:8080
uv run validation_test.py --server_url=http://localhost:8080
uv run fulfillment_test.py --server_url=http://localhost:8080
uv run order_test.py --server_url=http://localhost:8080
uv run protocol_test.py --server_url=http://localhost:8080
uv run idempotency_test.py --server_url=http://localhost:8080
uv run webhook_test.py --server_url=http://localhost:8080

# For webhook tests, you need to set the simulation secret
SIMULATION_SECRET=test_secret uv run python -m server  # Start server with secret
uv run webhook_test.py --server_url=http://localhost:8080 --simulation_secret=test_secret

# Use store-specific test data
uv run fulfillment_test.py \
  --server_url=http://localhost:8080 \
  --conformance_input=/path/to/store/data/conformance_input.json
```

---

## Conformance Test Suite

The UCP conformance tests validate that a store correctly implements the Universal Commerce Protocol. The standard test suite contains **50 tests** across 8 categories.

### Test Categories

| Category | Tests | Description | Importance |
|----------|-------|-------------|------------|
| `checkout_lifecycle` | 11 | Create, retrieve, update, complete, cancel checkouts | 🔴 **Critical** |
| `business_logic` | 8 | Totals calculation, discounts, buyer consent | 🔴 **Critical** |
| `validation` | 6 | Error handling for out-of-stock, invalid products, payment failures | 🔴 **Critical** |
| `fulfillment` | 11 | Shipping addresses, delivery options, free shipping | 🟡 Important |
| `order` | 4 | Order retrieval and fulfillment persistence | 🟡 Important |
| `protocol` | 3 | Discovery endpoint, version negotiation | 🔴 **Critical** |
| `idempotency` | 4 | Duplicate request handling | 🟡 Important |
| `webhook` | 3 | Order event notifications (placed, shipped) | 🟢 Optional |

### Test Importance Levels

- 🔴 **Critical** - Must pass for UCP compliance. These validate core protocol requirements.
- 🟡 **Important** - Should pass for production stores. May fail for specialized configurations.
- 🟢 **Optional** - Nice to have. Failure is acceptable for certain store types.

### Individual Tests Reference

<details>
<summary><b>checkout_lifecycle_test.py (11 tests) - 🔴 Critical</b></summary>

| Test | Description |
|------|-------------|
| `test_create_checkout` | Create a new checkout session |
| `test_get_checkout` | Retrieve an existing checkout |
| `test_update_checkout` | Update items in a checkout |
| `test_cancel_checkout` | Cancel a checkout session |
| `test_complete_checkout` | Complete checkout with payment |
| `test_cancel_is_idempotent` | Multiple cancel calls succeed |
| `test_cannot_update_canceled_checkout` | Updates fail on canceled checkouts |
| `test_cannot_complete_canceled_checkout` | Completion fails on canceled checkouts |
| `test_complete_is_idempotent` | Multiple complete calls succeed |
| `test_cannot_update_completed_checkout` | Updates fail on completed checkouts |
| `test_cannot_cancel_completed_checkout` | Cancel fails on completed checkouts |

</details>

<details>
<summary><b>business_logic_test.py (8 tests) - 🔴 Critical</b></summary>

| Test | Description |
|------|-------------|
| `test_totals_calculation_on_create` | Line items sum correctly on checkout creation |
| `test_totals_recalculation_on_update` | Totals update when items change |
| `test_discount_flow` | Percentage discount codes apply correctly |
| `test_multiple_discounts_accepted` | Multiple valid discount codes work |
| `test_multiple_discounts_one_rejected` | Invalid code rejected, valid ones apply |
| `test_fixed_amount_discount` | Fixed-amount discounts subtract correctly |
| `test_buyer_consent` | Marketing consent tracking works |
| `test_buyer_info_persistence` | Buyer information persists across sessions |

</details>

<details>
<summary><b>validation_test.py (6 tests) - 🔴 Critical</b></summary>

| Test | Description |
|------|-------------|
| `test_out_of_stock` | Proper error for out-of-stock items |
| `test_update_inventory_validation` | Inventory checks on checkout update |
| `test_product_not_found` | Proper error for non-existent products |
| `test_payment_failure` | Graceful handling of payment failures |
| `test_complete_without_fulfillment` | Error when completing without shipping |
| `test_structured_error_messages` | Error responses have proper structure |

</details>

<details>
<summary><b>fulfillment_test.py (11 tests) - 🟡 Important</b></summary>

| Test | Description |
|------|-------------|
| `test_fulfillment_flow` | Complete shipping selection flow |
| `test_dynamic_fulfillment` | Shipping rates update with address |
| `test_unknown_customer_no_address` | New customer address prompt |
| `test_known_customer_no_address` | Known customer address list |
| `test_known_customer_one_address` | Auto-select single saved address |
| `test_known_customer_multiple_addresses_selection` | Choose from multiple addresses |
| `test_known_customer_new_address` | Add new address for known customer |
| `test_new_user_new_address_persistence` | New addresses save correctly |
| `test_known_user_existing_address_reuse` | Saved addresses work across sessions |
| `test_free_shipping_on_expensive_order` | Free shipping threshold applies |
| `test_free_shipping_for_specific_item` | Item-specific promotions work |

</details>

<details>
<summary><b>order_test.py (4 tests) - 🟡 Important</b></summary>

| Test | Description |
|------|-------------|
| `test_order_retrieval` | Retrieve order after checkout completion |
| `test_order_fulfillment_retrieval` | Order includes fulfillment details |
| `test_order_update` | Order status updates correctly |
| `test_order_adjustments` | Post-purchase adjustments work |

</details>

<details>
<summary><b>protocol_test.py (3 tests) - 🔴 Critical</b></summary>

| Test | Description |
|------|-------------|
| `test_discovery` | `/.well-known/ucp` returns valid profile |
| `test_discovery_urls` | All URLs in profile are accessible |
| `test_version_negotiation` | Server rejects unsupported UCP versions |

</details>

<details>
<summary><b>idempotency_test.py (4 tests) - 🟡 Important</b></summary>

| Test | Description |
|------|-------------|
| `test_idempotency_create` | Same Idempotency-Key returns same checkout |
| `test_idempotency_update` | Duplicate updates are idempotent |
| `test_idempotency_complete` | Duplicate completions are idempotent |
| `test_idempotency_cancel` | Duplicate cancellations are idempotent |

</details>

<details>
<summary><b>webhook_test.py (3 tests) - 🟢 Optional</b></summary>

| Test | Description |
|------|-------------|
| `test_webhook_event_stream` | Order placed event fires on completion |
| `test_webhook_order_address_known_customer` | Webhook includes shipping for known customers |
| `test_webhook_order_address_new_address` | Webhook includes shipping for new addresses |

</details>

---

## Examples & Test Results

### Example Store Configurations

| Store | Type | Port | Config File | Key Features |
|-------|------|------|-------------|--------------|
| **electronics_store** | Electronics | 8080 | `electronics_store.yaml` | Product variations (storage, color) |
| **fashion_store** | Fashion | 8081 | `fashion_store.yaml` | Wishlists, size variations |
| **flower_shop** | Flower Shop | 8082 | `flower_shop.yaml` | Gift options, delivery dates |
| **grocery_store** | Grocery | 8084 | `grocery_store.yaml` | Perishables, inventory limits |
| **multi_store** | Multi-tenant | 8085 | `multi_store.yaml` | Multiple stores orchestration |
| **restaurant** | Restaurant | 8083 | `restaurant.yaml` | Delivery/pickup, meal customization |
| **subscription_service** | SaaS | 8086 | `subscription_service.yaml` | Recurring billing, no fulfillment |

### Conformance Test Results by Store

| Store | Passing | Status | Notes |
|-------|---------|--------|-------|
| **electronics_store** | 50/50 | ✅ Full Compliance | Standard configuration |
| **fashion_store** | 50/50 | ✅ Full Compliance | Standard configuration |
| **flower_shop** | 50/50 | ✅ Full Compliance | Standard configuration |
| **grocery_store** | 50/50 | ✅ Full Compliance | Standard configuration |
| **multi_store** | 50/50 | ✅ Full Compliance | Standard configuration |
| **restaurant** | 41/50 | ⚠️ Partial | Custom discounts, unlimited inventory |
| **subscription_service** | 0/50 | ⚠️ Expected | Fulfillment disabled by design |

### Detailed Test Matrix

| Test Category | electronics | fashion | flower | grocery | multi | restaurant | subscription |
|--------------|:-----------:|:-------:|:------:|:-------:|:-----:|:----------:|:------------:|
| checkout_lifecycle (11) | ✅ 11 | ✅ 11 | ✅ 11 | ✅ 11 | ✅ 11 | ✅ 11 | ❌ 0 |
| business_logic (8) | ✅ 8 | ✅ 8 | ✅ 8 | ✅ 8 | ✅ 8 | ⚠️ 4 | ❌ 0 |
| validation (6) | ✅ 6 | ✅ 6 | ✅ 6 | ✅ 6 | ✅ 6 | ⚠️ 4 | ❌ 0 |
| fulfillment (11) | ✅ 11 | ✅ 11 | ✅ 11 | ✅ 11 | ✅ 11 | ✅ 11 | ❌ 0 |
| order (4) | ✅ 4 | ✅ 4 | ✅ 4 | ✅ 4 | ✅ 4 | ✅ 4 | ❌ 0 |
| protocol (3) | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | ❌ 0 |
| idempotency (4) | ✅ 4 | ✅ 4 | ✅ 4 | ✅ 4 | ✅ 4 | ✅ 4 | ❌ 0 |
| webhook (3) | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | ✅ 3 | ❌ 0 |

---

## Creating UCP-Compliant Stores

### Requirements for Full Conformance (50/50)

To pass all 50 conformance tests, your store configuration must include:

#### 1. Standard Discount Codes
```yaml
capabilities:
  discount:
    enabled: true
    codes:
      - code: "10OFF"
        type: percentage
        value: 10
      - code: "WELCOME20"
        type: percentage
        value: 20
      - code: "FIXED500"
        type: fixed
        value: 500
```

#### 2. Realistic Inventory (with out-of-stock items)
```yaml
inventory:
  strategy: realistic  # NOT "unlimited"
  default_quantity: 100
  variance: 0.3
```

#### 3. Fulfillment with Free Shipping
```yaml
capabilities:
  fulfillment:
    enabled: true  # Must be true
    methods:
      - type: shipping
        options:
          - id: standard
            title: "Standard Shipping"
            price: 599
            delivery_days: [3, 5]
    free_shipping:
      enabled: true
      threshold: 3500  # Cents
```

#### 4. Webhooks Enabled
```yaml
capabilities:
  order:
    enabled: true
    webhooks:
      enabled: true
```

### Minimal UCP-Compliant Configuration

```yaml
store:
  name: "My Compliant Store"
  type: grocery

server:
  port: 8080
  transport:
    rest: true

capabilities:
  checkout:
    enabled: true
  order:
    enabled: true
    webhooks:
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
    free_shipping:
      enabled: true
      threshold: 3500
  discount:
    enabled: true
    codes:
      - code: "10OFF"
        type: percentage
        value: 10
      - code: "WELCOME20"
        type: percentage
        value: 20
      - code: "FIXED500"
        type: fixed
        value: 500

catalog:
  generation:
    strategy: template
    count: 50

inventory:
  strategy: realistic
  default_quantity: 100
```

---

## Understanding Test Failures

### When Custom Configurations Cause Failures

If you customize your store configuration, expect certain tests to fail:

| Configuration Change | Tests That Will Fail | Why |
|---------------------|---------------------|-----|
| `fulfillment.enabled: false` | All fulfillment, order, webhook tests | Shipping is required for these tests |
| `inventory.strategy: unlimited` | `test_out_of_stock`, `test_update_inventory_validation` | No out-of-stock scenarios possible |
| Custom discount codes | `test_discount_flow`, `test_multiple_discounts_*`, `test_fixed_amount_discount` | Tests expect specific codes |
| `webhooks.enabled: false` | All webhook tests | No event notifications |
| Different shipping options | `test_order_fulfillment_retrieval` | Expectation title mismatch |

### Acceptable Failure Scenarios

These failures are **acceptable** based on your store's business model:

| Store Type | Expected Failures | Reason |
|------------|------------------|--------|
| **Digital-only / SaaS** | All fulfillment tests | No physical shipping |
| **Restaurant** | Inventory validation | Restaurants often have unlimited inventory |
| **Custom promotions** | Discount tests | Using your own promo codes |
| **No webhooks** | Webhook tests | Not implementing event streaming |

### Tests That Should ALWAYS Pass

Regardless of configuration, these tests should pass for UCP compliance:

1. **Protocol Tests** (3 tests)
   - `test_discovery` - Your `/.well-known/ucp` endpoint must work
   - `test_discovery_urls` - All URLs in your profile must be accessible
   - `test_version_negotiation` - Must reject unsupported UCP versions

2. **Core Checkout** (5 tests)
   - `test_create_checkout`
   - `test_get_checkout`
   - `test_update_checkout`
   - `test_cancel_checkout`
   - `test_complete_checkout`

3. **Idempotency** (4 tests)
   - All idempotency tests ensure proper duplicate request handling

---

## Troubleshooting Test Failures

### Common Issues and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `connection refused` | Server not running | Start server with `uv run python -m server` |
| `unsupported_version` | Wrong UCP version | Use UCP-Agent header with version `2026-01-11` |
| `403 Forbidden` on simulate | Missing secret | Set `SIMULATION_SECRET` env var |
| `out_of_stock` on wrong item | Inventory mismatch | Use `--conformance_input` flag |
| Webhook tests fail | No webhook URL | Ensure agent profile has `webhook_url` |

### Running Tests with Custom Data

Each generated store includes a `data/conformance_input.json` file with store-specific test data:

```json
{
  "currency": "USD",
  "items": [
    {
      "id": "conformance_test_item",
      "title": "Conformance Test Item",
      "price": 3500
    }
  ],
  "out_of_stock_item": {
    "id": "laptops-004",
    "title": "UltraBook Laptops Item X1"
  },
  "free_shipping_item": {
    "id": "conformance_test_item",
    "title": "Conformance Test Item",
    "price": 3500
  }
}
```

Use this file for accurate testing:

```bash
uv run fulfillment_test.py \
  --server_url=http://localhost:8080 \
  --conformance_input=/path/to/store/data/conformance_input.json
```

---

## Additional Test Suites

Beyond the standard 50 tests, additional specialized tests are available:

| Test File | Tests | Description |
|-----------|-------|-------------|
| `binding_test.py` | 1 | Token binding for payment credentials |
| `ap2_test.py` | 1 | Apple Pay 2 mandate support |
| `card_credential_test.py` | 1 | Card payment processing |
| `simulation_url_security_test.py` | 3 | Simulation endpoint security |
| `invalid_input_test.py` | 3 | Malformed request handling |

Run these for comprehensive validation:

```bash
uv run binding_test.py --server_url=http://localhost:8080
uv run card_credential_test.py --server_url=http://localhost:8080
uv run simulation_url_security_test.py --server_url=http://localhost:8080 --simulation_secret=test_secret
```

---

## Examples

See the `examples/` directory for complete configuration examples:

- `grocery_store.yaml` - Full-featured grocery store (50/50 tests)
- `electronics_store.yaml` - Electronics with variations (50/50 tests)
- `fashion_store.yaml` - Fashion with wishlist (50/50 tests)
- `flower_shop.yaml` - Flower shop with gift options (50/50 tests)
- `restaurant.yaml` - Restaurant/food delivery (41/50 - custom config)
- `subscription_service.yaml` - SaaS subscriptions (0/50 - no fulfillment)
- `multi_store.yaml` - Multi-store orchestration (50/50 tests)

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

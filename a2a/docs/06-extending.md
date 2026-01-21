# Extending the Sample

## TL;DR

- **Add tool**: Define function in `agent.py`, add to `root_agent.tools`
- **Add product**: Edit `data/products.json`, add image to `data/images/`
- **Add capability**: Update profiles, type generator, and relevant tools

## Add a New Tool

### Step 1: Define the Tool

```python
# agent.py

def apply_discount(tool_context: ToolContext, promo_code: str) -> dict:
    """Apply a promotional code to the current checkout.

    Args:
        promo_code: The promotional code to apply (e.g., "SAVE10")

    Returns:
        Updated checkout with discount applied
    """
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)
    metadata = tool_context.state.get(ADK_UCP_METADATA_STATE)

    if not checkout_id:
        return _create_error_response("No active checkout")

    try:
        checkout = store.apply_discount(checkout_id, promo_code)
        return {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "success"
        }
    except ValueError as e:
        return _create_error_response(str(e))
```

### Step 2: Add to Agent

```python
# agent.py:455

root_agent = Agent(
    name="shopper_agent",
    model="gemini-3-flash-preview",
    tools=[
        search_shopping_catalog,
        add_to_checkout,
        remove_from_checkout,
        update_checkout,
        get_checkout,
        start_payment,
        update_customer_details,
        complete_checkout,
        apply_discount,  # NEW
    ],
    ...
)
```

### Step 3: Implement Store Method

```python
# store.py

def apply_discount(self, checkout_id: str, promo_code: str) -> Checkout:
    checkout = self._checkouts.get(checkout_id)
    if not checkout:
        raise ValueError("Checkout not found")

    # Validate promo code
    discount = self._validate_promo(promo_code)

    # Apply to checkout
    checkout.discounts = [discount]
    self._recalculate_checkout(checkout)

    return checkout
```

## Add Products

### Step 1: Edit products.json

```json
// data/products.json
{
  "productID": "SNACK-007",
  "sku": "SNACK-007",
  "name": "Organic Trail Mix",
  "@type": "Product",
  "image": ["http://localhost:10999/images/trail_mix.jpg"],
  "brand": {
    "name": "Nature's Best",
    "@type": "Brand"
  },
  "offers": {
    "price": "6.99",
    "priceCurrency": "USD",
    "availability": "InStock",
    "itemCondition": "NewCondition",
    "@type": "Offer"
  },
  "description": "A healthy mix of nuts and dried fruits",
  "gtin": "0123456789012",
  "mpn": "NB-TM-001",
  "category": "Food > Snacks > Trail Mix"
}
```

### Step 2: Add Image

Place `trail_mix.jpg` in `business_agent/src/business_agent/data/images/`

### Step 3: Restart Server

```bash
cd a2a/business_agent
uv run business_agent
```

## Custom Payment Handler

### Step 1: Update Merchant Profile

```json
// data/ucp.json
{
  "payment": {
    "handlers": [
      {
        "id": "stripe_handler",
        "name": "stripe.payment.provider",
        "version": "2026-01-11",
        "config": {
          "business_id": "acct_123456"
        }
      }
    ]
  }
}
```

### Step 2: Update Client Profile

```json
// chat-client/profile/agent_profile.json
{
  "payment": {
    "handlers": [
      {
        "id": "stripe_handler",
        "name": "stripe.payment.provider"
      }
    ]
  }
}
```

### Step 3: Implement Processor

```python
# payment_processor.py

class StripePaymentProcessor:
    async def process_payment(
        self,
        payment_data: PaymentInstrument,
        risk_data: dict | None = None
    ) -> Task:
        # Call Stripe API
        result = await stripe.PaymentIntent.create(
            amount=checkout.totals[-1].amount,
            currency=checkout.currency.lower(),
            payment_method=payment_data.credential.token
        )

        return Task(
            state=TaskState.completed if result.status == "succeeded"
                  else TaskState.failed
        )
```

## Add UCP Capability

### Step 1: Update Profiles

```json
// data/ucp.json - add to capabilities
{
  "name": "dev.ucp.shopping.loyalty",
  "version": "2026-01-11",
  "extends": "dev.ucp.shopping.checkout"
}
```

### Step 2: Update Type Generator

```python
# helpers/type_generator.py

if "dev.ucp.shopping.loyalty" in active_capability_names:
    selected_base_models.append(LoyaltyCheckout)
```

### Step 3: Create Checkout Type

```python
# In your models or type_generator.py

class LoyaltyCheckout(Checkout):
    loyalty_points: int | None = None
    rewards: list[Reward] | None = None
```

## Modify Checkout Flow

### Change Tax Calculation

```python
# store.py:_recalculate_checkout

# Instead of flat 10%
tax_rate = self._get_tax_rate(checkout.fulfillment.destination.address)
tax = int(subtotal * tax_rate)
```

### Add Minimum Order

```python
# store.py:start_payment

def start_payment(self, checkout_id: str) -> Checkout | str:
    checkout = self._checkouts.get(checkout_id)

    # Add minimum order check
    subtotal = next(t for t in checkout.totals if t.type == "subtotal").amount
    if subtotal < 1000:  # $10 minimum
        return "Minimum order is $10.00"

    # ... rest of validation
```

### Custom Fulfillment Options

```python
# store.py:_get_fulfillment_options

def _get_fulfillment_options(self, address: PostalAddress) -> list:
    options = [
        FulfillmentOptionResponse(name="Standard", price=500),
        FulfillmentOptionResponse(name="Express", price=1000),
    ]

    # Add same-day for local addresses
    if self._is_local(address):
        options.append(
            FulfillmentOptionResponse(name="Same Day", price=1500)
        )

    return options
```

# Operations

## Quick Start Commands

```bash
# Backend
cd a2a/business_agent
uv sync
cp env.example .env          # Add GOOGLE_API_KEY
uv run business_agent        # Starts on :10999

# Frontend
cd a2a/chat-client
npm install
npm run dev                  # Starts on :3000

# Verify
curl http://localhost:10999/.well-known/agent-card.json
curl http://localhost:10999/.well-known/ucp
```

## Manual Test Scenarios

### Happy Path

1. Open http://localhost:3000
2. Type "show me cookies"
3. Click "Add to Checkout" on a product
4. Enter email when prompted: `test@example.com`
5. Enter address: `123 Main St, San Francisco, CA 94105`
6. Click "Complete Payment"
7. Select a payment method
8. Click "Confirm Purchase"
9. Verify order confirmation appears

### Error Cases

| Scenario | Test | Expected |
|----------|------|----------|
| No checkout | Call `get_checkout` first | "Checkout not created" error |
| Missing address | Skip address, call `start_payment` | Prompt for address |
| Missing email | Skip email, call `start_payment` | Prompt for email |
| Invalid product | `add_to_checkout("INVALID-ID", 1)` | Product not found error |

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Server won't start | Missing `GOOGLE_API_KEY` | Add key to `.env` file |
| "Profile fetch failed" | Client not running | Start chat-client on :3000 |
| "Version unsupported" | Profile version mismatch | Align versions in both profiles |
| "Checkout not found" | Session expired | Add item first with `add_to_checkout` |
| UI not updating | State not refreshing | Check contextId in response |
| "Missing UCP metadata" | Header not sent | Verify `UCP-Agent` header |

## Debugging Tips

### Enable Verbose Logging

```python
# main.py - add at top
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Tool State

```python
# In any tool
def my_tool(tool_context: ToolContext, param: str) -> dict:
    print("State:", dict(tool_context.state))
    print("Checkout ID:", tool_context.state.get(ADK_USER_CHECKOUT_ID))
    # ...
```

### Check A2A Messages

```typescript
// App.tsx - in handleSendMessage
console.log("Request:", JSON.stringify(request, null, 2));
console.log("Response:", JSON.stringify(data, null, 2));
```

### Verify Endpoints

```bash
# Agent card (A2A discovery)
curl -s http://localhost:10999/.well-known/agent-card.json | jq .

# UCP profile
curl -s http://localhost:10999/.well-known/ucp | jq .

# Client profile
curl -s http://localhost:3000/profile/agent_profile.json | jq .
```

### Test A2A Directly

```bash
curl -X POST http://localhost:10999/ \
  -H "Content-Type: application/json" \
  -H "UCP-Agent: profile=\"http://localhost:3000/profile/agent_profile.json\"" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "show me products"}]
      }
    }
  }'
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GOOGLE_API_KEY` | Yes | Gemini API access |

## Ports

| Service | Port | URL |
|---------|------|-----|
| Backend | 10999 | http://localhost:10999 |
| Frontend | 3000 | http://localhost:3000 |

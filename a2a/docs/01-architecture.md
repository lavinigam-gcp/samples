# System Architecture

## TL;DR

- **4 layers**: A2A Server → Agent Executor → ADK Agent → Retail Store
- **2 protocols**: A2A (agent communication) + UCP (commerce data)
- **Request flow**: JSON-RPC → ADK Runner → Tool execution → Response

## System Overview

```mermaid
graph TB
    subgraph Client["Chat Client (React)"]
        UI[User Interface]
        A2AClient[A2A Client]
        CPP[CredentialProviderProxy]
    end

    subgraph Server["Cymbal Retail Agent (Python)"]
        A2AServer[A2A Starlette Server]
        Exec[ADKAgentExecutor]
        ProfileRes[ProfileResolver]

        subgraph ADK["ADK Layer"]
            Runner[Runner]
            Agent[Agent + 8 Tools]
            Session[Session Service]
        end

        subgraph Business["Business Layer"]
            Store[RetailStore]
            PayProc[MockPaymentProcessor]
        end
    end

    UI --> A2AClient
    A2AClient -->|JSON-RPC + UCP-Agent header| A2AServer
    A2AServer --> Exec
    Exec --> ProfileRes
    Exec --> Runner
    Runner --> Agent
    Agent --> Store
    Agent --> PayProc
    CPP --> UI
```

## Components

### Backend

| Component | File | Responsibility |
|-----------|------|----------------|
| A2A Server | `main.py` | HTTP server, routing, static files |
| Agent Executor | `agent_executor.py` | Bridge A2A ↔ ADK, session management |
| Profile Resolver | `ucp_profile_resolver.py` | UCP capability negotiation |
| ADK Agent | `agent.py` | LLM reasoning, tool execution |
| Retail Store | `store.py` | Products, checkouts, orders |
| Payment Processor | `payment_processor.py` | Mock payment handling |

### Frontend

| Component | File | Responsibility |
|-----------|------|----------------|
| App | `App.tsx` | State management, A2A messaging |
| ChatMessage | `components/ChatMessage.tsx` | Message rendering |
| Checkout | `components/Checkout.tsx` | Checkout display |
| ProductCard | `components/ProductCard.tsx` | Product cards |
| PaymentMethodSelector | `components/PaymentMethodSelector.tsx` | Payment selection |

## Request Flow

```mermaid
sequenceDiagram
    participant UI as React UI
    participant A2A as A2A Server
    participant Exec as AgentExecutor
    participant Agent as ADK Agent
    participant Store as RetailStore

    UI->>A2A: POST / (JSON-RPC + UCP-Agent header)
    A2A->>Exec: execute(context, queue)

    Note over Exec: 1. Resolve UCP profile
    Note over Exec: 2. Prepare input
    Note over Exec: 3. Get/create session

    Exec->>Agent: Runner.run_async()

    loop Tool Execution
        Agent->>Store: Tool call (e.g., add_to_checkout)
        Store-->>Agent: Result (Checkout)
        Note over Agent: after_tool_callback
    end

    Agent-->>Exec: Final response
    Note over Exec: after_agent_callback
    Exec-->>A2A: Parts[] (text + data)
    A2A-->>UI: JSON-RPC response
```

## Layer Responsibilities

| Layer | Input | Output | Key Class |
|-------|-------|--------|-----------|
| **A2A Server** | HTTP request | HTTP response | `A2AStarletteApplication` |
| **Agent Executor** | A2A context | Event queue | `ADKAgentExecutor` |
| **ADK Agent** | User query + state | Tool results | `Agent` (google.adk) |
| **Retail Store** | Method calls | Domain objects | `RetailStore` |

## Data Storage

All data is **in-memory** (mock implementation):

```python
class RetailStore:
    _products: dict[str, Product]    # Loaded from products.json
    _checkouts: dict[str, Checkout]  # Session-based
    _orders: dict[str, Checkout]     # Completed orders
```

## Discovery Endpoints

| Endpoint | Purpose | Source |
|----------|---------|--------|
| `/.well-known/agent-card.json` | A2A agent capabilities | `data/agent_card.json` |
| `/.well-known/ucp` | UCP merchant profile | `data/ucp.json` |
| `/images/*` | Product images | `data/images/` |

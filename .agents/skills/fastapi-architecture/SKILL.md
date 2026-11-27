---
name: fastapi-architecture
description: Design or revise boundaries in this FastAPI research RAG API. Use for "design the FastAPI architecture", "organize routers and services", "decide where this logic belongs", or a new domain or integration. Do not use for a single endpoint edit with no structural decision.
license: CC-BY-4.0
metadata:
  author: research-rag-api contributors
  version: 1.0.0
---

# FastAPI Architecture

Choose the smallest structure that keeps the API contract, domain rules, persistence, and external services understandable and testable.

## Instructions

### 1. Read existing constraints

Inspect the current tree and relevant entries in `docs/decisoes.md` and `docs/fases.md`. Treat accepted decisions as the baseline, identify superseded decisions, and distinguish settled choices from pending ones. The agreed direction is domain organization (`accounts`, `knowledge`, `chat`), Pydantic HTTP contracts, PostgreSQL application state, and OpenAI File Search callable from routes and CLI code. Check code before treating a planned component as implemented.

### 2. Trace one use case

Describe the request-to-response path and assign responsibilities:

| Responsibility | Default location |
|---|---|
| HTTP parsing, status, response contract | FastAPI route and Pydantic models |
| Reusable business rule or use case | Domain service or plain function |
| Database queries and transaction | Persistence boundary chosen for the phase |
| OpenAI request and result mapping | Integration service with an explicit contract |

Introduce a boundary when it enables reuse, isolates an external effect, or removes concrete coupling. Keep the current layout otherwise. Use `APIRouter` when a domain has enough routes to benefit from separate registration; see FastAPI's [multiple-file guide](https://fastapi.tiangolo.com/tutorial/bigger-applications/).

### 3. Specify contracts and failures

For each boundary, specify input, output, error translation, and ownership of state. Keep API schemas distinct from persistence models when they evolve for different reasons. Place ownership checks where every protected operation crosses. Choose `def` or `async def` based on the actual I/O library; consult the [FastAPI async guide](https://fastapi.tiangolo.com/async/) when unclear.

For RAG, preserve the selected system's vector-store isolation, saved conversation as the source of history, and a response that can include book and retrieved excerpt. If a request changes one of these, document a replacement decision rather than silently rewriting the old one.

### 4. Produce a concrete result

For design requests, provide a compact module map, one request flow, significant tradeoffs, and the next thin slice. For implementation requests, make the code change and test the affected contract. Record a durable change with the next decision number; mark its predecessor as superseded when applicable.

## Examples

- User: "Where should the OpenAI call go?" Result: a service called by the chat use case, with an input/output contract and a test replacement; the route owns HTTP concerns.
- User: "Split the app into modules." Result: a domain router and service map based on existing features, followed by a small move that preserves route behavior and a passing API test if implementation was requested.

## Common issues

- If two modules import each other, move their shared contract to the boundary that owns it instead of using runtime import tricks.
- If a proposed layer has no current responsibility, omit it and state what would justify adding it later.

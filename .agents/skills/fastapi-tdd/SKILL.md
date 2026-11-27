---
name: fastapi-tdd
description: Drive a FastAPI behavior change in this project with a red-green-refactor cycle. Use for "TDD", "write the test first", "add tests for this endpoint", or a behavior change needing regression coverage. Do not use for design-only discussion or tests that mirror implementation details.
license: CC-BY-4.0
metadata:
  author: research-rag-api contributors
  version: 1.0.0
---

# FastAPI TDD

Test observable behavior first, implement the smallest change that satisfies it, and improve the code while the test stays green.

## Instructions

### 1. Define one behavior

Turn the request into an HTTP or domain contract: input, expected output or status, and a relevant failure. Read nearby tests for local conventions. When a user is practicing, ask them to propose the behavior or first test before giving code unless they explicitly request implementation.

Use a plain unit test for a domain rule and `fastapi.testclient.TestClient` for validation, dependency wiring, status, and serialized response. Test the public contract rather than helper names or internal call order. See the [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/).

### 2. Red

Write one focused failing test and run `uv run pytest path/to/test_file.py -q`. Confirm it fails for the intended missing behavior. A collection error, syntax error, missing optional service, or unavailable network is a setup problem to fix before treating the test as red.

For routes, assert the expected status and relevant JSON fields. Avoid assertions such as `status_code != 422` when the contract expects `200`. Call `response.json()` when comparing the body.

### 3. Green and refactor

Implement only what the failing test requires. Run the focused test until it passes. Refactor confusing ownership or duplication without changing the contract, then rerun the focused test and `uv run pytest`. Add another test for a distinct boundary or failure rather than repeating the same assertion across many inputs.

Replace external services at their boundary. For a FastAPI dependency, use `app.dependency_overrides` and restore it after the test; see the [dependency override guide](https://fastapi.tiangolo.com/advanced/testing-dependencies/). Use a test database or replaceable repository for persistence and a fake OpenAI service for normal tests. If startup is part of the behavior, use `TestClient` as a context manager as in the [lifespan testing guide](https://fastapi.tiangolo.com/advanced/testing-events/).

### 4. Report evidence

Report the first red failure, green result, relevant suite result, and untested behavior. If the suite cannot run, give the exact command and blocker. Stop once the requested contract and important failure are covered.

## Examples

- User: "Use TDD for a dice interval endpoint." Result: assert the expected status and exact JSON, observe the intended failure, implement the route, then test an invalid face count separately.
- User: "Test chat without calling OpenAI." Result: replace the OpenAI boundary with a deterministic fake, assert response and source fields through `TestClient`, and clean up the fake after the test.

## Common issues

- If a test passes before the behavior exists, strengthen its assertion so it distinguishes the requested change.
- If a test depends on shared overrides or order, isolate its state with a fixture or `try/finally`, then run it alone and with the relevant suite.

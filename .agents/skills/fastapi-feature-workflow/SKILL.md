---
name: fastapi-feature-workflow
description: Deliver a FastAPI feature in this research RAG API from request through a verified vertical slice. Use for "add a FastAPI endpoint", "implement the next phase", or "build this API feature". Do not use for architecture discussion alone or isolated test design.
license: CC-BY-4.0
metadata:
  author: research-rag-api contributors
  version: 1.0.0
---

# FastAPI Feature Workflow

Deliver a small, reviewable behavior change that follows this project's current decisions.

## Instructions

### 1. Establish the slice

Read relevant code and tests, `docs/fases.md`, and accepted decisions in `docs/decisoes.md`. Define the smallest user-visible behavior: request, response, important failure case, and completion check. Resolve only pending choices needed for this slice. Record a lasting architectural decision when it changes the agreed design.

If the user asks to learn or practice, give a focused task and acceptance criteria before implementing it for them. If they ask for implementation, complete it and explain the decisions afterward.

### 2. Plan the boundaries

Locate the HTTP contract, business rule, and external effect. Keep Pydantic models at the API boundary. Move reusable domain behavior outside path operations when it has an independent reason to exist. Apply `fastapi-architecture` for a new domain or structural change. Apply `fastapi-tdd` for changed behavior that needs a regression test.

Keep the existing `main.py` layout while it remains easy to navigate. Introduce domain routers when real features make that layout harder to maintain; avoid empty layers for future phases.

### 3. Implement and verify

Use the project's installed dependencies and `uv` workflow. Run focused tests, then `uv run pytest`. Check the API contract through `TestClient`, including the important invalid input or authorization case. Consult the installed FastAPI skill or [official FastAPI documentation](https://fastapi.tiangolo.com/) for version-sensitive details.

If a check fails, identify whether the implementation or expectation is wrong, fix that cause, and rerun the affected check. Stop when the requested behavior passes its completion check, or report the concrete blocker and evidence.

### 4. Close the slice

Update the phase checklist only for work actually completed. Report behavior delivered, files changed, test commands and results, and remaining decisions or limitations.

## Examples

- User: "Add a route to list RPG systems." Result: a defined response contract, the smallest required data path, passing HTTP tests for success and a relevant failure case, and a phase update only if its criterion is met.
- User: "Implement chat with File Search." Result: identify the first chat slice, keep OpenAI access behind a callable service, test API behavior with that service replaced, and defer unrelated ingestion and frontend work.

## Common issues

- If a library or storage choice is still pending, resolve only what the slice requires and record the decision before building around it.
- If tests require live OpenAI access, add a replaceable boundary and test the application contract without network calls; reserve live checks for an explicit request.

.PHONY: start test sync check-lock

start:
	uv run fastapi dev main.py

test:
	uv run python -m pytest

sync:
	uv sync --locked

check-lock:
	uv lock --check
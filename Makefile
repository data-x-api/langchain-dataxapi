.PHONY: test integration_test lint generate build

test:
	uv run --group test pytest --disable-socket --allow-unix-socket tests/unit_tests

# Free: only dataxapi_find runs against the live API. Paid tools need DATAXAPI_API_KEY and DATAXAPI_RUN_PAID=1.
integration_test:
	uv run --group test pytest tests/integration_tests

lint:
	uv run --group lint ruff check . && uv run --group lint ruff format --check .

generate:
	uv run --group lint python scripts/generate_tools.py

build:
	uv build

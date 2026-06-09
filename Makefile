SHELL=/bin/bash
LINT_PATHS = packages/ apps/ tests/

# For docker-compose
COMPOSE_ENV ?= configs/local.env

# ---------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------

.PHONY: clean clean-build clean-pyc clean-test clean-docs

clean: clean-build clean-pyc clean-test clean-docs

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	find . -name '.coverage' -exec rm -r {} +
	rm -fr htmlcov/
	rm -fr .pytest_cache/
	rm -fr .mypy_cache/
	rm -fr .ruff_cache/

clean-docs:
	rm -fr docs/_build

# ---------------------------------------------------------------
# Checks (used in CI)
# ---------------------------------------------------------------

.PHONY: lint check-codestyle type-check test

lint:
	ruff check $(LINT_PATHS)

check-codestyle:
	ruff format --check $(LINT_PATHS)

type-check:
	mypy $(LINT_PATHS)

test:
	pytest tests/

# ---------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------

.PHONY: down

up:
	docker compose --env-file $(COMPOSE_ENV) up -d

down:
	docker compose down

# ---------------------------------------------------------------
# Local convenience
# ---------------------------------------------------------------

.PHONY: format ci build docs

format:
	ruff check --fix $(LINT_PATHS)
	ruff format $(LINT_PATHS)

# Run all checks (mirrors CI)
ci: lint check-codestyle type-check test

# Install all workspace packages and dev dependencies
build:
	uv pip install -e "packages/bss_core"
	uv pip install -e "packages/bss_valkey"
	uv pip install -e "packages/bss_data"
	uv pip install -e "packages/bss_encoder"
	uv pip install -e "apps/bss_cli"
	uv pip install -e ".[dev]"
	@echo "Build complete. Run with 'bss'"

# Generate HTML documentation
docs: build
	sphinx-build -b html docs docs/_build/html
	@echo "Docs built. Open docs/_build/html/index.html"

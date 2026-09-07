SHELL=/bin/bash

COMPOSE_ENV ?= configs/local.env

# ---------------------------------------------------------------
# Build & Test
# ---------------------------------------------------------------

.PHONY: build release test type-check lint check-codestyle format ci clean

build:
	cargo build --workspace

release:
	cargo build --workspace --release

test:
	cargo nextest run --workspace

type-check:
	cargo check --workspace

lint:
	cargo clippy --workspace -- -D warnings

check-codestyle:
	cargo fmt --all -- --check

format:
	cargo fmt --all

ci: type-check lint check-codestyle test

clean:
	cargo clean

# ---------------------------------------------------------------
# Docs
# ---------------------------------------------------------------

.PHONY: docs

docs:
	cargo doc --workspace --no-deps --open

# ---------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------

.PHONY: up down

up:
	docker compose --env-file $(COMPOSE_ENV) up -d

down:
	docker compose down

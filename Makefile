SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV ?= .venv
UV ?= uv
REGIX ?= regix
PORT ?= 8218
HOST ?= 127.0.0.1

ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: help venv sync install install-dev install-control install-transports install-all \
	test test-fast test-examples lint format check examples rest serve clean lock goal quality-regix

help: ## Show targets
	@echo "hillm — Hardware Interface LLM"
	@echo ""
	@echo "Setup:"
	@echo "  make sync              uv sync (workspace + dev)"
	@echo "  make install           editable core (pip fallback)"
	@echo "  make install-dev       core + dev + control layer"
	@echo "  make install-control   control packages only"
	@echo "  make install-transports optional serial/modbus/mqtt"
	@echo "  make install-all       dev + all transports"
	@echo "  make lock              regenerate uv.lock"
	@echo ""
	@echo "Run:"
	@echo "  make devices           list hardware profiles"
	@echo "  make scan              host hardware scan"
	@echo "  make health            dsl2hillm HEALTH"
	@echo "  make rest              start rest2hillm on :$(PORT)"
	@echo ""
	@echo "Test:"
	@echo "  make test              full pytest suite"
	@echo "  make test-fast         core + dsl tests"
	@echo "  make test-examples     examples/**/*.sh"
	@echo "  make examples          bash examples/run-all-dry-run.sh"
	@echo "  make check             lint + test"
	@echo "  make quality-regix     local core + adapter CC/length gate"
	@echo ""
	@echo "Release:"
	@echo "  make lint              ruff check"
	@echo "  make format            ruff format"
	@echo "  make clean             build artifacts + caches"
	@echo "  make goal              goal -a workflow"

venv:
	@test -x "$(VENV)/bin/python" || $(PYTHON) -m venv "$(VENV)"

_has_uv := $(shell command -v $(UV) >/dev/null 2>&1 && echo 1)

sync:
ifneq ($(strip $(_has_uv)),)
	$(UV) sync --all-packages --extra dev
else
	$(MAKE) install-dev
endif
	@echo "✓ hillm workspace ready"

install: venv
	$(VENV)/bin/pip install -e .
	@echo "✓ hillm core installed"

install-control: venv
	bash packages/install-dev.sh
	@echo "✓ control layer installed"

install-dev: venv
ifneq ($(strip $(_has_uv)),)
	$(UV) sync --all-packages --extra dev
else
	$(VENV)/bin/pip install -e ".[dev]"
	bash packages/install-dev.sh
endif
	@echo "✓ dev + control layer ready"

install-transports: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) sync --all-packages --extra dev --extra all-transports
else
	$(VENV)/bin/pip install -e ".[all-transports]"
endif
	@echo "✓ optional transports installed"

install-all: install-transports
	@echo "✓ full hillm install"

lock:
	$(UV) lock
	@echo "✓ uv.lock updated"

test: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run pytest tests/ packages/dsl2hillm/tests packages/uri2hillm/tests -v --tb=short
else
	$(VENV)/bin/pytest tests/ packages/dsl2hillm/tests packages/uri2hillm/tests -v --tb=short
endif

test-fast: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run pytest tests/test_hillm.py packages/dsl2hillm/tests -q --tb=short
else
	$(VENV)/bin/pytest tests/test_hillm.py packages/dsl2hillm/tests -q --tb=short
endif

test-examples: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run pytest tests/test_examples.py -v --tb=short
else
	$(VENV)/bin/pytest tests/test_examples.py -v --tb=short
endif

examples: install-dev
	bash examples/run-all-dry-run.sh

devices: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run hillm devices
else
	$(VENV)/bin/hillm devices
endif

scan: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run hillm scan
else
	$(VENV)/bin/hillm scan
endif

health: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run dsl2hillm HEALTH
else
	$(VENV)/bin/dsl2hillm HEALTH
endif

rest: install-dev
	@echo "REST API: http://$(HOST):$(PORT)/health"
ifneq ($(strip $(_has_uv)),)
	$(UV) run rest2hillm --host $(HOST) --port $(PORT)
else
	$(VENV)/bin/rest2hillm --host $(HOST) --port $(PORT)
endif

serve: rest

lint: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run ruff check src packages/*/src
else
	$(VENV)/bin/ruff check src packages/*/src
endif

format: install-dev
ifneq ($(strip $(_has_uv)),)
	$(UV) run ruff format src packages/*/src
else
	$(VENV)/bin/ruff format src packages/*/src
endif

check: lint test

clean:
	rm -rf build/ dist/ .pytest_cache .coverage htmlcov/
	rm -rf src/*.egg-info packages/*/*.egg-info packages/*/src/*.egg-info 2>/dev/null || true
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@echo "✓ cleaned"

goal: install-dev
	goal -a

quality-regix: ## Check current core and adapter source against complexity limits
	$(REGIX) gates --ref local --no-cache --config regix.yaml --workdir . --fail-on error

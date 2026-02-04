# BabySleepViz Development Commands
# Run `make help` to see available commands

.PHONY: help install fmt lint test check all

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install package with dev dependencies
	pip install -e ".[dev]"
	pre-commit install

fmt:  ## Auto-fix all linting and formatting issues
	ruff check --fix src/ tests/ scripts/ *.py
	ruff format src/ tests/ scripts/ *.py

lint:  ## Check for linting issues (no auto-fix)
	ruff check src/ tests/ scripts/ *.py
	ruff format --check src/ tests/ scripts/ *.py

test:  ## Run all tests
	pytest tests/ -v

check:  ## Run all checks (lint + test)
	$(MAKE) lint
	$(MAKE) test

all: fmt test  ## Format code and run tests

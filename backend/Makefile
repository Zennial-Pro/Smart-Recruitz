# SmartRecruitz backend — Makefile
# All targets run through the project virtualenv (.venv) so they work
# WITHOUT activating it first. Override PORT/HOST as needed:  make dev PORT=8001

VENV    := .venv
BIN     := $(VENV)/bin
# Invoke tools via `python -m` (the python symlink is stable) rather than the
# console scripts, whose shebangs break if the project/venv is moved.
PY      := $(BIN)/python
PIP     := $(PY) -m pip
UVICORN := $(PY) -m uvicorn
PYTEST  := $(PY) -m pytest
RUFF    := $(PY) -m ruff
MYPY    := $(PY) -m mypy
ALEMBIC := $(PY) -m alembic
HOST    ?= 0.0.0.0
PORT    ?= 8000
APP     := app.asgi:app

.DEFAULT_GOAL := help
.PHONY: help venv install dev run test test-unit test-int test-e2e test-cov \
        lint lint-fix typecheck migrate migrate-new migrate-down seed seed-test \
        db-clear db-clear-yes docker-up docker-down docker-build docker-logs clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ── Environment ────────────────────────────────────────────────────────────────
venv:  ## Create the virtualenv if missing
	@test -d $(VENV) || python3 -m venv $(VENV)

install: venv  ## Create venv + install the project (editable)
	$(PIP) install -e .

# ── Development ──────────────────────────────────────────────────────────────────
dev:  ## Run the API with autoreload (http://localhost:$(PORT))
	@echo "Starting SmartRecruitz API on http://localhost:$(PORT) (autoreload)..."
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT) --reload

run:  ## Run the API without autoreload (production-style)
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT)

# ── Testing ────────────────────────────────────────────────────────────────────
test:  ## Run all tests with coverage
	$(PYTEST) tests/ -v --cov=app --cov-report=term-missing

test-unit:  ## Run unit tests
	$(PYTEST) tests/unit/ -v

test-int:  ## Run integration tests
	$(PYTEST) tests/integration/ -v

test-e2e:  ## Run end-to-end tests
	$(PYTEST) tests/e2e/ -v

test-cov:  ## Run tests with HTML/XML coverage
	$(PYTEST) tests/ -v --cov=app --cov-report=html --cov-report=xml

# ── Code Quality ─────────────────────────────────────────────────────────────────
lint:  ## Lint + format check
	$(RUFF) check .
	$(RUFF) format --check .

lint-fix:  ## Auto-fix lint + format
	$(RUFF) check --fix .
	$(RUFF) format .

typecheck:  ## Strict type check
	$(MYPY) app/ --strict

# ── Database ───────────────────────────────────────────────────────────────────
migrate:  ## Apply migrations (alembic upgrade head)
	$(ALEMBIC) upgrade head

migrate-new:  ## Autogenerate a new migration (prompts for a message)
	@read -p "Migration message: " msg; \
	$(ALEMBIC) revision --autogenerate -m "$$msg"

migrate-down:  ## Roll back one migration
	$(ALEMBIC) downgrade -1

# ── Seed Data ──────────────────────────────────────────────────────────────────
seed:  ## Seed reference data
	$(PY) -m seeds.seed_runner

seed-test:  ## Seed test candidates
	$(PY) scripts/seed_test_candidates.py

# ── Danger zone ──────────────────────────────────────────────────────────────────
db-clear:  ## Clear the database (interactive)
	$(PY) scripts/clear_db.py

db-clear-yes:  ## Clear the database (no prompt)
	$(PY) scripts/clear_db.py --yes

# ── Docker ─────────────────────────────────────────────────────────────────────
docker-up:  ## Start docker stack
	docker compose -f docker/docker-compose.yml up -d

docker-down:  ## Stop docker stack
	docker compose -f docker/docker-compose.yml down

docker-build:  ## Build docker images
	docker compose -f docker/docker-compose.yml build

docker-logs:  ## Tail docker logs
	docker compose -f docker/docker-compose.yml logs -f

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean:  ## Remove caches and coverage artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache

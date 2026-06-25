.PHONY: help install test lint lint-fix fmt fmt-check typecheck qa \
        example-invoice example-info example-history example-static-wallet \
        example-webhook example-balance example-payout example-payout-info \
        example-services example-rates example-aml-links example-refund webhook-inspect \
        build publish publish-test \
        docker-build docker-shell docker-webhook docker-qa clean

POETRY ?= poetry

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (poetry install)
	$(POETRY) install --with dev

test: ## Run the pytest suite
	$(POETRY) run pytest -q

lint: ## Run ruff (no autofix)
	$(POETRY) run ruff check .

lint-fix: ## Run ruff with --fix
	$(POETRY) run ruff check --fix .

fmt: ## Apply ruff format
	$(POETRY) run ruff format .

fmt-check: ## Fail if any file would be reformatted
	$(POETRY) run ruff format --check .

typecheck: ## Run mypy in strict mode
	$(POETRY) run mypy

qa: ## Run all quality gates (lint + fmt-check + typecheck + tests)
	$(POETRY) run ruff check .
	$(POETRY) run ruff format --check .
	$(POETRY) run mypy
	$(POETRY) run pytest -q

# ---------- examples ----------------------------------------------------------

example-invoice: ## Create a test invoice via the API
	$(POETRY) run python examples/01_create_invoice.py

example-info: ## Look up payment info (pass ID=<uuid|order_id>)
	$(POETRY) run python examples/02_get_payment_info.py $(ID)

example-history: ## List recent payments
	$(POETRY) run python examples/03_list_payment_history.py

example-static-wallet: ## Create a static (top-up) wallet
	$(POETRY) run python examples/04_create_static_wallet.py

example-webhook: ## Run the webhook listener on http://localhost:8000
	$(POETRY) run python examples/05_handle_webhook.py

example-balance: ## Show merchant + personal balances
	$(POETRY) run python examples/06_get_balance.py

example-payout: ## Create a payout (env HELEKET_PAYOUT_ADDRESS recommended)
	$(POETRY) run python examples/07_create_payout.py

example-payout-info: ## Look up a payout (pass ID=<uuid|order_id>)
	$(POETRY) run python examples/08_get_payout_info.py $(ID)

example-services: ## List supported (currency, network) pairs
	$(POETRY) run python examples/09_list_services.py

example-rates: ## Print exchange rates for a fiat currency (CCY=USD)
	$(POETRY) run python examples/10_exchange_rates.py $(CCY)

example-aml-links: ## AML links for a blocked payment (pass ID=<uuid|order_id>)
	$(POETRY) run python examples/11_aml_links.py $(ID)

example-refund: ## Refund an invoice (UUID=<invoice-uuid> ADDRESS=<addr>)
	$(POETRY) run python examples/12_refund.py $(UUID) $(ADDRESS)

# ---------- CLI ---------------------------------------------------------------

webhook-inspect: ## Verify a webhook from FILE=<path> or stdin (KEY=...)
	$(POETRY) run heleket-webhook-inspect --key=$(KEY) \
		$(if $(FILE),--file=$(FILE),) $(if $(TYPE),--type=$(TYPE),)

# ---------- Release -----------------------------------------------------------

build: qa ## Run the QA gates, then build sdist + wheel into dist/
	$(POETRY) build

publish: ## Publish dist/ to PyPI (run `make build` first; needs a configured token)
	$(POETRY) publish

publish-test: ## Publish to TestPyPI (configure the `testpypi` repository first)
	$(POETRY) publish --repository testpypi

# ---------- Docker ------------------------------------------------------------

docker-build: ## Build the dev image
	docker compose build

docker-shell: ## Open a shell inside the container
	docker compose run --rm cli sh

docker-webhook: ## Run the webhook example in a container
	docker compose up webhook

docker-qa: ## Run the QA suite in a container
	docker compose up --build qa

clean: ## Remove build artifacts
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage

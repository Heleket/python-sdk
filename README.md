# Heleket Python integration (reference)

A production-grade reference SDK for the [Heleket](https://heleket.com) cryptocurrency payment API. Written for **Python 3.11+**, published as `heleket-sdk` — works with FastAPI, Django, Flask, or plain scripts.

Covers the full documented surface (payments, payouts, balance, services, exchange rates), ships with pytest tests, runnable examples, byte-fidelity webhook verification, debug mode wired into your choice of logger, a `heleket-webhook-inspect` CLI, and a Docker harness.

Runtime dependencies: **Pydantic v2** (typed DTOs) and **requests** (HTTP). Everything else comes from the standard library.

## Quickstart

```python
from heleket_sdk import HeleketPayment
from heleket_sdk.types import CreateInvoiceRequest

client = HeleketPayment(merchant_id=merchant_id, api_key=payment_key)

invoice = client.create_invoice(
    CreateInvoiceRequest(
        amount="15.00",
        currency="USD",
        order_id="order-42",
        lifetime=3600,
    )
)

print(invoice.url)  # → https://pay.heleket.com/pay/<uuid>
```

## Install

```bash
poetry add heleket-sdk
# or
pip install heleket-sdk
```

Requirements: Python 3.11+ (StrEnum, Self type, better type hints). Tested with CPython 3.11 and 3.12.

## Documentation

Full reference lives in [`docs/`](docs/README.md):

- [01 — Installation](docs/01-installation.md)
- [02 — Configuration](docs/02-configuration.md)
- [03 — Architecture](docs/03-architecture.md)
- [04 — Payments API](docs/04-payments.md)
- [05 — Payouts API](docs/05-payouts.md)
- [06 — Webhooks](docs/06-webhooks.md) ⚑ critical reading
- [07 — Debugging](docs/07-debugging.md)
- [08 — Testing](docs/08-testing.md)
- [09 — Error handling](docs/09-error-handling.md)
- [10 — Reference (statuses, currencies, endpoints)](docs/10-reference.md)
- [12 — Troubleshooting](docs/12-troubleshooting.md)

## What's in the box

```
src/heleket_sdk/         Source — single source of truth
src/heleket_sdk/webhook  Webhook signature verifier (byte-fidelity)
tests/                   pytest suite + FakeTransport for offline testing
examples/                Ten runnable scripts covering every endpoint
bin/                     heleket-webhook-inspect — CLI for verifying webhook payloads
docker/                  Multi-stage Dockerfile (python:3.11-slim)
docs/                    Full module documentation
pyproject.toml           Poetry build + ruff + mypy + pytest config
```

## Common tasks

```bash
make install              # poetry install --with dev
make test                 # pytest -q
make lint                 # ruff check
make fmt                  # ruff format
make fmt-check            # ruff format --check
make typecheck            # mypy in strict mode
make qa                   # All quality gates
make example-invoice      # Create a real invoice (needs .env)
make example-webhook      # Run the webhook listener on :8000
make webhook-inspect KEY=$K FILE=evt.json  # Inspect a captured webhook
make docker-shell         # Drop into a containerized Python 3.11 shell
make help                 # Full target list
```

## Security notes (read this)

- **Use `verify_raw` for production webhooks.** `verify(decoded)` is convenience-only and lossy — it can't recover the PHP-style `\/` slash escapes that Heleket's server sends. See [docs/06-webhooks.md](docs/06-webhooks.md).
- **De-duplicate replays.** Use a `(uuid, status)` key in your DB before doing side-effect work. SQLAlchemy and redis-py examples in [docs/06-webhooks.md](docs/06-webhooks.md#idempotency-and-replay-protection).
- **Whitelist Heleket's webhook source IP `31.133.220.8`** at your reverse proxy or firewall.
- **Two separate API keys** — payments and payouts. Mixing them breaks webhook verification.
- **The SDK never logs API keys.** Debug-mode entries include URL, method, body, and status — but the `sign` header and API key are explicitly excluded.

## License

MIT.

# 01 — Installation

## Requirements

- **Python 3.11 or newer.** The SDK uses `StrEnum`, `Self`, structural typing patterns, and PEP 604 union syntax.
- **Poetry 1.6+** if you build with Poetry. Plain `pip` also works.

## From PyPI (when published)

```bash
poetry add heleket-sdk
# or
pip install heleket-sdk
```

## From this reference folder

This integration directory IS a Poetry project. Install it into a venv:

```bash
cd api-integrations/python
poetry install --with dev
```

Or with plain pip in editable mode:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Verifying the installation

```bash
make test          # 54 pytest tests
make example-invoice   # End-to-end smoke test (needs .env)
```

## Public surface

```python
from heleket_sdk import (
    HeleketPayment, HeleketPayout,
    ClientOptions,
    PaymentStatus, PayoutStatus, CourseSource,
    WebhookVerifier, WebhookPayload,
    HeleketError, ApiError, ValidationError, HttpError, SignatureError,
)

from heleket_sdk.types import (
    CreateInvoiceRequest, Invoice,
    CreatePayoutRequest, Payout,
    HistoryOptions, HistoryPage,
    # ...
)
```

## .env configuration

The examples directory expects a `.env` file in the project root. Start from the template:

```bash
cp .env.example .env
# Edit HELEKET_MERCHANT_ID, HELEKET_PAYMENT_KEY, HELEKET_PAYOUT_KEY
```

For production Django / FastAPI deployments, prefer the framework's settings module or environment variables.

## Next steps

- [02 — Configuration](02-configuration.md): per-request timeouts, custom transports
- [03 — Architecture](03-architecture.md): how requests flow through the SDK

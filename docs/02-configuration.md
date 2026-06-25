# 02 — Configuration

The SDK requires two values: your **merchant UUID** and the **API key** that matches the operation you're performing.

Heleket issues **two distinct API keys**:

| Key | Used for |
|---|---|
| Payment key | `/v1/payment/*`, `/v1/wallet/*`, `/v1/balance`, `/v1/exchange-rate/*`, payment + wallet webhooks |
| Payout key | `/v1/payout/*`, `/v1/transfer/*`, payout webhooks |

Mixing them breaks both API calls and webhook signature verification.

> **One cross-key exception:** `/v1/payment/refund` is a payment-domain path but is
> signed with the **payout** API key, so it is exposed as `HeleketPayout.refund()`.
> `HeleketPayment` does not expose `refund()` at all.

## Minimal construction

```python
from heleket_sdk import HeleketPayment, HeleketPayout

payment = HeleketPayment(merchant_id=merchant_id, api_key=payment_key)
payout = HeleketPayout(merchant_id=merchant_id, api_key=payout_key)
```

Both clients are thread-safe — share a single instance across all your request handlers.

## With options

`ClientOptions` is a plain dataclass:

```python
from heleket_sdk import ClientOptions, HeleketPayment

options = ClientOptions(
    debug=True,                # dump every request/response
    timeout=60.0,              # per-request HTTP timeout (seconds)
)

client = HeleketPayment(merchant_id=merchant_id, api_key=payment_key, options=options)
```

### Options reference

| Field | Default | Description |
|---|---|---|
| `base_url` | `"https://api.heleket.com"` | Override the API host (testing/staging only) |
| `timeout` | `30.0` | Per-request HTTP timeout in seconds |
| `debug` | `False` | Toggle debug logging |
| `logger` | `stderr_sink` | Route debug entries to your logger |
| `transport` | `None` (defaults to `RequestsTransport`) | Swap out the HTTP layer |

## Django

Construct the clients at module level so they're shared across requests:

```python
# myapp/heleket.py
from django.conf import settings
from heleket_sdk import HeleketPayment, HeleketPayout

payment = HeleketPayment(
    merchant_id=settings.HELEKET_MERCHANT_ID,
    api_key=settings.HELEKET_PAYMENT_KEY,
)
payout = HeleketPayout(
    merchant_id=settings.HELEKET_MERCHANT_ID,
    api_key=settings.HELEKET_PAYOUT_KEY,
)
```

```python
# views.py
from .heleket import payment
```

## FastAPI

Wire the clients as dependencies:

```python
from functools import lru_cache
from fastapi import Depends, FastAPI
from heleket_sdk import HeleketPayment

@lru_cache
def get_payment() -> HeleketPayment:
    return HeleketPayment(merchant_id=settings.merchant_id, api_key=settings.payment_key)

app = FastAPI()

@app.post("/checkout")
def checkout(payment: HeleketPayment = Depends(get_payment)):
    ...
```

## Plugging in a custom HTTP transport

Use cases: corporate proxy, retries, instrumentation, intermediate signing gateways.

```python
import time
from heleket_sdk import HttpError, RequestsTransport, Transport, TransportResponse

class RetryingTransport:
    def __init__(self) -> None:
        self._delegate = RequestsTransport()

    def round_trip(self, method, url, headers, body, timeout) -> TransportResponse:
        for attempt in range(3):
            try:
                return self._delegate.round_trip(method, url, headers, body, timeout)
            except HttpError:
                if attempt == 2:
                    raise
                time.sleep(0.2 * (2 ** attempt))

options = ClientOptions(transport=RetryingTransport())
```

The contract is documented on `heleket_sdk._transport.Transport` — the body bytes you receive are the exact bytes the SDK signed; do not modify them.

## Reading config from .env files

The SDK does not read `.env`. The `examples/_bootstrap.py` module shows a 30-line inline reader if you want one. Production code should use a proper config layer (Django settings, Pydantic Settings, `python-decouple`, etc.).

# 08 — Testing

The SDK ships with pytest and a `FakeTransport` you can borrow for your own tests.

## Running the SDK's own suite

```bash
make test                       # pytest -q — 54 tests
pytest tests/test_signature.py  # one file
pytest -k webhook               # by keyword
```

Coverage at a glance:

- `test_signature.py` — formula, empty-body collapse, **cross-language parity vector**
- `test_status.py` — enum coverage including `UNKNOWN` fallback
- `test_config.py` — defaults + validation
- `test_payment.py` / `test_payout.py` — FakeTransport-driven
- `test_webhook.py` — includes the PHP-style payload regression test
- `test_transport.py` — spins up a real loopback `http.server`

## FakeTransport — your friend for unit tests

```python
from heleket_sdk import HeleketPayment, ClientOptions
from heleket_sdk.types import CreateInvoiceRequest

from tests.fakes import FakeTransport  # or relative to your own test layout

def test_creates_invoice():
    fake = FakeTransport().enqueue_json({
        "state": 0,
        "result": {"uuid": "u1", "url": "https://pay.heleket.com/pay/x"},
    })

    client = HeleketPayment(
        merchant_id="merchant",
        api_key="key",
        options=ClientOptions(transport=fake),
    )
    invoice = client.create_invoice(
        CreateInvoiceRequest(amount="15", currency="USD", order_id="o-1")
    )

    assert invoice.uuid == "u1"

    # Assertions against what the client SENT:
    sent = fake.last_request()
    assert sent.method == "POST"
    assert sent.url == "https://api.heleket.com/v1/payment"
    assert sent.headers["merchant"] == "merchant"
```

API:

| Call | What it does |
|---|---|
| `.enqueue_json(payload)` | Queue a 200 response with this JSON body |
| `.enqueue_json(payload, 422)` | Queue a non-200 response (validation, etc.) |
| `.enqueue(TransportResponse)` | Queue a fully custom response |
| `.fail_next("reset")` | Queue a transport-level failure (raises HttpError) |
| `.requests` | Every request the client made, in order |
| `.last_request()` | Most recent request — convenient for single-call tests |

## Webhook verification tests

```python
from heleket_sdk import sign, WebhookVerifier

def test_verify_round_trip():
    body = '{"type":"payment","uuid":"u1","status":"paid"}'
    signature = sign(body, "my-secret")
    signed = f'{{"type":"payment","uuid":"u1","status":"paid","sign":"{signature}"}}'

    verifier = WebhookVerifier("my-secret")
    payload = verifier.verify_raw(signed)
    assert payload.status == "paid"
```

## Integration testing with a real loopback HTTP server

When you want to test the actual HTTP path (TLS, header propagation through your reverse proxy logic, etc.), spin up `http.server.HTTPServer`. `tests/test_transport.py` shows the pattern.

## Property-based ideas

Heleket's API is fairly closed-world, but two properties worth pinning down:

1. `sign(body, key)` is purely a function of `body` + `key` — no clock, no randomness. Same inputs → same hex.
2. `verify_raw(raw)` accepts the bytes of any object whose `sign` field is correct, **regardless of key order**. Shuffle non-sign fields, sign, verify.

## pytest fixtures for FastAPI / Django

If your handler is a route, use the framework's test client:

```python
# FastAPI
from fastapi.testclient import TestClient
from app.main import app

def test_webhook_endpoint(client_app: TestClient):
    body = b'{"type":"payment","uuid":"u1","status":"paid","sign":"<signature>"}'
    response = client_app.post(
        "/heleket-webhook",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 200
```

```python
# Django
from django.test import Client

def test_webhook_endpoint():
    c = Client()
    response = c.post(
        "/heleket-webhook",
        data=b'{"type":"payment","uuid":"u1","status":"paid","sign":"<signature>"}',
        content_type="application/json",
    )
    assert response.status_code == 200
```

Pre-compute the signature in your test setup with `heleket_sdk.sign(...)`.

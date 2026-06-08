# 06 — Webhooks

**Required reading before going live.** Get this wrong and either you'll process unauthorized "payments" (security incident) or you'll reject every real webhook (operational incident).

## What Heleket sends

When an invoice or payout changes state, Heleket POSTs a JSON body to your `url_callback`. The body always contains a `sign` field with the signature of the body **with `sign` removed**:

```
sign = md5(base64(json_body_minus_sign) + api_key)
```

The same formula as outgoing requests. **The API key must be the one matching the webhook type:**

| Webhook `type` | API key to verify with |
|---|---|
| `payment`, `wallet` | Payment key |
| `payout` | Payout key |

## Verifying with the SDK

```python
from heleket_sdk import SignatureError, WebhookVerifier

verifier = WebhookVerifier(payment_api_key)

try:
    payload = verifier.verify_raw(raw_bytes)
    # signature confirmed — payload is trustworthy
except SignatureError as e:
    log.warning("Heleket signature mismatch: %s", e.reason)
    # Return HTTP 400 — DO NOT execute side effects.
```

**Pass the raw request bytes**, exactly as received. Do NOT call `request.json()`, `json.loads`, or any other transformation before verification — those mutate the bytes and break the signature.

## Why `verify_raw` and not `verify(dict)`?

Heleket's PHP server JSON-encodes with two non-default behaviours:

1. **Insertion-order keys** (Python's `json` preserves this since 3.7, ✅).
2. **Forward slashes escaped as `\/`** (Python's `json.dumps` does NOT, ❌).

If you `json.loads(raw) → json.dumps(...)`, the `\/` escapes vanish and the signature breaks. `verify_raw` works around this by stripping only the `sign` field from the raw bytes (precision regex with the captured hex), then hashing the remainder.

`verify(dict)` re-encodes through Python's `json` — useful for fixtures and Python-to-Python tests, **not safe for real Heleket traffic**.

## Reading raw bytes in popular frameworks

### FastAPI

```python
from fastapi import FastAPI, HTTPException, Request
from heleket_sdk import SignatureError, WebhookVerifier

app = FastAPI()
verifier = WebhookVerifier(settings.payment_key)

@app.post("/heleket-webhook")
async def webhook(request: Request) -> dict:
    raw = await request.body()
    try:
        payload = verifier.verify_raw(raw)
    except SignatureError as e:
        raise HTTPException(400, e.reason) from e
    # ... process payload ...
    return {"ok": True}
```

`Request.body()` returns the raw bytes — do NOT call `await request.json()`.

### Django

```python
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from heleket_sdk import SignatureError, WebhookVerifier

verifier = WebhookVerifier(settings.HELEKET_PAYMENT_KEY)

@csrf_exempt
@require_POST
def webhook(request):
    try:
        payload = verifier.verify_raw(request.body)
    except SignatureError as e:
        return HttpResponseBadRequest(e.reason)
    # ... process payload ...
    return HttpResponse("OK")
```

`request.body` is bytes — never `request.POST`, which parses form data.

### Flask

```python
from flask import Flask, request, abort
from heleket_sdk import SignatureError, WebhookVerifier

app = Flask(__name__)
verifier = WebhookVerifier(settings.PAYMENT_KEY)

@app.post("/heleket-webhook")
def webhook():
    try:
        payload = verifier.verify_raw(request.get_data())
    except SignatureError as e:
        abort(400, e.reason)
    # ... process payload ...
    return "OK"
```

### Plain `http.server`

See `examples/05_handle_webhook.py`.

## Idempotency and replay protection

**Heleket WILL replay webhooks.** When your handler 5xxs, times out, or simply takes too long, the server retries. Operators can also manually re-trigger via the dashboard. Your handler MUST be idempotent.

The standard pattern is a unique index on `(uuid, status)`:

### Postgres / SQLAlchemy

```python
from sqlalchemy import Column, DateTime, String, UniqueConstraint, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class HeleketEvent(Base):
    __tablename__ = "heleket_webhook_event"
    uuid = Column(String, primary_key=True)
    status = Column(String, primary_key=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

def record_if_new(session, payload) -> bool:
    try:
        session.add(HeleketEvent(uuid=payload.uuid, status=payload.status))
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False  # duplicate — already handled
```

### Redis (redis-py)

```python
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def record_if_new(payload) -> bool:
    key = f"heleket:event:{payload.uuid}:{payload.status}"
    # SET with NX (only if not exists) and EX (TTL in seconds = 7 days)
    return r.set(key, "1", nx=True, ex=86400 * 7) is True
```

Then your handler becomes:

```python
payload = verifier.verify_raw(raw)
if not record_if_new(payload):
    return HttpResponse("dup")  # already processed
# do real work
```

## Source IP allow-list

Add `31.133.220.8` to your reverse proxy or firewall. Webhooks arriving from anywhere else are forged.

## Quick sanity check

Capture a real webhook in production, save it to a file, and run:

```bash
make webhook-inspect KEY=$HELEKET_PAYMENT_KEY FILE=evt.json
```

If you see `signature: valid`, the key, body, and verification logic line up. If not, the inspector prints actionable hints.

## Going further

- Cross-language test: a single PHP-signed payload verifies in all five SDKs (PHP, Go, Node, Java, Python). The verifier here was specifically written to match.
- For maximum belt-and-braces, after a 200 OK reply you can call `get_info()` to double-check the payment state before crediting the customer.

# 09 — Error handling

All SDK exceptions extend `HeleketError`, which is a plain `Exception`. Everything is unchecked in the Python sense — the caller decides when to catch.

## Hierarchy

```
HeleketError                  (base, plain Exception)
├── ApiError                  (state != 0 or non-2xx response)
│   └── ValidationError       (HTTP 422 with field-level errors)
├── HttpError                 (DNS / TCP / TLS / timeout)
└── SignatureError            (webhook signature mismatch)
```

## Catching them

```python
from heleket_sdk import (
    ApiError, HttpError, HeleketError, ValidationError,
)

try:
    client.create_invoice(request)
except ValidationError as e:
    # The server rejected the input. e.fields is a dict[str, list[str]]
    # of field_name → list of error messages.
    for field, messages in e.fields.items():
        print(f"  {field}: {', '.join(messages)}")
except ApiError as e:
    # Any other state != 0 response. Use str(e), e.http_status, e.raw_body.
    log.error("Heleket says: %s (HTTP %s)", e, e.http_status)
except HttpError as e:
    # Transport failure — the request never reached Heleket OR we never got a reply.
    # Safe to retry with exponential backoff.
    log.error("transport: %s", e)
except HeleketError as e:
    # Catch-all if you don't care to distinguish.
    log.error("heleket error: %s", e)
```

`ValidationError` is a subclass of `ApiError`, so a `except ApiError` block alone is fine if you don't need to surface per-field messages.

## When each one fires

| Trigger | Exception |
|---|---|
| HTTP 422 with `errors` map | `ValidationError` |
| HTTP 200 but `state != 0` | `ApiError` |
| HTTP 4xx/5xx without parseable JSON | `ApiError` |
| Failure to JSON-encode the request | `ApiError` |
| Failure to JSON-decode the response | `ApiError` |
| `requests.RequestException` | `HttpError` |
| Connection timeout | `HttpError` |
| Webhook signature doesn't match | `SignatureError` |
| Webhook missing `sign` field | `SignatureError` |
| Webhook body isn't valid JSON | `SignatureError` |

## Should I retry?

Yes for `HttpError` — transient by definition. Use exponential backoff and a circuit breaker (`tenacity`, `backoff`) so a regional outage doesn't melt your worker pool.

**No** for `ApiError`/`ValidationError` — they reflect a server-side decision that won't change on retry.

**Never** for `SignatureError` — it's either tampering or a bug in your handler. Log loudly and return 400.

## What about wrapping for your domain?

Many merchants prefer to translate SDK exceptions into a domain-specific result before they bubble up:

```python
from dataclasses import dataclass

@dataclass
class CheckoutResult:
    ok: bool
    url: str | None = None
    error: str | None = None

def create_checkout(order):
    try:
        invoice = client.create_invoice(...)
        return CheckoutResult(ok=True, url=invoice.url)
    except ValidationError as e:
        return CheckoutResult(ok=False, error=str(e))
    except ApiError as e:
        return CheckoutResult(ok=False, error=e.raw_body)
    except HttpError:
        return CheckoutResult(ok=False, error="provider unavailable")
```

That way callers don't need to know they're talking to Heleket.

## Tenacity example

```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from heleket_sdk import HttpError

@retry(
    retry=retry_if_exception_type(HttpError),
    wait=wait_exponential(multiplier=0.2, max=2),
    stop=stop_after_attempt(3),
    reraise=True,
)
def create_invoice_with_retries(client, request):
    return client.create_invoice(request)
```

Critically: retry only on `HttpError`, never on `ApiError`.

## Things to NOT do

- **Don't** catch `Exception` blindly. You'll swallow `KeyboardInterrupt`, `SystemExit`, and bugs in your own code.
- **Don't** treat `SignatureError` as recoverable. Always return HTTP 400 and refuse to process.
- **Don't** rely on `str(e)` text for control flow — use the exception type.

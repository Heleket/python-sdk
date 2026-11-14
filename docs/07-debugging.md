# 07 — Debugging

## Turn on debug mode

```python
from heleket_sdk import ClientOptions, HeleketPayment

options = ClientOptions(debug=True)
client = HeleketPayment(merchant_id=merchant_id, api_key=payment_key, options=options)
```

Every request emits two `DebugEntry` dataclasses: one for the outgoing request, one for the response (or one for the error). They go to the configured `DebugSink` — by default, `stderr_sink`, which writes one line per entry to `sys.stderr`.

Sample output:

```
[heleket][→ POST https://api.heleket.hk/v1/payment] {"amount":"15.00","currency":"USD","order_id":"order-42"}
[heleket][← 200] {"state":0,"result":{"uuid":"...","url":"https:\/\/pay.heleket.hk\/pay\/..."}}
```

## What's NOT logged

The `DebugEntry` dataclass contains: kind, method, url, body, status, message. It deliberately does NOT contain:

- The API key
- The `sign` header (would let an observer replay requests)
- Any other request headers

If you read the `BaseClient` source you'll see headers are computed inside `BaseClient._post()` and only the body + URL flow into `DebugEntry`.

## Routing to a real logger

The default sink writes plain text to stderr — fine for examples and CLIs, not great for structured logging. Plug in any logger:

### `logging` (stdlib)

```python
import logging

log = logging.getLogger("heleket")

def sink(entry):
    if entry.kind == "request":
        log.debug("→ %s %s\n%s", entry.method, entry.url, entry.body)
    elif entry.kind == "response":
        log.debug("← %s\n%s", entry.status, entry.body)
    elif entry.kind == "error":
        log.warning("× %s", entry.message)

options = ClientOptions(debug=True, logger=sink)
```

### `structlog`

```python
import structlog

logger = structlog.get_logger("heleket")

def sink(entry):
    logger.bind(kind=entry.kind, status=entry.status).info(
        "heleket", url=entry.url, method=entry.method, body=entry.body
    )

options = ClientOptions(debug=True, logger=sink)
```

### JSON to stdout (Datadog / Loki / ELK)

```python
import json
import sys
from dataclasses import asdict

def sink(entry):
    sys.stdout.write(json.dumps(asdict(entry)) + "\n")
    sys.stdout.flush()
```

## Capturing requests in tests

Use `FakeTransport` (see `tests/fakes.py`). It records every request the client made — call `fake.last_request()` and assert against `.method`, `.url`, `.body`, `.headers`. The `sign` header is preserved because tests often want to verify it.

## Common debug scenarios

### "Why did my request fail?"

```python
try:
    client.create_invoice(...)
except ApiError as e:
    log.error("HTTP %s body=%s", e.http_status, e.raw_body)
```

`raw_body` is the literal response Heleket sent — usually contains the most useful message.

### "Am I sending what I think I'm sending?"

Enable debug and look at the body line. If you see `(empty body)` but expected JSON, your request DTO probably has no non-None fields — Pydantic's `exclude_none=True` skipped them all.

### "The signature works locally but breaks in prod"

99% of the time it's a proxy mutating the body (re-encoding multipart, trimming whitespace, etc.). Use `verify_raw` and verify nothing in front of your app touches the request bytes.

## Next

- [08 — Testing](08-testing.md): writing pytest tests against the SDK
- [12 — Troubleshooting](12-troubleshooting.md): common pitfalls

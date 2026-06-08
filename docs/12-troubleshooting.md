# 12 — Troubleshooting

## "signature mismatch" on webhooks

The single most common production issue. Causes, in rough order of likelihood:

1. **You used the wrong API key.** Payment-typed events sign with the payment key; payout events sign with the payout key.
2. **Something between Heleket and your app mutated the body.** Nginx `proxy_buffering`, `mod_security`, a JSON-validating middleware, etc. Verify against the raw bytes from the very edge of your network.
3. **Your handler parsed and re-serialized the body before passing it to the verifier.** This almost always loses the `\/` slash escapes. Use `verify_raw` with the raw bytes — `request.body` in Django, `await request.body()` in FastAPI, `request.get_data()` in Flask.
4. **The API key has been rotated** but the running app still has the old one cached.
5. **Trailing newline** added by your file editor when saving captured webhook payloads. The CLI strips trailing `\n`/`\r` — if you're verifying the body inside your own app, do the same.

Quick test:

```bash
make webhook-inspect KEY=$HELEKET_PAYMENT_KEY FILE=captured.json
```

If the CLI says `valid` but your handler says `INVALID`, your handler is mutating the body. Bisect the middleware chain.

## "validation failed: amount (validation.required)" on every request

Your Pydantic model dropped the field. Most common cause: you wrote `Field(default=None)` but forgot to declare `populate_by_name=True` in the request model's config — incoming `alias` collisions can occasionally cause the wrong name to be sent. Print `request.model_dump(by_alias=True, exclude_none=True)` to confirm what's about to go over the wire.

## "merchant header missing" or "401"

The `merchant` header carries your merchant UUID. The SDK sets it on every request — if you wrote a custom `Transport`, make sure it forwards the headers it received verbatim.

## `HttpError: transport failed: ...`

Wrapped `requests.RequestException`. Inspect `error.__cause__` for the underlying `ConnectionError`, `Timeout`, etc. Retry-with-backoff is appropriate; never retry `ApiError`.

## "non-JSON response (HTTP 502)"

Heleket returned HTML or an empty body — usually a transient incident on their side or your proxy. Retry. The exception's `raw_body` shows the actual content.

## Pydantic validation errors on a response

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Invoice
amount
  Input should be a valid string [type=string_type, input_value=15, input_type=int]
```

Heleket returned a value in a shape the SDK didn't expect. Usually:

- API changed a number field from string to int (or vice versa) — open an issue.
- Your local copy of the SDK is older than the API. `poetry update heleket-sdk`.

Workaround: catch `pydantic.ValidationError` and fall back to `getattr(error, "errors")()` to get the field-level breakdown.

## "Decimal incompatible with str"

The SDK uses `str` for monetary amounts to avoid float-precision pitfalls. Convert at the boundary:

```python
from decimal import Decimal

amount = Decimal("15.00")
request = CreateInvoiceRequest(
    amount=f"{amount:.2f}",
    currency="USD",
    order_id="order-1",
)
```

## Examples fail with "Missing env var: HELEKET_MERCHANT_ID"

The bootstrap reads `.env` from the current working directory **and** the parent. Either run examples from `api-integrations/python/` or pass the variables in your environment:

```bash
HELEKET_MERCHANT_ID=... HELEKET_PAYMENT_KEY=... \
  python examples/01_create_invoice.py
```

## `ModuleNotFoundError: heleket_sdk`

Either run inside the Poetry venv (`poetry shell` then `python ...`), or `pip install -e .` so the editable install is on your `sys.path`.

## `pip install -e .` complains about README.md missing

You're working from a freshly-cloned checkout. Make sure `README.md` exists — Poetry requires it because `pyproject.toml` declares `readme = "README.md"`.

## Docker build is slow on the first run

Poetry downloads ~20MB of dependencies on the first build. They're cached in `/app/.venv` inside the image; subsequent `docker compose build` calls reuse the layer.

## Tests pass but ruff fails

Run `make fmt` once to apply formatting, commit the diff, then `make fmt-check` will be clean.

## Still stuck?

- Crank `debug=True` in `ClientOptions` — you'll see the exact bytes leaving the SDK.
- Re-read [06 — Webhooks](06-webhooks.md) for byte-fidelity details.
- The PHP, Go, Node, and Java SDKs solved the same problems — their docs may use slightly different language that clicks.

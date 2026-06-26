# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Cursor, Copilot, …) working on
or integrating the **Heleket Python SDK**. Humans: this doubles as a fast
architecture tour — see [`docs/`](docs/README.md) for the full reference.

## What this is

The reference Python SDK for the [Heleket](https://heleket.com) cryptocurrency
payment API: payments, payouts, balance, exchange rates, services, and signed
webhooks. Typed end-to-end (Pydantic v2 models, ships `py.typed`).

- Package: **`heleket-sdk`** on PyPI · import as **`heleket_sdk`**.
- Python **3.11+** (uses `StrEnum`, `X | Y` types, `Self`).
- Runtime deps: **Pydantic v2** (`>=2.5`) and **requests** (`>=2.31`); everything
  else is stdlib.
- Upstream API docs: <https://doc.heleket.com>.

## Repository map

| Path | Purpose |
|---|---|
| `src/heleket_sdk/` | Package source. Public names re-exported from `__init__.py`; `*.py` prefixed `_` are internal. |
| `src/heleket_sdk/py.typed` | PEP 561 marker — keep it; it's what makes the types ship. |
| `tests/` | pytest suite + `tests/fakes.py` `FakeTransport` for offline HTTP. |
| `examples/` | Twelve runnable scripts (`01`..`12`), one per endpoint + `_bootstrap.py`. Need `.env`. |
| `bin/heleket-webhook-inspect` | CLI to verify/dump a webhook payload (entry point `heleket_sdk._cli:main`). |
| `docs/` | Full English reference (architecture, every endpoint, webhooks, …). |
| `Makefile` | `make qa`, `make test`, `make lint`, `make typecheck`, examples, Docker. |
| `.github/workflows/` | `ci.yml` (gate) · `publish.yml` (Trusted Publishing on `v*` tags). |

## Architecture

```
HeleketPayment / HeleketPayout      (one method per endpoint; typed in, typed out)
   └─ BaseClient                    (the ONLY place that does HTTP: _post / _get → _send)
        ├─ ClientOptions            (base_url, timeout, debug, logger, transport)
        ├─ sign()                   (md5(base64(body) + api_key); constant_time_equal)
        ├─ Transport (Protocol)     → RequestsTransport (default, swappable)
        └─ DebugSink                (request/response trace when debug=True)

WebhookVerifier → WebhookPayload                 (verify inbound signatures)
PaymentStatus / PayoutStatus / AmlLinkStatus     (is_final(), is_successful())
HeleketError ← ApiError / ValidationError / HttpError / SignatureError
types.py                                         (Pydantic request/response models)
```

`src/heleket_sdk/_base_client.py::_send()` is the heart: it encodes params
(`model_dump(by_alias=True, exclude_none=True)`), signs the **exact** bytes, sets
the `merchant` / `sign` / `Content-Type` / `User-Agent` headers, dispatches via the
transport, and turns the response into either the parsed `result` or a typed error.
`_post` and `_get` both delegate to `_send`.

## Conventions (follow these)

- **Typed in, typed out.** Endpoints take Pydantic request models (defined in
  `types.py`) and return Pydantic response models. Response models use
  `extra="ignore"`, so new server fields never break deserialization.
- **Sign the exact wire bytes.** `_encode_body` yields the JSON string and `sign()`
  hashes that same string. No params / empty dict → `""` → sign collapses to
  `md5(api_key)`. Never re-encode between signing and sending.
- **Drop nulls.** Optional fields default to `None` and are stripped via
  `exclude_none=True` (Pydantic) or a comprehension (raw dicts).
- **Keyword-only credentials.** `HeleketPayment(merchant_id=..., api_key=..., options=...)`;
  positional args are rejected to prevent silently swapping the two strings.
- **Error model:** HTTP 422 → `ValidationError` (`.fields` = per-field messages);
  `state != 0` → `ApiError` (`.http_status`, `.raw_body`); transport failure →
  `HttpError`; bad webhook signature → `SignatureError`. All extend `HeleketError`.
- **`from __future__ import annotations`** in every module; Python 3.11+ syntax;
  clients are thread-safe (immutable config + shared `requests.Session`).

## How to add an endpoint

1. Add request/response models to `types.py` (snake_case fields; alias only for
   `from` and Heleket's camelCase pagination keys).
2. Add a method to `HeleketPayment` / `HeleketPayout` calling
   `self._post("/v1/...", request)` (or `self._get(path)` for read-only,
   path-only endpoints; call with no args for an empty body). Guard
   "one of uuid/order_id" preconditions with `ValueError`. Return
   `Model.model_validate(result)`.
3. Add a unit test in `tests/test_payment.py` / `test_payout.py` using
   `FakeTransport` — assert method, URL, signed headers, body, and parsed result.
   No network.
4. If user-facing, add a runnable `examples/NN_*.py` (+ a `Makefile` target).
5. Run `make qa`.

## Running things

```bash
make install      # poetry install --with dev
make test         # pytest -q
make lint         # ruff check .
make fmt          # ruff format .
make typecheck    # mypy (strict)
make qa           # lint + format-check + typecheck + tests (the gate; CI runs 3.11 & 3.12)
```

Tests are fully offline via `FakeTransport` — never hit the real API in tests.
Examples read credentials from `.env` (copy `.env.example`).

## Gotchas (do not get these wrong)

- **Webhook byte-fidelity trap.** Use `WebhookVerifier.verify_raw(raw_bytes)` in
  production — it hashes the exact bytes Heleket sent (PHP-style `\/` slash
  escapes, insertion-order keys). `verify(decoded_dict)` re-encodes via
  `json.dumps` and is convenience-only — **not** safe for real traffic. See
  [`docs/06-webhooks.md`](docs/06-webhooks.md).
- **Two separate API keys.** Payments and payouts use different keys; a webhook of
  the wrong kind fails verification. `HeleketPayment` vs `HeleketPayout`.
- **Refund is the cross-key exception.** `/v1/payment/refund` is a payment-domain
  path but is signed with the **payout** key, so it lives on
  `HeleketPayout.refund()`. `HeleketPayment` does **not** expose `refund()` —
  calling it raises `AttributeError`.
- **`get_exchange_rates` is the only GET** (`/v1/exchange-rate/{ccy}/list`; input
  in the path, empty signed body). Every other endpoint is a POST, even reads.
- **AML links** (`get_aml_links(uuid=None, order_id=None)`) return questionnaire
  links for a blocked (`locked`) payment; statuses are `AmlLinkStatus`.
- **Always verify webhook signatures** before trusting a payload; whitelist
  Heleket's source IP `31.133.220.8`.
- **Never log API keys.** Debug entries carry method, URL, and body only — never
  the `sign` header or the key.

## Releasing / versioning

- One PyPI package = one repo: published from `github.com/Heleket/python-sdk`.
- Version lives in **two** places: `pyproject.toml` and
  `src/heleket_sdk/_version.py` (the latter feeds the `User-Agent`). **Bump both.**
- Tagging `vX.Y.Z` triggers [`.github/workflows/publish.yml`](.github/workflows/publish.yml),
  which builds, `twine check`s, asserts the tag matches the `pyproject` version,
  and publishes to PyPI via **Trusted Publishing** (OIDC — no API tokens).
- See [`CHANGELOG.md`](CHANGELOG.md) and [`UPGRADING.md`](UPGRADING.md).

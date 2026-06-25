# 03 — Architecture

```
┌───────────────────────┐    ┌───────────────────────┐
│ HeleketPayment        │    │ HeleketPayout         │
│  • create_invoice     │    │  • create_payout      │
│  • get_info           │    │  • refund             │
│  • get_aml_links      │    │  • get_info           │
│  • list_history       │    │  • list_history       │
│  • create_static_wallet│   │  • calculate_withdrawal│
│  • list_services      │    │  • list_services      │
│  • get_balance        │    │  • transfer_to_*      │
│  • get_exchange_rates │    │                       │
└──────────┬────────────┘    └──────────┬────────────┘
           │                            │
           └────────────┬───────────────┘
                        ▼
                ┌────────────────────┐
                │ BaseClient         │   encode → sign → dispatch → parse envelope
                └────────┬───────────┘
                         ▼
                ┌────────────────────┐    ┌──────────────────┐
                │ Transport (proto)  │ ←── │ DebugSink         │
                └────────┬───────────┘    └──────────────────┘
                         ▼
                ┌─────────────────────────┐
                │ RequestsTransport       │   uses `requests.Session`
                └─────────────────────────┘
```

## Modules and responsibilities

| Module | Role |
|---|---|
| `heleket_sdk` | Public re-exports — `HeleketPayment`, `HeleketPayout`, `ClientOptions`, status enums, errors |
| `heleket_sdk.types` | Request and response Pydantic models |
| `heleket_sdk._errors` | Exception hierarchy (all extend `HeleketError`, all unchecked) |
| `heleket_sdk._transport` | `Transport` Protocol + default `RequestsTransport` |
| `heleket_sdk._debug` | `DebugSink`, `DebugEntry`, `stderr_sink` |
| `heleket_sdk.webhook` | `WebhookVerifier`, `WebhookPayload` — separate so frameworks can import only what they need |

## Request lifecycle

1. **Encode.** `BaseClient._encode_body` runs the params through Pydantic's `model_dump(by_alias=True, exclude_none=True)` so unset optional fields drop out. `None` and empty objects serialise to the empty string.
2. **Sign.** `Signature.sign(body, api_key)` computes `md5(base64(body) + api_key)`. For empty bodies this collapses to `md5(api_key)`.
3. **Dispatch.** Headers are `merchant: <UUID>`, `sign: <hex>`, `Content-Type: application/json`. The `Transport` protocol owns the actual HTTP call.
4. **Debug.** If `debug=True`, request + response are dumped via the configured `DebugSink`.
5. **Parse.** `BaseClient._parse_response` unwraps `{state, result, message, errors}`. Non-zero `state` raises `ApiError`; HTTP 422 raises `ValidationError`; bad JSON raises `ApiError` with the raw body attached.

> The signing math is identical for both clients; only the key changes (payment key vs payout key). One endpoint crosses the divide: `/v1/payment/refund` is a payment-domain path signed with the **payout** key, so it lives on `HeleketPayout.refund()`.

## DTO design

- **Pydantic v2 models, not dataclasses.** Validates incoming data (catch wire-format drift early), and serialises with `model_dump(by_alias=True, exclude_none=True)` so unset fields are skipped.
- **Snake-case wire fields.** Python's convention matches the wire format, so most fields need no aliasing. Only `from` (Python keyword) and Heleket's CamelCase pagination keys (`nextCursor`, `hasPages`) use `Field(alias=...)`.
- **Optional fields use `None`.** Together with `exclude_none=True` in dumping, optional fields don't appear in the outgoing JSON.
- **Forward compatibility.** Response models set `model_config = ConfigDict(extra="ignore")` — if Heleket adds a field tomorrow, your code keeps deserializing.

## Concurrency

`requests.Session` is thread-safe for read operations and connection pooling. `HeleketPayment` / `HeleketPayout` hold only immutable config and the shared transport, so they're safe to share across threads. Construct once at startup, inject everywhere.

## Why two webhook methods

`WebhookVerifier.verify_raw(body)` hashes the raw bytes minus the `sign` field, surgically removed with a regex. This is the only entry point that survives Heleket's PHP-encoded payloads (insertion-order keys, escaped forward slashes).

`WebhookVerifier.verify(payload_dict)` re-encodes through `json.dumps` before hashing. It's a convenience for already-decoded payloads where you can't preserve the bytes — useful for fixtures and test doubles, **not safe for production traffic**.

# 10 — Reference

## Payment statuses (`PaymentStatus`)

| Enum | Wire value | Final? | Successful? |
|---|---|---|---|
| `PAID` | `paid` | yes | yes |
| `PAID_OVER` | `paid_over` | yes | yes |
| `WRONG_AMOUNT` | `wrong_amount` | yes | no |
| `PROCESS` | `process` | no | no |
| `CONFIRM_CHECK` | `confirm_check` | no | no |
| `WRONG_AMOUNT_WAITING` | `wrong_amount_waiting` | no | no |
| `CHECK` | `check` | no | no |
| `FAIL` | `fail` | yes | no |
| `CANCEL` | `cancel` | yes | no |
| `SYSTEM_FAIL` | `system_fail` | yes | no |
| `REFUND_PROCESS` | `refund_process` | no | no |
| `REFUND_FAIL` | `refund_fail` | yes | no |
| `REFUND_PAID` | `refund_paid` | yes | no |
| `LOCKED` | `locked` | yes | no |
| `UNKNOWN` | `unknown` | no | no |

`UNKNOWN` is the fallback when the server returns a string the SDK doesn't recognise — your code keeps running, but `is_final()`/`is_successful()` return `False`. Open an issue if you see it in production.

## Payout statuses (`PayoutStatus`)

| Enum | Wire value | Final? | Successful? |
|---|---|---|---|
| `PROCESS` | `process` | no | no |
| `CHECK` | `check` | no | no |
| `PAID` | `paid` | yes | yes |
| `FAIL` | `fail` | yes | no |
| `CANCEL` | `cancel` | yes | no |
| `SYSTEM_FAIL` | `system_fail` | yes | no |
| `UNKNOWN` | `unknown` | no | no |

## AML link statuses (`AmlLinkStatus`)

Returned per item by `get_aml_links()` for a blocked (locked) payment.

| Enum | Wire value | Final? | Successful? |
|---|---|---|---|
| `INIT` | `init` | no | no |
| `PENDING` | `pending` | no | no |
| `COMPLETED` | `completed` | yes | yes |
| `EXPIRED` | `expired` | yes | no |
| `UNKNOWN` | `unknown` | no | no |

`UNKNOWN` is the fallback when the server returns an unrecognised string, same as the other status enums.

## Course sources (`CourseSource`)

Sets which exchange-rate provider Heleket uses for fiat-to-crypto conversion.

| Enum | Wire value |
|---|---|
| `BINANCE` | `Binance` |
| `BINANCE_P2P` | `BinanceP2P` |
| `EXMO` | `Exmo` |
| `KUCOIN` | `Kucoin` |

## Endpoint cheat-sheet

### Payments (`HeleketPayment`)

| Method | HTTP | Path |
|---|---|---|
| `create_invoice` | POST | `/v1/payment` |
| `get_info` | POST | `/v1/payment/info` |
| `get_aml_links` | POST | `/v1/payment/aml-links` |
| `list_history` | POST | `/v1/payment/list` (+ `?cursor=`) |
| `create_static_wallet` | POST | `/v1/wallet` |
| `generate_qr_code` | POST | `/v1/wallet/qr` |
| `block_static_wallet` | POST | `/v1/wallet/block-address` |
| `refund_blocked_wallet` | POST | `/v1/wallet/blocked-address-refund` |
| `resend_webhook` | POST | `/v1/payment/resend` |
| `test_webhook` | POST | `/v1/test-webhook/{payment\|wallet}` |
| `list_services` | POST | `/v1/payment/services` |
| `get_balance` | POST | `/v1/balance` |
| `get_exchange_rates` | GET | `/v1/exchange-rate/{ccy}/list` |

### Payouts (`HeleketPayout`)

| Method | HTTP | Path |
|---|---|---|
| `create_payout` | POST | `/v1/payout` |
| `refund` | POST | `/v1/payment/refund` (signed with payout key) |
| `get_info` | POST | `/v1/payout/info` |
| `list_history` | POST | `/v1/payout/list` (+ `?cursor=`) |
| `calculate_withdrawal` | POST | `/v1/payout/calculate` |
| `list_services` | POST | `/v1/payout/services` |
| `transfer_to_personal` | POST | `/v1/transfer/to-personal` |
| `transfer_to_business` | POST | `/v1/transfer/to-business` |

Two things to note:

- **Most requests use POST**, even reads. The only `GET` is `get_exchange_rates` (`/v1/exchange-rate/{ccy}/list`) — it carries its input in the path, so the signed body is empty (`sign = md5(api_key)`).
- **`refund` is the only cross-key endpoint:** a payment-domain path (`/v1/payment/refund`) signed with the **payout** key, exposed as `HeleketPayout.refund()`. `HeleketPayment` does not expose `refund()`.

## Wire envelope

Every response looks like:

```json
{
  "state":  0,                 // 0 = success, non-zero = error
  "result": { ... },           // typed payload (object, array, or null)
  "message": "string",         // optional human-readable message
  "errors":  { ... }           // optional field → [messages] on 422
}
```

The SDK unwraps `result` for you. Use `ApiError.raw_body` if you ever need the full envelope.

## Signature formula

```
sign = md5( base64(json_body) + api_key )
```

`json_body` is the literal request body. For an empty body, `base64("")` is the empty string, so the formula collapses to `md5(api_key)`.

The Python implementation lives in `heleket_sdk.sign(bytes_or_str, api_key)` and produces byte-identical output to the PHP, Go, Node, and Java SDKs — there's a cross-language parity test in `tests/test_signature.py`.

## Webhook source IP

Add `31.133.220.8` to your reverse proxy / firewall allow-list.

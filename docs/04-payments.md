# 04 — Payments API

All operations live on `HeleketPayment`. Construct it with the merchant UUID + **payment** API key.

```python
from heleket_sdk import HeleketPayment

client = HeleketPayment(merchant_id=merchant_id, api_key=payment_key)
```

## Creating an invoice

```python
from heleket_sdk.types import CreateInvoiceRequest

invoice = client.create_invoice(
    CreateInvoiceRequest(
        amount="15.00",
        currency="USD",
        order_id="order-42",
        lifetime=3600,
        url_callback="https://your.site/heleket-webhook",
        url_success="https://your.site/thanks",
    )
)

print(invoice.url)     # payment page URL
print(invoice.uuid)    # Heleket's UUID
```

`amount` is a `str` to avoid float drift. Use `str(Decimal("15.00"))` if you carry money in `Decimal`.

## Looking up a payment

```python
from heleket_sdk.types import InfoOptions

invoice = client.get_info(InfoOptions.by_order_id("order-42"))
# or
invoice = client.get_info(InfoOptions.by_uuid("8b03432e-..."))
```

The SDK raises `ValueError` if you pass `InfoOptions()` with both fields empty — fail-fast instead of letting the server reject the call.

`invoice.effective_status()` returns `PaymentStatus.from(status or payment_status)`. Use it instead of switching on the raw string.

## Listing history

```python
from heleket_sdk.types import HistoryOptions

page = client.list_history(HistoryOptions(
    date_from="2024-01-01 00:00:00",
    date_to="2024-01-31 23:59:59",
))

for invoice in page.items:
    print(invoice.uuid, invoice.effective_status())

next_cursor = page.paginate.next_cursor if page.paginate else None
if next_cursor:
    page = client.list_history(HistoryOptions(cursor=next_cursor))
```

## Static (top-up) wallets

For subscriptions or recurring top-ups, create a long-lived wallet bound to one order ID. Repeated payments to that address all flow through the same `url_callback`.

```python
from heleket_sdk.types import CreateStaticWalletRequest

wallet = client.create_static_wallet(
    CreateStaticWalletRequest(currency="USDT", network="TRON", order_id="customer-7")
)

print(wallet.address)
```

When you need to retire a wallet:

```python
from heleket_sdk.types import BlockStaticWalletRequest

client.block_static_wallet(BlockStaticWalletRequest(order_id="customer-7"))
client.refund_blocked_wallet(wallet.uuid, recovery_address)
```

## QR codes

```python
qr = client.generate_qr_code(wallet.wallet_uuid)
# qr.image is a base64-encoded PNG; render it however you like.
```

## Refunds

```python
from heleket_sdk.types import RefundRequest

result = client.refund(RefundRequest(
    uuid="8b03...",
    address=customer_wallet_address,
    is_subtract=True,
))
```

`is_subtract=True` deducts the network fee from the refund (so the merchant absorbs only the amount).

## Test webhooks

Trigger a synthetic webhook to your `url_callback` so you can exercise your handler without making a real payment:

```python
from heleket_sdk.types import TestWebhookRequest

client.test_webhook(TestWebhookRequest(
    type="payment",                                # or "wallet"
    url_callback="https://your.site/heleket-webhook",
    status="paid",                                 # any status
    order_id="order-42",
))
```

## Balance + services + rates

```python
balance = client.get_balance()
for row in balance.merchant:
    print(row.currency_code, row.balance)

services = client.list_services()
rates = client.get_exchange_rates("USD")
```

## Errors

```python
from heleket_sdk import ApiError, HttpError, ValidationError

try:
    client.create_invoice(...)
except ValidationError as e:
    # HTTP 422 — Heleket rejected the input.
    for field, messages in e.fields.items():
        log.warning("  %s: %s", field, ", ".join(messages))
except ApiError as e:
    # state != 0 — business error.
    log.error("Heleket said: %s (HTTP %s)", e, e.http_status)
except HttpError as e:
    # Transport failure — DNS, TCP, TLS, timeout.
    log.error("Could not reach Heleket: %s", e)
```

See [09 — Error handling](09-error-handling.md) for the full hierarchy.

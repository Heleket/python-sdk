# 05 — Payouts API

All operations live on `HeleketPayout`. Construct it with the merchant UUID + **payout** API key (distinct from the payment key — see [02 — Configuration](02-configuration.md)).

```python
from heleket_sdk import HeleketPayout

client = HeleketPayout(merchant_id=merchant_id, api_key=payout_key)
```

## Creating a payout

```python
from heleket_sdk.types import CreatePayoutRequest

payout = client.create_payout(CreatePayoutRequest(
    amount="5",
    currency="USDT",
    order_id="po-1",
    address="TXyzAddress...",
    is_subtract=True,
    network="TRON",
    url_callback="https://your.site/heleket-payout-webhook",
))

print(payout.status.value)  # process | check | paid | fail | cancel | system_fail
```

`is_subtract=True` means the network fee comes off the payout amount (recipient receives `amount - commission`). `False` means the merchant covers the fee.

## Looking up a payout

```python
from heleket_sdk.types import InfoOptions

payout = client.get_info(InfoOptions.by_order_id("po-1"))
# or
payout = client.get_info(InfoOptions.by_uuid("8b03432e-..."))
```

Use `payout.status.is_final()` to check for terminal states. See [10 — Reference](10-reference.md) for the status table.

## Calculating a withdrawal before sending

Preview the commission without actually creating a payout:

```python
from heleket_sdk.types import CalculateRequest

calc = client.calculate_withdrawal(
    CalculateRequest(currency="USDT", network="TRON", amount="100")
)

print(f"commission: {calc.commission}")
print(f"you receive: {calc.merchant_amount}")
```

## Listing payout history

Same pattern as payment history:

```python
from heleket_sdk.types import HistoryOptions

page = client.list_history(HistoryOptions())
next_cursor = page.paginate.next_cursor if page.paginate else None
```

## Catalogue of supported pairs

```python
services = client.list_services()
for s in services:
    print(f"{s.currency} {s.network} available={s.is_available}")
```

## Transfers between business and personal balances

```python
t1 = client.transfer_to_personal("10", "USDT")
t2 = client.transfer_to_business("5", "USDT")
```

## Errors

Same hierarchy as `HeleketPayment` — catch `ValidationError`, `ApiError`, `HttpError`. See [09 — Error handling](09-error-handling.md).

## Webhook for the payout lifecycle

Heleket calls your `url_callback` with `type="payout"`. Verify it with the **payout** API key:

```python
from heleket_sdk import WebhookVerifier

verifier = WebhookVerifier(payout_api_key)
payload = verifier.verify_raw(raw_bytes)

if payload.is_payout() and payload.is_final() and payload.is_successful():
    # Mark the order paid out.
    ...
```

Details: [06 — Webhooks](06-webhooks.md).

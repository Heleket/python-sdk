# Upgrading

## 0.3 → 0.4

The default API host moved from `api.heleket.com` to `api.heleket.hk`. No code
changes are needed unless you hard-coded the old host. To keep using another
domain, pass `ClientOptions(domain="heleket.com")` (requests go to
`https://api.<domain>`); an explicit `base_url` still takes precedence.
`ClientOptions.base_url` now defaults to `None` and is resolved to a `str` on
construction, so `options.base_url` is always a string.

## 0.2 → 0.3

`refund` moved from `HeleketPayment` to `HeleketPayout`. The Heleket API now signs
`POST /v1/payment/refund` with the **payout** API key, so a payment client can no
longer produce a valid signature for it.

`HeleketPayment` no longer exposes `refund()` — calling it raises `AttributeError`.
Switch to `HeleketPayout.refund()`:

```python
from heleket_sdk import HeleketPayment, HeleketPayout
from heleket_sdk.types import RefundRequest

# Before (0.2 and earlier)
payment = HeleketPayment(merchant_id=merchant_id, api_key=payment_key)
payment.refund(RefundRequest(uuid=invoice_uuid, address=addr, is_subtract=True))

# After (0.3)
payout = HeleketPayout(merchant_id=merchant_id, api_key=payout_key)
payout.refund(RefundRequest(uuid=invoice_uuid, address=addr, is_subtract=True))
```

Everything else is unchanged.

## 0.1 → 0.2

Purely additive — no caller changes required:

- New `HeleketPayment.get_aml_links(uuid=None, order_id=None)` returns the
  AML/KYC/SoF questionnaire links for a blocked (locked) payment, alongside a new
  `AmlLinkStatus` enum with `is_final()` / `is_successful()` helpers.
- `HeleketPayment.get_exchange_rates()` now issues a `GET` request instead of a
  `POST`. The method signature and return type are identical, so existing code
  keeps working.

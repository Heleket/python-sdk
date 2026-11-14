# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-11-14

### Added
- `ClientOptions(domain=...)` (default `"heleket.hk"`) and `DEFAULT_DOMAIN`.
  Requests go to `https://api.<domain>`; an explicit `base_url` still wins.
- Examples read `HELEKET_DOMAIN` alongside `HELEKET_BASE_URL`.

### Changed
- The default domain is now `heleket.hk` (was `heleket.com`): API host
  `https://api.heleket.hk`, docs and links updated. `ClientOptions.base_url`
  now defaults to `None` and is resolved to a `str` in `__post_init__`.
  See [`UPGRADING.md`](UPGRADING.md).

## [0.3.0] - 2026-06-25

### Added
- `HeleketPayout.refund(request)` → `POST /v1/payment/refund`. Refunds are now
  signed with the **payout** API key, so the method lives on `HeleketPayout`.

### Removed
- `HeleketPayment.refund()`. The Heleket API signs `/v1/payment/refund` with the
  payout key, which a payment client does not hold, so it can no longer sign a
  valid refund. Use `HeleketPayout.refund()` instead — e.g.
  `HeleketPayout(merchant_id=merchant_id, api_key=payout_key).refund(request)`.
  See [`UPGRADING.md`](UPGRADING.md).

## [0.2.0] - 2026-06-25

### Added
- `HeleketPayment.get_aml_links(uuid=None, order_id=None)` → `POST
  /v1/payment/aml-links`: AML/KYC/SoF questionnaire links for a blocked (locked)
  payment, plus `AmlLinkStatus` with `is_final()` / `is_successful()` helpers.

### Changed
- `HeleketPayment.get_exchange_rates()` now issues a `GET` request (was `POST`).
  The method signature and return type are unchanged.

## [0.1.0]

Initial reference implementation of the Heleket cryptocurrency payment API.

### Added
- `HeleketPayment` / `HeleketPayout` clients with typed Pydantic request/response
  models.
- Payments API: invoices, info, history, static wallets, QR codes, refunds,
  webhook resend, test webhooks.
- Payouts API: payouts, info, history, fee calculation, transfers, services.
- Balance and exchange-rate endpoints.
- Signed webhook verification (`WebhookVerifier`, `WebhookPayload`) with
  constant-time comparison.
- Swappable HTTP transport (`Transport`, `RequestsTransport`, plus `FakeTransport`
  for offline tests).
- Debug mode (`DebugSink`) and a webhook inspector CLI (`heleket-webhook-inspect`).
- Status enums (`PaymentStatus`, `PayoutStatus`) with `is_final()` /
  `is_successful()` helpers.

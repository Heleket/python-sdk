"""Client for the Heleket Payments API plus balance + exchange-rate endpoints.

Construct with the merchant UUID and the payment API key. Pass an optional
:class:`ClientOptions` to tune timeouts, debug logging, or the HTTP transport.

The client is thread-safe — it carries only immutable config and a
thread-safe ``requests.Session``. Share a single instance across all your
request handlers.

Errors:

* :class:`ValidationError` on HTTP 422
* :class:`ApiError` on any other ``state != 0``
* :class:`HttpError` on transport failure
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from ._base_client import BaseClient
from ._errors import ApiError
from .types import (
    Balance,
    BlockedWallet,
    BlockStaticWalletRequest,
    CreateInvoiceRequest,
    CreateStaticWalletRequest,
    ExchangeRate,
    HistoryOptions,
    HistoryPage,
    InfoOptions,
    Invoice,
    QrCode,
    RefundRequest,
    RefundResult,
    Service,
    StaticWallet,
    TestWebhookRequest,
)

if TYPE_CHECKING:
    from ._config import ClientOptions

__all__ = ["HeleketPayment"]


class HeleketPayment(BaseClient):
    """Client for ``/v1/payment/*``, ``/v1/wallet/*``, ``/v1/balance``, ``/v1/exchange-rate/*``."""

    def __init__(
        self,
        *,
        merchant_id: str,
        api_key: str,
        options: ClientOptions | None = None,
    ) -> None:
        super().__init__(merchant_id=merchant_id, api_key=api_key, options=options)

    # ---------- invoices ----------------------------------------------------

    def create_invoice(self, request: CreateInvoiceRequest) -> Invoice:
        """Create a new invoice."""
        result = self._post("/v1/payment", request)
        return Invoice.model_validate(result)

    def get_info(self, options: InfoOptions) -> Invoice:
        """Look up an invoice by UUID or ``order_id``."""
        if options.is_empty():
            raise ValueError("heleket: one of uuid or order_id must be set")
        result = self._post("/v1/payment/info", options)
        return Invoice.model_validate(result)

    def list_history(self, options: HistoryOptions) -> HistoryPage[Invoice]:
        """Paginated payment history."""
        path = "/v1/payment/list"
        if options.cursor:
            path = f"{path}?cursor={quote(options.cursor)}"
        result = self._post(path, options)
        return HistoryPage[Invoice].model_validate(result)

    # ---------- static wallets ----------------------------------------------

    def create_static_wallet(self, request: CreateStaticWalletRequest) -> StaticWallet:
        """Create a persistent top-up wallet bound to an ``order_id``."""
        result = self._post("/v1/wallet", request)
        return StaticWallet.model_validate(result)

    def generate_qr_code(self, merchant_payment_uuid: str) -> QrCode:
        """Generate a base64 QR-code image for an existing static wallet."""
        result = self._post(
            "/v1/wallet/qr",
            {"merchant_payment_uuid": merchant_payment_uuid},
        )
        return QrCode.model_validate(result)

    def block_static_wallet(self, request: BlockStaticWalletRequest) -> BlockedWallet:
        """Stop a static wallet from accepting further transfers."""
        if request.is_empty():
            raise ValueError("heleket: one of uuid or order_id must be set")
        result = self._post("/v1/wallet/block-address", request)
        return BlockedWallet.model_validate(result)

    def refund_blocked_wallet(self, uuid: str, address: str) -> RefundResult:
        """Send the contents of a blocked wallet to a recovery address."""
        result = self._post(
            "/v1/wallet/blocked-address-refund",
            {"uuid": uuid, "address": address},
        )
        return RefundResult.model_validate(result)

    # ---------- refunds + replays ------------------------------------------

    def refund(self, request: RefundRequest) -> RefundResult:
        """Refund an invoice in full or in part."""
        if request.is_empty():
            raise ValueError("heleket: one of uuid or order_id must be set")
        result = self._post("/v1/payment/refund", request)
        return RefundResult.model_validate(result)

    def resend_webhook(self, options: InfoOptions) -> None:
        """Ask Heleket to redeliver the last webhook for the invoice."""
        if options.is_empty():
            raise ValueError("heleket: one of uuid or order_id must be set")
        self._post("/v1/payment/resend", options)

    def test_webhook(self, request: TestWebhookRequest) -> None:
        """Send a synthetic webhook event to the merchant's callback URL."""
        if request.type not in ("payment", "wallet"):
            raise ValueError("heleket: TestWebhookRequest.type must be 'payment' or 'wallet'")
        if request.is_empty_identifier():
            raise ValueError("heleket: one of uuid or order_id must be set")
        self._post(f"/v1/test-webhook/{request.type}", request)

    # ---------- catalogue + balance + rates --------------------------------

    def list_services(self) -> list[Service]:
        """Catalogue of supported (currency, network) pairs for payments."""
        result = self._post("/v1/payment/services")
        if result is None:
            return []
        return [Service.model_validate(item) for item in result]

    def get_balance(self) -> Balance:
        """Merchant + personal balances by currency.

        The API wraps the data in a one-element array of ``{ balance: {...} }`` —
        we unwrap it here so callers get a clean :class:`Balance` instance.
        """
        result = self._post("/v1/balance")
        if not isinstance(result, list) or not result:
            return Balance()
        first = result[0]
        if not isinstance(first, dict):
            raise ApiError("failed to decode balance: expected dict", 200, str(first))
        balance = first.get("balance")
        if balance is None:
            return Balance()
        return Balance.model_validate(balance)

    def get_exchange_rates(self, currency: str) -> list[ExchangeRate]:
        """Exchange-rate list for a given fiat currency."""
        path = f"/v1/exchange-rate/{quote(currency)}/list"
        result = self._post(path)
        if result is None:
            return []
        return [ExchangeRate.model_validate(item) for item in result]

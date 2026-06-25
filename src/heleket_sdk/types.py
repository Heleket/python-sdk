"""Pydantic models for every Heleket request and response.

Every model uses ``alias_generator=to_camel_snake`` so snake_case wire fields
map to Python attribute names of the same shape — Python is one of the few
languages where idiom and wire format already agree.

Optional outgoing fields default to ``None`` and are stripped on serialisation
(see ``BaseClient._encode_body``). Response models set
``model_config = ConfigDict(extra="ignore")`` so unknown future fields don't
crash deserialisation.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from ._status import AmlLinkStatus, CourseSource, PaymentStatus, PayoutStatus

__all__ = [
    # Requests
    "CreateInvoiceRequest",
    "CreateStaticWalletRequest",
    "BlockStaticWalletRequest",
    "RefundRequest",
    "TestWebhookRequest",
    "InfoOptions",
    "HistoryOptions",
    "CreatePayoutRequest",
    "CalculateRequest",
    "CurrencyNetwork",
    # Responses
    "Invoice",
    "StaticWallet",
    "QrCode",
    "BlockedWallet",
    "RefundResult",
    "AmlLink",
    "Service",
    "ServiceLimit",
    "ServiceCommission",
    "Balance",
    "WalletBalance",
    "ExchangeRate",
    "Payout",
    "Calculation",
    "Transfer",
    "HistoryPage",
    "Pagination",
    "Conversion",
]

T = TypeVar("T")

_REQUEST_CONFIG = ConfigDict(populate_by_name=True, extra="forbid")
_RESPONSE_CONFIG = ConfigDict(extra="ignore", populate_by_name=True)


# ---------- shared --------------------------------------------------------------


class CurrencyNetwork(BaseModel):
    """A (currency, network) pair — used by ``currencies`` and ``except_currencies``."""

    model_config = _REQUEST_CONFIG

    currency: str
    network: str | None = None


# ---------- payments: requests ----------------------------------------------


class CreateInvoiceRequest(BaseModel):
    model_config = _REQUEST_CONFIG

    amount: str
    currency: str
    order_id: str
    network: str | None = None
    url_return: str | None = None
    url_success: str | None = None
    url_callback: str | None = None
    is_payment_multiple: bool | None = None
    lifetime: int | None = None
    to_currency: str | None = None
    subtract: int | None = None
    accuracy_payment_percent: str | None = None
    additional_data: str | None = None
    currencies: list[CurrencyNetwork] | None = None
    except_currencies: list[CurrencyNetwork] | None = None
    course_source: CourseSource | None = None
    from_referral_code: str | None = None
    discount_percent: int | None = None
    is_refresh: bool | None = None
    payer_email: str | None = None


class CreateStaticWalletRequest(BaseModel):
    model_config = _REQUEST_CONFIG

    currency: str
    network: str
    order_id: str
    url_callback: str | None = None


class BlockStaticWalletRequest(BaseModel):
    model_config = _REQUEST_CONFIG

    uuid: str | None = None
    order_id: str | None = None
    is_force_refund: bool | None = None

    def is_empty(self) -> bool:
        return not (self.uuid or self.order_id)


class RefundRequest(BaseModel):
    model_config = _REQUEST_CONFIG

    address: str
    is_subtract: bool
    uuid: str | None = None
    order_id: str | None = None

    def is_empty(self) -> bool:
        return not (self.uuid or self.order_id)


class TestWebhookRequest(BaseModel):
    """Request for ``POST /v1/test-webhook/{payment|wallet|payout}``."""

    model_config = _REQUEST_CONFIG

    type: str = Field(description="payment | wallet | payout")
    url_callback: str
    currency: str | None = None
    network: str | None = None
    uuid: str | None = None
    order_id: str | None = None
    status: str | None = None

    def is_empty_identifier(self) -> bool:
        return not (self.uuid or self.order_id)


class InfoOptions(BaseModel):
    """Identifier for ``uuid OR order_id`` read endpoints."""

    model_config = _REQUEST_CONFIG

    uuid: str | None = None
    order_id: str | None = None

    @classmethod
    def by_uuid(cls, uuid: str) -> InfoOptions:
        return cls(uuid=uuid)

    @classmethod
    def by_order_id(cls, order_id: str) -> InfoOptions:
        return cls(order_id=order_id)

    def is_empty(self) -> bool:
        return not (self.uuid or self.order_id)


class HistoryOptions(BaseModel):
    """Filter for the paginated history endpoints.

    The ``cursor`` field is NOT sent as a body field — it goes on the URL.
    Annotate it as a Pydantic ``Field(exclude=True)``.
    """

    model_config = _REQUEST_CONFIG

    date_from: str | None = None
    date_to: str | None = None
    cursor: str | None = Field(default=None, exclude=True)


# ---------- payments: responses ---------------------------------------------


class Conversion(BaseModel):
    model_config = _RESPONSE_CONFIG

    to_currency: str | None = None
    commission: str | None = None
    rate: str | None = None
    amount: str | None = None


class Invoice(BaseModel):
    model_config = _RESPONSE_CONFIG

    uuid: str | None = None
    order_id: str | None = None
    amount: str | None = None
    payment_amount: str | None = None
    payment_amount_usd: str | None = None
    payer_amount: str | None = None
    payer_currency: str | None = None
    currency: str | None = None
    merchant_amount: str | None = None
    network: str | None = None
    address: str | None = None
    from_address: str | None = Field(default=None, alias="from")
    txid: str | None = None
    payment_status: PaymentStatus | None = None
    status: PaymentStatus | None = None
    url: str | None = None
    expired_at: int | None = None
    is_final: bool | None = None
    additional_data: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    commission: str | None = None
    address_qr_code: str | None = None
    discount_percent: int | None = None
    discount: str | None = None
    convert: Conversion | None = None

    def effective_status(self) -> PaymentStatus | None:
        """Return ``status`` if set, otherwise ``payment_status``."""
        return self.status if self.status is not None else self.payment_status


class StaticWallet(BaseModel):
    model_config = _RESPONSE_CONFIG

    uuid: str | None = None
    wallet_uuid: str | None = None
    order_id: str | None = None
    address: str | None = None
    network: str | None = None
    currency: str | None = None
    url: str | None = None


class QrCode(BaseModel):
    model_config = _RESPONSE_CONFIG

    image: str | None = None


class BlockedWallet(BaseModel):
    model_config = _RESPONSE_CONFIG

    uuid: str | None = None
    status: str | None = None


class RefundResult(BaseModel):
    model_config = _RESPONSE_CONFIG

    # The /v1/payment/refund response is essentially "ok / not ok" — the API
    # echoes whatever metadata is convenient.
    commission: str | None = None
    amount: str | None = None
    currency: str | None = None
    txid: str | None = None
    network: str | None = None
    address: str | None = None
    status: str | None = None


class AmlLink(BaseModel):
    """One AML/KYC/SoF questionnaire link for a blocked (locked) payment.

    Returned per item by :meth:`HeleketPayment.get_aml_links`. Hand ``link`` to
    the end user to complete the questionnaire and unblock the payment.
    """

    model_config = _RESPONSE_CONFIG

    link: str | None = None
    expired_at: str | None = None
    status: AmlLinkStatus | None = None


class ServiceLimit(BaseModel):
    model_config = _RESPONSE_CONFIG

    min_amount: str | None = None
    max_amount: str | None = None


class ServiceCommission(BaseModel):
    model_config = _RESPONSE_CONFIG

    fee_amount: str | None = None
    percent: str | None = None


class Service(BaseModel):
    model_config = _RESPONSE_CONFIG

    network: str | None = None
    currency: str | None = None
    is_available: bool | None = None
    limit: ServiceLimit | None = None
    commission: ServiceCommission | None = None


class WalletBalance(BaseModel):
    model_config = _RESPONSE_CONFIG

    uuid: str | None = None
    balance: str | None = None
    currency_code: str | None = None


class Balance(BaseModel):
    model_config = _RESPONSE_CONFIG

    merchant: list[WalletBalance] = Field(default_factory=list)
    user: list[WalletBalance] = Field(default_factory=list)


class ExchangeRate(BaseModel):
    model_config = _RESPONSE_CONFIG

    from_currency: str | None = Field(default=None, alias="from")
    to: str | None = None
    course: str | None = None
    source: str | None = None


# ---------- payouts ---------------------------------------------------------


class CreatePayoutRequest(BaseModel):
    model_config = _REQUEST_CONFIG

    amount: str
    currency: str
    order_id: str
    address: str
    is_subtract: bool
    network: str | None = None
    url_callback: str | None = None
    to_currency: str | None = None
    course_source: str | None = None
    from_currency: str | None = None
    priority: str | None = None
    memo: str | None = None


class CalculateRequest(BaseModel):
    model_config = _REQUEST_CONFIG

    currency: str
    network: str
    amount: str
    is_subtract: bool | None = None


class Payout(BaseModel):
    model_config = _RESPONSE_CONFIG

    uuid: str | None = None
    amount: str | None = None
    currency: str | None = None
    commission: str | None = None
    merchant_amount: str | None = None
    network: str | None = None
    address: str | None = None
    txid: str | None = None
    status: PayoutStatus | None = None
    is_final: bool | None = None
    balance: Any = None  # mixed type in the API (number or string)
    payer_currency: str | None = None
    payer_amount: Any = None
    order_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Calculation(BaseModel):
    model_config = _RESPONSE_CONFIG

    commission: str | None = None
    merchant_amount: str | None = None
    amount: str | None = None
    network: str | None = None
    currency: str | None = None


class Transfer(BaseModel):
    model_config = _RESPONSE_CONFIG

    user_wallet_uuid: str | None = None
    merchant_wallet_uuid: str | None = None
    amount: str | None = None
    currency: str | None = None


# ---------- pagination -------------------------------------------------------


class Pagination(BaseModel):
    model_config = _RESPONSE_CONFIG

    count: int | None = None
    has_pages: bool | None = Field(default=None, alias="hasPages")
    next_cursor: str | None = Field(default=None, alias="nextCursor")
    previous_cursor: str | None = Field(default=None, alias="previousCursor")
    per_page: int | None = Field(default=None, alias="perPage")


class HistoryPage(BaseModel, Generic[T]):
    model_config = _RESPONSE_CONFIG

    items: list[T] = Field(default_factory=list)
    paginate: Pagination | None = None

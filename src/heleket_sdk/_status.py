"""Status enums for payments and payouts.

Both enums use string values (the literal wire format) and override
``_missing_`` so unrecognised values fall back to ``UNKNOWN`` rather than
crashing — keeps merchant code running when Heleket introduces a new status.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["PaymentStatus", "PayoutStatus", "AmlLinkStatus", "CourseSource"]


class PaymentStatus(StrEnum):
    """Payment statuses. See https://doc.heleket.hk/methods/payments/payment-statuses."""

    PAID = "paid"
    PAID_OVER = "paid_over"
    WRONG_AMOUNT = "wrong_amount"
    PROCESS = "process"
    CONFIRM_CHECK = "confirm_check"
    WRONG_AMOUNT_WAITING = "wrong_amount_waiting"
    CHECK = "check"
    FAIL = "fail"
    CANCEL = "cancel"
    SYSTEM_FAIL = "system_fail"
    REFUND_PROCESS = "refund_process"
    REFUND_FAIL = "refund_fail"
    REFUND_PAID = "refund_paid"
    LOCKED = "locked"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PaymentStatus:
        return cls.UNKNOWN

    def is_final(self) -> bool:
        """Reports whether the status is terminal — invoice won't transition further."""
        return self in _PAYMENT_FINAL

    def is_successful(self) -> bool:
        """Reports whether the status represents a successful payment."""
        return self in (PaymentStatus.PAID, PaymentStatus.PAID_OVER)


_PAYMENT_FINAL: frozenset[PaymentStatus] = frozenset(
    {
        PaymentStatus.PAID,
        PaymentStatus.PAID_OVER,
        PaymentStatus.WRONG_AMOUNT,
        PaymentStatus.FAIL,
        PaymentStatus.CANCEL,
        PaymentStatus.SYSTEM_FAIL,
        PaymentStatus.REFUND_FAIL,
        PaymentStatus.REFUND_PAID,
        PaymentStatus.LOCKED,
    }
)


class PayoutStatus(StrEnum):
    """Payout statuses. See https://doc.heleket.hk/methods/payouts/payout-statuses."""

    PROCESS = "process"
    CHECK = "check"
    PAID = "paid"
    FAIL = "fail"
    CANCEL = "cancel"
    SYSTEM_FAIL = "system_fail"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> PayoutStatus:
        return cls.UNKNOWN

    def is_final(self) -> bool:
        return self in _PAYOUT_FINAL

    def is_successful(self) -> bool:
        return self is PayoutStatus.PAID


_PAYOUT_FINAL: frozenset[PayoutStatus] = frozenset(
    {PayoutStatus.PAID, PayoutStatus.FAIL, PayoutStatus.CANCEL, PayoutStatus.SYSTEM_FAIL}
)


class AmlLinkStatus(StrEnum):
    """AML/KYC/SoF questionnaire-link statuses.

    Returned per item by :meth:`HeleketPayment.get_aml_links` for a blocked
    (locked) payment. "Final" statuses are terminal — the link won't transition
    further; intermediate statuses may still change while the user works through
    the questionnaire.
    """

    INIT = "init"
    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> AmlLinkStatus:
        return cls.UNKNOWN

    def is_final(self) -> bool:
        """Reports whether the link is terminal — it won't transition further."""
        return self in _AML_LINK_FINAL

    def is_successful(self) -> bool:
        """Reports whether the questionnaire was completed."""
        return self is AmlLinkStatus.COMPLETED


_AML_LINK_FINAL: frozenset[AmlLinkStatus] = frozenset(
    {AmlLinkStatus.COMPLETED, AmlLinkStatus.EXPIRED}
)


class CourseSource(StrEnum):
    """Exchange-rate sources accepted by create-invoice and create-payout."""

    BINANCE = "Binance"
    BINANCE_P2P = "BinanceP2P"
    EXMO = "Exmo"
    KUCOIN = "Kucoin"

"""Status enum behaviour."""

from __future__ import annotations

from heleket_sdk import AmlLinkStatus, PaymentStatus, PayoutStatus


def test_payment_wire_values_round_trip() -> None:
    for status in PaymentStatus:
        assert PaymentStatus(status.value) is status


def test_payment_unknown_wire_falls_back_to_unknown() -> None:
    assert PaymentStatus("not_a_real_status") is PaymentStatus.UNKNOWN


def test_payment_final_statuses() -> None:
    for s in (
        PaymentStatus.PAID,
        PaymentStatus.PAID_OVER,
        PaymentStatus.WRONG_AMOUNT,
        PaymentStatus.FAIL,
        PaymentStatus.CANCEL,
        PaymentStatus.SYSTEM_FAIL,
        PaymentStatus.REFUND_FAIL,
        PaymentStatus.REFUND_PAID,
        PaymentStatus.LOCKED,
    ):
        assert s.is_final(), s

    for s in (
        PaymentStatus.PROCESS,
        PaymentStatus.CONFIRM_CHECK,
        PaymentStatus.WRONG_AMOUNT_WAITING,
        PaymentStatus.CHECK,
        PaymentStatus.REFUND_PROCESS,
        PaymentStatus.UNKNOWN,
    ):
        assert not s.is_final(), s


def test_payment_successful_statuses() -> None:
    assert PaymentStatus.PAID.is_successful()
    assert PaymentStatus.PAID_OVER.is_successful()

    for s in (
        PaymentStatus.WRONG_AMOUNT,
        PaymentStatus.FAIL,
        PaymentStatus.CANCEL,
        PaymentStatus.PROCESS,
        PaymentStatus.REFUND_PAID,
    ):
        assert not s.is_successful(), s


def test_payout_wire_values_round_trip() -> None:
    for status in PayoutStatus:
        assert PayoutStatus(status.value) is status


def test_payout_unknown_wire_falls_back_to_unknown() -> None:
    assert PayoutStatus("not_a_real_status") is PayoutStatus.UNKNOWN


def test_payout_final_and_successful() -> None:
    assert PayoutStatus.PAID.is_final()
    assert PayoutStatus.PAID.is_successful()
    assert PayoutStatus.FAIL.is_final()
    assert not PayoutStatus.FAIL.is_successful()
    assert not PayoutStatus.PROCESS.is_final()
    assert not PayoutStatus.UNKNOWN.is_final()


def test_aml_link_wire_values_round_trip() -> None:
    for status in AmlLinkStatus:
        assert AmlLinkStatus(status.value) is status


def test_aml_link_unknown_wire_falls_back_to_unknown() -> None:
    assert AmlLinkStatus("not_a_real_status") is AmlLinkStatus.UNKNOWN


def test_aml_link_status_classification() -> None:
    assert AmlLinkStatus.COMPLETED.is_final()
    assert AmlLinkStatus.EXPIRED.is_final()
    assert not AmlLinkStatus.INIT.is_final()
    assert not AmlLinkStatus.PENDING.is_final()

    assert AmlLinkStatus.COMPLETED.is_successful()
    assert not AmlLinkStatus.EXPIRED.is_successful()
    assert not AmlLinkStatus.PENDING.is_successful()
    assert not AmlLinkStatus.INIT.is_successful()

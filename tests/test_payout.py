"""HeleketPayout behaviour."""

from __future__ import annotations

import base64
import hashlib

import pytest

from fakes import FakeTransport
from heleket_sdk import ApiError, ClientOptions, HeleketPayout
from heleket_sdk.types import (
    CalculateRequest,
    CreatePayoutRequest,
    InfoOptions,
    RefundRequest,
)

MERCHANT_ID = "8b03432e-385b-4670-8d06-064591096795"
API_KEY = "payout-key-xyz"


def _client(fake: FakeTransport) -> HeleketPayout:
    return HeleketPayout(
        merchant_id=MERCHANT_ID,
        api_key=API_KEY,
        options=ClientOptions(transport=fake),
    )


def _md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def test_create_payout_sends_signed_post() -> None:
    fake = FakeTransport().enqueue_json(
        {
            "state": 0,
            "result": {
                "uuid": "po-1",
                "amount": "5",
                "currency": "USDT",
                "status": "process",
                "order_id": "po-order-1",
            },
        }
    )

    payout = _client(fake).create_payout(
        CreatePayoutRequest(
            amount="5",
            currency="USDT",
            order_id="po-order-1",
            address="TXyz123",
            is_subtract=True,
            network="TRON",
            url_callback="https://example.com/cb",
        )
    )
    assert payout.uuid == "po-1"
    assert payout.currency == "USDT"

    sent = fake.last_request()
    assert sent.method == "POST"
    assert sent.url == "https://api.heleket.com/v1/payout"
    # snake_case must survive serialization (no camelCase)
    assert '"is_subtract":true' in sent.body
    assert '"order_id":"po-order-1"' in sent.body


def test_get_info_rejects_empty_input() -> None:
    fake = FakeTransport()
    with pytest.raises(ValueError):
        _client(fake).get_info(InfoOptions())


def test_calculate_withdrawal_round_trips() -> None:
    fake = FakeTransport().enqueue_json(
        {
            "state": 0,
            "result": {
                "commission": "0.5",
                "merchant_amount": "4.5",
                "amount": "5",
                "network": "TRON",
                "currency": "USDT",
            },
        }
    )

    calc = _client(fake).calculate_withdrawal(
        CalculateRequest(currency="USDT", network="TRON", amount="5")
    )
    assert calc.merchant_amount == "4.5"


def test_transfer_to_personal_sends_amount_and_currency() -> None:
    fake = FakeTransport().enqueue_json(
        {
            "state": 0,
            "result": {
                "user_wallet_uuid": "u-1",
                "merchant_wallet_uuid": "m-1",
                "amount": "1",
                "currency": "USDT",
            },
        }
    )

    transfer = _client(fake).transfer_to_personal("1", "USDT")
    assert transfer.user_wallet_uuid == "u-1"
    assert fake.last_request().url == "https://api.heleket.com/v1/transfer/to-personal"


def test_api_error_propagates() -> None:
    fake = FakeTransport().enqueue_json({"state": 1, "message": "insufficient funds"})
    with pytest.raises(ApiError):
        _client(fake).get_info(InfoOptions.by_uuid("po-1"))


def test_list_services_issues_empty_body() -> None:
    fake = FakeTransport().enqueue_json({"state": 0, "result": []})

    _client(fake).list_services()
    assert fake.last_request().body == ""
    assert fake.last_request().url == "https://api.heleket.com/v1/payout/services"


def test_refund_posts_to_payment_refund_signed_with_payout_key() -> None:
    fake = FakeTransport().enqueue_json(
        {"state": 0, "result": {"uuid": "inv-1", "status": "refund_process"}}
    )

    _client(fake).refund(RefundRequest(uuid="inv-1", address="TBaCkAdDrEsS", is_subtract=True))

    sent = fake.last_request()
    assert sent.method == "POST"
    assert sent.url == "https://api.heleket.com/v1/payment/refund"

    expected_body = '{"address":"TBaCkAdDrEsS","is_subtract":true,"uuid":"inv-1"}'
    assert sent.body == expected_body

    # The whole point of the move: refund is signed with the PAYOUT key.
    assert sent.headers["sign"] == _md5_hex(
        base64.b64encode(expected_body.encode("utf-8")).decode("ascii") + API_KEY
    )

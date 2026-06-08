"""HeleketPayment behaviour driven by FakeTransport."""

from __future__ import annotations

import base64
import hashlib

import pytest

from fakes import FakeTransport
from heleket_sdk import (
    ApiError,
    ClientOptions,
    HeleketPayment,
    HttpError,
    ValidationError,
)
from heleket_sdk.types import (
    CreateInvoiceRequest,
    HistoryOptions,
    InfoOptions,
)

MERCHANT_ID = "8b03432e-385b-4670-8d06-064591096795"
API_KEY = "payment-key-abc"


def _client(fake: FakeTransport) -> HeleketPayment:
    return HeleketPayment(
        merchant_id=MERCHANT_ID,
        api_key=API_KEY,
        options=ClientOptions(transport=fake),
    )


def _md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def test_create_invoice_sends_signed_json_post() -> None:
    fake = FakeTransport().enqueue_json(
        {"state": 0, "result": {"uuid": "uuid-1", "order_id": "order-1"}}
    )

    invoice = _client(fake).create_invoice(
        CreateInvoiceRequest(amount="15", currency="USD", order_id="order-1")
    )
    assert invoice.uuid == "uuid-1"
    assert invoice.order_id == "order-1"

    sent = fake.last_request()
    assert sent.method == "POST"
    assert sent.url == "https://api.heleket.com/v1/payment"
    assert sent.headers["merchant"] == MERCHANT_ID
    assert sent.headers["Content-Type"] == "application/json"
    # User-Agent tags the client so Heleket support can identify it.
    assert sent.headers["User-Agent"].startswith("heleket-python-sdk/")

    expected_body = '{"amount":"15","currency":"USD","order_id":"order-1"}'
    assert sent.body == expected_body

    expected_sign = _md5_hex(
        base64.b64encode(expected_body.encode("utf-8")).decode("ascii") + API_KEY
    )
    assert sent.headers["sign"] == expected_sign


def test_empty_params_signs_the_empty_string() -> None:
    fake = FakeTransport().enqueue_json(
        {"state": 0, "result": [{"balance": {"merchant": [], "user": []}}]}
    )

    balance = _client(fake).get_balance()
    assert balance.merchant == []
    assert balance.user == []

    sent = fake.last_request()
    assert sent.body == ""
    assert sent.headers["sign"] == _md5_hex(API_KEY)


def test_validation_error_becomes_typed_exception() -> None:
    fake = FakeTransport().enqueue_json(
        {"state": 1, "errors": {"amount": ["validation.required"]}},
        status_code=422,
    )

    with pytest.raises(ValidationError) as excinfo:
        _client(fake).create_invoice(CreateInvoiceRequest(amount="", currency="", order_id=""))
    assert excinfo.value.http_status == 422
    assert excinfo.value.fields == {"amount": ["validation.required"]}


def test_api_error_propagates_message() -> None:
    fake = FakeTransport().enqueue_json({"state": 1, "message": "merchant is blocked"})

    with pytest.raises(ApiError) as excinfo:
        _client(fake).get_info(InfoOptions.by_order_id("o-1"))
    assert "merchant is blocked" in str(excinfo.value)


def test_transport_failure_becomes_http_error() -> None:
    fake = FakeTransport().fail_next("connection reset")

    with pytest.raises(HttpError):
        _client(fake).create_invoice(CreateInvoiceRequest(amount="1", currency="USD", order_id="x"))


def test_credentials_are_keyword_only() -> None:
    """Positional ``merchant_id`` / ``api_key`` is rejected to prevent swaps.

    The arguments are both strings of similar length; passing them positionally
    invited a hard-to-spot bug where they get swapped silently and the first
    request returns a generic state != 0 error.
    """
    with pytest.raises(TypeError):
        HeleketPayment(MERCHANT_ID, API_KEY)  # type: ignore[misc]


def test_get_info_rejects_empty_input() -> None:
    fake = FakeTransport()
    with pytest.raises(ValueError):
        _client(fake).get_info(InfoOptions())


def test_list_history_appends_cursor_to_url() -> None:
    fake = FakeTransport().enqueue_json({"state": 0, "result": {"items": [], "paginate": {}}})

    page = _client(fake).list_history(
        HistoryOptions(date_from="2024-01-01", date_to="2024-01-02", cursor="abc==")
    )
    assert page.items == []
    assert fake.last_request().url == "https://api.heleket.com/v1/payment/list?cursor=abc%3D%3D"


def test_list_services_issues_empty_body() -> None:
    fake = FakeTransport().enqueue_json({"state": 0, "result": []})

    services = _client(fake).list_services()
    assert services == []
    assert fake.last_request().body == ""


def test_get_exchange_rates_encodes_currency() -> None:
    fake = FakeTransport().enqueue_json({"state": 0, "result": []})

    rates = _client(fake).get_exchange_rates("USD")
    assert rates == []
    assert fake.last_request().url == "https://api.heleket.com/v1/exchange-rate/USD/list"


def test_debug_sink_sees_request_and_response() -> None:
    entries: list = []
    fake = FakeTransport().enqueue_json({"state": 0, "result": {"uuid": "u-1", "order_id": "o-1"}})

    client = HeleketPayment(
        merchant_id=MERCHANT_ID,
        api_key=API_KEY,
        options=ClientOptions(transport=fake, debug=True, logger=entries.append),
    )
    client.create_invoice(CreateInvoiceRequest(amount="1", currency="USD", order_id="o-1"))

    assert len(entries) == 2
    assert entries[0].kind == "request"
    assert entries[1].kind == "response"

    # The API key never appears in any logged entry.
    for entry in entries:
        for value in (entry.body or "", entry.url or ""):
            assert API_KEY not in value

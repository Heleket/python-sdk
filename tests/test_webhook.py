"""WebhookVerifier behaviour, including the PHP-style payload regression."""

from __future__ import annotations

import json
from typing import Any

import pytest

from heleket_sdk import SignatureError, WebhookVerifier, sign

API_KEY = "webhook-secret"


def _signed(fields: dict[str, Any]) -> tuple[dict[str, Any], str]:
    body = json.dumps(fields, separators=(",", ":"))
    signature = sign(body, API_KEY)
    payload = {**fields, "sign": signature}
    return payload, json.dumps(payload, separators=(",", ":"))


def test_verify_raw_accepts_valid_python_encoded_payload() -> None:
    _, raw = _signed(
        {
            "type": "payment",
            "uuid": "pmt-1",
            "order_id": "order-1",
            "status": "paid",
            "is_final": True,
            "amount": "15.00",
            "txid": "0xabc",
            "network": "bsc",
        }
    )

    payload = WebhookVerifier(API_KEY).verify_raw(raw)
    assert payload.is_payment()
    assert payload.uuid == "pmt-1"
    assert payload.order_id == "order-1"
    assert payload.status == "paid"
    assert payload.is_final()
    assert payload.is_successful()


def test_verify_raw_rejects_tampered_payload() -> None:
    _, raw = _signed({"type": "payment", "uuid": "u1", "status": "paid"})
    tampered = raw.replace('"status":"paid"', '"status":"fail"')

    with pytest.raises(SignatureError):
        WebhookVerifier(API_KEY).verify_raw(tampered)


def test_verify_raw_rejects_missing_sign() -> None:
    with pytest.raises(SignatureError):
        WebhookVerifier(API_KEY).verify_raw('{"type":"payment"}')


def test_verify_raw_rejects_wrong_key() -> None:
    _, raw = _signed({"type": "payment", "status": "paid"})
    with pytest.raises(SignatureError):
        WebhookVerifier("a-different-key").verify_raw(raw)


def test_verify_raw_rejects_invalid_json() -> None:
    with pytest.raises(SignatureError):
        WebhookVerifier(API_KEY).verify_raw("not json")


def test_verify_raw_rejects_json_arrays() -> None:
    with pytest.raises(SignatureError):
        WebhookVerifier(API_KEY).verify_raw("[1,2,3]")


def test_verify_raw_rejects_invalid_utf8_bytes() -> None:
    """Non-UTF-8 bytes surface as SignatureError, not UnicodeDecodeError.

    A merchant's webhook handler typically catches SignatureError → 400.
    A bare UnicodeDecodeError would bubble up as a 500 and leak a stack
    trace, so the SDK must normalise this.
    """
    with pytest.raises(SignatureError, match="UTF-8"):
        WebhookVerifier(API_KEY).verify_raw(b"\xff\xfe\x00bad")


def test_verify_raw_handles_php_style_payload() -> None:
    """The critical regression test.

    Real Heleket webhooks arrive as PHP ``json_encode`` output: insertion-
    order keys plus forward slashes escaped as ``\\/``. Python's ``json``
    module preserves insertion order but does NOT escape slashes. ``verify_raw``
    must hash the raw bytes so the escapes survive intact.
    """
    body_without_sign = (
        r'{"type":"payment","uuid":"u1","status":"paid",'
        r'"url":"https:\/\/pay.heleket.hk\/pay\/abc"}'
    )
    computed_sign = sign(body_without_sign, API_KEY)
    body = (
        r'{"type":"payment","uuid":"u1","status":"paid",'
        r'"url":"https:\/\/pay.heleket.hk\/pay\/abc","sign":"' + computed_sign + '"}'
    )

    payload = WebhookVerifier(API_KEY).verify_raw(body)
    assert payload.uuid == "u1"
    assert payload.status == "paid"


def test_verify_raw_handles_sign_as_first_field() -> None:
    body_without_sign = '{"type":"payment","uuid":"u1","status":"paid"}'
    computed_sign = sign(body_without_sign, API_KEY)
    body = '{"sign":"' + computed_sign + '","type":"payment","uuid":"u1","status":"paid"}'

    payload = WebhookVerifier(API_KEY).verify_raw(body)
    assert payload.status == "paid"


def test_verify_raw_handles_sign_as_only_field() -> None:
    computed_sign = sign("{}", API_KEY)
    body = '{"sign":"' + computed_sign + '"}'

    # Stripped body becomes "{}" — what was signed.
    payload = WebhookVerifier(API_KEY).verify_raw(body)
    assert payload.uuid == ""


def test_verify_raw_handles_sign_in_middle() -> None:
    body_without_sign = '{"type":"payment","uuid":"u1","status":"paid"}'
    computed_sign = sign(body_without_sign, API_KEY)
    body = '{"type":"payment","uuid":"u1","sign":"' + computed_sign + '","status":"paid"}'

    payload = WebhookVerifier(API_KEY).verify_raw(body)
    assert payload.status == "paid"


def test_verify_convenience_works_for_python_encoded_payload() -> None:
    payload, _ = _signed({"type": "payout", "uuid": "po-7", "status": "paid", "is_final": True})

    result = WebhookVerifier(API_KEY).verify(payload)
    assert result.is_payout()
    assert result.is_successful()


def test_payload_exposes_raw_dict() -> None:
    _, raw = _signed(
        {
            "type": "payment",
            "uuid": "u1",
            "status": "paid",
            "unknown_future_field": "preserve me",
        }
    )

    payload = WebhookVerifier(API_KEY).verify_raw(raw)
    assert payload.raw.get("unknown_future_field") == "preserve me"

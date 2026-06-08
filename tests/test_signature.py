"""Signature parity tests.

The cross-language vector here is identical to the one used in the PHP, Go,
Node, and Java SDKs. All five implementations MUST produce the same hex.
"""

from __future__ import annotations

import base64
import hashlib

import pytest

from heleket_sdk import constant_time_equal, sign


def _md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def test_empty_body_collapses_to_md5_of_key() -> None:
    api_key = "super-secret-key"
    expected = _md5_hex(api_key)

    assert sign(b"", api_key) == expected
    assert sign("", api_key) == expected


def test_matches_doc_formula() -> None:
    body = b'{"amount":"15","currency":"USD","order_id":"1"}'
    api_key = "merchant-api-key-42"
    expected = _md5_hex(base64.b64encode(body).decode("ascii") + api_key)

    assert sign(body, api_key) == expected


def test_cross_language_parity_vector() -> None:
    """Identical input vector used by PHP, Go, Node, and Java SDKs."""
    body = '{"amount":"15","currency":"USD","order_id":"1"}'
    api_key = "merchant-api-key-42"
    expected = _md5_hex(base64.b64encode(body.encode("utf-8")).decode("ascii") + api_key)

    assert sign(body, api_key) == expected


def test_byte_and_string_overloads_agree() -> None:
    body = '{"hello":"world"}'
    api_key = "key"
    assert sign(body, api_key) == sign(body.encode("utf-8"), api_key)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("abc", "abc", True),
        ("abc", "abd", False),
        ("abc", "ABC", False),
        ("abc", "abcd", False),
        ("", "", True),
        (None, "abc", False),
        ("abc", None, False),
        (None, None, False),
    ],
)
def test_constant_time_equality(a: str | None, b: str | None, expected: bool) -> None:
    assert constant_time_equal(a, b) is expected

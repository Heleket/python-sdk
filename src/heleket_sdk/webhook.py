"""Webhook signature verification.

Use the API key that matches the webhook type:

* ``payment`` / ``wallet`` → payment API key
* ``payout`` → payout API key

Two methods are exposed:

* :meth:`WebhookVerifier.verify_raw` — **preferred**. Works on the raw
  request bytes; surgically removes the ``sign`` field with a precise regex
  and hashes the remainder. This is the only entry point that handles real
  Heleket webhooks correctly, because Heleket's PHP server emits
  insertion-order keys and escapes forward slashes as ``\\/``.
* :meth:`WebhookVerifier.verify` — convenience for already-decoded payloads
  (e.g. fixtures). Lossy — re-serialises through Python's ``json`` module, so
  the original byte layout is gone. Do NOT use for live Heleket traffic.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ._errors import SignatureError
from ._signature import constant_time_equal, sign
from ._status import PaymentStatus, PayoutStatus

__all__ = ["WebhookVerifier", "WebhookPayload"]


@dataclass(frozen=True, slots=True)
class WebhookPayload:
    """A verified webhook event. Constructed by :class:`WebhookVerifier`."""

    raw: dict[str, Any] = field(default_factory=dict)
    sign: str = ""

    @property
    def type(self) -> str:
        return _str(self.raw.get("type"))

    @property
    def uuid(self) -> str:
        return _str(self.raw.get("uuid"))

    @property
    def order_id(self) -> str:
        return _str(self.raw.get("order_id"))

    @property
    def amount(self) -> str:
        return _str(self.raw.get("amount"))

    @property
    def payment_amount(self) -> str:
        return _str(self.raw.get("payment_amount"))

    @property
    def merchant_amount(self) -> str:
        return _str(self.raw.get("merchant_amount"))

    @property
    def commission(self) -> str:
        return _str(self.raw.get("commission"))

    @property
    def status(self) -> str:
        return _str(self.raw.get("status"))

    @property
    def txid(self) -> str:
        return _str(self.raw.get("txid"))

    @property
    def network(self) -> str:
        return _str(self.raw.get("network"))

    @property
    def currency(self) -> str:
        return _str(self.raw.get("currency"))

    @property
    def payer_currency(self) -> str:
        return _str(self.raw.get("payer_currency"))

    @property
    def from_address(self) -> str:
        return _str(self.raw.get("from"))

    def is_payment(self) -> bool:
        return self.type in ("payment", "wallet")

    def is_payout(self) -> bool:
        return self.type == "payout"

    def is_final(self) -> bool:
        """Reports whether the event won't transition further.

        Returns ``True`` if **either** the server set ``is_final: true``
        **or** the status enum is terminal. The status check runs even when
        the server sent ``is_final: false`` — this guards against server-side
        bugs where a terminal status (``paid``, ``fail``, ``cancel``…) is
        delivered without the matching ``is_final`` flag. Returns ``False``
        for unknown statuses.
        """
        if self.raw.get("is_final") is True:
            return True
        if self.is_payout():
            return PayoutStatus(self.status).is_final()
        return PaymentStatus(self.status).is_final()

    def is_successful(self) -> bool:
        """Reports whether the event represents a successful payment or payout."""
        if self.is_payout():
            return PayoutStatus(self.status).is_successful()
        return PaymentStatus(self.status).is_successful()


def _str(value: Any) -> str:
    return "" if value is None else str(value)


class WebhookVerifier:
    """Verifier for Heleket webhook signatures."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        self._api_key = api_key

    def verify_raw(self, raw_body: bytes | str) -> WebhookPayload:
        """Verify the signature of a raw JSON body.

        **Preferred entry point** — handles PHP-style slash escapes by
        hashing the raw bytes minus the ``sign`` field. Pass the exact bytes
        you received from the network; do NOT call ``json.loads`` and
        re-serialise first.

        Raises :class:`SignatureError` on malformed JSON, missing sign, or
        mismatch.
        """
        if isinstance(raw_body, bytes):
            try:
                body = raw_body.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SignatureError(f"body is not valid UTF-8: {exc}") from exc
        else:
            body = raw_body

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SignatureError(f"body is not valid JSON: {exc}") from exc

        if not isinstance(decoded, dict):
            raise SignatureError("body must be a JSON object")

        sign_value = decoded.get("sign")
        if not isinstance(sign_value, str) or not sign_value:
            raise SignatureError("missing or empty sign field")

        stripped = _strip_sign_field(body, sign_value)
        expected = sign(stripped, self._api_key)

        if not constant_time_equal(expected, sign_value):
            raise SignatureError("signature mismatch")

        return WebhookPayload(raw=decoded, sign=sign_value)

    def verify(self, payload: dict[str, Any]) -> WebhookPayload:
        """Verify an already-decoded payload.

        Lossy convenience — re-serialises through :func:`json.dumps`, which
        does NOT reproduce PHP's ``\\/`` slash escapes. Only safe for
        payloads originally encoded by Python's ``json`` module (typically
        test fixtures).
        """
        sign_value = payload.get("sign")
        if not isinstance(sign_value, str) or not sign_value:
            raise SignatureError("missing or empty sign field")

        without_sign = {k: v for k, v in payload.items() if k != "sign"}
        # json.dumps with separators=(",",":") matches what BaseClient sends —
        # use the same encoding here so a Java/Python round trip is stable.
        reencoded = json.dumps(without_sign, separators=(",", ":"))
        expected = sign(reencoded, self._api_key)

        if not constant_time_equal(expected, sign_value):
            raise SignatureError("signature mismatch")

        return WebhookPayload(raw=payload, sign=sign_value)


# ---------------------------------------------------------------------------- #
# raw-body sign-field stripping
# ---------------------------------------------------------------------------- #


def _strip_sign_field(body: str, expected_sign: str) -> str:
    """Remove ``"sign":"<hex>"`` from a raw JSON body, preserving every other byte.

    Handles three positions:

    * sign-first:  ``{"sign":"...","other":...}``
    * sign-middle: ``{"a":...,"sign":"...","b":...}``
    * sign-last:   ``{"other":...,"sign":"..."}``

    The neighbouring comma is consumed so the resulting JSON stays valid.
    """
    pattern = re.compile(r'"sign"\s*:\s*"' + re.escape(expected_sign) + r'"')
    match = pattern.search(body)
    if match is None:
        raise SignatureError("sign field not found at expected position in raw body")
    start, end = match.start(), match.end()

    # Try to consume a leading comma (sign is NOT first).
    s = start
    while s > 0 and body[s - 1] in " \t\n\r":
        s -= 1
    if s > 0 and body[s - 1] == ",":
        return body[: s - 1] + body[end:]

    # Otherwise consume a trailing comma (sign IS first, others follow).
    e = end
    while e < len(body) and body[e] in " \t\n\r":
        e += 1
    if e < len(body) and body[e] == ",":
        return body[:start] + body[e + 1 :]

    # No neighbouring comma — sign was the only field.
    return body[:start] + body[end:]

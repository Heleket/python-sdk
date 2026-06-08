"""Heleket request and webhook signature.

Formula (per https://doc.heleket.com/general/request-format):

    sign = md5( base64(json_body) + api_key )

For requests with no parameters, pass an empty bytes object — base64-encoding it
yields the empty string, so the hash collapses to ``md5(api_key)``.

The body argument MUST be the exact bytes that will be sent over the wire.
The same routine is used to produce outgoing request signatures and to verify
incoming webhook signatures.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

__all__ = ["sign", "constant_time_equal"]


def sign(body: bytes | str, api_key: str) -> str:
    """Compute the Heleket signature for the given body and API key.

    Both ``bytes`` and ``str`` bodies are accepted. Strings are UTF-8 encoded.
    """
    if isinstance(body, str):
        body = body.encode("utf-8")
    encoded = base64.b64encode(body).decode("ascii")
    return hashlib.md5((encoded + api_key).encode("utf-8")).hexdigest()  # noqa: S324


def constant_time_equal(expected: str | None, actual: str | None) -> bool:
    """Constant-time equality check for hex signatures.

    Returns ``False`` if either side is ``None`` or the strings differ in
    length. Use this in webhook verification — equality with ``==`` would
    leak timing information.
    """
    if expected is None or actual is None:
        return False
    if len(expected) != len(actual):
        return False
    return hmac.compare_digest(expected, actual)

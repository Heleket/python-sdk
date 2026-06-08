"""Exception hierarchy for the Heleket SDK.

All exceptions extend :class:`HeleketError`, which is a plain ``Exception`` —
they're unchecked in the Python sense. Catch the specific subclass you care
about, or :class:`HeleketError` to handle the SDK's whole surface uniformly.
"""

from __future__ import annotations

__all__ = [
    "HeleketError",
    "ApiError",
    "ValidationError",
    "HttpError",
    "SignatureError",
]


class HeleketError(Exception):
    """Base class for every exception raised by the SDK."""


class ApiError(HeleketError):
    """Raised when Heleket responds with ``state != 0`` (business error).

    Carries the HTTP status and raw response body so callers can log or
    surface the exact server reply.
    """

    def __init__(self, message: str, http_status: int = 0, raw_body: str = "") -> None:
        super().__init__(message)
        self.http_status = http_status
        self.raw_body = raw_body


class ValidationError(ApiError):
    """Raised on HTTP 422. Carries a ``fields`` dict mapping field → messages."""

    def __init__(
        self,
        message: str,
        http_status: int,
        fields: dict[str, list[str]],
        raw_body: str = "",
    ) -> None:
        super().__init__(message, http_status, raw_body)
        self.fields = fields


class HttpError(HeleketError):
    """Raised when the HTTP transport itself fails.

    DNS, TCP, TLS, timeout, broken pipe. The API was never reached, or no
    response was received.
    """


class SignatureError(HeleketError):
    """Raised by :class:`WebhookVerifier` when the signature does not match.

    Treat as a hard security failure — never trust the payload contents in
    this case.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"heleket signature error: {reason}")
        self.reason = reason

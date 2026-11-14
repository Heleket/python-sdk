"""Heleket Python SDK.

A reference implementation of the `Heleket <https://heleket.hk>`_
cryptocurrency payment API. Covers payments, payouts, balance, services,
exchange rates, and webhook verification.

Public entry points::

    from heleket_sdk import HeleketPayment, HeleketPayout
    from heleket_sdk import ClientOptions
    from heleket_sdk import WebhookVerifier
    from heleket_sdk import PaymentStatus, PayoutStatus
    from heleket_sdk import HeleketError, ApiError, ValidationError, HttpError, SignatureError

See ``docs/`` for the full reference.
"""

from __future__ import annotations

from ._config import DEFAULT_BASE_URL, DEFAULT_DOMAIN, DEFAULT_TIMEOUT_SECONDS, ClientOptions
from ._debug import DebugEntry, DebugSink, stderr_sink
from ._errors import (
    ApiError,
    HeleketError,
    HttpError,
    SignatureError,
    ValidationError,
)
from ._signature import constant_time_equal, sign
from ._status import AmlLinkStatus, CourseSource, PaymentStatus, PayoutStatus
from ._transport import RequestsTransport, Transport, TransportResponse
from ._version import __version__
from .payment import HeleketPayment
from .payout import HeleketPayout
from .webhook import WebhookPayload, WebhookVerifier

__all__ = [
    # Clients
    "HeleketPayment",
    "HeleketPayout",
    # Configuration
    "ClientOptions",
    "DEFAULT_BASE_URL",
    "DEFAULT_DOMAIN",
    "DEFAULT_TIMEOUT_SECONDS",
    # Webhook
    "WebhookVerifier",
    "WebhookPayload",
    # Enums
    "PaymentStatus",
    "PayoutStatus",
    "AmlLinkStatus",
    "CourseSource",
    # Errors
    "HeleketError",
    "ApiError",
    "ValidationError",
    "HttpError",
    "SignatureError",
    # Transport
    "Transport",
    "TransportResponse",
    "RequestsTransport",
    # Debug
    "DebugEntry",
    "DebugSink",
    "stderr_sink",
    # Low-level signature
    "sign",
    "constant_time_equal",
    # Metadata
    "__version__",
]

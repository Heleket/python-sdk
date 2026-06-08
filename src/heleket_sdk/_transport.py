"""HTTP transport for the SDK.

The :class:`Transport` protocol defines the contract: take an HTTP request,
return a :class:`TransportResponse` with the raw body preserved verbatim.

The default :class:`RequestsTransport` wraps :mod:`requests`. Merchants who
need custom behaviour (proxies, retries, instrumentation) can implement the
protocol themselves and pass the instance via ``ClientOptions(transport=...)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import requests

from ._errors import HttpError

__all__ = ["Transport", "TransportResponse", "RequestsTransport"]


@dataclass(frozen=True, slots=True)
class TransportResponse:
    """Immutable HTTP response captured by a :class:`Transport`.

    The raw body is preserved as a string so signature checks and the debug
    logger see the exact bytes Heleket sent.
    """

    status_code: int
    body: str
    headers: dict[str, str] = field(default_factory=dict)

    def is_successful(self) -> bool:
        return 200 <= self.status_code < 300


class Transport(Protocol):
    """HTTP transport contract.

    Implementations MUST forward the body bytes verbatim — the SDK has
    already signed those exact bytes, and any mutation would invalidate the
    signature.

    Raise :class:`HttpError` on transport-level failure.
    """

    def round_trip(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: str,
        timeout: float,
    ) -> TransportResponse: ...


class RequestsTransport:
    """Default :class:`Transport` implementation, built on :mod:`requests`.

    Holds a single ``requests.Session`` for connection pooling — safe to
    share across threads, since :class:`HeleketPayment`/``HeleketPayout``
    themselves are thread-safe.
    """

    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def round_trip(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: str,
        timeout: float,
    ) -> TransportResponse:
        try:
            response = self._session.request(
                method=method,
                url=url,
                headers=headers,
                data=body.encode("utf-8") if body else None,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise HttpError(f"transport failed: {exc}") from exc

        return TransportResponse(
            status_code=response.status_code,
            body=response.text,
            headers={k.lower(): v for k, v in response.headers.items()},
        )

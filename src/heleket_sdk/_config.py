"""Client options for :class:`HeleketPayment` / :class:`HeleketPayout`.

:class:`ClientOptions` is a plain dataclass — not a Pydantic model — because
it can hold non-serialisable values like a ``DebugSink`` callable or a
custom transport.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._debug import DebugSink, stderr_sink

if TYPE_CHECKING:
    from ._transport import Transport

__all__ = ["ClientOptions", "DEFAULT_BASE_URL", "DEFAULT_DOMAIN", "DEFAULT_TIMEOUT_SECONDS"]

DEFAULT_DOMAIN = "heleket.hk"
DEFAULT_BASE_URL = "https://api.heleket.hk"
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(slots=True)
class ClientOptions:
    """Optional settings passed to ``HeleketPayment`` / ``HeleketPayout``.

    ``transport`` defaults to a fresh :class:`RequestsTransport` lazily, so
    constructing ``ClientOptions()`` doesn't open a TCP socket pool.

    The request host is ``https://api.<domain>``. An explicit ``base_url``
    takes precedence over ``domain``. After construction ``base_url`` is
    always a ``str``.
    """

    base_url: str | None = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    debug: bool = False
    logger: DebugSink = field(default=stderr_sink)
    transport: Transport | None = None
    domain: str = DEFAULT_DOMAIN

    def __post_init__(self) -> None:
        domain = self.domain
        if (
            not isinstance(domain, str)
            or not domain.strip()
            or "://" in domain
            or "/" in domain
            or any(c.isspace() for c in domain)
        ):
            raise ValueError("domain must be a bare host name such as 'heleket.hk'")
        # Explicit base_url wins; otherwise derive it from the domain.
        base_url = self.base_url if self.base_url else f"https://api.{domain}"
        # Normalise the base URL (drop trailing slashes) so callers can pass
        # either form interchangeably.
        self.base_url = base_url.rstrip("/")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")

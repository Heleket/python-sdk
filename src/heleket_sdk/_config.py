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

__all__ = ["ClientOptions", "DEFAULT_BASE_URL", "DEFAULT_TIMEOUT_SECONDS"]

DEFAULT_BASE_URL = "https://api.heleket.com"
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(slots=True)
class ClientOptions:
    """Optional settings passed to ``HeleketPayment`` / ``HeleketPayout``.

    ``transport`` defaults to a fresh :class:`RequestsTransport` lazily, so
    constructing ``ClientOptions()`` doesn't open a TCP socket pool.
    """

    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    debug: bool = False
    logger: DebugSink = field(default=stderr_sink)
    transport: Transport | None = None

    def __post_init__(self) -> None:
        # Normalise the base URL (drop trailing slashes) so callers can pass
        # either form interchangeably.
        self.base_url = self.base_url.rstrip("/")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")

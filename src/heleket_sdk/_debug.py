"""Debug logging for the Heleket SDK.

A :class:`DebugSink` receives :class:`DebugEntry` objects when the client is
constructed with ``debug=True``. The default sink writes one line per entry
to ``stderr``; plug in your own to route to ``logging``, ``structlog``, or
anywhere else.

**Security:** entries never carry the API key or the ``sign`` header.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

__all__ = ["DebugEntry", "DebugSink", "stderr_sink"]

EntryKind = Literal["request", "response", "error"]


@dataclass(frozen=True, slots=True)
class DebugEntry:
    """A single debug event.

    Use the ``request``/``response``/``error`` classmethods rather than the
    constructor when calling from your own code.
    """

    kind: EntryKind
    method: str | None = None
    url: str | None = None
    body: str | None = None
    status: int | None = None
    message: str | None = None

    @classmethod
    def request(cls, method: str, url: str, body: str) -> DebugEntry:
        return cls(kind="request", method=method, url=url, body=body)

    @classmethod
    def response(cls, status: int, body: str) -> DebugEntry:
        return cls(kind="response", status=status, body=body)

    @classmethod
    def error(cls, message: str) -> DebugEntry:
        return cls(kind="error", message=message)


DebugSink = Callable[[DebugEntry], None]


def stderr_sink(entry: DebugEntry) -> None:
    """Default :class:`DebugSink`. Writes a one-line summary per entry to ``stderr``."""
    if entry.kind == "request":
        body = entry.body if entry.body else "(empty body)"
        print(f"[heleket][→ {entry.method} {entry.url}] {body}", file=sys.stderr)
    elif entry.kind == "response":
        body = entry.body if entry.body else "(empty body)"
        print(f"[heleket][← {entry.status}] {body}", file=sys.stderr)
    elif entry.kind == "error":
        print(f"[heleket][error] {entry.message}", file=sys.stderr)

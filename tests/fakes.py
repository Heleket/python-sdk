"""In-memory ``Transport`` test double.

Enqueue canned responses with :meth:`enqueue_json`, then inspect what the
client sent via :attr:`requests` / :meth:`last_request`. Calls pop responses
in FIFO order — the test fails fast if the queue runs dry.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from heleket_sdk import HttpError, TransportResponse


@dataclass(frozen=True, slots=True)
class RecordedRequest:
    """What a client sent through :class:`FakeTransport`."""

    method: str
    url: str
    headers: dict[str, str]
    body: str


@dataclass(slots=True)
class FakeTransport:
    """``Transport``-compatible recorder."""

    _queue: deque[TransportResponse | HttpError] = field(default_factory=deque)
    requests: list[RecordedRequest] = field(default_factory=list)

    def enqueue(self, response: TransportResponse) -> FakeTransport:
        self._queue.append(response)
        return self

    def enqueue_json(self, payload: Any, status_code: int = 200) -> FakeTransport:
        body = json.dumps(payload, separators=(",", ":"))
        return self.enqueue(
            TransportResponse(
                status_code=status_code,
                body=body,
                headers={"content-type": "application/json"},
            )
        )

    def fail_next(self, message: str = "transport failed") -> FakeTransport:
        self._queue.append(HttpError(message))
        return self

    def round_trip(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: str,
        timeout: float,
    ) -> TransportResponse:
        self.requests.append(
            RecordedRequest(
                method=method,
                url=url,
                headers=dict(headers),
                body=body,
            )
        )

        if not self._queue:
            raise RuntimeError(f"FakeTransport: no enqueued response for {method} {url}")

        nxt = self._queue.popleft()
        if isinstance(nxt, HttpError):
            raise nxt
        return nxt

    def last_request(self) -> RecordedRequest:
        if not self.requests:
            raise RuntimeError("FakeTransport: no requests recorded")
        return self.requests[-1]

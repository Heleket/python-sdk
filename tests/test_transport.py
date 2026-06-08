"""Integration test for :class:`RequestsTransport` against a real loopback server."""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from heleket_sdk import HttpError, RequestsTransport


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""

        self.server.recorded.append(  # type: ignore[attr-defined]
            {
                "method": self.command,
                "path": self.path,
                "headers": {k.lower(): v for k, v in self.headers.items()},
                "body": body.decode("utf-8"),
            }
        )

        response = json.dumps({"state": 0, "result": {"ok": True}}, separators=(",", ":")).encode(
            "utf-8"
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):  # noqa: A002 — match stdlib signature
        # Silence the server's stderr output during tests.
        return


@pytest.fixture()
def server():  # type: ignore[no-untyped-def]
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    httpd.recorded = []  # type: ignore[attr-defined]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd
    finally:
        httpd.shutdown()
        thread.join(timeout=1)


def test_forwards_body_and_headers_verbatim(server) -> None:  # type: ignore[no-untyped-def]
    transport = RequestsTransport()
    port = server.server_address[1]

    response = transport.round_trip(
        method="POST",
        url=f"http://127.0.0.1:{port}/v1/payment",
        headers={
            "merchant": "test-merchant",
            "sign": "abcdef",
            "Content-Type": "application/json",
        },
        body='{"amount":"1"}',
        timeout=5.0,
    )

    assert response.status_code == 200
    assert response.body == '{"state":0,"result":{"ok":true}}'

    sent = server.recorded[0]
    assert sent["method"] == "POST"
    assert sent["path"] == "/v1/payment"
    assert sent["body"] == '{"amount":"1"}'
    assert sent["headers"]["merchant"] == "test-merchant"
    assert sent["headers"]["sign"] == "abcdef"
    assert "content-type" in response.headers


def test_empty_body_is_sent_as_no_body(server) -> None:  # type: ignore[no-untyped-def]
    transport = RequestsTransport()
    port = server.server_address[1]

    response = transport.round_trip(
        method="POST",
        url=f"http://127.0.0.1:{port}/v1/services",
        headers={},
        body="",
        timeout=5.0,
    )

    assert response.status_code == 200
    assert server.recorded[0]["body"] == ""


def test_connection_failure_raises_http_error() -> None:
    transport = RequestsTransport()

    # Find a guaranteed-closed port: bind, get the port, close, then connect.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    closed_port = sock.getsockname()[1]
    sock.close()

    with pytest.raises(HttpError):
        transport.round_trip(
            method="POST",
            url=f"http://127.0.0.1:{closed_port}/",
            headers={},
            body="",
            timeout=1.0,
        )

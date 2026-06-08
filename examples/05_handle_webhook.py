"""Webhook listener.

Run with::

    python examples/05_handle_webhook.py
    # or: make example-webhook

Then point your Heleket invoice's ``url_callback`` at ``http://<host>:8000/``
(use ngrok or similar for local development).

The handler verifies the signature against ``HELEKET_PAYMENT_KEY`` via
:meth:`WebhookVerifier.verify_raw` — the byte-fidelity entry point. REQUIRED
for real Heleket webhooks because they're PHP-encoded with insertion-order
keys and ``\\/`` slash escapes.
"""

from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import env_optional, env_require  # noqa: E402
from heleket_sdk import SignatureError, WebhookVerifier  # noqa: E402

_VERIFIER = WebhookVerifier(env_require("HELEKET_PAYMENT_KEY"))


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""

        try:
            payload = _VERIFIER.verify_raw(body)
        except SignatureError as error:
            print(f"[heleket] signature mismatch: {error.reason}", file=sys.stderr)
            self._reply(400, "invalid signature")
            return

        print(
            f"[heleket] {payload.type} {payload.order_id} "
            f"status={payload.status} is_final={payload.is_final()}"
        )

        # PRODUCTION: de-duplicate by (uuid, status). Heleket replays events
        # after retries and operators can resend manually. See
        # docs/06-webhooks.md for the recommended idempotency pattern.

        self._reply(200, "OK")

    def _reply(self, status: int, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):  # noqa: A002
        # Quiet the default access logging — print() lines above are clearer.
        return


def main() -> int:
    port = int(env_optional("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), _Handler)  # noqa: S104 — explicit
    print(f"listening on :{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())

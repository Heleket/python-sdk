"""``heleket-webhook-inspect`` — verify a captured webhook payload.

Usage::

    # Preferred: pass the API key via env var so it doesn't land in shell
    # history or appear in `ps` output.
    export HELEKET_API_KEY=$HELEKET_PAYMENT_KEY
    echo '{"type":"payment",...}' | heleket-webhook-inspect

    # Or pass it explicitly (less safe — recorded in shell history).
    heleket-webhook-inspect --key=$KEY --file=webhook.json
    heleket-webhook-inspect --key=$KEY --type=payout --file=webhook.json

Exit codes:

* ``0`` — payload valid, signature verified
* ``1`` — payload could not be parsed
* ``2`` — signature does not match
* ``3`` — missing arguments
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ._errors import SignatureError
from .webhook import WebhookVerifier

_COLOR_RESET = "\x1b[0m"
_COLOR_RED = "\x1b[31m"
_COLOR_GREEN = "\x1b[32m"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="heleket-webhook-inspect",
        description="Verify a captured Heleket webhook payload.",
    )
    parser.add_argument(
        "--key",
        required=False,
        help=(
            "API key used to sign the webhook. Falls back to the HELEKET_API_KEY "
            "env var if omitted (preferred — keeps the key out of shell history)."
        ),
    )
    parser.add_argument("--file", help="Path to a webhook JSON file. Defaults to stdin.")
    parser.add_argument("--type", help="Expected payload type (payment | payout | wallet)")
    args = parser.parse_args(argv)

    api_key = args.key or os.environ.get("HELEKET_API_KEY", "")
    if not api_key:
        sys.stderr.write(
            "Usage: heleket-webhook-inspect [--key=<api-key>] "
            "[--file=<path>] [--type=payment|payout]\n"
            "Set HELEKET_API_KEY in the environment to avoid passing the key on "
            "the command line.\n"
        )
        return 3

    body = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()

    # Trim trailing newline added by shells / editors — Heleket signs the exact
    # bytes it sends, which never have a trailing newline.
    body = body.rstrip("\r\n")

    if not body:
        sys.stderr.write("No input received. Pipe a JSON payload to stdin or pass --file=<path>.\n")
        return 1

    try:
        parsed: dict[str, Any] = json.loads(body)
    except json.JSONDecodeError as error:
        sys.stderr.write(f"Input is not valid JSON: {error}\n")
        return 1

    print("Heleket webhook inspector")
    print("-" * 40)
    for field in ("type", "uuid", "order_id", "status", "amount", "network", "txid"):
        _print_field(field, parsed.get(field))

    if "is_final" in parsed:
        value = parsed["is_final"]
        text = "yes" if value is True else "no" if value is False else str(value)
        print(f"  {'is_final':<10} {text}")
    else:
        print(f"  {'is_final':<10} (missing)")

    sign_value = parsed.get("sign")
    if isinstance(sign_value, str):
        truncated = sign_value if len(sign_value) <= 16 else sign_value[:16] + "…"
        print(f"  {'sign':<10} {truncated}")
    else:
        print(f"  {'sign':<10} (missing)")

    if args.type and parsed.get("type") and args.type != parsed["type"]:
        sys.stderr.write(f"\nWarning: --type={args.type} but payload type is {parsed['type']}\n")

    try:
        WebhookVerifier(api_key).verify_raw(body)
    except SignatureError as error:
        print()
        print(f"signature: {_COLOR_RED}INVALID{_COLOR_RESET} — {error.reason}")
        print("Hints:")
        print("  - Are you using the same API key that was configured when the webhook was sent?")
        print(
            "  - Payment webhooks sign with the payment key; "
            "payout webhooks sign with the payout key."
        )
        print(
            "  - If you re-serialised the payload before passing it here, "
            "the slash escaping may have been lost."
        )
        return 2

    print()
    print(f"signature: {_COLOR_GREEN}valid{_COLOR_RESET}")
    return 0


def _print_field(name: str, value: Any) -> None:
    label = f"  {name:<10}"
    if value is None:
        print(f"{label} (missing)")
    elif isinstance(value, str):
        print(f"{label} {value}")
    else:
        print(f"{label} {json.dumps(value)}")


if __name__ == "__main__":
    sys.exit(main())

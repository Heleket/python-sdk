"""Create a one-shot invoice and print the payment URL.

Run with::

    python examples/01_create_invoice.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import env_optional, make_payment, pretty_print, random_order_id  # noqa: E402
from heleket_sdk import ValidationError  # noqa: E402
from heleket_sdk.types import CreateInvoiceRequest  # noqa: E402


def main() -> int:
    client = make_payment()
    request = CreateInvoiceRequest(
        amount="15.00",
        currency="USD",
        order_id=random_order_id("demo"),
        lifetime=3600,
        url_callback=env_optional("HELEKET_WEBHOOK_URL") or None,
    )

    try:
        invoice = client.create_invoice(request)
    except ValidationError as error:
        print("Validation failed:", file=sys.stderr)
        for field, messages in error.fields.items():
            print(f"  {field}: {', '.join(messages)}", file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001
        print(f"create invoice: {error}", file=sys.stderr)
        return 3

    pretty_print("Invoice created", invoice)
    print()
    print(f"Payment page: {invoice.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

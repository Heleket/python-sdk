"""Look up a payment by uuid OR order_id.

Run with::

    python examples/02_get_payment_info.py <uuid|order_id>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import make_payment, pretty_print  # noqa: E402
from heleket_sdk import ApiError  # noqa: E402
from heleket_sdk.types import InfoOptions  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: 02_get_payment_info.py <uuid|order_id>", file=sys.stderr)
        return 1

    identifier = sys.argv[1]
    options = (
        InfoOptions.by_uuid(identifier)
        if re.fullmatch(r"[0-9a-fA-F-]{32,36}", identifier)
        else InfoOptions.by_order_id(identifier)
    )

    try:
        invoice = make_payment().get_info(options)
    except ApiError as error:
        print(f"get info: {error}", file=sys.stderr)
        return 2

    pretty_print("Invoice", invoice)
    status = invoice.effective_status()
    print(f"status: {status.value if status else '?'}")
    print(f"is_final: {bool(invoice.is_final)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Refund a paid invoice.

Refund lives on the PAYOUT client: ``/v1/payment/refund`` is signed with the
payout API key, not the payment key.

Run with::

    python examples/12_refund.py <invoice-uuid> <refund-address>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import make_payout, pretty_print  # noqa: E402
from heleket_sdk import ApiError, ValidationError  # noqa: E402
from heleket_sdk.types import RefundRequest  # noqa: E402


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: 12_refund.py <invoice-uuid> <refund-address>", file=sys.stderr)
        return 1

    uuid, address = sys.argv[1], sys.argv[2]

    # Refund is signed with the payout key, so it lives on HeleketPayout.
    client = make_payout()

    try:
        refund = client.refund(RefundRequest(uuid=uuid, address=address, is_subtract=True))
    except ValidationError as error:
        print("Validation failed:", file=sys.stderr)
        for field, messages in error.fields.items():
            print(f"  {field}: {', '.join(messages)}", file=sys.stderr)
        return 2
    except ApiError as error:
        print(f"API error (HTTP {error.http_status}): {error}", file=sys.stderr)
        return 3

    pretty_print("Refund requested", refund)
    return 0


if __name__ == "__main__":
    sys.exit(main())

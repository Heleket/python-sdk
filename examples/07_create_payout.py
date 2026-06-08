"""Create a withdrawal."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import env_optional, make_payout, pretty_print, random_order_id  # noqa: E402
from heleket_sdk import ValidationError  # noqa: E402
from heleket_sdk.types import CreatePayoutRequest  # noqa: E402


def main() -> int:
    client = make_payout()
    request = CreatePayoutRequest(
        amount="5",
        currency="USDT",
        order_id=random_order_id("po"),
        address=env_optional("HELEKET_PAYOUT_ADDRESS", "TWalletAddressHere"),
        is_subtract=True,
        network="TRON",
        url_callback=env_optional("HELEKET_WEBHOOK_URL") or None,
    )

    try:
        payout = client.create_payout(request)
    except ValidationError as error:
        print("Validation failed:", file=sys.stderr)
        for field, messages in error.fields.items():
            print(f"  {field}: {', '.join(messages)}", file=sys.stderr)
        return 2

    pretty_print("Payout", payout)
    print(f"status: {payout.status.value if payout.status else '?'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

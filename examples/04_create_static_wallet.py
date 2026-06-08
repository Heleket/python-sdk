"""Create a long-lived top-up wallet pinned to one order ID."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import env_optional, make_payment, pretty_print, random_order_id  # noqa: E402
from heleket_sdk.types import CreateStaticWalletRequest  # noqa: E402


def main() -> int:
    client = make_payment()
    wallet = client.create_static_wallet(
        CreateStaticWalletRequest(
            currency="USDT",
            network="TRON",
            order_id=random_order_id("static"),
            url_callback=env_optional("HELEKET_WEBHOOK_URL") or None,
        )
    )
    pretty_print("Static wallet", wallet)
    print()
    print(f"Send funds to: {wallet.address}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

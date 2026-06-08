"""Read merchant + personal balances."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import make_payment  # noqa: E402
from heleket_sdk.types import WalletBalance  # noqa: E402


def _print_row(row: WalletBalance) -> None:
    print(f"  {(row.currency_code or '-'):<8}  balance={row.balance}  uuid={row.uuid}")


def main() -> int:
    balance = make_payment().get_balance()

    print("=== Merchant balance ===")
    for row in balance.merchant:
        _print_row(row)

    print()
    print("=== Personal balance ===")
    for row in balance.user:
        _print_row(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())

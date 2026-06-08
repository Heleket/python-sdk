"""Walk the paginated /v1/payment/list endpoint."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import make_payment  # noqa: E402
from heleket_sdk.types import HistoryOptions  # noqa: E402


def main() -> int:
    client = make_payment()
    cursor: str | None = None
    page = 0
    total = 0

    while True:
        result = client.list_history(HistoryOptions(cursor=cursor))
        page += 1
        total += len(result.items)
        print(f"--- page {page} ({len(result.items)} items) ---")
        for invoice in result.items:
            status = invoice.effective_status()
            print(
                f"  {invoice.uuid}  status={status.value if status else '?'}"
                f"  amount={invoice.amount} {invoice.currency}"
            )

        next_cursor = result.paginate.next_cursor if result.paginate else None
        if not next_cursor:
            break
        cursor = next_cursor

    print()
    print(f"Total invoices fetched: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

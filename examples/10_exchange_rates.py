"""Print exchange rates for the given fiat currency."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import make_payment  # noqa: E402


def main() -> int:
    currency = sys.argv[1] if len(sys.argv) > 1 else "USD"
    rates = make_payment().get_exchange_rates(currency)

    print(f"Rates for {currency}:")
    for rate in rates:
        print(f"  {rate.from_currency} → {rate.to}  {rate.course}  (source={rate.source})")

    print()
    print(f"Total: {len(rates)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

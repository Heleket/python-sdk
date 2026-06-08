"""List supported (currency, network) pairs for payments."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import make_payment  # noqa: E402


def main() -> int:
    services = make_payment().list_services()

    print(f"{'CURR':<8} {'NETWORK':<12} {'AVAILABLE':<10}")
    print("-" * 30)
    for service in services:
        availability = "yes" if service.is_available else "no"
        print(f"{(service.currency or '-'):<8} {(service.network or '-'):<12} {availability:<10}")

    print()
    print(f"Total: {len(services)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

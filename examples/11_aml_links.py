"""AML/KYC/SoF questionnaire links for a blocked (locked) payment.

Run with::

    python examples/11_aml_links.py <uuid|order_id>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _bootstrap import make_payment, pretty_print  # noqa: E402

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: 11_aml_links.py <uuid|order_id>", file=sys.stderr)
        return 1

    identifier = sys.argv[1]
    client = make_payment()

    # Caller can pass either a UUID or an order_id; we try UUID first.
    if _UUID_RE.match(identifier):
        links = client.get_aml_links(uuid=identifier)
    else:
        links = client.get_aml_links(order_id=identifier)

    pretty_print("AML links", links)

    # Hand each `link` to the end user so they can complete the questionnaire.
    for link in links:
        status = link.status
        marker = "(final)" if status and status.is_final() else "(in progress)"
        print()
        print(link.link)
        print(f"  status: {status.value if status else '?'} {marker}")
        print(f"  expires: {link.expired_at}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

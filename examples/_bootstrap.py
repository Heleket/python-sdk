"""Shared bootstrap for the examples directory.

* Tiny inline ``.env`` loader (no python-dotenv dependency)
* Factories for :class:`HeleketPayment` / :class:`HeleketPayout`
* Pretty-print helper
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from heleket_sdk import ClientOptions, HeleketPayment, HeleketPayout

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent


def _load_env() -> None:
    for candidate in (_ROOT / ".env", _HERE / ".env"):
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            os.environ.setdefault(key, value)
        return


_load_env()


def env_require(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        sys.stderr.write(f"Missing env var: {name}\nCopy .env.example to .env and fill it in.\n")
        sys.exit(1)
    return value


def env_optional(name: str, fallback: str = "") -> str:
    return os.environ.get(name, fallback)


def _client_options() -> ClientOptions:
    base_url = env_optional("HELEKET_BASE_URL", "")
    kwargs: dict[str, Any] = {"debug": env_optional("HELEKET_DEBUG", "0") in ("1", "true")}
    if base_url:
        kwargs["base_url"] = base_url
    return ClientOptions(**kwargs)


def make_payment() -> HeleketPayment:
    return HeleketPayment(
        merchant_id=env_require("HELEKET_MERCHANT_ID"),
        api_key=env_require("HELEKET_PAYMENT_KEY"),
        options=_client_options(),
    )


def make_payout() -> HeleketPayout:
    return HeleketPayout(
        merchant_id=env_require("HELEKET_MERCHANT_ID"),
        api_key=env_require("HELEKET_PAYOUT_KEY"),
        options=_client_options(),
    )


def pretty_print(label: str, value: Any) -> None:
    print(f"=== {label} ===")
    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True, exclude_none=True)
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def random_order_id(prefix: str) -> str:
    return f"{prefix}-{int(time.time())}"

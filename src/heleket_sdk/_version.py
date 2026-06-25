"""Single source of truth for the SDK version.

Lives in its own module so :mod:`_base_client` can read it for the
``User-Agent`` header without triggering a circular import via ``__init__``.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.3.0"

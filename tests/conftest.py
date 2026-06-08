"""pytest fixtures shared across the suite."""

from __future__ import annotations

import sys
from pathlib import Path

# Make the ``tests/fakes.py`` module importable without installing the package
# in editable mode. ``tests/`` is already on sys.path during collection, but
# being explicit keeps IDE configurations happy.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

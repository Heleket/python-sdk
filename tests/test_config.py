"""ClientOptions behaviour."""

from __future__ import annotations

import pytest

from heleket_sdk import ClientOptions, stderr_sink


def test_defaults() -> None:
    opts = ClientOptions()
    assert opts.base_url == "https://api.heleket.com"
    assert opts.timeout == 30.0
    assert opts.debug is False
    assert opts.logger is stderr_sink
    assert opts.transport is None  # lazily created in BaseClient


def test_trailing_slash_stripped() -> None:
    opts = ClientOptions(base_url="https://staging.example.com/")
    assert opts.base_url == "https://staging.example.com"


def test_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ClientOptions(timeout=0)
    with pytest.raises(ValueError):
        ClientOptions(timeout=-1)


def test_custom_logger() -> None:
    captured = []

    def sink(entry):  # type: ignore[no-untyped-def]
        captured.append(entry)

    opts = ClientOptions(debug=True, logger=sink)
    assert opts.logger is sink

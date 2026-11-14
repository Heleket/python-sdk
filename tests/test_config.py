"""ClientOptions behaviour."""

from __future__ import annotations

import pytest

from heleket_sdk import DEFAULT_BASE_URL, DEFAULT_DOMAIN, ClientOptions, stderr_sink


def test_defaults() -> None:
    opts = ClientOptions()
    assert opts.base_url == "https://api.heleket.hk"
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


def test_default_domain_and_base_url() -> None:
    assert DEFAULT_DOMAIN == "heleket.hk"
    assert DEFAULT_BASE_URL == "https://api.heleket.hk"
    assert ClientOptions().domain == "heleket.hk"


def test_domain_builds_base_url() -> None:
    assert ClientOptions(domain="example.org").base_url == "https://api.example.org"


def test_base_url_overrides_domain() -> None:
    opts = ClientOptions(base_url="https://staging.example.com", domain="example.org")
    assert opts.base_url == "https://staging.example.com"


@pytest.mark.parametrize("bad", ["", "  ", "https://example.org", "example.org/path", "a b.com"])
def test_invalid_domain_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        ClientOptions(domain=bad)

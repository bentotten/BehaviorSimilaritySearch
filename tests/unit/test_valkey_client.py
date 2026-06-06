"""Unit tests for bss_valkey.valkey_client."""

import pytest
import valkey as _valkey
from pytest_mock import MockerFixture

import bss_valkey.valkey_client as _vc_module
from bss_valkey.valkey_client import (
    DEFAULT_MAX_PING_RETRIES,
    DEFAULT_PING_RETRY_DELAY,
    ValkeyClient,
    get_client,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the module-level singleton before each test."""
    _vc_module.valkey_client = None


# ---------------------------------------------------------------------------
# ValkeyClient
# ---------------------------------------------------------------------------


def test_ping_succeeds_immediately(mocker: MockerFixture) -> None:
    """ping() returns without raising when the server responds on first attempt."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.ping.return_value = True
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    ValkeyClient(host="127.0.0.1", port=6379).ping(max_retries=1, retry_delay=0)

    assert mock_valkey.ping.call_count == 1


def test_ping_succeeds_on_retry(mocker: MockerFixture) -> None:
    """ping() succeeds after an initial failure without raising."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.ping.side_effect = [
        _valkey.exceptions.ConnectionError("refused"),
        True,
    ]
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    ValkeyClient(host="127.0.0.1", port=6379).ping(max_retries=2, retry_delay=0)

    assert mock_valkey.ping.call_count == 2


def test_ping_exhausts_retries_then_raises(mocker: MockerFixture) -> None:
    """ping() raises ConnectionError after exhausting all retries."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.ping.side_effect = _valkey.exceptions.ConnectionError("refused")
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    with pytest.raises(ConnectionError, match="Could not connect"):
        ValkeyClient(host="127.0.0.1", port=6379).ping(max_retries=3, retry_delay=0)

    assert mock_valkey.ping.call_count == 3


def test_client_property_returns_underlying_valkey(mocker: MockerFixture) -> None:
    """client property returns the underlying valkey.Valkey instance."""
    mock_valkey = mocker.MagicMock()
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    assert ValkeyClient(host="127.0.0.1", port=6379).client is mock_valkey


# ---------------------------------------------------------------------------
# get_client (singleton)
# ---------------------------------------------------------------------------


def test_get_client_returns_same_instance(mocker: MockerFixture) -> None:
    """get_client() returns the same instance on repeated calls."""
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mocker.MagicMock())

    assert get_client(host="127.0.0.1", port=6379) is get_client()


def test_get_client_without_args_uses_defaults(mocker: MockerFixture) -> None:
    """get_client() with no args creates a client using valkey library defaults."""
    mock_valkey = mocker.MagicMock()
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    client = get_client()
    assert client is not None


def test_default_constants() -> None:
    """Default retry constants match documented values."""
    assert DEFAULT_MAX_PING_RETRIES == 5
    assert DEFAULT_PING_RETRY_DELAY == 2.0

"""Unit tests for bss_valkey.valkey_client."""

import pytest
import valkey as _valkey
from pytest_mock import MockerFixture

import bss_valkey.valkey_client as bss_valkey_client_module
from bss_valkey.valkey_client import (
    DEFAULT_VALKEY_HOST,
    DEFAULT_VALKEY_PORT,
    ValkeyClient,
    get_client,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the module-level singleton before each test."""
    bss_valkey_client_module.valkey_client = None


# ---------------------------------------------------------------------------
# Valkey singleton getter
# ---------------------------------------------------------------------------


def test_get_client_returns_same_instance(mocker: MockerFixture) -> None:
    """get_client() returns the same instance on repeated calls."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.get_connection_kwargs.return_value = {
        "host": DEFAULT_VALKEY_HOST,
        "port": DEFAULT_VALKEY_PORT,
    }
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    assert get_client(host="127.0.0.1", port=6379) is get_client()
    assert get_client() is get_client()


def test_get_client_without_args(mocker: MockerFixture) -> None:
    """get_client() with no args creates a client using valkey library defaults."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.get_connection_kwargs.return_value = {
        "host": DEFAULT_VALKEY_HOST,
        "port": DEFAULT_VALKEY_PORT,
    }
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    # Should exist. Not testing defaults directly as these are a part of the Valkey dep.
    assert get_client() is not None


def test_get_client_warns_when_called_with_different_host_or_port(
    capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    """get_client() prints a warning when already initialised with different host/port."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.get_connection_kwargs.return_value = {
        "host": DEFAULT_VALKEY_HOST,
        "port": DEFAULT_VALKEY_PORT,
    }
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    get_client(host=DEFAULT_VALKEY_HOST, port=DEFAULT_VALKEY_PORT)
    get_client(host="10.0.0.1", port=6380)

    # TODO: Replace with logger (https://github.com/bentotten/BehaviorSimilaritySearch/issues/17)
    assert "Warning!" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# ValkeyClient
# ---------------------------------------------------------------------------


def test_ping_succeeds_immediately(mocker: MockerFixture) -> None:
    """ping() returns without raising when the server responds on first attempt."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.ping.return_value = True
    mock_valkey.get_connection_kwargs.return_value = {
        "host": DEFAULT_VALKEY_HOST,
        "port": DEFAULT_VALKEY_PORT,
    }
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
    mock_valkey.get_connection_kwargs.return_value = {
        "host": DEFAULT_VALKEY_HOST,
        "port": DEFAULT_VALKEY_PORT,
    }
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    ValkeyClient(host="127.0.0.1", port=6379).ping(max_retries=2, retry_delay=0)

    assert mock_valkey.ping.call_count == 2


def test_ping_exhausts_retries_then_raises(mocker: MockerFixture) -> None:
    """ping() raises ConnectionError after exhausting all retries."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.ping.side_effect = _valkey.exceptions.ConnectionError("refused")
    mock_valkey.get_connection_kwargs.return_value = {
        "host": DEFAULT_VALKEY_HOST,
        "port": DEFAULT_VALKEY_PORT,
    }
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    with pytest.raises(ConnectionError, match="Could not connect"):
        ValkeyClient(host="127.0.0.1", port=6379).ping(max_retries=3, retry_delay=0)

    assert mock_valkey.ping.call_count == 3


def test_client_property_returns_underlying_valkey(mocker: MockerFixture) -> None:
    """client property returns the underlying valkey.Valkey instance."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.get_connection_kwargs.return_value = {
        "host": DEFAULT_VALKEY_HOST,
        "port": DEFAULT_VALKEY_PORT,
    }
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    assert ValkeyClient(host="127.0.0.1", port=6379).client is mock_valkey


def test_host_property_returns_resolved_host(mocker: MockerFixture) -> None:
    """host property returns the host resolved from the connection pool."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.get_connection_kwargs.return_value = {"host": "10.0.0.1", "port": 6379}
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    assert ValkeyClient(host="10.0.0.1", port=6379).host == "10.0.0.1"


def test_port_property_returns_resolved_port(mocker: MockerFixture) -> None:
    """port property returns the port resolved from the connection pool."""
    mock_valkey = mocker.MagicMock()
    mock_valkey.get_connection_kwargs.return_value = {"host": "127.0.0.1", "port": 6380}
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=mock_valkey)

    assert ValkeyClient(host="127.0.0.1", port=6380).port == 6380

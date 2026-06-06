"""Integration tests — cross-package interactions."""

import pytest
from pytest_mock import MockerFixture

from bss_valkey.valkey_client import ValkeyClient
from tests.fakes.fake_valkey import FailingFakeValkey, FakeValkey

# ---------------------------------------------------------------------------
# Valkey Integration Tests
# ---------------------------------------------------------------------------


def test_ping_succeeds_with_fake_valkey(mocker: MockerFixture) -> None:
    """ValkeyClient.ping() succeeds when backed by FakeValkey."""
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=FakeValkey())

    ValkeyClient(host="127.0.0.1", port=6379).ping(max_retries=1, retry_delay=0)


def test_ping_exhausts_retries_with_failing_fake(mocker: MockerFixture) -> None:
    """ValkeyClient.ping() raises ConnectionError when the server is always unreachable."""
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=FailingFakeValkey())

    with pytest.raises(ConnectionError, match="Could not connect"):
        ValkeyClient(host="127.0.0.1", port=6379).ping(max_retries=2, retry_delay=0)

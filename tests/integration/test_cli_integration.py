"""Integration tests for the CLI module."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

import bss_valkey.valkey_client as bss_valkey_client_module
from bss_cli import DEFAULT_PROFILE_CONFIG_PATH, DEFAULT_VALKEY_HOST, DEFAULT_VALKEY_PORT
from bss_cli.cli import bootstrap
from tests.fakes.fake_valkey import FailingFakeValkey, FakeValkey

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the Valkey singleton before each test."""
    bss_valkey_client_module.valkey_client = None


@pytest.fixture()
def config_file_env_type(tmp_path: Path) -> Path:
    """Write a minimal valid local.env to a temp file."""
    env_file = tmp_path / "local.env"
    env_file.write_text(f"VALKEY_HOST={DEFAULT_VALKEY_HOST}\nVALKEY_PORT={DEFAULT_VALKEY_PORT}\n")
    return env_file


# ---------------------------------------------------------------------------
# Bootstrap integration tests
# ---------------------------------------------------------------------------


def test_bootstrap_happy_path(config_file_env_type: Path, mocker: MockerFixture) -> None:
    """bootstrap() completes without raising."""
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=FakeValkey())

    bootstrap(config_file_env_type, DEFAULT_PROFILE_CONFIG_PATH)  # should not raise


def test_bootstrap_raises_with_unreachable_valkey(
    config_file_env_type: Path, mocker: MockerFixture
) -> None:
    """bootstrap() raises ConnectionError when FakeValkey always fails to ping."""
    mocker.patch("bss_valkey.valkey_client.valkey.Valkey", return_value=FailingFakeValkey())

    with pytest.raises(ConnectionError, match="Could not connect"):
        bootstrap(config_file_env_type, DEFAULT_PROFILE_CONFIG_PATH)

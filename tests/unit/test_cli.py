"""Unit tests for bss_cli."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from bss_cli import __version__
from bss_cli.cli import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_VALKEY_HOST,
    DEFAULT_VALKEY_PORT,
    bootstrap,
    build_parser,
    main,
)

# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


def test_version_defined() -> None:
    """__version__ is a non-empty string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parser_no_subcommand_sets_command_none() -> None:
    """No subcommand sets command to None."""
    assert build_parser().parse_args([]).command is None


def test_parser_default_config_path() -> None:
    """--config_path defaults to DEFAULT_CONFIG_PATH."""
    assert build_parser().parse_args(["bootstrap"]).config_path == DEFAULT_CONFIG_PATH


def test_parser_accepts_custom_config_path() -> None:
    """--config_path accepts an explicit path."""
    custom = Path("configs/custom.env")
    args = build_parser().parse_args(["--config_path", str(custom), "bootstrap"])
    assert args.config_path == custom


def test_parser_bootstrap_is_valid_subcommand() -> None:
    """bootstrap is a recognised subcommand."""
    assert build_parser().parse_args(["bootstrap"]).command == "bootstrap"


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def test_bootstrap_succeeds_when_ping_succeeds(mocker: MockerFixture) -> None:
    """Test bootstrap completes without raising when ping succeeds."""
    mocker.patch(
        "bss_cli.cli.load_config",
        return_value={"VALKEY_HOST": DEFAULT_VALKEY_HOST, "VALKEY_PORT": DEFAULT_VALKEY_PORT},
    )
    mock_client = mocker.MagicMock()
    mock_client.ping.return_value = None
    mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    bootstrap(DEFAULT_CONFIG_PATH)  # should not raise


def test_bootstrap_uses_defaults_when_config_keys_absent(mocker: MockerFixture) -> None:
    """bootstrap falls back to defaults when config dict has no Valkey keys."""
    mocker.patch("bss_cli.cli.load_config", return_value={})
    mock_client = mocker.MagicMock()
    mock_client.ping.return_value = None
    mock_get = mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    bootstrap(DEFAULT_CONFIG_PATH)

    mock_get.assert_called_once_with(host=DEFAULT_VALKEY_HOST, port=int(DEFAULT_VALKEY_PORT))


def test_bootstrap_exits_on_connection_failure(mocker: MockerFixture) -> None:
    """bootstrap calls sys.exit(1) when ping raises ConnectionError."""
    mocker.patch(
        "bss_cli.cli.load_config",
        return_value={"VALKEY_HOST": DEFAULT_VALKEY_HOST, "VALKEY_PORT": DEFAULT_VALKEY_PORT},
    )
    mock_client = mocker.MagicMock()
    mock_client.ping.side_effect = ConnectionError("unreachable")
    mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    with pytest.raises(SystemExit) as exc_info:
        bootstrap(DEFAULT_CONFIG_PATH)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main_no_args_prints_help(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    """main() with no subcommand prints help without raising."""
    mocker.patch("sys.argv", ["bss"])
    main()
    assert "bootstrap" in capsys.readouterr().out

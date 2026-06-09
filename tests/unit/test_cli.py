"""Unit tests for bss_cli."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from bss_cli import (
    DEFAULT_ENV_CONFIG_PATH,
    DEFAULT_MAX_PING_RETRIES,
    DEFAULT_PING_RETRY_DELAY,
    DEFAULT_VALKEY_HOST,
    DEFAULT_VALKEY_PORT,
    __version__,
)
from bss_cli.cli import bootstrap, build_parser, create_profiles, main, start_search_backend

# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


def test_version_defined() -> None:
    """__version__ is a non-empty string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main_no_args_prints_help(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    """main() with no subcommand prints the full help text."""
    # sys.argv must be patched so argparse sees an empty argument list.
    # Without this, argparse reads pytest's own argv (e.g. the test file path)
    # and exits with an unrecognised argument error.
    mocker.patch("sys.argv", ["bss"])
    main()
    # TODO: Replace with logger (https://github.com/bentotten/BehaviorSimilaritySearch/issues/17)
    assert capsys.readouterr().out == build_parser().format_help()


def test_main_dispatches_bootstrap(mocker: MockerFixture) -> None:
    """main() calls bootstrap() with config paths when bootstrap subcommand is used."""
    mocker.patch("sys.argv", ["bss", "bootstrap"])
    mock_bootstrap = mocker.patch("bss_cli.cli.bootstrap")

    main()

    mock_bootstrap.assert_called_once_with(DEFAULT_ENV_CONFIG_PATH)


def test_main_dispatches_bootstrap_with_custom_paths(mocker: MockerFixture) -> None:
    """main() passes custom paths to bootstrap() when provided."""
    env_path = "configs/foo.env"
    mocker.patch(
        "sys.argv",
        ["bss", "--env_config", env_path, "bootstrap"],
    )
    mock_bootstrap = mocker.patch("bss_cli.cli.bootstrap")

    main()

    mock_bootstrap.assert_called_once_with(Path(env_path))


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parser_default_configs() -> None:
    """Config paths default to proper defaults."""
    bootstrap_args = build_parser().parse_args(["bootstrap"])
    assert bootstrap_args.env_config == DEFAULT_ENV_CONFIG_PATH


def test_parser_accepts_custom_env_config_path() -> None:
    """--env_config accepts an explicit path."""
    custom_env_path = Path("configs/custom_path.env")
    args = build_parser().parse_args(["--env_config", str(custom_env_path), "bootstrap"])
    assert args.env_config == custom_env_path


def test_parser_no_subcommand_sets_command_none() -> None:
    """No subcommand sets command to None."""
    assert build_parser().parse_args([]).command is None


def test_parser_bootstrap_is_valid_subcommand() -> None:
    """bootstrap is a recognised subcommand."""
    assert build_parser().parse_args(["bootstrap"]).command == "bootstrap"


# ---------------------------------------------------------------------------
# start_search_backend
# ---------------------------------------------------------------------------


def test_start_search_backend_creates_backend_with_correct_values(mocker: MockerFixture) -> None:
    """start_search_backend reads config and calls subfunctions with correct values."""
    host = DEFAULT_VALKEY_HOST
    port = DEFAULT_VALKEY_PORT
    max_retries = DEFAULT_MAX_PING_RETRIES
    retry_delay = DEFAULT_PING_RETRY_DELAY

    mock_load = mocker.patch(
        "bss_cli.cli.load_config",
        return_value={
            "VALKEY_HOST": host,
            "VALKEY_PORT": port,
            "VALKEY_PING_MAX_RETRIES": max_retries,
            "VALKEY_PING_RETRY_DELAY": retry_delay,
        },
    )
    mock_client = mocker.MagicMock()
    mock_get_client = mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    start_search_backend(DEFAULT_ENV_CONFIG_PATH)

    mock_load.assert_called_once_with(DEFAULT_ENV_CONFIG_PATH)
    mock_get_client.assert_called_once_with(host=host, port=int(port))
    mock_client.ping.assert_called_once_with(
        max_retries=int(max_retries), retry_delay=int(retry_delay)
    )


def test_start_search_backend_creates_backend_with_custom_values(
    mocker: MockerFixture, fake_env_config: dict[str, str]
) -> None:
    """start_search_backend reads config and calls subfunctions with correct values."""
    env_path = Path("foobar")
    host = fake_env_config["VALKEY_HOST"]
    port = fake_env_config["VALKEY_PORT"]
    max_retries = fake_env_config["VALKEY_PING_MAX_RETRIES"]
    retry_delay = fake_env_config["VALKEY_PING_RETRY_DELAY"]

    mock_load = mocker.patch(
        "bss_cli.cli.load_config",
        return_value={
            "VALKEY_HOST": host,
            "VALKEY_PORT": port,
            "VALKEY_PING_MAX_RETRIES": max_retries,
            "VALKEY_PING_RETRY_DELAY": retry_delay,
        },
    )
    mock_client = mocker.MagicMock()
    mock_get_client = mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    start_search_backend(Path(str(env_path)))

    mock_load.assert_called_once_with(env_path)
    mock_get_client.assert_called_once_with(host=host, port=int(port))
    mock_client.ping.assert_called_once_with(
        max_retries=int(max_retries),
        retry_delay=int(retry_delay),
    )


def test_start_search_backend_uses_defaults_when_config_keys_absent(
    mocker: MockerFixture,
) -> None:
    """start_search_backend falls back to defaults when config has no keys."""
    mocker.patch("bss_cli.cli.load_config", return_value={})
    mock_client = mocker.MagicMock()
    mock_client.ping.return_value = None
    mock_get_client = mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    start_search_backend(DEFAULT_ENV_CONFIG_PATH)

    mock_get_client.assert_called_once_with(host=DEFAULT_VALKEY_HOST, port=int(DEFAULT_VALKEY_PORT))


def test_start_search_backend_succeeds_when_ping_succeeds(mocker: MockerFixture) -> None:
    """start_search_backend completes without raising when ping succeeds."""
    mocker.patch(
        "bss_cli.cli.load_config",
        return_value={"VALKEY_HOST": DEFAULT_VALKEY_HOST, "VALKEY_PORT": DEFAULT_VALKEY_PORT},
    )
    mock_client = mocker.MagicMock()
    mock_client.ping.return_value = None
    mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    start_search_backend(DEFAULT_ENV_CONFIG_PATH)  # should not raise


def test_start_search_backend_raises_on_connection_failure(mocker: MockerFixture) -> None:
    """start_search_backend raises ConnectionError when ping fails."""
    mocker.patch(
        "bss_cli.cli.load_config",
        return_value={"VALKEY_HOST": DEFAULT_VALKEY_HOST, "VALKEY_PORT": DEFAULT_VALKEY_PORT},
    )
    mock_client = mocker.MagicMock()
    mock_client.ping.side_effect = ConnectionError("unreachable")
    mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    with pytest.raises(ConnectionError, match="unreachable"):
        start_search_backend(DEFAULT_ENV_CONFIG_PATH)


# ---------------------------------------------------------------------------
# create_profiles
# ---------------------------------------------------------------------------


def test_create_profiles_calls_create_index_with_correct_config_dict(
    mocker: MockerFixture, fake_profile_config: dict[str, object]
) -> None:
    """create_profiles calls create_index with the expected config dict."""

    # TODO: Load from profile file (see: https://github.com/bentotten/BehaviorSimilaritySearch/issues/25)
    # Mock out and check load_config()

    mock_client = mocker.MagicMock()
    mocker.patch("bss_cli.cli.get_client", return_value=mock_client)
    mock_create_index = mocker.patch("bss_cli.cli.create_index")

    # TODO: Load from profile file (see: https://github.com/bentotten/BehaviorSimilaritySearch/issues/25)
    create_profiles()

    mock_create_index.assert_called_once_with(mock_client, fake_profile_config)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def test_bootstrap_calls_subfunctions_with_correct_values(mocker: MockerFixture) -> None:
    """bootstrap calls all subfunctions with correct arguments."""
    mock_start_search_backend_call = mocker.patch("bss_cli.cli.start_search_backend")
    mock_create_profiles = mocker.patch("bss_cli.cli.create_profiles")
    mock_load_data = mocker.patch("bss_cli.cli.load_data")
    mock_encode_data = mocker.patch("bss_cli.cli.encode_data")
    mock_store_vectors = mocker.patch("bss_cli.cli.store_vectors")

    bootstrap(DEFAULT_ENV_CONFIG_PATH)

    # Normally we dont want to test implementation details in this way, but here we want to ensure
    # appropriate values are being passed through subcommand without becoming corrupted or switched.
    mock_start_search_backend_call.assert_called_once_with(DEFAULT_ENV_CONFIG_PATH)
    mock_create_profiles.assert_called_once()
    mock_load_data.assert_called_once_with()
    mock_encode_data.assert_called_once_with()
    mock_store_vectors.assert_called_once_with()

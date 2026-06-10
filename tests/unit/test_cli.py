"""Unit tests for bss_cli."""

from pathlib import Path

import numpy as np
import pytest
from pytest_mock import MockerFixture

from bss_cli import (
    DEFAULT_DATA_DIR,
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

    mock_bootstrap.assert_called_once_with(
        env_config_path=DEFAULT_ENV_CONFIG_PATH, data_path=DEFAULT_DATA_DIR
    )


def test_main_dispatches_bootstrap_with_custom_paths(mocker: MockerFixture) -> None:
    """main() passes custom paths to bootstrap() when provided."""
    env_path = "configs/foo.env"
    data_path = "data/custom"
    mocker.patch(
        "sys.argv",
        ["bss", "--env_config", env_path, "--data_path", data_path, "bootstrap"],
    )
    mock_bootstrap = mocker.patch("bss_cli.cli.bootstrap")

    main()

    mock_bootstrap.assert_called_once_with(
        env_config_path=Path(env_path), data_path=Path(data_path)
    )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parser_default_configs() -> None:
    """Config paths default to proper defaults."""
    bootstrap_args = build_parser().parse_args(["bootstrap"])
    assert bootstrap_args.env_config == DEFAULT_ENV_CONFIG_PATH
    assert bootstrap_args.data_path == DEFAULT_DATA_DIR


def test_parser_accepts_custom_env_config_path() -> None:
    """--env_config accepts an explicit path."""
    custom_env_path = Path("configs/custom_path.env")
    args = build_parser().parse_args(["--env_config", str(custom_env_path), "bootstrap"])
    assert args.env_config == custom_env_path


def test_parser_accepts_custom_data_path() -> None:
    """--data_path accepts an explicit path."""
    custom_data_path = Path("data/custom")
    args = build_parser().parse_args(["--data_path", str(custom_data_path), "bootstrap"])
    assert args.data_path == custom_data_path


def test_parser_no_subcommand_sets_command_none() -> None:
    """No subcommand sets command to None."""
    assert build_parser().parse_args([]).command is None


def test_parser_bootstrap_is_valid_subcommand() -> None:
    """bootstrap is a recognised subcommand."""
    assert build_parser().parse_args(["bootstrap"]).command == "bootstrap"


# ---------------------------------------------------------------------------
# start_search_backend
# ---------------------------------------------------------------------------


def test_start_search_backend_uses_provided_config_values(
    mocker: MockerFixture, fake_env_config: dict[str, str]
) -> None:
    """start_search_backend reads host, port, and retry params from the config dict."""
    mock_client = mocker.MagicMock()
    mock_get_client = mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    start_search_backend(fake_env_config)

    mock_get_client.assert_called_once_with(
        host=fake_env_config["VALKEY_HOST"],
        port=int(fake_env_config["VALKEY_PORT"]),
    )
    mock_client.ping.assert_called_once_with(
        max_retries=int(fake_env_config["VALKEY_PING_MAX_RETRIES"]),
        retry_delay=int(fake_env_config["VALKEY_PING_RETRY_DELAY"]),
    )


def test_start_search_backend_uses_defaults_when_keys_absent(
    mocker: MockerFixture,
) -> None:
    """start_search_backend falls back to defaults when the config is empty."""
    mock_client = mocker.MagicMock()
    mock_client.ping.return_value = None
    mock_get_client = mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    start_search_backend({})

    mock_get_client.assert_called_once_with(host=DEFAULT_VALKEY_HOST, port=int(DEFAULT_VALKEY_PORT))
    mock_client.ping.assert_called_once_with(
        max_retries=int(DEFAULT_MAX_PING_RETRIES),
        retry_delay=int(DEFAULT_PING_RETRY_DELAY),
    )


def test_start_search_backend_succeeds_when_ping_succeeds(mocker: MockerFixture) -> None:
    """start_search_backend completes without raising when ping succeeds."""
    mock_client = mocker.MagicMock()
    mock_client.ping.return_value = None
    mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    start_search_backend({})  # should not raise


def test_start_search_backend_raises_on_connection_failure(mocker: MockerFixture) -> None:
    """start_search_backend raises ConnectionError when ping fails."""
    mock_client = mocker.MagicMock()
    mock_client.ping.side_effect = ConnectionError("unreachable")
    mocker.patch("bss_cli.cli.get_client", return_value=mock_client)

    with pytest.raises(ConnectionError, match="unreachable"):
        start_search_backend({})


# ---------------------------------------------------------------------------
# create_profiles
# ---------------------------------------------------------------------------


def test_create_profiles_calls_create_index_with_provided_config(
    mocker: MockerFixture, fake_profile_config: dict[str, object]
) -> None:
    """create_profiles forwards the supplied profile config to create_index."""
    mock_client = mocker.MagicMock()
    mock_get_client = mocker.patch("bss_cli.cli.get_client", return_value=mock_client)
    mock_create_index = mocker.patch("bss_cli.cli.create_index")

    create_profiles(fake_profile_config)

    mock_get_client.assert_called_once_with()
    mock_create_index.assert_called_once_with(mock_client, fake_profile_config)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def test_bootstrap_calls_subfunctions_with_correct_values(
    mocker: MockerFixture, fake_env_config: dict[str, str]
) -> None:
    """bootstrap loads config, initialises encoder, then runs each pipeline step in order."""
    embedding_dim = 512

    fake_encoder = mocker.MagicMock()
    fake_encoder.embedding_dim = embedding_dim
    fake_samples = [{"filename": "a.png", "data": b"<png>"}]
    fake_arrays = [np.zeros((4, 4, 3), dtype=np.uint8)]
    fake_embeddings = np.zeros((1, embedding_dim), dtype=np.float32)
    fake_encoder.encode_images.return_value = fake_embeddings

    mock_load_config = mocker.patch("bss_cli.cli.load_config", return_value=fake_env_config)
    mock_get_encoder = mocker.patch("bss_cli.cli.get_encoder", return_value=fake_encoder)
    mock_start_backend = mocker.patch("bss_cli.cli.start_search_backend")
    mock_create_profiles = mocker.patch("bss_cli.cli.create_profiles")
    mock_load_data = mocker.patch("bss_cli.cli.load_data", return_value=fake_samples)
    mock_to_numpy = mocker.patch("bss_cli.cli.image_bytes_to_numpy", return_value=fake_arrays)
    mock_store_vectors = mocker.patch("bss_cli.cli.store_vectors")

    bootstrap(DEFAULT_ENV_CONFIG_PATH, DEFAULT_DATA_DIR)

    # Normally we don't assert on internal call wiring, but here we want to confirm
    # values are forwarded through subcommand boundaries without being switched.
    mock_load_config.assert_called_once_with(DEFAULT_ENV_CONFIG_PATH)
    mock_get_encoder.assert_called()  # called at init and again to retrieve singleton
    mock_start_backend.assert_called_once_with(fake_env_config)
    mock_create_profiles.assert_called_once()
    mock_load_data.assert_called_once_with(DEFAULT_DATA_DIR)
    mock_to_numpy.assert_called_once_with(fake_samples)
    fake_encoder.encode_images.assert_called_once_with(fake_arrays)
    mock_store_vectors.assert_called_once_with()


def test_bootstrap_builds_profile_config_from_encoder_dim(
    mocker: MockerFixture, fake_env_config: dict[str, str]
) -> None:
    """bootstrap builds the profile config so its vector dim matches the encoder."""
    embedding_dim = 768

    fake_encoder = mocker.MagicMock()
    fake_encoder.embedding_dim = embedding_dim
    fake_encoder.encode_images.return_value = np.zeros((0, embedding_dim), dtype=np.float32)

    mocker.patch("bss_cli.cli.load_config", return_value=fake_env_config)
    mocker.patch("bss_cli.cli.get_encoder", return_value=fake_encoder)
    mocker.patch("bss_cli.cli.start_search_backend")
    mock_create_profiles = mocker.patch("bss_cli.cli.create_profiles")
    mocker.patch("bss_cli.cli.load_data", return_value=[])
    mocker.patch("bss_cli.cli.image_bytes_to_numpy", return_value=[])
    mocker.patch("bss_cli.cli.store_vectors")

    bootstrap(DEFAULT_ENV_CONFIG_PATH, DEFAULT_DATA_DIR)

    profile_config = mock_create_profiles.call_args.args[0]
    assert profile_config["vector_field"]["dim"] == embedding_dim
    assert profile_config["index_name"] == "profile_1"
    assert profile_config["index_config"]["data_structure"] == "HASH"
    assert profile_config["index_config"]["prefixes"] == ["frame:"]
    assert profile_config["vector_field"]["algorithm"] == "HNSW"
    assert profile_config["vector_field"]["distance_metric"] == "COSINE"

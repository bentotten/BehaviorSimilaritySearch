"""Command-line interface for BehaviorSimilaritySearch."""

import argparse
from pathlib import Path
from typing import Any

from bss_data.dataloader import DEFAULT_DATA_DIR, load_data
from bss_encoder.encoder import encode_data

from bss_core.config import load_config

# NOTE: If changing base module, also change in __init__.py
from bss_valkey import (
    DEFAULT_MAX_PING_RETRIES,
    DEFAULT_PING_RETRY_DELAY,
    DEFAULT_VALKEY_HOST,
    DEFAULT_VALKEY_PORT,
)
from bss_valkey.valkey_client import get_client
from bss_valkey.vector_similarity_search import create_index, store_vectors

#: Default file for environment/connection configurations
DEFAULT_ENV_CONFIG_PATH = Path("configs/local.env")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="behavior-similarity-search",
        description="Behavior Similarity Search.",
    )
    parser.add_argument(
        "--env_config",
        type=Path,
        default=DEFAULT_ENV_CONFIG_PATH,
        metavar="PATH",
        help=f"Path to environment/connection config file (default: {DEFAULT_ENV_CONFIG_PATH}).",
    )
    parser.add_argument(
        "--data_path",
        type=Path,
        default=DEFAULT_DATA_DIR,
        metavar="PATH",
        help=f"Path to directory or bucket containing data (default: {DEFAULT_DATA_DIR}).",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "bootstrap",
        help="Bootstrap search backend and verify connections.",
    )

    return parser


def start_search_backend(search_backend_config: dict[str, str]) -> None:
    """Start and initialize search backend (e.g. Valkey server).

    Args:
        search_backend_config: Configurations for search backend host.
    """

    host: str = search_backend_config.get("VALKEY_HOST", DEFAULT_VALKEY_HOST)
    port: int = int(search_backend_config.get("VALKEY_PORT", DEFAULT_VALKEY_PORT))
    max_retries: int = int(
        search_backend_config.get("VALKEY_PING_MAX_RETRIES", DEFAULT_MAX_PING_RETRIES)
    )
    retry_delay: int = int(
        search_backend_config.get("VALKEY_PING_RETRY_DELAY", DEFAULT_PING_RETRY_DELAY)
    )

    # TODO: Replace with logger (https://github.com/bentotten/BehaviorSimilaritySearch/issues/17)
    print(f"Pinging Valkey at {host}:{port} ...", end=" ", flush=True)

    client = get_client(host=host, port=port)
    client.ping(max_retries=max_retries, retry_delay=retry_delay)


def create_profiles(profile_config: dict[str, Any]) -> None:
    """Create search profiles with the search backend.

    Args:
        profile_config: Configurations for profile to use with search backend.
    """

    # For Valkey, indices == profiles
    create_index(get_client(), profile_config)


def bootstrap(env_config_path: Path, data_path: Path) -> None:
    """Bootstrap search backend (e.g. Valkey).

    Args:
        env_config_path: Path to the config file to load.
        data_path: Path to the data directory.
    """

    search_backend_config: dict[str, str] = load_config(env_config_path)

    # TODO: Load from file instead of hardcoded (see: https://github.com/bentotten/BehaviorSimilaritySearch/issues/31)
    encoder_config: dict[str, Any] = {
        "embedding_dim": 512,
    }

    # TODO: Load from profile file instead of hardcoded (see: https://github.com/bentotten/BehaviorSimilaritySearch/issues/25)
    profile_config: dict[str, Any] = {
        "index_name": "profile_1",
        "index_config": {
            "data_structure": "HASH",
            "prefixes": ["frame:"],
        },
        "vector_field": {
            "field_name": "embedding",
            "algorithm": "HNSW",
            "vector_type": "FLOAT32",
            "dim": 512,
            "distance_metric": "COSINE",
        },
    }

    assert profile_config["vector_field"]["dim"] == encoder_config["embedding_dim"], (
        f"Profile vector dim ({profile_config['vector_field']['dim']}) "
        f"does not match encoder embedding dim ({encoder_config['embedding_dim']})"
    )

    start_search_backend(search_backend_config)

    create_profiles(encoder_config)

    samples = load_data(data_path)

    # ImageSample and MediaSample are structurally compatible TypedDicts —
    # mypy enforces field matching at this boundary without import coupling.
    # _embeddings = encode_data(samples, encoder_config)
    encode_data()

    # Upload data to search backend
    store_vectors()

    print("Hello Valkey!")


def main() -> None:
    """Entry point for the command-line interface.

    Parses command-line arguments and dispatches to the appropriate handler.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "bootstrap":
        bootstrap(env_config_path=args.env_config, data_path=args.data_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

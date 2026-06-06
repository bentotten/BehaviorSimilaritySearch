"""Command-line interface for BehaviorSimilaritySearch."""

import argparse
import sys
from pathlib import Path

from bss_core.config import load_config
from bss_valkey.valkey_client import DEFAULT_MAX_PING_RETRIES, DEFAULT_PING_RETRY_DELAY, get_client

#: Default file for configurations
DEFAULT_CONFIG_PATH = Path("configs/local.env")
#: Default Valkey ip/host
DEFAULT_VALKEY_HOST = "127.0.0.1"
#: Default Valkey port
DEFAULT_VALKEY_PORT = "6379"


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
        "--config_path",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        metavar="PATH",
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH}).",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "bootstrap",
        help="Bootstrap search backend and verify connections.",
    )

    return parser


def bootstrap(config_path: Path) -> None:
    """Bootstrap search backend (e.g. Valkey).

    Args:
        config_path: Path to the config file to load.
    """
    config: dict[str, str] = load_config(config_path)
    host: str = config.get("VALKEY_HOST", DEFAULT_VALKEY_HOST)
    port: int = int(config.get("VALKEY_PORT", DEFAULT_VALKEY_PORT))
    max_retries: int = int(config.get("VALKEY_PING_MAX_RETRIES", DEFAULT_MAX_PING_RETRIES))
    retry_delay: int = int(config.get("VALKEY_PING_RETRY_DELAY", DEFAULT_PING_RETRY_DELAY))

    # TODO: Replace with logger (https://github.com/bentotten/BehaviorSimilaritySearch/issues/17)
    print(f"Pinging Valkey at {host}:{port} ...", end=" ", flush=True)

    client = get_client(host=host, port=port)

    try:
        client.ping(max_retries=max_retries, retry_delay=retry_delay)
        print("Hello Valkey!")
    except ConnectionError as e:
        print(f"FAILED: {e}")
        sys.exit(1)


def main() -> None:
    """Entry point for the command-line interface.

    Parses command-line arguments and dispatches to the appropriate handler.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "bootstrap":
        bootstrap(args.config_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

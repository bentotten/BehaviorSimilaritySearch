"""bss_cli — command-line interface for BehaviorSimilaritySearch."""

from importlib.metadata import version

from bss_data.dataloader import DEFAULT_DATA_DIR

from bss_cli.cli import DEFAULT_ENV_CONFIG_PATH
from bss_valkey import (
    DEFAULT_MAX_PING_RETRIES,
    DEFAULT_PING_RETRY_DELAY,
    DEFAULT_VALKEY_HOST,
    DEFAULT_VALKEY_PORT,
)

__version__ = version("behavior-similarity-search-cli")

__all__ = [
    "DEFAULT_ENV_CONFIG_PATH",
    "DEFAULT_MAX_PING_RETRIES",
    "DEFAULT_PING_RETRY_DELAY",
    "DEFAULT_VALKEY_HOST",
    "DEFAULT_VALKEY_PORT",
    "DEFAULT_DATA_DIR",
]

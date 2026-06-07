"""bss_valkey — Valkey library for BehaviorSimilaritySearch."""

from importlib.metadata import version

from bss_valkey.valkey_client import (
    DEFAULT_MAX_PING_RETRIES,
    DEFAULT_PING_RETRY_DELAY,
    DEFAULT_VALKEY_HOST,
    DEFAULT_VALKEY_PORT,
)

__version__ = version("behavior-similarity-search-valkey")

# Re-export here to allow pass-through at the top level
__all__ = [
    "DEFAULT_MAX_PING_RETRIES",
    "DEFAULT_PING_RETRY_DELAY",
    "DEFAULT_VALKEY_HOST",
    "DEFAULT_VALKEY_PORT",
]

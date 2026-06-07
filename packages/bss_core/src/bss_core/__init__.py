"""bss_core — core library for BehaviorSimilaritySearch."""

from importlib.metadata import version

from bss_core.metadata import MediaMetadata, create_media_metadata

__all__ = [
    "MediaMetadata",
    "create_media_metadata",
]

__version__ = version("behavior-similarity-search-core")

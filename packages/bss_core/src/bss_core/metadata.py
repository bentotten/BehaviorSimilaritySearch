"""Media metadata schema for Valkey Vector Similarity Search storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class MediaMetadata:
    """Metadata and vector payload for a single item stored in Valkey VSS.

    This is a transfer object that bridges the data/encoding layer and the
    Valkey storage layer. It carries everything needed to insert a vector
    with its associated metadata into an index.

    Attributes:
        key: Unique identifier for this record (e.g. "oxford_pets:Abyssinian_042").
        vector: The encoded vector from the encoder.
        label: Class or action label associated with the source sample.
        media_type: Discriminator string — "image" or "video".
        source_path: Original file path of the source data on disk.
        ingested_at: UTC timestamp of when this record was created.
    """

    key: str
    vector: list[float]
    label: str
    media_type: str
    source_path: str
    ingested_at: datetime

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.key:
            raise ValueError("key must be a non-empty string.")
        if not self.vector:
            raise ValueError("vector must be a non-empty list of floats.")
        if self.media_type not in ("image", "video"):
            raise ValueError(f"media_type must be 'image' or 'video', got '{self.media_type}'.")


def create_media_metadata(
    key: str,
    vector: list[float],
    label: str,
    media_type: str,
    source_path: str,
) -> MediaMetadata:
    """Create a MediaMetadata with the current UTC timestamp.

    Convenience factory that fills in ingested_at automatically.

    Args:
        key: Unique identifier for this record.
        vector: The encoded vector.
        label: Class or action label.
        media_type: "image" or "video".
        source_path: Original file path.

    Returns:
        A fully populated MediaMetadata.
    """
    return MediaMetadata(
        key=key,
        vector=vector,
        label=label,
        media_type=media_type,
        source_path=source_path,
        ingested_at=datetime.now(UTC),
    )

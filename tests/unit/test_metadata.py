"""Unit tests for bss_core.metadata."""

from datetime import UTC, datetime

import pytest

from bss_core.metadata import MediaMetadata, create_media_metadata

# ---------------------------------------------------------------------------
# MediaMetadata dataclass
# ---------------------------------------------------------------------------


def test_valid_image_record() -> None:
    """MediaMetadata accepts valid image metadata."""
    now = datetime.now(UTC)
    record = MediaMetadata(
        key="pets:Abyssinian_042",
        vector=[0.1, 0.2, 0.3],
        label="Abyssinian",
        media_type="image",
        source_path="/data/oxford_pets/images/Abyssinian_042.jpg",
        ingested_at=now,
    )

    assert record.key == "pets:Abyssinian_042"
    assert record.vector == [0.1, 0.2, 0.3]
    assert record.label == "Abyssinian"
    assert record.media_type == "image"
    assert record.source_path == "/data/oxford_pets/images/Abyssinian_042.jpg"
    assert record.ingested_at == now


def test_valid_video_record() -> None:
    """MediaMetadata accepts valid video metadata."""
    now = datetime.now(UTC)
    record = MediaMetadata(
        key="hmdb51:running_clip_003",
        vector=[0.5, -0.2, 0.8, 0.1],
        label="running",
        media_type="video",
        source_path="/data/hmdb51/running/clip_003",
        ingested_at=now,
    )

    assert record.key == "hmdb51:running_clip_003"
    assert record.media_type == "video"
    assert record.label == "running"


def test_record_is_frozen() -> None:
    """MediaMetadata is immutable."""
    now = datetime.now(UTC)
    record = MediaMetadata(
        key="test:001",
        vector=[1.0, 2.0],
        label="cat",
        media_type="image",
        source_path="/tmp/cat.jpg",
        ingested_at=now,
    )

    with pytest.raises(AttributeError):
        record.key = "test:002"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_empty_key_raises() -> None:
    """Empty key raises ValueError."""
    with pytest.raises(ValueError, match="key must be a non-empty string"):
        MediaMetadata(
            key="",
            vector=[1.0],
            label="cat",
            media_type="image",
            source_path="/tmp/cat.jpg",
            ingested_at=datetime.now(UTC),
        )


def test_empty_vector_raises() -> None:
    """Empty vector raises ValueError."""
    with pytest.raises(ValueError, match="vector must be a non-empty list"):
        MediaMetadata(
            key="test:001",
            vector=[],
            label="cat",
            media_type="image",
            source_path="/tmp/cat.jpg",
            ingested_at=datetime.now(UTC),
        )


def test_invalid_media_type_raises() -> None:
    """Invalid media_type raises ValueError."""
    with pytest.raises(ValueError, match="media_type must be 'image' or 'video'"):
        MediaMetadata(
            key="test:001",
            vector=[1.0, 2.0],
            label="cat",
            media_type="audio",
            source_path="/tmp/cat.wav",
            ingested_at=datetime.now(UTC),
        )


# ---------------------------------------------------------------------------
# create_media_metadata factory
# ---------------------------------------------------------------------------


def test_factory_sets_timestamp() -> None:
    """create_media_metadata auto-fills ingested_at with current UTC time."""
    before = datetime.now(UTC)
    record = create_media_metadata(
        key="test:auto_ts",
        vector=[0.1, 0.2],
        label="dog",
        media_type="image",
        source_path="/tmp/dog.jpg",
    )
    after = datetime.now(UTC)

    assert before <= record.ingested_at <= after
    assert record.ingested_at.tzinfo is not None


def test_factory_passes_all_fields() -> None:
    """create_media_metadata passes all arguments to MediaMetadata."""
    record = create_media_metadata(
        key="hmdb51:jumping_007",
        vector=[0.5, 0.6, 0.7],
        label="jumping",
        media_type="video",
        source_path="/data/hmdb51/jumping/clip_007",
    )

    assert record.key == "hmdb51:jumping_007"
    assert record.vector == [0.5, 0.6, 0.7]
    assert record.label == "jumping"
    assert record.media_type == "video"
    assert record.source_path == "/data/hmdb51/jumping/clip_007"


def test_factory_validates_same_as_direct_construction() -> None:
    """create_media_metadata raises on invalid input just like direct construction."""
    with pytest.raises(ValueError, match="key must be a non-empty string"):
        create_media_metadata(
            key="",
            vector=[1.0],
            label="cat",
            media_type="image",
            source_path="/tmp/cat.jpg",
        )

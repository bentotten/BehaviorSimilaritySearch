"""Unit tests for bss_data.dataset."""

from pathlib import Path

import pytest
from PIL import Image

from bss_data.dataset import Dataset, MediaType, Sample, image_sample, video_sample

# ---------------------------------------------------------------------------
# Sample dataclass
# ---------------------------------------------------------------------------


def test_image_sample_factory() -> None:
    """image_sample() creates a Sample with media_type=IMAGE."""
    img = Image.new("RGB", (10, 10))
    sample = image_sample(image=img, label="cat", path=Path("/tmp/cat.jpg"))

    assert sample.media_type == MediaType.IMAGE
    assert sample.image is img
    assert sample.label == "cat"
    assert sample.path == Path("/tmp/cat.jpg")
    assert sample.frames == []


def test_video_sample_factory() -> None:
    """video_sample() creates a Sample with media_type=VIDEO."""
    frames = [Image.new("RGB", (10, 10)) for _ in range(5)]
    sample = video_sample(frames=frames, label="running", path=Path("/tmp/clip"))

    assert sample.media_type == MediaType.VIDEO
    assert sample.image is None
    assert sample.frames == frames
    assert sample.label == "running"
    assert sample.path == Path("/tmp/clip")


def test_image_sample_defaults() -> None:
    """image_sample() provides sensible defaults for label and path."""
    img = Image.new("RGB", (10, 10))
    sample = image_sample(image=img)

    assert sample.label == ""
    assert sample.path is None


def test_video_sample_defaults() -> None:
    """video_sample() provides sensible defaults for label and path."""
    frames = [Image.new("RGB", (10, 10))]
    sample = video_sample(frames=frames)

    assert sample.label == ""
    assert sample.path is None


def test_sample_is_frozen() -> None:
    """Sample is immutable (frozen dataclass)."""
    img = Image.new("RGB", (10, 10))
    sample = image_sample(image=img, label="dog")

    with pytest.raises(AttributeError):
        sample.label = "cat"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Sample validation
# ---------------------------------------------------------------------------


def test_image_sample_requires_image() -> None:
    """IMAGE sample without an image raises ValueError."""
    with pytest.raises(ValueError, match="IMAGE samples must have 'image' set"):
        Sample(media_type=MediaType.IMAGE, image=None)


def test_video_sample_requires_frames() -> None:
    """VIDEO sample without frames raises ValueError."""
    with pytest.raises(ValueError, match="VIDEO samples must have at least one frame"):
        Sample(media_type=MediaType.VIDEO, frames=[])


def test_video_sample_no_frames_default() -> None:
    """VIDEO sample with default empty frames raises ValueError."""
    with pytest.raises(ValueError, match="VIDEO samples must have at least one frame"):
        Sample(media_type=MediaType.VIDEO)


# ---------------------------------------------------------------------------
# MediaType enum
# ---------------------------------------------------------------------------


def test_media_type_values() -> None:
    """MediaType has IMAGE and VIDEO members with string values."""
    assert MediaType.IMAGE.value == "image"
    assert MediaType.VIDEO.value == "video"


# ---------------------------------------------------------------------------
# Dataset protocol
# ---------------------------------------------------------------------------


class _ConformingDataset:
    """Minimal implementation satisfying the Dataset protocol."""

    def __init__(self, samples: list[Sample]) -> None:
        self._samples = samples

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, index: int) -> Sample:
        return self._samples[index]


class _NonConformingDataset:
    """Class that does NOT satisfy the Dataset protocol."""

    pass


def test_conforming_class_is_dataset_instance() -> None:
    """A class with __len__ and __getitem__ satisfies the Dataset protocol."""
    ds = _ConformingDataset([])
    assert isinstance(ds, Dataset)


def test_non_conforming_class_is_not_dataset_instance() -> None:
    """A class without required methods does not satisfy the Dataset protocol."""
    obj = _NonConformingDataset()
    assert not isinstance(obj, Dataset)

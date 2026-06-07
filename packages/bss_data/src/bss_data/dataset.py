"""Dataset protocol and base types for BehaviorSimilaritySearch."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from PIL import Image


class MediaType(Enum):
    """Discriminator for the kind of media a sample contains."""

    IMAGE = "image"
    VIDEO = "video"


@dataclass(frozen=True)
class Sample:
    """A single dataset sample that can hold either an image or video frames.

    For image samples, ``image`` is set and ``frames`` is empty.
    For video samples, ``frames`` contains the ordered list of PIL images
    representing the clip, and ``image`` is None.

    Attributes:
        media_type: Whether this sample is an image or video clip.
        image: The loaded PIL image (IMAGE samples only).
        frames: Ordered frames of a video clip (VIDEO samples only).
        label: Human-readable label or class name. Empty string if unlabeled.
        path: Original file path on disk, if available.
    """

    media_type: MediaType
    image: Image.Image | None = None
    frames: list[Image.Image] = field(default_factory=list)
    label: str = ""
    path: Path | None = None

    def __post_init__(self) -> None:
        """Validate that the sample content matches its media_type."""
        if self.media_type == MediaType.IMAGE and self.image is None:
            raise ValueError("IMAGE samples must have 'image' set.")
        if self.media_type == MediaType.VIDEO and not self.frames:
            raise ValueError("VIDEO samples must have at least one frame in 'frames'.")


def image_sample(
    image: Image.Image,
    label: str = "",
    path: Path | None = None,
) -> Sample:
    """Convenience constructor for an image sample.

    Args:
        image: The PIL image.
        label: Optional label string.
        path: Optional source file path.

    Returns:
        A Sample with media_type=IMAGE.
    """
    return Sample(media_type=MediaType.IMAGE, image=image, label=label, path=path)


def video_sample(
    frames: list[Image.Image],
    label: str = "",
    path: Path | None = None,
) -> Sample:
    """Convenience constructor for a video clip sample.

    Args:
        frames: Ordered list of PIL images representing video frames.
        label: Optional label string.
        path: Optional source file path.

    Returns:
        A Sample with media_type=VIDEO.
    """
    return Sample(media_type=MediaType.VIDEO, frames=frames, label=label, path=path)


@runtime_checkable
class Dataset(Protocol):
    """Protocol for datasets that provide indexed access to samples.

    Any class implementing __len__ and __getitem__ can be used as a Dataset
    with the DataLoader.
    """

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        ...

    def __getitem__(self, index: int) -> Sample:
        """Return the sample at the given index.

        Args:
            index: Zero-based sample index.

        Returns:
            The corresponding Sample.

        Raises:
            IndexError: If the index is out of range.
        """
        ...

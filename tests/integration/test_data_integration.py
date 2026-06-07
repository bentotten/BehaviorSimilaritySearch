"""Integration tests — bss_data cross-module interactions.

Verifies that ImageDirectoryDataset, OxfordPetsDataset, and VideoDirectoryDataset
work correctly with the DataLoader, and that the full pipeline from disk to
batched samples operates as expected.
"""

from pathlib import Path

import pytest
from PIL import Image

from bss_data.dataloader import DataLoader
from bss_data.dataset import Dataset, MediaType, Sample, image_sample, video_sample
from bss_data.image_directory import ImageDirectoryDataset
from bss_data.oxford_pets import OxfordPetsDataset
from bss_data.video_directory import VideoDirectoryDataset

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def labeled_image_dir(tmp_path: Path) -> Path:
    """Create a directory structure mimicking a labeled image dataset."""
    for breed in ("siamese", "persian", "tabby"):
        breed_dir = tmp_path / breed
        breed_dir.mkdir()
        for i in range(4):
            img = Image.new("RGB", (8, 8), color=(i * 30, i * 20, i * 10))
            img.save(breed_dir / f"{breed}_{i}.jpg")
    return tmp_path


@pytest.fixture()
def oxford_pets_dir(tmp_path: Path) -> Path:
    """Create a directory structure mimicking the Oxford Pets dataset."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    breeds_and_counts = [
        ("Abyssinian", 5),
        ("Bengal", 3),
        ("Birman", 4),
    ]
    for breed, count in breeds_and_counts:
        for i in range(count):
            img = Image.new("RGB", (8, 8))
            img.save(images_dir / f"{breed}_{i + 1}.jpg")
    return tmp_path


@pytest.fixture()
def video_clip_dir(tmp_path: Path) -> Path:
    """Create a directory structure mimicking an action recognition video dataset."""
    for action, clip_counts in [("running", [3, 4]), ("jumping", [5])]:
        action_dir = tmp_path / action
        action_dir.mkdir()
        for clip_idx, num_frames in enumerate(clip_counts):
            clip_dir = action_dir / f"clip_{clip_idx:03d}"
            clip_dir.mkdir()
            for frame_idx in range(num_frames):
                img = Image.new("RGB", (8, 8), color=(frame_idx * 20, 0, 0))
                img.save(clip_dir / f"frame_{frame_idx:04d}.jpg")
    return tmp_path


# ---------------------------------------------------------------------------
# ImageDirectoryDataset + DataLoader
# ---------------------------------------------------------------------------


def test_image_directory_with_dataloader(labeled_image_dir: Path) -> None:
    """ImageDirectoryDataset feeds batches through DataLoader correctly."""
    ds = ImageDirectoryDataset(labeled_image_dir)
    loader = DataLoader(ds, batch_size=4)

    total_samples = 0
    labels_seen: set[str] = set()

    for batch in loader:
        assert len(batch) <= 4
        for sample in batch:
            assert isinstance(sample, Sample)
            assert sample.media_type == MediaType.IMAGE
            assert isinstance(sample.image, Image.Image)
            assert sample.image.mode == "RGB"
            assert sample.label != ""
            labels_seen.add(sample.label)
            total_samples += 1

    assert total_samples == 12  # 3 breeds × 4 images
    assert labels_seen == {"siamese", "persian", "tabby"}


def test_image_directory_dataloader_drop_last(labeled_image_dir: Path) -> None:
    """DataLoader with drop_last=True discards incomplete batches."""
    ds = ImageDirectoryDataset(labeled_image_dir)
    loader = DataLoader(ds, batch_size=5, drop_last=True)
    batches = list(loader)

    assert len(batches) == 2  # 12 // 5 = 2 full batches, remainder dropped
    assert all(len(b) == 5 for b in batches)


def test_image_directory_dataloader_shuffle(labeled_image_dir: Path) -> None:
    """DataLoader with shuffle yields all samples regardless of order."""
    ds = ImageDirectoryDataset(labeled_image_dir)
    loader = DataLoader(ds, batch_size=4, shuffle=True)
    all_samples = [s for batch in loader for s in batch]

    assert len(all_samples) == 12
    labels = {s.label for s in all_samples}
    assert labels == {"siamese", "persian", "tabby"}


# ---------------------------------------------------------------------------
# OxfordPetsDataset + DataLoader
# ---------------------------------------------------------------------------


def test_oxford_pets_with_dataloader(oxford_pets_dir: Path) -> None:
    """OxfordPetsDataset feeds batches through DataLoader correctly."""
    ds = OxfordPetsDataset(data_dir=oxford_pets_dir, download=False)
    loader = DataLoader(ds, batch_size=4)

    total_samples = 0
    labels_seen: set[str] = set()

    for batch in loader:
        assert len(batch) <= 4
        for sample in batch:
            assert isinstance(sample, Sample)
            assert sample.media_type == MediaType.IMAGE
            assert isinstance(sample.image, Image.Image)
            labels_seen.add(sample.label)
            total_samples += 1

    assert total_samples == 12  # 5 + 3 + 4
    assert labels_seen == {"Abyssinian", "Bengal", "Birman"}


def test_oxford_pets_dataloader_multiple_epochs(oxford_pets_dir: Path) -> None:
    """DataLoader can iterate over OxfordPetsDataset multiple times (epochs)."""
    ds = OxfordPetsDataset(data_dir=oxford_pets_dir, download=False)
    loader = DataLoader(ds, batch_size=6)

    for _epoch in range(3):
        all_samples = [s for batch in loader for s in batch]
        assert len(all_samples) == 12


# ---------------------------------------------------------------------------
# VideoDirectoryDataset + DataLoader
# ---------------------------------------------------------------------------


def test_video_directory_with_dataloader(video_clip_dir: Path) -> None:
    """VideoDirectoryDataset feeds video clip batches through DataLoader."""
    ds = VideoDirectoryDataset(video_clip_dir)
    loader = DataLoader(ds, batch_size=2)

    total_clips = 0
    labels_seen: set[str] = set()

    for batch in loader:
        assert len(batch) <= 2
        for sample in batch:
            assert isinstance(sample, Sample)
            assert sample.media_type == MediaType.VIDEO
            assert sample.image is None
            assert len(sample.frames) > 0
            assert all(isinstance(f, Image.Image) for f in sample.frames)
            labels_seen.add(sample.label)
            total_clips += 1

    assert total_clips == 3  # 2 running + 1 jumping
    assert labels_seen == {"running", "jumping"}


def test_video_directory_dataloader_drop_last(video_clip_dir: Path) -> None:
    """DataLoader with drop_last=True works with video clips."""
    ds = VideoDirectoryDataset(video_clip_dir)
    loader = DataLoader(ds, batch_size=2, drop_last=True)
    batches = list(loader)

    assert len(batches) == 1  # 3 // 2 = 1 full batch
    assert len(batches[0]) == 2


def test_video_directory_dataloader_shuffle(video_clip_dir: Path) -> None:
    """DataLoader with shuffle yields all video clips."""
    ds = VideoDirectoryDataset(video_clip_dir)
    loader = DataLoader(ds, batch_size=2, shuffle=True)
    all_samples = [s for batch in loader for s in batch]

    assert len(all_samples) == 3
    labels = {s.label for s in all_samples}
    assert labels == {"running", "jumping"}


# ---------------------------------------------------------------------------
# Mixed media: DataLoader handles both image and video samples
# ---------------------------------------------------------------------------


def test_dataloader_handles_mixed_media() -> None:
    """DataLoader works with a dataset containing both image and video samples."""

    class MixedDataset:
        """Dataset yielding both image and video samples."""

        def __init__(self) -> None:
            self._items: list[Sample] = [
                image_sample(image=Image.new("RGB", (4, 4)), label="cat"),
                video_sample(frames=[Image.new("RGB", (4, 4)) for _ in range(3)], label="running"),
                image_sample(image=Image.new("RGB", (4, 4)), label="dog"),
                video_sample(frames=[Image.new("RGB", (4, 4)) for _ in range(2)], label="jumping"),
            ]

        def __len__(self) -> int:
            return len(self._items)

        def __getitem__(self, index: int) -> Sample:
            return self._items[index]

    ds = MixedDataset()
    loader = DataLoader(ds, batch_size=2)
    batches = list(loader)

    assert len(batches) == 2
    all_samples = [s for batch in batches for s in batch]

    image_samples = [s for s in all_samples if s.media_type == MediaType.IMAGE]
    video_samples = [s for s in all_samples if s.media_type == MediaType.VIDEO]

    assert len(image_samples) == 2
    assert len(video_samples) == 2


# ---------------------------------------------------------------------------
# Protocol conformance in integration context
# ---------------------------------------------------------------------------


def test_all_datasets_satisfy_protocol(
    labeled_image_dir: Path, oxford_pets_dir: Path, video_clip_dir: Path
) -> None:
    """All dataset implementations satisfy the Dataset protocol."""
    img_ds = ImageDirectoryDataset(labeled_image_dir)
    pets_ds = OxfordPetsDataset(data_dir=oxford_pets_dir, download=False)
    video_ds = VideoDirectoryDataset(video_clip_dir)

    assert isinstance(img_ds, Dataset)
    assert isinstance(pets_ds, Dataset)
    assert isinstance(video_ds, Dataset)


def test_dataloader_works_with_any_conforming_dataset() -> None:
    """DataLoader works with any object conforming to the Dataset protocol."""

    class InMemoryDataset:
        """Tiny in-memory dataset for protocol conformance test."""

        def __init__(self) -> None:
            self._items = [
                image_sample(image=Image.new("RGB", (4, 4)), label=f"item_{i}") for i in range(5)
            ]

        def __len__(self) -> int:
            return len(self._items)

        def __getitem__(self, index: int) -> Sample:
            return self._items[index]

    ds = InMemoryDataset()
    assert isinstance(ds, Dataset)

    loader = DataLoader(ds, batch_size=2)
    batches = list(loader)
    assert len(batches) == 3  # 2 + 2 + 1
    assert sum(len(b) for b in batches) == 5

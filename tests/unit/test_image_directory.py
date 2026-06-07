"""Unit tests for bss_data.image_directory."""

from pathlib import Path

import pytest
from PIL import Image

from bss_data.dataset import Dataset, MediaType, Sample
from bss_data.image_directory import ImageDirectoryDataset

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def image_dir(tmp_path: Path) -> Path:
    """Create a temp directory with a few test images in subdirectories."""
    cats_dir = tmp_path / "cats"
    dogs_dir = tmp_path / "dogs"
    cats_dir.mkdir()
    dogs_dir.mkdir()

    # Create small valid images
    for i in range(3):
        img = Image.new("RGB", (4, 4), color=(i * 50, 0, 0))
        img.save(cats_dir / f"cat_{i}.jpg")

    for i in range(2):
        img = Image.new("RGB", (4, 4), color=(0, i * 50, 0))
        img.save(dogs_dir / f"dog_{i}.png")

    return tmp_path


@pytest.fixture()
def flat_image_dir(tmp_path: Path) -> Path:
    """Create a temp directory with images directly in root (no subdirs)."""
    for i in range(2):
        img = Image.new("RGB", (4, 4), color=(0, 0, i * 50))
        img.save(tmp_path / f"image_{i}.jpg")
    return tmp_path


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


def test_raises_if_root_does_not_exist() -> None:
    """Constructor raises FileNotFoundError for nonexistent directory."""
    with pytest.raises(FileNotFoundError, match="Image directory not found"):
        ImageDirectoryDataset(Path("/tmp/nonexistent_dir_12345"))


def test_raises_if_no_images_found(tmp_path: Path) -> None:
    """Constructor raises ValueError when directory has no image files."""
    (tmp_path / "readme.txt").write_text("not an image")
    with pytest.raises(ValueError, match="No image files found"):
        ImageDirectoryDataset(tmp_path)


def test_loads_images_from_subdirectories(image_dir: Path) -> None:
    """Dataset finds images across subdirectories when recursive=True."""
    ds = ImageDirectoryDataset(image_dir, recursive=True)
    assert len(ds) == 5


def test_non_recursive_only_finds_top_level(image_dir: Path) -> None:
    """Dataset with recursive=False only finds images in root directory."""
    # image_dir has images only in subdirs, so non-recursive should find none
    with pytest.raises(ValueError, match="No image files found"):
        ImageDirectoryDataset(image_dir, recursive=False)


def test_non_recursive_finds_flat_images(flat_image_dir: Path) -> None:
    """Dataset with recursive=False finds images directly in root."""
    ds = ImageDirectoryDataset(flat_image_dir, recursive=False)
    assert len(ds) == 2


def test_custom_extensions(tmp_path: Path) -> None:
    """Dataset respects custom extensions filter."""
    img = Image.new("RGB", (4, 4))
    img.save(tmp_path / "photo.png")
    img.save(tmp_path / "photo.jpg")

    ds = ImageDirectoryDataset(tmp_path, extensions=frozenset({".png"}))
    assert len(ds) == 1


# ---------------------------------------------------------------------------
# __getitem__
# ---------------------------------------------------------------------------


def test_getitem_returns_sample(image_dir: Path) -> None:
    """__getitem__ returns a Sample with image, label, and path."""
    ds = ImageDirectoryDataset(image_dir)
    sample = ds[0]

    assert isinstance(sample, Sample)
    assert sample.media_type == MediaType.IMAGE
    assert isinstance(sample.image, Image.Image)
    assert sample.image.mode == "RGB"
    assert sample.path is not None
    assert sample.path.exists()


def test_getitem_label_from_subdirectory(image_dir: Path) -> None:
    """Labels are derived from subdirectory names."""
    ds = ImageDirectoryDataset(image_dir)
    labels = {ds[i].label for i in range(len(ds))}
    assert "cats" in labels
    assert "dogs" in labels


def test_getitem_label_empty_for_root_images(flat_image_dir: Path) -> None:
    """Label is empty string for images directly in root."""
    ds = ImageDirectoryDataset(flat_image_dir)
    for i in range(len(ds)):
        assert ds[i].label == ""


def test_getitem_index_out_of_range(image_dir: Path) -> None:
    """__getitem__ raises IndexError for invalid indices."""
    ds = ImageDirectoryDataset(image_dir)
    with pytest.raises(IndexError):
        ds[100]
    with pytest.raises(IndexError):
        ds[-1]


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_conforms_to_dataset_protocol(image_dir: Path) -> None:
    """ImageDirectoryDataset satisfies the Dataset protocol."""
    ds = ImageDirectoryDataset(image_dir)
    assert isinstance(ds, Dataset)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_root_property(image_dir: Path) -> None:
    """root property returns the directory passed at construction."""
    ds = ImageDirectoryDataset(image_dir)
    assert ds.root == image_dir

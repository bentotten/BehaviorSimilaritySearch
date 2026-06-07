"""Unit tests for bss_data.oxford_pets."""

from pathlib import Path

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from bss_data.dataset import Dataset, MediaType, Sample
from bss_data.oxford_pets import OxfordPetsDataset, _extract_breed_from_filename

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def pets_dir(tmp_path: Path) -> Path:
    """Create a fake Oxford Pets directory structure with sample images."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    filenames = [
        "Abyssinian_1.jpg",
        "Abyssinian_2.jpg",
        "Bengal_1.jpg",
        "german_shorthaired_3.jpg",
        "great_pyrenees_10.jpg",
    ]
    for name in filenames:
        img = Image.new("RGB", (4, 4))
        img.save(images_dir / name)

    return tmp_path


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


def test_loads_from_existing_directory(pets_dir: Path) -> None:
    """Constructor loads images from pre-existing data directory."""
    ds = OxfordPetsDataset(data_dir=pets_dir, download=False)
    assert len(ds) == 5


def test_raises_when_not_found_and_download_false(tmp_path: Path) -> None:
    """Constructor raises FileNotFoundError when data is missing and download=False."""
    with pytest.raises(FileNotFoundError, match="Dataset not found"):
        OxfordPetsDataset(data_dir=tmp_path / "missing", download=False)


def test_triggers_download_when_missing(tmp_path: Path, mocker: MockerFixture) -> None:
    """Constructor calls _download when data directory does not exist."""
    target_dir = tmp_path / "pets"
    mock_download = mocker.patch.object(OxfordPetsDataset, "_download")

    # After _download is called, simulate that the images dir was created
    images_dir = target_dir / "images"

    def fake_download() -> None:
        images_dir.mkdir(parents=True)
        img = Image.new("RGB", (4, 4))
        img.save(images_dir / "Cat_1.jpg")

    mock_download.side_effect = fake_download

    ds = OxfordPetsDataset(data_dir=target_dir, download=True)
    mock_download.assert_called_once()
    assert len(ds) == 1


# ---------------------------------------------------------------------------
# __getitem__
# ---------------------------------------------------------------------------


def test_getitem_returns_sample(pets_dir: Path) -> None:
    """__getitem__ returns a valid Sample with image, label, and path."""
    ds = OxfordPetsDataset(data_dir=pets_dir, download=False)
    sample = ds[0]

    assert isinstance(sample, Sample)
    assert sample.media_type == MediaType.IMAGE
    assert isinstance(sample.image, Image.Image)
    assert sample.image.mode == "RGB"
    assert sample.path is not None
    assert sample.path.exists()


def test_getitem_extracts_breed_label(pets_dir: Path) -> None:
    """Labels are breed names extracted from filenames."""
    ds = OxfordPetsDataset(data_dir=pets_dir, download=False)
    labels = {ds[i].label for i in range(len(ds))}
    assert "Abyssinian" in labels
    assert "Bengal" in labels
    assert "german_shorthaired" in labels
    assert "great_pyrenees" in labels


def test_getitem_index_out_of_range(pets_dir: Path) -> None:
    """__getitem__ raises IndexError for invalid indices."""
    ds = OxfordPetsDataset(data_dir=pets_dir, download=False)
    with pytest.raises(IndexError):
        ds[100]
    with pytest.raises(IndexError):
        ds[-1]


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_conforms_to_dataset_protocol(pets_dir: Path) -> None:
    """OxfordPetsDataset satisfies the Dataset protocol."""
    ds = OxfordPetsDataset(data_dir=pets_dir, download=False)
    assert isinstance(ds, Dataset)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_data_dir_property(pets_dir: Path) -> None:
    """data_dir property returns the directory passed at construction."""
    ds = OxfordPetsDataset(data_dir=pets_dir, download=False)
    assert ds.data_dir == pets_dir


# ---------------------------------------------------------------------------
# _extract_breed_from_filename
# ---------------------------------------------------------------------------


class TestExtractBreedFromFilename:
    """Tests for the breed name extraction helper."""

    def test_simple_breed(self) -> None:
        """Single-word breed with numeric suffix."""
        assert _extract_breed_from_filename("Abyssinian_100") == "Abyssinian"

    def test_multi_word_breed(self) -> None:
        """Multi-word breed with underscores."""
        assert _extract_breed_from_filename("german_shorthaired_3") == "german_shorthaired"

    def test_breed_with_long_number(self) -> None:
        """Breed followed by multi-digit number."""
        assert _extract_breed_from_filename("great_pyrenees_199") == "great_pyrenees"

    def test_no_numeric_suffix_returns_full_stem(self) -> None:
        """Fallback returns full stem when pattern doesn't match."""
        assert _extract_breed_from_filename("nodigits") == "nodigits"

    def test_trailing_non_digit_returns_full_stem(self) -> None:
        """When last segment is not all digits, returns full stem."""
        assert _extract_breed_from_filename("breed_abc") == "breed_abc"

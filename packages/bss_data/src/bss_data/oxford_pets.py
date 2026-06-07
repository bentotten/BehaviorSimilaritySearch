"""Oxford-IIIT Pet Dataset loader.

Downloads and provides access to the Oxford-IIIT Pet Dataset:
https://www.robots.ox.ac.uk/~vgg/data/pets/

The dataset contains 37 pet breeds with roughly 200 images each.
"""

from __future__ import annotations

import tarfile
import urllib.request
from pathlib import Path

from PIL import Image

from bss_data.dataset import Sample, image_sample

#: Base URL for the Oxford-IIIT Pets dataset.
_BASE_URL = "https://www.robots.ox.ac.uk/~vgg/data/pets/data"

#: Image archive filename.
_IMAGES_ARCHIVE = "images.tar.gz"

#: Default download location relative to project data directory.
DEFAULT_DATA_DIR = Path("data/oxford_pets")

#: File extensions to include from the archive.
_IMAGE_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})


class OxfordPetsDataset:
    """Oxford-IIIT Pet Dataset.

    Provides indexed access to the Oxford-IIIT Pet images. Downloads the
    dataset on first use if not already present on disk.

    The breed label is extracted from the filename convention used by the
    dataset: ``BreedName_123.jpg`` → ``BreedName``.

    Args:
        data_dir: Directory where the dataset will be stored.
        download: Whether to download the dataset if not already present.

    Raises:
        FileNotFoundError: If data is not present and download is False.
        RuntimeError: If download fails.
    """

    def __init__(
        self,
        data_dir: Path = DEFAULT_DATA_DIR,
        *,
        download: bool = True,
    ) -> None:
        self._data_dir = data_dir
        self._images_dir = data_dir / "images"

        if not self._images_dir.exists():
            if not download:
                raise FileNotFoundError(
                    f"Dataset not found at {self._images_dir}. "
                    "Set download=True to fetch it automatically."
                )
            self._download()

        self._samples: list[Path] = sorted(
            p
            for p in self._images_dir.iterdir()
            if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS
        )

    @property
    def data_dir(self) -> Path:
        """Root directory where dataset files are stored."""
        return self._data_dir

    def __len__(self) -> int:
        """Return the number of images in the dataset."""
        return len(self._samples)

    def __getitem__(self, index: int) -> Sample:
        """Load and return the image at the given index.

        The label is the breed name derived from the filename.

        Args:
            index: Zero-based sample index.

        Returns:
            A Sample with the loaded image, breed label, and path.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self._samples):
            raise IndexError(f"Index {index} out of range for dataset of size {len(self._samples)}")

        path = self._samples[index]
        image = Image.open(path).convert("RGB")
        label = _extract_breed_from_filename(path.stem)

        return image_sample(image=image, label=label, path=path)

    def _download(self) -> None:
        """Download and extract the Oxford-IIIT Pets image archive."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        archive_path = self._data_dir / _IMAGES_ARCHIVE
        url = f"{_BASE_URL}/{_IMAGES_ARCHIVE}"

        try:
            print(f"Downloading Oxford-IIIT Pets dataset from {url} ...")
            urllib.request.urlretrieve(url, archive_path)  # noqa: S310
        except Exception as exc:
            raise RuntimeError(f"Failed to download dataset from {url}") from exc

        try:
            print(f"Extracting {archive_path} ...")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=self._data_dir, filter="data")  # noqa: S202
        finally:
            archive_path.unlink(missing_ok=True)

        if not self._images_dir.exists():
            raise RuntimeError(
                f"Extraction completed but expected directory {self._images_dir} was not created."
            )


def _extract_breed_from_filename(stem: str) -> str:
    """Extract the breed name from an Oxford Pets filename stem.

    The convention is ``Breed_Name_123`` where trailing digits and the
    underscore before them are the image index.

    Args:
        stem: Filename without extension (e.g. ``Abyssinian_100``).

    Returns:
        Breed name with underscores preserved (e.g. ``Abyssinian``).
    """
    # Split from the right on underscore; the last segment is the numeric index
    parts = stem.rsplit("_", maxsplit=1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    # Fallback: return the full stem if pattern doesn't match
    return stem

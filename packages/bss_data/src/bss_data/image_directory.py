"""Dataset implementation for loading images from a local directory."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from bss_data.dataset import Sample, image_sample

#: File extensions recognized as images.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"})


class ImageDirectoryDataset:
    """Load images from a directory on disk.

    Scans the given root directory (optionally recursively) for image files
    and exposes them as indexable samples. Labels are derived from the
    immediate parent directory name of each image.

    Args:
        root: Path to the image directory.
        recursive: If True, scan subdirectories as well.
        extensions: Set of valid file extensions (with leading dot, lowercase).

    Raises:
        FileNotFoundError: If root does not exist.
        ValueError: If no image files are found.
    """

    def __init__(
        self,
        root: Path,
        *,
        recursive: bool = True,
        extensions: frozenset[str] = SUPPORTED_EXTENSIONS,
    ) -> None:
        if not root.exists():
            raise FileNotFoundError(f"Image directory not found: {root}")

        pattern = "**/*" if recursive else "*"
        self._samples: list[Path] = sorted(
            p for p in root.glob(pattern) if p.is_file() and p.suffix.lower() in extensions
        )

        if not self._samples:
            raise ValueError(f"No image files found in {root}")

        self._root = root

    @property
    def root(self) -> Path:
        """Root directory this dataset was created from."""
        return self._root

    def __len__(self) -> int:
        """Return the number of images found."""
        return len(self._samples)

    def __getitem__(self, index: int) -> Sample:
        """Load and return the image at the given index.

        The label is the name of the image's parent directory relative to root.
        If the image sits directly in root, the label is empty.

        Args:
            index: Zero-based sample index.

        Returns:
            A Sample with the loaded image, label, and path.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self._samples):
            raise IndexError(f"Index {index} out of range for dataset of size {len(self._samples)}")

        path = self._samples[index]
        image = Image.open(path).convert("RGB")

        # Derive label from parent dir name relative to root
        relative = path.parent.relative_to(self._root)
        label = str(relative) if relative != Path(".") else ""

        return image_sample(image=image, label=label, path=path)

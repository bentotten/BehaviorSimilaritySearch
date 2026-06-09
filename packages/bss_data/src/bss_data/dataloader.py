"""Dataloader for BehaviorSimilaritySearch."""

from pathlib import Path
from typing import TypedDict


class ImageSample(TypedDict):
    """A single loaded image sample."""

    filename: str
    data: bytes


#: Default path to the sample data directory.
DEFAULT_DATA_DIR = Path("data/sample")

#: Supported image file extensions.
SUPPORTED_EXTENSIONS: set[str] = {".jpeg", ".jpg", ".png"}


def load_data(data_path: Path = DEFAULT_DATA_DIR) -> list[ImageSample]:
    """Load image files from a directory into memory.

    Each image is returned as a dictionary with its filename and raw bytes.

    Args:
        data_path: Path to the directory containing image files.

    Returns:
        A list of ImageSamples

    Raises:
        FileNotFoundError: If data_path does not exist.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    samples: list[ImageSample] = []

    for file_path in sorted(data_path.iterdir()):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            samples.append(
                {
                    "filename": file_path.name,
                    "data": file_path.read_bytes(),
                }
            )

    return samples

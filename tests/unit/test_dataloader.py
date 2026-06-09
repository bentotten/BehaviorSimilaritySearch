"""Unit tests for bss_data.dataloader."""

from pathlib import Path

import pytest
from bss_data.dataloader import (
    ImageSample,
    load_data,
)

# ---------------------------------------------------------------------------
# load_data
# ---------------------------------------------------------------------------


def test_load_data_raises_file_not_found_for_missing_directory(tmp_path: Path) -> None:
    """load_data raises FileNotFoundError when the directory does not exist."""
    nonexistent = tmp_path / "nonexistent"

    with pytest.raises(FileNotFoundError, match="Data directory not found"):
        load_data(nonexistent)


def test_load_data_returns_empty_list_for_empty_directory(tmp_path: Path) -> None:
    """load_data returns an empty list when the directory has no files."""
    assert load_data(tmp_path) == []


def test_load_data_ignores_unsupported_extensions(tmp_path: Path) -> None:
    """load_data skips files that are not in SUPPORTED_EXTENSIONS."""
    (tmp_path / "readme.txt").write_text("not an image")
    (tmp_path / "data.csv").write_text("1,2,3")
    (tmp_path / "script.py").write_text("print('hi')")

    assert load_data(tmp_path) == []


def test_load_data_loads_supported_extensions(tmp_path: Path) -> None:
    """load_data loads files with .jpg, .jpeg, and .png extensions with correct data."""
    jpg_content = b"\xff\xd8\xff\xe0jpg-data"
    jpeg_content = b"\xff\xd8\xff\xe0jpeg-data"
    png_content = b"\x89PNG\r\n\x1a\npng-data"

    (tmp_path / "image.jpg").write_bytes(jpg_content)
    (tmp_path / "photo.jpeg").write_bytes(jpeg_content)
    (tmp_path / "graphic.png").write_bytes(png_content)

    results = load_data(tmp_path)

    assert len(results) == 3

    samples_by_filename = {sample["filename"]: sample["data"] for sample in results}
    assert samples_by_filename["image.jpg"] == jpg_content
    assert samples_by_filename["photo.jpeg"] == jpeg_content
    assert samples_by_filename["graphic.png"] == png_content


def test_load_data_is_case_insensitive_for_extensions(tmp_path: Path) -> None:
    """load_data matches extensions regardless of case."""
    content = b"fake-image-bytes"
    (tmp_path / "upper.JPG").write_bytes(content)
    (tmp_path / "mixed.Png").write_bytes(content)

    results = load_data(tmp_path)

    assert len(results) == 2


def test_load_data_returns_image_sample_typed_dicts(tmp_path: Path) -> None:
    """load_data returns dicts conforming to the ImageSample TypedDict shape."""
    (tmp_path / "a.png").write_bytes(b"png-bytes")

    results = load_data(tmp_path)

    sample: ImageSample = results[0]
    assert isinstance(sample["filename"], str)
    assert isinstance(sample["data"], bytes)


def test_load_data_returns_results_sorted_by_filename(tmp_path: Path) -> None:
    """load_data returns samples sorted alphabetically by filename."""
    (tmp_path / "c_image.png").write_bytes(b"c")
    (tmp_path / "a_image.png").write_bytes(b"a")
    (tmp_path / "b_image.png").write_bytes(b"b")

    results = load_data(tmp_path)

    filenames = [sample["filename"] for sample in results]
    assert filenames == ["a_image.png", "b_image.png", "c_image.png"]


def test_load_data_loads_only_images_from_mixed_directory(tmp_path: Path) -> None:
    """load_data picks up images and skips non-image files in a mixed directory."""
    (tmp_path / "photo.jpg").write_bytes(b"jpg-data")
    (tmp_path / "notes.txt").write_text("some notes")
    (tmp_path / "diagram.png").write_bytes(b"png-data")
    (tmp_path / "archive.zip").write_bytes(b"PK\x03\x04")

    results = load_data(tmp_path)

    assert len(results) == 2
    filenames = [sample["filename"] for sample in results]
    assert "photo.jpg" in filenames
    assert "diagram.png" in filenames

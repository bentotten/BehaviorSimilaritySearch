"""Unit tests for bss_data.dataloader."""

from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from bss_data.dataloader import (
    ImageSample,
    image_bytes_to_numpy,
    load_data,
)
from PIL import Image, UnidentifiedImageError

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


# ---------------------------------------------------------------------------
# image_bytes_to_numpy
# ---------------------------------------------------------------------------


def _encode_pil_image(image: Image.Image, image_format: str = "PNG") -> bytes:
    """Encode a PIL image to bytes using the requested image format."""
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def _make_rgb_png_bytes(
    width: int = 4,
    height: int = 3,
    color: tuple[int, int, int] = (255, 0, 0),
) -> bytes:
    """Return PNG bytes for a solid-color RGB image."""
    return _encode_pil_image(Image.new("RGB", (width, height), color=color))


def test_image_bytes_to_numpy_returns_empty_list_for_empty_input() -> None:
    """image_bytes_to_numpy returns an empty list when given no samples."""
    assert image_bytes_to_numpy([]) == []


def test_image_bytes_to_numpy_returns_one_array_per_sample() -> None:
    """image_bytes_to_numpy returns one numpy array per input sample."""
    samples: list[ImageSample] = [
        {"filename": "a.png", "data": _make_rgb_png_bytes()},
        {"filename": "b.png", "data": _make_rgb_png_bytes()},
        {"filename": "c.png", "data": _make_rgb_png_bytes()},
    ]

    arrays = image_bytes_to_numpy(samples)

    assert len(arrays) == 3
    assert all(isinstance(array, np.ndarray) for array in arrays)


def test_image_bytes_to_numpy_returns_uint8_rgb_arrays() -> None:
    """Decoded arrays are shape (H, W, 3) and dtype uint8."""
    width, height = 5, 4
    samples: list[ImageSample] = [
        {"filename": "a.png", "data": _make_rgb_png_bytes(width=width, height=height)}
    ]

    arrays = image_bytes_to_numpy(samples)

    assert arrays[0].dtype == np.uint8
    assert arrays[0].ndim == 3
    assert arrays[0].shape == (height, width, 3)


def test_image_bytes_to_numpy_preserves_pixel_values() -> None:
    """Decoded array contains the original solid color."""
    samples: list[ImageSample] = [
        {"filename": "red.png", "data": _make_rgb_png_bytes(2, 2, color=(255, 0, 0))}
    ]

    arrays = image_bytes_to_numpy(samples)

    expected = np.full((2, 2, 3), [255, 0, 0], dtype=np.uint8)
    np.testing.assert_array_equal(arrays[0], expected)


def test_image_bytes_to_numpy_converts_grayscale_to_rgb() -> None:
    """Single-channel images are converted to 3-channel RGB."""
    grayscale_bytes = _encode_pil_image(Image.new("L", (3, 3), color=128))
    samples: list[ImageSample] = [{"filename": "g.png", "data": grayscale_bytes}]

    arrays = image_bytes_to_numpy(samples)

    assert arrays[0].shape == (3, 3, 3)
    assert arrays[0].dtype == np.uint8


def test_image_bytes_to_numpy_converts_rgba_to_rgb() -> None:
    """RGBA images are converted to 3-channel RGB (alpha discarded)."""
    rgba_bytes = _encode_pil_image(Image.new("RGBA", (2, 2), color=(10, 20, 30, 128)))
    samples: list[ImageSample] = [{"filename": "rgba.png", "data": rgba_bytes}]

    arrays = image_bytes_to_numpy(samples)

    assert arrays[0].shape == (2, 2, 3)


def test_image_bytes_to_numpy_decodes_jpeg() -> None:
    """JPEG-encoded bytes are accepted alongside PNG."""
    jpeg_bytes = _encode_pil_image(Image.new("RGB", (4, 4), color=(0, 255, 0)), image_format="JPEG")
    samples: list[ImageSample] = [{"filename": "a.jpg", "data": jpeg_bytes}]

    arrays = image_bytes_to_numpy(samples)

    assert arrays[0].shape == (4, 4, 3)
    assert arrays[0].dtype == np.uint8


def test_image_bytes_to_numpy_preserves_input_order() -> None:
    """Output ordering matches the input sample ordering."""
    samples: list[ImageSample] = [
        {"filename": "a.png", "data": _make_rgb_png_bytes(2, 2, color=(10, 10, 10))},
        {"filename": "b.png", "data": _make_rgb_png_bytes(2, 2, color=(20, 20, 20))},
        {"filename": "c.png", "data": _make_rgb_png_bytes(2, 2, color=(30, 30, 30))},
    ]

    arrays = image_bytes_to_numpy(samples)

    assert arrays[0][0, 0].tolist() == [10, 10, 10]
    assert arrays[1][0, 0].tolist() == [20, 20, 20]
    assert arrays[2][0, 0].tolist() == [30, 30, 30]


def test_image_bytes_to_numpy_raises_on_undecodable_bytes() -> None:
    """Invalid image bytes propagate a PIL error rather than being silently ignored."""
    samples: list[ImageSample] = [{"filename": "broken.png", "data": b"not an image"}]

    with pytest.raises(UnidentifiedImageError):
        image_bytes_to_numpy(samples)

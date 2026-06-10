"""Integration tests — encoder package and its callers.

The CLIP backbone is replaced with a lightweight stand-in so these tests
exercise the real ClipEncoder, get_encoder factory, and dataloader code
paths without downloading model weights.
"""

from __future__ import annotations

import types
from io import BytesIO
from pathlib import Path

import bss_encoder.encoder as encoder_module
import numpy as np
import pytest
import torch
from bss_data.dataloader import image_bytes_to_numpy, load_data
from bss_encoder.clip_encoder import ClipEncoder
from bss_encoder.encoder import EncoderConfig, get_encoder
from PIL import Image
from pytest_mock import MockerFixture

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 8


class FakeClipModel:
    """Minimal stand-in for an open_clip model.

    Exposes the surface ClipEncoder needs without loading real weights:
      * .visual.output_dim
      * .to(device) / .eval() (returning self)
      * .encode_image(batch_tensor)
    """

    def __init__(self, embedding_dim: int = EMBEDDING_DIM) -> None:
        self.visual = types.SimpleNamespace(output_dim=embedding_dim)
        self._dim = embedding_dim

    def to(self, _device: torch.device) -> FakeClipModel:
        return self

    def eval(self) -> FakeClipModel:
        return self

    def encode_image(self, batch: torch.Tensor) -> torch.Tensor:
        rows = [
            torch.arange(self._dim, dtype=torch.float32) + (row_index + 1)
            for row_index in range(batch.shape[0])
        ]
        return torch.stack(rows, dim=0)


def _fake_preprocess(_image: object) -> torch.Tensor:
    return torch.zeros(3, 4, 4, dtype=torch.float32)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_encoder_singleton() -> None:
    """Reset the global encoder singleton before each test."""
    encoder_module.encoder_instance = None


@pytest.fixture()
def patched_open_clip(mocker: MockerFixture) -> None:
    """Replace open_clip.create_model_and_transforms with a fast stub."""
    mocker.patch(
        "bss_encoder.clip_encoder.open_clip.create_model_and_transforms",
        return_value=(FakeClipModel(), None, _fake_preprocess),
    )


@pytest.fixture()
def image_directory(tmp_path: Path) -> Path:
    """Create a directory with three solid-color PNG images on disk."""
    for index, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        image = Image.new("RGB", (4, 4), color=color)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        (tmp_path / f"sample_{index}.png").write_bytes(buffer.getvalue())
    return tmp_path


# ---------------------------------------------------------------------------
# Factory wiring
# ---------------------------------------------------------------------------


def test_get_encoder_returns_clip_encoder_for_clip_config(
    patched_open_clip: None,
) -> None:
    """get_encoder produces a real ClipEncoder when type='clip'."""
    encoder = get_encoder(EncoderConfig(type="clip", device="cpu"))

    assert isinstance(encoder, ClipEncoder)
    assert encoder.embedding_dim == EMBEDDING_DIM


def test_get_encoder_caches_instance_across_calls(
    patched_open_clip: None,
) -> None:
    """The singleton survives across modules and calls."""
    first = get_encoder(EncoderConfig(device="cpu"))
    second = get_encoder()

    assert first is second


# ---------------------------------------------------------------------------
# Cross-package: dataloader → encoder
# ---------------------------------------------------------------------------


def test_dataloader_to_encoder_pipeline_produces_embeddings(
    image_directory: Path, patched_open_clip: None
) -> None:
    """Loaded PNG bytes flow end-to-end through to a (N, dim) embedding matrix."""
    samples = load_data(image_directory)
    arrays = image_bytes_to_numpy(samples)

    encoder = get_encoder(EncoderConfig(device="cpu", normalize=False))
    embeddings = encoder.encode_images(arrays)

    assert embeddings.shape == (3, EMBEDDING_DIM)
    assert embeddings.dtype == np.float32


def test_pipeline_with_normalization_returns_unit_vectors(
    image_directory: Path, patched_open_clip: None
) -> None:
    """When normalize_embeddings is enabled each row has unit L2 norm."""
    samples = load_data(image_directory)
    arrays = image_bytes_to_numpy(samples)

    encoder = get_encoder(EncoderConfig(device="cpu", normalize=True))
    embeddings = encoder.encode_images(arrays)

    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, np.ones(len(arrays)), atol=1e-5)


def test_pipeline_video_encoding_returns_single_vector(
    image_directory: Path, patched_open_clip: None
) -> None:
    """Encoding loaded frames as a video yields a single (dim,) vector."""
    samples = load_data(image_directory)
    arrays = image_bytes_to_numpy(samples)

    encoder = get_encoder(EncoderConfig(device="cpu", normalize=False))
    embedding = encoder.encode_video(arrays)

    assert embedding.shape == (EMBEDDING_DIM,)
    assert embedding.dtype == np.float32


def test_pipeline_respects_small_batch_size(image_directory: Path, patched_open_clip: None) -> None:
    """A batch_size smaller than the input still produces one embedding per image."""
    samples = load_data(image_directory)
    arrays = image_bytes_to_numpy(samples)

    encoder = get_encoder(EncoderConfig(device="cpu", batch_size=1, normalize=False))
    embeddings = encoder.encode_images(arrays)

    assert embeddings.shape == (len(arrays), EMBEDDING_DIM)

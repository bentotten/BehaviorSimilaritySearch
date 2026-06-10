"""Unit tests for bss_encoder.clip_encoder.

The real CLIP backbone is replaced with a lightweight stand-in so these
tests run quickly and do not touch the network or download weights.
"""

from __future__ import annotations

import types
from collections.abc import Iterator

import numpy as np
import pytest
import torch
from bss_encoder.clip_encoder import ClipEncoder, ClipEncoderConfig
from pytest_mock import MockerFixture

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 8


class FakeClipModel:
    """Minimal stand-in for an open_clip model.

    Implements only the surface that ClipEncoder relies on:
      * .visual.output_dim
      * .to(device) and .eval() (returning self for chaining)
      * .encode_image(batch_tensor)

    encode_image returns deterministic, distinct vectors per row so that
    tests can verify ordering, batching, and pooling behavior.
    """

    def __init__(self, embedding_dim: int = EMBEDDING_DIM) -> None:
        self.visual = types.SimpleNamespace(output_dim=embedding_dim)
        self._dim = embedding_dim
        self.encode_calls: list[int] = []

    def to(self, device: torch.device) -> FakeClipModel:
        self._device = device
        return self

    def eval(self) -> FakeClipModel:
        return self

    def encode_image(self, batch: torch.Tensor) -> torch.Tensor:
        batch_size = batch.shape[0]
        self.encode_calls.append(batch_size)
        # Each row is [k+1, k+2, ..., k+dim] for row index k. Distinct, non-zero.
        rows = [
            torch.arange(self._dim, dtype=torch.float32) + (row_index + 1)
            for row_index in range(batch_size)
        ]
        return torch.stack(rows, dim=0)


def _fake_preprocess(_image: object) -> torch.Tensor:
    """Return a fixed-shape tensor regardless of input image."""
    return torch.zeros(3, 4, 4, dtype=torch.float32)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_clip_model() -> FakeClipModel:
    """A FakeClipModel reused inside a single test."""
    return FakeClipModel(embedding_dim=EMBEDDING_DIM)


@pytest.fixture()
def patched_open_clip(
    mocker: MockerFixture, fake_clip_model: FakeClipModel
) -> Iterator[FakeClipModel]:
    """Replace open_clip.create_model_and_transforms with a fast stub."""
    mocker.patch(
        "bss_encoder.clip_encoder.open_clip.create_model_and_transforms",
        return_value=(fake_clip_model, None, _fake_preprocess),
    )
    yield fake_clip_model


def _make_image(height: int = 4, width: int = 4, channels: int = 3) -> np.ndarray:
    """Return a deterministic uint8 image of the requested shape."""
    return np.full((height, width, channels), fill_value=128, dtype=np.uint8)


# ---------------------------------------------------------------------------
# ClipEncoderConfig
# ---------------------------------------------------------------------------


def test_clip_encoder_config_has_documented_defaults() -> None:
    """ClipEncoderConfig defaults match the values declared in the dataclass."""
    config = ClipEncoderConfig()
    assert config.model_name == "ViT-B-32"
    assert config.pretrained == "laion2b_s34b_b79k"
    assert config.device == "cuda"
    assert config.batch_size == 16
    assert config.normalize_embeddings is True


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_init_loads_clip_model_with_configured_name_and_weights(
    mocker: MockerFixture, fake_clip_model: FakeClipModel
) -> None:
    """ClipEncoder forwards model_name/pretrained to open_clip on init."""
    mock_create = mocker.patch(
        "bss_encoder.clip_encoder.open_clip.create_model_and_transforms",
        return_value=(fake_clip_model, None, _fake_preprocess),
    )

    config = ClipEncoderConfig(
        model_name="ViT-B-32",
        pretrained="weights",
        device="cpu",
    )
    ClipEncoder(config)

    mock_create.assert_called_once_with("ViT-B-32", pretrained="weights")


def test_init_uses_default_config_when_none_passed(
    mocker: MockerFixture, fake_clip_model: FakeClipModel
) -> None:
    """Constructing ClipEncoder() with no config falls back to ClipEncoderConfig()."""
    mocker.patch(
        "bss_encoder.clip_encoder.open_clip.create_model_and_transforms",
        return_value=(fake_clip_model, None, _fake_preprocess),
    )

    encoder = ClipEncoder()

    assert encoder.config == ClipEncoderConfig()


def test_init_resolves_cuda_to_cpu_when_unavailable(
    mocker: MockerFixture, fake_clip_model: FakeClipModel
) -> None:
    """A 'cuda' request falls back to CPU when CUDA is not available."""
    mocker.patch("bss_encoder.clip_encoder.torch.cuda.is_available", return_value=False)
    mocker.patch(
        "bss_encoder.clip_encoder.open_clip.create_model_and_transforms",
        return_value=(fake_clip_model, None, _fake_preprocess),
    )

    encoder = ClipEncoder(ClipEncoderConfig(device="cuda"))

    assert encoder.device == torch.device("cpu")


def test_init_uses_cuda_device_when_available(
    mocker: MockerFixture, fake_clip_model: FakeClipModel
) -> None:
    """A 'cuda' request uses the cuda device when available."""
    mocker.patch("bss_encoder.clip_encoder.torch.cuda.is_available", return_value=True)
    mocker.patch(
        "bss_encoder.clip_encoder.open_clip.create_model_and_transforms",
        return_value=(fake_clip_model, None, _fake_preprocess),
    )

    encoder = ClipEncoder(ClipEncoderConfig(device="cuda"))

    assert encoder.device == torch.device("cuda")


# ---------------------------------------------------------------------------
# embedding_dim
# ---------------------------------------------------------------------------


def test_embedding_dim_returns_models_visual_output_dim(
    patched_open_clip: FakeClipModel,
) -> None:
    """embedding_dim is read from model.visual.output_dim."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu"))
    assert encoder.embedding_dim == EMBEDDING_DIM


# ---------------------------------------------------------------------------
# encode_image
# ---------------------------------------------------------------------------


def test_encode_image_returns_one_dimensional_vector(
    patched_open_clip: FakeClipModel,
) -> None:
    """encode_image returns a 1D vector with embedding_dim entries."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu"))

    embedding = encoder.encode_image(_make_image())

    assert embedding.shape == (EMBEDDING_DIM,)
    assert embedding.dtype == np.float32


# ---------------------------------------------------------------------------
# encode_images
# ---------------------------------------------------------------------------


def test_encode_images_raises_on_empty_input(patched_open_clip: FakeClipModel) -> None:
    """encode_images raises ValueError when given no images."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu"))

    with pytest.raises(ValueError, match="at least one image"):
        encoder.encode_images([])


def test_encode_images_returns_two_dimensional_array(
    patched_open_clip: FakeClipModel,
) -> None:
    """encode_images returns a (N, embedding_dim) float32 array."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu", normalize_embeddings=False))

    embeddings = encoder.encode_images([_make_image() for _ in range(3)])

    assert embeddings.shape == (3, EMBEDDING_DIM)
    assert embeddings.dtype == np.float32


def test_encode_images_respects_batch_size(patched_open_clip: FakeClipModel) -> None:
    """encode_images splits the input into batches of at most batch_size."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu", batch_size=2, normalize_embeddings=False))

    encoder.encode_images([_make_image() for _ in range(5)])

    # 5 images with batch_size=2 -> batches of 2, 2, 1.
    assert patched_open_clip.encode_calls == [2, 2, 1]


def test_encode_images_normalizes_when_configured(
    patched_open_clip: FakeClipModel,
) -> None:
    """Each row has unit L2 norm when normalize_embeddings=True."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu", normalize_embeddings=True))

    embeddings = encoder.encode_images([_make_image() for _ in range(3)])

    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, np.ones(3), atol=1e-5)


def test_encode_images_does_not_normalize_when_disabled(
    patched_open_clip: FakeClipModel,
) -> None:
    """When normalize_embeddings is False the raw model output is returned."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu", normalize_embeddings=False))

    embeddings = encoder.encode_images([_make_image()])

    # Fake model returns [1, 2, ..., EMBEDDING_DIM] for the first row.
    expected = np.arange(EMBEDDING_DIM, dtype=np.float32) + 1.0
    np.testing.assert_array_equal(embeddings[0], expected)


# ---------------------------------------------------------------------------
# encode_video
# ---------------------------------------------------------------------------


def test_encode_video_raises_on_empty_input(patched_open_clip: FakeClipModel) -> None:
    """encode_video raises ValueError when given no frames."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu"))

    with pytest.raises(ValueError, match="at least one frame"):
        encoder.encode_video([])


def test_encode_video_returns_one_dimensional_vector(
    patched_open_clip: FakeClipModel,
) -> None:
    """encode_video returns a 1D vector with embedding_dim entries."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu", normalize_embeddings=False))

    embedding = encoder.encode_video([_make_image() for _ in range(3)])

    assert embedding.shape == (EMBEDDING_DIM,)
    assert embedding.dtype == np.float32


def test_encode_video_is_mean_of_frame_embeddings(
    patched_open_clip: FakeClipModel,
) -> None:
    """Without normalization, the video embedding equals the mean over frames."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu", normalize_embeddings=False))
    frames = [_make_image() for _ in range(4)]

    expected = encoder.encode_images(frames).mean(axis=0)
    actual = encoder.encode_video(frames)

    np.testing.assert_allclose(actual, expected, rtol=1e-5)


def test_encode_video_normalizes_when_configured(
    patched_open_clip: FakeClipModel,
) -> None:
    """When normalization is enabled the video embedding has unit L2 norm."""
    encoder = ClipEncoder(ClipEncoderConfig(device="cpu", normalize_embeddings=True))

    embedding = encoder.encode_video([_make_image() for _ in range(3)])

    np.testing.assert_allclose(np.linalg.norm(embedding), 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# _numpy_to_pil_image
# ---------------------------------------------------------------------------


def test_numpy_to_pil_image_accepts_three_channel_uint8() -> None:
    """A standard (H, W, 3) uint8 array is converted to an RGB image."""
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    pil_image = ClipEncoder._numpy_to_pil_image(image)

    assert pil_image.mode == "RGB"
    assert pil_image.size == (4, 4)


def test_numpy_to_pil_image_converts_grayscale_to_rgb() -> None:
    """A single-channel array is widened to RGB."""
    image = np.zeros((4, 4, 1), dtype=np.uint8)
    pil_image = ClipEncoder._numpy_to_pil_image(image)

    assert pil_image.mode == "RGB"
    assert pil_image.size == (4, 4)


def test_numpy_to_pil_image_converts_rgba_to_rgb() -> None:
    """A 4-channel array is converted to RGB (alpha discarded)."""
    image = np.zeros((4, 4, 4), dtype=np.uint8)
    pil_image = ClipEncoder._numpy_to_pil_image(image)

    assert pil_image.mode == "RGB"


def test_numpy_to_pil_image_clips_and_casts_non_uint8() -> None:
    """Non-uint8 arrays are clipped to [0, 255] and cast to uint8."""
    image = np.array([[[300.0, -10.0, 128.0]]], dtype=np.float32)

    pil_image = ClipEncoder._numpy_to_pil_image(image)

    pixel = np.array(pil_image)[0, 0]
    assert pixel.tolist() == [255, 0, 128]


def test_numpy_to_pil_image_rejects_two_dimensional_array() -> None:
    """Arrays without an explicit channel dimension are rejected."""
    image = np.zeros((4, 4), dtype=np.uint8)

    with pytest.raises(ValueError, match="height, width, channels"):
        ClipEncoder._numpy_to_pil_image(image)


def test_numpy_to_pil_image_rejects_unsupported_channel_count() -> None:
    """Channel counts other than 1, 3, or 4 are rejected."""
    image = np.zeros((4, 4, 2), dtype=np.uint8)

    with pytest.raises(ValueError, match="1, 3, or 4 channels"):
        ClipEncoder._numpy_to_pil_image(image)


# ---------------------------------------------------------------------------
# _normalize_numpy_vector
# ---------------------------------------------------------------------------


def test_normalize_numpy_vector_returns_unit_vector() -> None:
    """A non-zero vector is scaled to unit L2 norm."""
    vector = np.array([3.0, 4.0], dtype=np.float32)

    normalized = ClipEncoder._normalize_numpy_vector(vector)

    np.testing.assert_allclose(np.linalg.norm(normalized), 1.0, atol=1e-6)
    np.testing.assert_allclose(normalized, np.array([0.6, 0.8]), atol=1e-6)


def test_normalize_numpy_vector_raises_on_zero_vector() -> None:
    """A zero vector cannot be normalized."""
    with pytest.raises(ValueError, match="zero-vector"):
        ClipEncoder._normalize_numpy_vector(np.zeros(4, dtype=np.float32))


# ---------------------------------------------------------------------------
# _resolve_device
# ---------------------------------------------------------------------------


def test_resolve_device_returns_explicit_device_when_not_cuda() -> None:
    """Non-cuda device strings are returned as-is."""
    assert ClipEncoder._resolve_device("cpu") == torch.device("cpu")


def test_resolve_device_falls_back_to_cpu_when_cuda_unavailable(
    mocker: MockerFixture,
) -> None:
    """A 'cuda' request falls back to CPU when CUDA is not available."""
    mocker.patch("bss_encoder.clip_encoder.torch.cuda.is_available", return_value=False)

    assert ClipEncoder._resolve_device("cuda") == torch.device("cpu")


def test_resolve_device_uses_cuda_when_available(mocker: MockerFixture) -> None:
    """A 'cuda' request stays on cuda when CUDA is available."""
    mocker.patch("bss_encoder.clip_encoder.torch.cuda.is_available", return_value=True)

    assert ClipEncoder._resolve_device("cuda") == torch.device("cuda")

"""Unit tests for bss_encoder.encoder."""

from collections.abc import Sequence
from dataclasses import FrozenInstanceError

import bss_encoder.encoder as encoder_module
import numpy as np
import pytest
from bss_encoder.encoder import Encoder, EncoderConfig, _encoder_factory, get_encoder
from pytest_mock import MockerFixture

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """Reset the module-level encoder singleton before each test."""
    encoder_module.encoder_instance = None


# ---------------------------------------------------------------------------
# EncoderConfig
# ---------------------------------------------------------------------------


def test_encoder_config_has_documented_defaults() -> None:
    """EncoderConfig defaults match the values declared in the dataclass."""
    config = EncoderConfig()
    assert config.type == "clip"
    assert config.model_name == "ViT-B-32"
    assert config.pretrained == "laion2b_s34b_b79k"
    assert config.device == "cuda"
    assert config.batch_size == 16
    assert config.normalize is True


def test_encoder_config_is_frozen() -> None:
    """EncoderConfig is a frozen dataclass and cannot be mutated after creation."""
    config = EncoderConfig()
    with pytest.raises(FrozenInstanceError):
        config.type = "other"  # type: ignore[misc]


def test_encoder_config_supports_custom_values() -> None:
    """Custom EncoderConfig values are preserved on the instance."""
    config = EncoderConfig(
        type="clip",
        model_name="custom",
        pretrained="weights",
        device="cpu",
        batch_size=4,
        normalize=False,
    )
    assert config.model_name == "custom"
    assert config.pretrained == "weights"
    assert config.device == "cpu"
    assert config.batch_size == 4
    assert config.normalize is False


# ---------------------------------------------------------------------------
# Encoder ABC
# ---------------------------------------------------------------------------


def test_encoder_cannot_be_instantiated_directly() -> None:
    """The Encoder ABC raises TypeError when instantiated."""
    with pytest.raises(TypeError):
        Encoder()  # type: ignore[abstract]


def test_encoder_subclass_must_implement_all_abstract_methods() -> None:
    """A subclass missing any abstract method also cannot be instantiated."""

    class IncompleteEncoder(Encoder):
        @property
        def embedding_dim(self) -> int:
            return 1

        # Missing encode_image / encode_images / encode_video.

    with pytest.raises(TypeError):
        IncompleteEncoder()  # type: ignore[abstract]


def test_encoder_concrete_subclass_can_be_instantiated() -> None:
    """A subclass implementing every abstract method can be instantiated."""

    class CompleteEncoder(Encoder):
        @property
        def embedding_dim(self) -> int:
            return 4

        def encode_image(self, image: np.ndarray) -> np.ndarray:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        def encode_images(self, images: Sequence[np.ndarray]) -> np.ndarray:
            return np.zeros((len(images), self.embedding_dim), dtype=np.float32)

        def encode_video(self, frames: Sequence[np.ndarray]) -> np.ndarray:
            return np.zeros(self.embedding_dim, dtype=np.float32)

    assert CompleteEncoder().embedding_dim == 4


# ---------------------------------------------------------------------------
# _encoder_factory
# ---------------------------------------------------------------------------


def test_encoder_factory_creates_clip_encoder(mocker: MockerFixture) -> None:
    """The factory creates a ClipEncoder instance for type='clip'."""
    fake_encoder = mocker.MagicMock(spec=Encoder)
    mock_clip_encoder = mocker.patch(
        "bss_encoder.clip_encoder.ClipEncoder", return_value=fake_encoder
    )

    result = _encoder_factory(EncoderConfig(type="clip"))

    assert result is fake_encoder
    mock_clip_encoder.assert_called_once()


def test_encoder_factory_passes_translated_config(mocker: MockerFixture) -> None:
    """The factory translates EncoderConfig fields into a ClipEncoderConfig."""
    mock_clip_encoder = mocker.patch("bss_encoder.clip_encoder.ClipEncoder")
    mock_clip_config_class = mocker.patch("bss_encoder.clip_encoder.ClipEncoderConfig")

    config = EncoderConfig(
        type="clip",
        model_name="custom-model",
        pretrained="custom-weights",
        device="cpu",
        batch_size=4,
        normalize=False,
    )
    _encoder_factory(config)

    mock_clip_config_class.assert_called_once_with(
        model_name="custom-model",
        pretrained="custom-weights",
        device="cpu",
        batch_size=4,
        normalize_embeddings=False,
    )
    mock_clip_encoder.assert_called_once_with(mock_clip_config_class.return_value)


def test_encoder_factory_raises_for_unknown_type() -> None:
    """The factory raises ValueError for an unknown encoder kind."""
    with pytest.raises(ValueError, match="Unknown encoder kind"):
        _encoder_factory(EncoderConfig(type="not-a-real-encoder"))


# ---------------------------------------------------------------------------
# get_encoder singleton
# ---------------------------------------------------------------------------


def test_get_encoder_initializes_with_default_config(mocker: MockerFixture) -> None:
    """The first call to get_encoder() initializes the singleton with defaults."""
    fake_encoder = mocker.MagicMock(spec=Encoder)
    mock_factory = mocker.patch("bss_encoder.encoder._encoder_factory", return_value=fake_encoder)

    result = get_encoder()

    assert result is fake_encoder
    mock_factory.assert_called_once_with(EncoderConfig())


def test_get_encoder_initializes_with_provided_config(mocker: MockerFixture) -> None:
    """The first call to get_encoder() uses the supplied config."""
    fake_encoder = mocker.MagicMock(spec=Encoder)
    mock_factory = mocker.patch("bss_encoder.encoder._encoder_factory", return_value=fake_encoder)
    config = EncoderConfig(device="cpu", batch_size=2)

    get_encoder(config)

    mock_factory.assert_called_once_with(config)


def test_get_encoder_returns_cached_singleton(mocker: MockerFixture) -> None:
    """Subsequent calls return the cached instance without rebuilding it."""
    fake_encoder = mocker.MagicMock(spec=Encoder)
    mock_factory = mocker.patch("bss_encoder.encoder._encoder_factory", return_value=fake_encoder)

    first = get_encoder()
    second = get_encoder(EncoderConfig(device="cpu"))

    assert first is second
    assert mock_factory.call_count == 1

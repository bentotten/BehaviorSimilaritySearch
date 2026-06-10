"""Interface and factory for encoder backends in BehaviorSimilaritySearch."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EncoderConfig:
    """Configuration for an encoder instance."""

    type: str = "clip"
    model_name: str = "ViT-B-32"
    pretrained: str = "laion2b_s34b_b79k"
    device: str = "cuda"
    batch_size: int = 16
    normalize: bool = True


class Encoder(ABC):
    """Base interface for image/video embedding models."""

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Return output vector dimension."""

    @abstractmethod
    def encode_image(self, image: np.ndarray) -> np.ndarray:
        """Encode one image into a 1-D embedding vector."""

    @abstractmethod
    def encode_images(self, images: Sequence[np.ndarray]) -> np.ndarray:
        """Encode multiple images into a 2-D array of embeddings."""

    @abstractmethod
    def encode_video(self, frames: Sequence[np.ndarray]) -> np.ndarray:
        """Encode a short video clip into a 1-D embedding vector."""


#: Global singleton
encoder_instance: Encoder | None = None


def get_encoder(config: EncoderConfig | None = None) -> Encoder:
    """Initialize the global encoder singleton.

    Creates the encoder from config and caches it. Subsequent calls
    return the cached instance (config is ignored after first init).

    Args:
        config: Encoder configuration. Uses defaults if not provided.

    Returns:
        The initialized Encoder instance.
    """
    global encoder_instance

    if encoder_instance is None:
        config = config or EncoderConfig()
        encoder_instance = _encoder_factory(config)

    return encoder_instance


def _encoder_factory(config: EncoderConfig) -> Encoder:
    """Factory function to create an encoder from config.

    Args:
        config: Encoder configuration specifying the backend kind.

    Returns:
        A concrete Encoder instance.

    Raises:
        ValueError: If the encoder kind is not recognized.
    """
    if config.type == "clip":
        from bss_encoder.clip_encoder import ClipEncoder, ClipEncoderConfig

        # TODO: Read from file instead (see: https://github.com/bentotten/BehaviorSimilaritySearch/issues/34)
        clip_config = ClipEncoderConfig(
            model_name=config.model_name,
            pretrained=config.pretrained,
            device=config.device,
            batch_size=config.batch_size,
            normalize_embeddings=config.normalize,
        )
        return ClipEncoder(clip_config)

    raise ValueError(f"Unknown encoder kind: {config.type!r}. Supported: 'clip'.")

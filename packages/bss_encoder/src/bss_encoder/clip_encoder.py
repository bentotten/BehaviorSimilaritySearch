"""CLIP-backed encoder implementation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import open_clip
import torch
from PIL import Image

from bss_encoder.encoder import Encoder


@dataclass(frozen=True)
class ClipEncoderConfig:
    """Configuration for a CLIP image/video encoder."""

    model_name: str = "ViT-B-32"
    pretrained: str = "laion2b_s34b_b79k"
    device: str = "cuda"
    batch_size: int = 16
    normalize_embeddings: bool = True


class ClipEncoder(Encoder):
    """Encode images and short video clips using CLIP.

    Video encoding is initially implemented as:
        frame embeddings -> mean pooling -> optional normalization

    This keeps the public interface stable while allowing a future video
    autoencoder or Triton-backed model to replace this implementation.
    """

    def __init__(self, config: ClipEncoderConfig | None = None) -> None:
        self.config = config or ClipEncoderConfig()
        self.device = self._resolve_device(self.config.device)

        model, _, preprocess = open_clip.create_model_and_transforms(
            self.config.model_name,
            pretrained=self.config.pretrained,
        )

        self.model = model.to(self.device)
        self.model.eval()
        self.preprocess = preprocess

    @property
    def embedding_dim(self) -> int:
        """Return the CLIP image embedding dimension."""
        return int(self.model.visual.output_dim)

    def encode_image(self, image: np.ndarray) -> np.ndarray:
        """Encode one image into a 1D embedding vector."""
        embeddings = self.encode_images([image])
        return embeddings[0]  # type: ignore[no-any-return]

    def encode_images(self, images: Sequence[np.ndarray]) -> np.ndarray:
        """Encode multiple images into a 2D array of embeddings."""
        if not images:
            raise ValueError("images must contain at least one image")

        batches: list[np.ndarray] = []

        for start_index in range(0, len(images), self.config.batch_size):
            image_batch = images[start_index : start_index + self.config.batch_size]
            input_tensor = self._prepare_image_batch(image_batch)

            with torch.inference_mode():
                embeddings = self.model.encode_image(input_tensor)

            if self.config.normalize_embeddings:
                embeddings = torch.nn.functional.normalize(embeddings, dim=-1)

            batches.append(embeddings.cpu().numpy().astype(np.float32))

        return np.concatenate(batches, axis=0)

    def encode_video(self, frames: Sequence[np.ndarray]) -> np.ndarray:
        """Encode a video clip by mean-pooling frame embeddings."""
        if not frames:
            raise ValueError("frames must contain at least one frame")

        frame_embeddings = self.encode_images(frames)
        video_embedding = np.mean(frame_embeddings, axis=0)

        if self.config.normalize_embeddings:
            video_embedding = self._normalize_numpy_vector(video_embedding)

        return video_embedding.astype(np.float32)  # type: ignore[no-any-return]

    def _prepare_image_batch(self, images: Sequence[np.ndarray]) -> torch.Tensor:
        pil_images = [self._numpy_to_pil_image(image) for image in images]
        tensors = [self.preprocess(image) for image in pil_images]
        return torch.stack(tensors, dim=0).to(self.device)

    @staticmethod
    def _numpy_to_pil_image(image: np.ndarray) -> Image.Image:
        if image.ndim != 3:
            raise ValueError(
                f"Expected image with shape [height, width, channels], got {image.shape}"
            )

        if image.shape[2] not in {1, 3, 4}:
            raise ValueError(f"Expected image with 1, 3, or 4 channels, got {image.shape[2]}")

        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)

        if image.shape[2] == 1:
            image = image[:, :, 0]
            return Image.fromarray(image, mode="L").convert("RGB")

        if image.shape[2] == 4:
            return Image.fromarray(image, mode="RGBA").convert("RGB")

        return Image.fromarray(image, mode="RGB")

    @staticmethod
    def _normalize_numpy_vector(vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)

        if norm == 0:
            raise ValueError("Cannot normalize zero-vector embedding")

        return vector / norm  # type: ignore[no-any-return]

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        if device == "cuda" and not torch.cuda.is_available():
            return torch.device("cpu")

        return torch.device(device)

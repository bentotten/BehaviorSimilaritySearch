"""Dataset implementation for loading video clips from a directory of frame sequences.

Supports directory layouts where each video clip is stored as a folder of
ordered frame images (common for datasets like HMDB51, UCF101 when pre-extracted).

Expected structure:
    root/
        action_label/
            clip_001/
                frame_0001.jpg
                frame_0002.jpg
                ...
            clip_002/
                frame_0001.jpg
                ...
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from bss_data.dataset import Sample, video_sample

#: File extensions recognized as frame images.
FRAME_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".bmp"})


class VideoDirectoryDataset:
    """Load video clips from a directory of frame sequences.

    Each subdirectory under a label directory is treated as a single video clip.
    Frames within a clip directory are sorted alphabetically and loaded in order.

    Directory layout::

        root/
            label_a/
                clip_001/
                    frame_001.jpg
                    frame_002.jpg
                clip_002/
                    ...
            label_b/
                ...

    Args:
        root: Path to the root directory containing label subdirectories.
        extensions: Set of valid frame file extensions (with leading dot, lowercase).
        min_frames: Minimum number of frames required for a clip to be included.

    Raises:
        FileNotFoundError: If root does not exist.
        ValueError: If no valid video clips are found.
    """

    def __init__(
        self,
        root: Path,
        *,
        extensions: frozenset[str] = FRAME_EXTENSIONS,
        min_frames: int = 1,
    ) -> None:
        if not root.exists():
            raise FileNotFoundError(f"Video directory not found: {root}")

        self._root = root
        self._extensions = extensions
        self._min_frames = min_frames

        # Discover clips: root / label / clip_dir
        self._clips: list[tuple[str, Path]] = []
        for label_dir in sorted(root.iterdir()):
            if not label_dir.is_dir():
                continue
            label = label_dir.name
            for clip_dir in sorted(label_dir.iterdir()):
                if not clip_dir.is_dir():
                    continue
                frame_count = sum(
                    1 for f in clip_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions
                )
                if frame_count >= min_frames:
                    self._clips.append((label, clip_dir))

        if not self._clips:
            raise ValueError(f"No valid video clips found in {root}")

    @property
    def root(self) -> Path:
        """Root directory this dataset was created from."""
        return self._root

    def __len__(self) -> int:
        """Return the number of video clips found."""
        return len(self._clips)

    def __getitem__(self, index: int) -> Sample:
        """Load and return all frames for the clip at the given index.

        Args:
            index: Zero-based clip index.

        Returns:
            A Sample with media_type=VIDEO, frames loaded in sorted order.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= len(self._clips):
            raise IndexError(f"Index {index} out of range for dataset of size {len(self._clips)}")

        label, clip_dir = self._clips[index]
        frame_paths = sorted(
            p for p in clip_dir.iterdir() if p.is_file() and p.suffix.lower() in self._extensions
        )
        frames = [Image.open(p).convert("RGB") for p in frame_paths]

        return video_sample(frames=frames, label=label, path=clip_dir)

"""Unit tests for bss_data.video_directory."""

from pathlib import Path

import pytest
from PIL import Image

from bss_data.dataset import Dataset, MediaType, Sample
from bss_data.video_directory import VideoDirectoryDataset

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def video_dir(tmp_path: Path) -> Path:
    """Create a temp directory mimicking a video clip dataset.

    Structure:
        root/
            running/
                clip_001/  (3 frames)
                clip_002/  (2 frames)
            jumping/
                clip_001/  (4 frames)
    """
    for label, clips in [("running", [3, 2]), ("jumping", [4])]:
        label_dir = tmp_path / label
        label_dir.mkdir()
        for clip_idx, num_frames in enumerate(clips):
            clip_dir = label_dir / f"clip_{clip_idx:03d}"
            clip_dir.mkdir()
            for frame_idx in range(num_frames):
                img = Image.new("RGB", (8, 8), color=(frame_idx * 30, 0, 0))
                img.save(clip_dir / f"frame_{frame_idx:04d}.jpg")

    return tmp_path


@pytest.fixture()
def single_clip_dir(tmp_path: Path) -> Path:
    """Create a directory with a single clip."""
    label_dir = tmp_path / "action"
    label_dir.mkdir()
    clip_dir = label_dir / "clip_000"
    clip_dir.mkdir()
    for i in range(5):
        img = Image.new("RGB", (4, 4))
        img.save(clip_dir / f"frame_{i:04d}.png")
    return tmp_path


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


def test_raises_if_root_does_not_exist() -> None:
    """Constructor raises FileNotFoundError for nonexistent directory."""
    with pytest.raises(FileNotFoundError, match="Video directory not found"):
        VideoDirectoryDataset(Path("/tmp/nonexistent_video_dir_12345"))


def test_raises_if_no_clips_found(tmp_path: Path) -> None:
    """Constructor raises ValueError when no valid clips exist."""
    # Create a label dir with no clip subdirs
    (tmp_path / "empty_label").mkdir()
    with pytest.raises(ValueError, match="No valid video clips found"):
        VideoDirectoryDataset(tmp_path)


def test_raises_if_clips_have_no_frames(tmp_path: Path) -> None:
    """Constructor raises ValueError when clip dirs have no frame images."""
    label_dir = tmp_path / "action"
    label_dir.mkdir()
    clip_dir = label_dir / "clip_000"
    clip_dir.mkdir()
    (clip_dir / "notes.txt").write_text("not a frame")

    with pytest.raises(ValueError, match="No valid video clips found"):
        VideoDirectoryDataset(tmp_path)


def test_loads_clips_from_structure(video_dir: Path) -> None:
    """Dataset discovers all valid clips."""
    ds = VideoDirectoryDataset(video_dir)
    assert len(ds) == 3  # 2 running clips + 1 jumping clip


def test_min_frames_filter(video_dir: Path) -> None:
    """Clips with fewer than min_frames are excluded."""
    ds = VideoDirectoryDataset(video_dir, min_frames=3)
    # Only clips with >= 3 frames: running/clip_001 (3), jumping/clip_001 (4)
    assert len(ds) == 2


def test_custom_extensions(tmp_path: Path) -> None:
    """Dataset respects custom frame extensions filter."""
    label_dir = tmp_path / "walk"
    label_dir.mkdir()
    clip_dir = label_dir / "clip_000"
    clip_dir.mkdir()

    img = Image.new("RGB", (4, 4))
    img.save(clip_dir / "frame_0.png")
    img.save(clip_dir / "frame_1.jpg")

    # Only include .png
    ds = VideoDirectoryDataset(tmp_path, extensions=frozenset({".png"}))
    sample = ds[0]
    assert len(sample.frames) == 1


# ---------------------------------------------------------------------------
# __getitem__
# ---------------------------------------------------------------------------


def test_getitem_returns_video_sample(video_dir: Path) -> None:
    """__getitem__ returns a Sample with media_type=VIDEO and frames."""
    ds = VideoDirectoryDataset(video_dir)
    sample = ds[0]

    assert isinstance(sample, Sample)
    assert sample.media_type == MediaType.VIDEO
    assert sample.image is None
    assert len(sample.frames) > 0
    assert all(isinstance(f, Image.Image) for f in sample.frames)
    assert all(f.mode == "RGB" for f in sample.frames)


def test_getitem_frames_are_ordered(single_clip_dir: Path) -> None:
    """Frames within a clip are loaded in sorted filename order."""
    ds = VideoDirectoryDataset(single_clip_dir)
    sample = ds[0]
    assert len(sample.frames) == 5


def test_getitem_label_from_parent_dir(video_dir: Path) -> None:
    """Labels are derived from the label directory name."""
    ds = VideoDirectoryDataset(video_dir)
    labels = {ds[i].label for i in range(len(ds))}
    assert "running" in labels
    assert "jumping" in labels


def test_getitem_path_is_clip_directory(video_dir: Path) -> None:
    """Sample path points to the clip directory."""
    ds = VideoDirectoryDataset(video_dir)
    sample = ds[0]
    assert sample.path is not None
    assert sample.path.is_dir()


def test_getitem_index_out_of_range(video_dir: Path) -> None:
    """__getitem__ raises IndexError for invalid indices."""
    ds = VideoDirectoryDataset(video_dir)
    with pytest.raises(IndexError):
        ds[100]
    with pytest.raises(IndexError):
        ds[-1]


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_conforms_to_dataset_protocol(video_dir: Path) -> None:
    """VideoDirectoryDataset satisfies the Dataset protocol."""
    ds = VideoDirectoryDataset(video_dir)
    assert isinstance(ds, Dataset)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_root_property(video_dir: Path) -> None:
    """root property returns the directory passed at construction."""
    ds = VideoDirectoryDataset(video_dir)
    assert ds.root == video_dir

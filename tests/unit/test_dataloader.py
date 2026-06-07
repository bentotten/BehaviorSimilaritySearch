"""Unit tests for bss_data.dataloader."""

from __future__ import annotations

import pytest
from PIL import Image

from bss_data.dataloader import DataLoader
from bss_data.dataset import Sample, image_sample

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeDataset:
    """Minimal dataset for testing the DataLoader."""

    def __init__(self, size: int) -> None:
        self._samples = [
            image_sample(image=Image.new("RGB", (4, 4)), label=f"label_{i}") for i in range(size)
        ]

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, index: int) -> Sample:
        return self._samples[index]


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


def test_raises_for_invalid_batch_size() -> None:
    """DataLoader raises ValueError for batch_size < 1."""
    ds = FakeDataset(10)
    with pytest.raises(ValueError, match="batch_size must be >= 1"):
        DataLoader(ds, batch_size=0)
    with pytest.raises(ValueError, match="batch_size must be >= 1"):
        DataLoader(ds, batch_size=-5)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_batch_size_property() -> None:
    """batch_size property reflects the value passed at construction."""
    ds = FakeDataset(10)
    loader = DataLoader(ds, batch_size=4)
    assert loader.batch_size == 4


def test_dataset_property() -> None:
    """dataset property returns the underlying dataset."""
    ds = FakeDataset(10)
    loader = DataLoader(ds, batch_size=4)
    assert loader.dataset is ds


# ---------------------------------------------------------------------------
# __len__
# ---------------------------------------------------------------------------


def test_len_evenly_divisible() -> None:
    """__len__ when dataset size is evenly divisible by batch_size."""
    ds = FakeDataset(10)
    loader = DataLoader(ds, batch_size=5)
    assert len(loader) == 2


def test_len_with_remainder() -> None:
    """__len__ rounds up when there is a remainder batch."""
    ds = FakeDataset(7)
    loader = DataLoader(ds, batch_size=3)
    assert len(loader) == 3  # 3 + 3 + 1


def test_len_drop_last() -> None:
    """__len__ excludes incomplete batch when drop_last=True."""
    ds = FakeDataset(7)
    loader = DataLoader(ds, batch_size=3, drop_last=True)
    assert len(loader) == 2  # 3 + 3, drops the 1


def test_len_empty_dataset() -> None:
    """__len__ is 0 for an empty dataset."""
    ds = FakeDataset(0)
    loader = DataLoader(ds, batch_size=4)
    assert len(loader) == 0


# ---------------------------------------------------------------------------
# __iter__
# ---------------------------------------------------------------------------


def test_iter_yields_correct_batch_sizes() -> None:
    """Iteration yields full batches and a smaller final batch."""
    ds = FakeDataset(7)
    loader = DataLoader(ds, batch_size=3)
    batches = list(loader)

    assert len(batches) == 3
    assert len(batches[0]) == 3
    assert len(batches[1]) == 3
    assert len(batches[2]) == 1


def test_iter_drop_last_discards_remainder() -> None:
    """Iteration with drop_last=True omits the incomplete final batch."""
    ds = FakeDataset(7)
    loader = DataLoader(ds, batch_size=3, drop_last=True)
    batches = list(loader)

    assert len(batches) == 2
    assert all(len(b) == 3 for b in batches)


def test_iter_all_samples_present_without_shuffle() -> None:
    """Without shuffle, all samples are yielded in order."""
    ds = FakeDataset(5)
    loader = DataLoader(ds, batch_size=2)
    all_samples = [s for batch in loader for s in batch]

    assert len(all_samples) == 5
    assert [s.label for s in all_samples] == [f"label_{i}" for i in range(5)]


def test_iter_shuffle_produces_all_samples() -> None:
    """With shuffle=True, all samples are still present (just reordered)."""
    ds = FakeDataset(10)
    loader = DataLoader(ds, batch_size=3, shuffle=True)
    all_samples = [s for batch in loader for s in batch]

    assert len(all_samples) == 10
    labels = sorted(s.label for s in all_samples)
    assert labels == sorted(f"label_{i}" for i in range(10))


def test_iter_evenly_divisible() -> None:
    """Iteration with evenly divisible dataset yields only full batches."""
    ds = FakeDataset(6)
    loader = DataLoader(ds, batch_size=3)
    batches = list(loader)

    assert len(batches) == 2
    assert all(len(b) == 3 for b in batches)


def test_iter_empty_dataset_yields_nothing() -> None:
    """Iteration over empty dataset yields no batches."""
    ds = FakeDataset(0)
    loader = DataLoader(ds, batch_size=4)
    batches = list(loader)

    assert batches == []


def test_iter_batch_contains_sample_instances() -> None:
    """Each item in a batch is a Sample instance."""
    ds = FakeDataset(3)
    loader = DataLoader(ds, batch_size=2)
    for batch in loader:
        for item in batch:
            assert isinstance(item, Sample)


def test_multiple_iterations_are_independent() -> None:
    """DataLoader can be iterated multiple times."""
    ds = FakeDataset(4)
    loader = DataLoader(ds, batch_size=2)

    first_pass = list(loader)
    second_pass = list(loader)

    assert len(first_pass) == len(second_pass) == 2

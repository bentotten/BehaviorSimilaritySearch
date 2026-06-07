"""DataLoader for batching and iterating over datasets."""

from __future__ import annotations

import random
from collections.abc import Iterator

from bss_data.dataset import Dataset, Sample


class DataLoader:
    """Iterable data loader that yields batches of samples from a dataset.

    Provides batching, optional shuffling, and drop-last semantics suitable
    for training loops. Designed to be compatible with any object satisfying
    the Dataset protocol.

    Args:
        dataset: Any object implementing the Dataset protocol (__len__ + __getitem__).
        batch_size: Number of samples per batch.
        shuffle: Whether to randomize sample order each iteration.
        drop_last: If True, drop the final batch when it is smaller than batch_size.

    Raises:
        ValueError: If batch_size is less than 1.
    """

    def __init__(
        self,
        dataset: Dataset,
        *,
        batch_size: int = 32,
        shuffle: bool = False,
        drop_last: bool = False,
    ) -> None:
        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")

        self._dataset = dataset
        self._batch_size = batch_size
        self._shuffle = shuffle
        self._drop_last = drop_last

    @property
    def batch_size(self) -> int:
        """Number of samples per batch."""
        return self._batch_size

    @property
    def dataset(self) -> Dataset:
        """The underlying dataset."""
        return self._dataset

    def __len__(self) -> int:
        """Return the number of batches per full iteration.

        When drop_last is True, incomplete final batches are excluded from the count.
        """
        n = len(self._dataset)
        if self._drop_last:
            return n // self._batch_size
        return (n + self._batch_size - 1) // self._batch_size

    def __iter__(self) -> Iterator[list[Sample]]:
        """Yield batches of samples.

        Each batch is a list of Sample objects. The final batch may be
        smaller than batch_size unless drop_last is True.
        """
        indices = list(range(len(self._dataset)))

        if self._shuffle:
            random.shuffle(indices)

        batch: list[Sample] = []
        for idx in indices:
            batch.append(self._dataset[idx])
            if len(batch) == self._batch_size:
                yield batch
                batch = []

        if batch and not self._drop_last:
            yield batch

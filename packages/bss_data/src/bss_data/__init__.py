"""bss_data — dataset loading and data pipeline utilities for BehaviorSimilaritySearch."""

from importlib.metadata import version

from bss_data.dataloader import DataLoader
from bss_data.dataset import Dataset, MediaType, Sample, image_sample, video_sample
from bss_data.image_directory import ImageDirectoryDataset
from bss_data.oxford_pets import OxfordPetsDataset
from bss_data.video_directory import VideoDirectoryDataset

__all__ = [
    "DataLoader",
    "Dataset",
    "ImageDirectoryDataset",
    "MediaType",
    "OxfordPetsDataset",
    "Sample",
    "VideoDirectoryDataset",
    "image_sample",
    "video_sample",
]

__version__ = version("behavior-similarity-search-data")

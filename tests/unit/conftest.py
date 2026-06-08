"""Shared functionality and fixtures for unit tests."""

import pytest


@pytest.fixture()
def fake_profile_config() -> dict[str, object]:
    """Return the hardcoded profile config dict that create_profiles currently produces."""
    return {
        "index_name": "fake_index",
        "index_config": {
            "data_structure": "HASH",
            "prefixes": ["frame:"],
        },
        "vector_field": {
            "field_name": "embedding",
            "algorithm": "HNSW",
            "vector_type": "FLOAT32",
            "dim": 512,
            "distance_metric": "COSINE",
        },
    }

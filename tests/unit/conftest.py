"""Shared functionality and fixtures for unit tests."""

import pytest
from pytest_mock import MockerFixture

from bss_valkey.valkey_client import ValkeyClient


@pytest.fixture()
def mock_client(mocker: MockerFixture) -> ValkeyClient:
    """Return a mock ValkeyClient with a mock underlying client."""
    client = mocker.MagicMock(spec=ValkeyClient)
    client.client.execute_command = mocker.MagicMock()
    return client  # type: ignore[no-any-return]  # mock satisfies ValkeyClient at runtime


@pytest.fixture()
def fake_profile_config() -> dict[str, object]:
    """Create fake profile configurations."""
    return {
        "index_name": "profile_1",
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


@pytest.fixture()
def fake_env_config() -> dict[str, str]:
    """Create fake environment/connection configurations for the search backend."""
    return {
        "VALKEY_HOST": "10.0.0.1",
        "VALKEY_PORT": "6380",
        "VALKEY_PING_MAX_RETRIES": "99",
        "VALKEY_PING_RETRY_DELAY": "999",
    }

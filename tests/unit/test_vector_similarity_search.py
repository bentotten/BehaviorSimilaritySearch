"""Unit tests for bss_valkey.vector_similarity_search."""

import pytest
from pytest_mock import MockerFixture

from bss_valkey.valkey_client import ValkeyClient
from bss_valkey.vector_similarity_search import (
    IndexConfig,
    VectorFieldConfig,
    build_create_index_command,
    create_index,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_client(mocker: MockerFixture) -> ValkeyClient:
    """Return a mock ValkeyClient with a mock underlying client."""
    client = mocker.MagicMock(spec=ValkeyClient)
    client.client.execute_command = mocker.MagicMock()
    return client  # type: ignore [no-any-return] # Mock causing problems


# ---------------------------------------------------------------------------
# Dataclass defaults
# ---------------------------------------------------------------------------


def test_vector_field_config_hnsw_params_defaults_to_none() -> None:
    """VectorFieldConfig.hnsw_params defaults to None."""
    config = VectorFieldConfig("embedding", "HNSW", "FLOAT32", 512, "COSINE")
    assert config.hnsw_params is None


def test_index_config_skip_initial_scan_defaults_to_false() -> None:
    """IndexConfig.skip_initial_scan defaults to False."""
    config = IndexConfig("HASH", ["frame:"])
    assert config.skip_initial_scan is False


# ---------------------------------------------------------------------------
# create_index
# ---------------------------------------------------------------------------


def test_build_create_index_command_minimal(fake_profile_config: dict[str, object]) -> None:
    """build_create_index_command produces correct command with minimal config."""
    cmd = build_create_index_command(fake_profile_config)

    index_config = fake_profile_config["index_config"]
    vector_field = fake_profile_config["vector_field"]
    assert isinstance(index_config, dict)
    assert isinstance(vector_field, dict)

    assert cmd[0] == "FT.CREATE"
    assert cmd[1] == fake_profile_config["index_name"]
    assert cmd[2] == "ON"
    assert cmd[3] == index_config["data_structure"]
    assert cmd[4] == "PREFIX"
    assert cmd[5] == len(index_config["prefixes"])
    assert cmd[6] == index_config["prefixes"][0]
    assert "SKIPINITIALSCAN" not in cmd
    assert "SCHEMA" in cmd
    schema_idx = cmd.index("SCHEMA")
    assert cmd[schema_idx + 1] == vector_field["field_name"]
    assert cmd[schema_idx + 2] == "VECTOR"
    assert cmd[schema_idx + 3] == vector_field["algorithm"]
    # attr_count = TYPE, FLOAT32, DIM, 512, DISTANCE_METRIC, COSINE = 6
    assert cmd[schema_idx + 4] == 6
    assert cmd[schema_idx + 5] == "TYPE"
    assert cmd[schema_idx + 6] == vector_field["vector_type"]
    assert cmd[schema_idx + 7] == "DIM"
    assert cmd[schema_idx + 8] == vector_field["dim"]
    assert cmd[schema_idx + 9] == "DISTANCE_METRIC"
    assert cmd[schema_idx + 10] == vector_field["distance_metric"]


def test_build_create_index_command_includes_skip_initial_scan() -> None:
    """build_create_index_command includes SKIPINITIALSCAN when configured."""
    config: dict[str, object] = {
        "index_name": "idx",
        "index_config": {
            "data_structure": "HASH",
            "prefixes": ["doc:"],
            "skip_initial_scan": True,
        },
        "vector_field": {
            "field_name": "vec",
            "algorithm": "FLAT",
            "vector_type": "FLOAT32",
            "dim": 256,
            "distance_metric": "L2",
        },
    }
    cmd = build_create_index_command(config)
    assert "SKIPINITIALSCAN" in cmd


def test_build_create_index_command_multiple_prefixes() -> None:
    """build_create_index_command handles multiple prefixes."""
    config: dict[str, object] = {
        "index_name": "multi_idx",
        "index_config": {
            "data_structure": "JSON",
            "prefixes": ["frame:", "clip:"],
        },
        "vector_field": {
            "field_name": "embedding",
            "algorithm": "HNSW",
            "vector_type": "FLOAT32",
            "dim": 768,
            "distance_metric": "IP",
        },
    }
    cmd = build_create_index_command(config)
    prefix_idx = cmd.index("PREFIX")
    assert cmd[prefix_idx + 1] == 2
    assert cmd[prefix_idx + 2] == "frame:"
    assert cmd[prefix_idx + 3] == "clip:"


# ---------------------------------------------------------------------------
# build_create_index_command — HNSW params
# ---------------------------------------------------------------------------


def test_build_create_index_command_includes_all_hnsw_params() -> None:
    """build_create_index_command includes all HNSW tuning params when set."""
    config: dict[str, object] = {
        "index_name": "idx",
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
            "hnsw_params": {
                "initial_cap": 10000,
                "m": 16,
                "ef_construction": 200,
                "ef_runtime": 10,
            },
        },
    }
    cmd = build_create_index_command(config)
    assert "INITIAL_CAP" in cmd
    assert 10000 in cmd
    assert "M" in cmd
    assert 16 in cmd
    assert "EF_CONSTRUCTION" in cmd
    assert 200 in cmd
    assert "EF_RUNTIME" in cmd
    assert 10 in cmd


def test_build_create_index_command_includes_partial_hnsw_params() -> None:
    """build_create_index_command only includes HNSW params that are set."""
    config: dict[str, object] = {
        "index_name": "idx",
        "index_config": {
            "data_structure": "HASH",
            "prefixes": ["item:"],
        },
        "vector_field": {
            "field_name": "vec",
            "algorithm": "HNSW",
            "vector_type": "FLOAT32",
            "dim": 128,
            "distance_metric": "L2",
            "hnsw_params": {
                "m": 32,
                "ef_runtime": 50,
            },
        },
    }
    cmd = build_create_index_command(config)
    assert "M" in cmd
    assert 32 in cmd
    assert "EF_RUNTIME" in cmd
    assert 50 in cmd
    assert "INITIAL_CAP" not in cmd
    assert "EF_CONSTRUCTION" not in cmd


def test_build_create_index_command_hnsw_params_attr_count_is_correct() -> None:
    """attr_count accounts for HNSW params in addition to base vector attributes."""
    config: dict[str, object] = {
        "index_name": "idx",
        "index_config": {
            "data_structure": "HASH",
            "prefixes": ["v:"],
        },
        "vector_field": {
            "field_name": "vec",
            "algorithm": "HNSW",
            "vector_type": "FLOAT32",
            "dim": 64,
            "distance_metric": "COSINE",
            "hnsw_params": {
                "initial_cap": 5000,
                "m": 8,
            },
        },
    }
    cmd = build_create_index_command(config)
    schema_idx = cmd.index("SCHEMA")
    # attr_count = TYPE, FLOAT32, DIM, 64, DISTANCE_METRIC, COSINE, INITIAL_CAP, 5000, M, 8 = 10
    assert cmd[schema_idx + 4] == 10


# ---------------------------------------------------------------------------
# build_create_index_command — FLAT algorithm
# ---------------------------------------------------------------------------


def test_build_create_index_command_flat_algorithm_no_hnsw() -> None:
    """build_create_index_command works with FLAT algorithm and no HNSW params."""
    config: dict[str, object] = {
        "index_name": "flat_idx",
        "index_config": {
            "data_structure": "HASH",
            "prefixes": ["doc:"],
        },
        "vector_field": {
            "field_name": "vec",
            "algorithm": "FLAT",
            "vector_type": "FLOAT32",
            "dim": 256,
            "distance_metric": "L2",
        },
    }
    cmd = build_create_index_command(config)
    assert "FLAT" in cmd
    assert "INITIAL_CAP" not in cmd
    assert "M" not in cmd
    assert "EF_CONSTRUCTION" not in cmd
    assert "EF_RUNTIME" not in cmd


# ---------------------------------------------------------------------------
# create_index — executes command
# ---------------------------------------------------------------------------


def test_create_index_calls_execute_command(
    mock_client: ValkeyClient, fake_profile_config: dict[str, object]
) -> None:
    """create_index calls execute_command with the built command."""
    create_index(mock_client, fake_profile_config)

    mock_client.client.execute_command.assert_called_once()  # type: ignore[attr-defined]  # mock
    cmd = mock_client.client.execute_command.call_args[0]  # type: ignore[attr-defined]  # mock
    assert cmd[0] == "FT.CREATE"
    assert cmd[1] == fake_profile_config["index_name"]

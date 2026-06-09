"""Valkey Vector Similarity Search module for BehaviorSimilaritySearch."""

from __future__ import annotations

from dataclasses import dataclass, fields

from bss_valkey.valkey_client import ValkeyClient


@dataclass
class HNSWParams:
    """Tunable parameters for the HNSW algorithm.

    See: https://github.com/valkey-io/valkey-search/blob/main/QUICK_START.md#working-with-vector-search
    """

    #: Pre-allocated capacity for vectors
    initial_cap: int | None = None
    #: Max outgoing edges per graph node
    m: int | None = None
    #: Search width during index construction
    ef_construction: int | None = None
    #: Search width at query time
    ef_runtime: int | None = None


@dataclass
class VectorFieldConfig:
    """Configuration for a vector field in a Valkey index.

    See: https://github.com/valkey-io/valkey-search/blob/main/QUICK_START.md#working-with-vector-search
    """

    #: Field name in the hash/JSON sample
    field_name: str
    #: Index algorithm (e.g. FLAT, HNSW)
    algorithm: str
    #: Element data type (e.g. FLOAT32)
    vector_type: str
    #: Dimensionality of vectors stored in this field (e.g. 512)
    dim: int
    #: Distance metric (e.g. L2, IP, COSINE)
    distance_metric: str
    #: Optional HNSW tuning parameters (only relevant for HNSW algorithm)
    hnsw_params: HNSWParams | None = None


@dataclass
class IndexConfig:
    """Top-level index configuration.

    See: https://github.com/valkey-io/valkey-search/blob/main/QUICK_START.md#working-with-vector-search
    """

    #: Data structure type (e.g. HASH, JSON)
    data_structure: str
    #: Key prefixes to index
    prefixes: list[str]
    #: Whether to skip indexing existing keys
    skip_initial_scan: bool = False


def build_create_index_command(index_config_data: dict[str, object]) -> list[str | int]:
    """Build an FT.CREATE command from raw config data (e.g. parsed from YAML).

    Args:
        index_config_data: A dictionary containing index_name, index_config,
            and vector_field keys as read from a YAML profile config.

    Returns:
        The command tokens to pass to execute_command.
    """
    index_name = str(index_config_data["index_name"])

    # Hydrate index config
    raw_index = index_config_data["index_config"]
    assert isinstance(raw_index, dict)
    index_config = IndexConfig(
        data_structure=str(raw_index["data_structure"]),
        prefixes=list(raw_index["prefixes"]),
        skip_initial_scan=bool(raw_index.get("skip_initial_scan", False)),
    )

    # Hydrate vector field config
    raw_vector = index_config_data["vector_field"]
    assert isinstance(raw_vector, dict)
    hnsw_params: HNSWParams | None = None
    if "hnsw_params" in raw_vector and raw_vector["hnsw_params"] is not None:
        raw_hnsw = raw_vector["hnsw_params"]
        hnsw_params = HNSWParams(**raw_hnsw)

    vector_field = VectorFieldConfig(
        field_name=str(raw_vector["field_name"]),
        algorithm=str(raw_vector["algorithm"]),
        vector_type=str(raw_vector["vector_type"]),
        dim=int(raw_vector["dim"]),
        distance_metric=str(raw_vector["distance_metric"]),
        hnsw_params=hnsw_params,
    )

    # Build command
    cmd: list[str | int] = [
        "FT.CREATE",
        index_name,
        "ON",
        index_config.data_structure,
        "PREFIX",
        len(index_config.prefixes),
        *index_config.prefixes,
    ]
    if index_config.skip_initial_scan:
        cmd.append("SKIPINITIALSCAN")

    vector_attributes: list[str | int] = [
        "TYPE",
        vector_field.vector_type,
        "DIM",
        vector_field.dim,
        "DISTANCE_METRIC",
        vector_field.distance_metric,
    ]

    if vector_field.hnsw_params is not None:
        for field in fields(vector_field.hnsw_params):
            value = getattr(vector_field.hnsw_params, field.name)
            if value is not None:
                vector_attributes.extend([field.name.upper(), value])

    cmd.extend(
        [
            "SCHEMA",
            vector_field.field_name,
            "VECTOR",
            vector_field.algorithm,
            len(vector_attributes),
            *vector_attributes,
        ]
    )

    return cmd


def create_index(client: ValkeyClient, index_config_data: dict[str, object]) -> None:
    """Create a vector similarity search index in Valkey.

    Args:
        client: The ValkeyClient instance.
        index_config_data: Raw config dict for a single index.
    """
    cmd = build_create_index_command(index_config_data)
    client.execute_command(*cmd)


def store_vectors() -> None:
    # Stub
    pass

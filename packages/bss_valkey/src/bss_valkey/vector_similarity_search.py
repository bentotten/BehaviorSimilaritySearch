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

    #: Field name in the hash/JSON document
    field_name: str
    #: Index algorithm (e.g. FLAT, HNSW)
    algorithm: str
    #: Element data type (e.g. FLOAT32)
    vector_type: str
    #: Number of dimensions
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


def create_index(
    client: ValkeyClient,
    index_name: str,
    index_config: IndexConfig,
    vector_field: VectorFieldConfig,
) -> None:
    """Create a vector similarity search index in Valkey.

    Args:
        client: The ValkeyClient instance.
        index_name: Name of the index to create.
        index_config: Index-level configuration (e.g. data structure, prefixes, scan behavior).
        vector_field: Vector field schema including algorithm, dimensions, and tuning parameters.
    """
    # Build initial section of command string
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

    # Build vector-specific parameters
    vector_attributes: list[str | int] = [
        "TYPE",
        vector_field.vector_type,
        "DIM",
        vector_field.dim,
        "DISTANCE_METRIC",
        vector_field.distance_metric,
    ]

    # If HNSW params are present, add them here
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

    client.client.execute_command(*cmd)  # type: ignore[no-untyped-call]


def store_vectors() -> None:
    # Stub
    pass

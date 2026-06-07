"""Fake Valkey client for use in tests."""

import valkey as valkey

from bss_valkey.valkey_client import (
    DEFAULT_VALKEY_HOST,
    DEFAULT_VALKEY_PORT,
)


class FakeValkey:
    """Fake Valkey engine.

    Supports basic Valkey operations for use in tests
    without requiring a running Valkey instance.
    """

    def __init__(self) -> None:
        pass

    def ping(self) -> bool:
        """Simulate a successful PING response.

        Returns:
            bool: Always True.
        """
        return True

    def get_connection_kwargs(self) -> dict[str, str | int]:
        """Return simulated connection kwargs.

        Returns:
            dict: Host and port as the valkey library would return them.
        """
        return {"host": DEFAULT_VALKEY_HOST, "port": DEFAULT_VALKEY_PORT}


class FailingFakeValkey(FakeValkey):
    """FakeValkey variant that always has problems.

    Simulates a Valkey instance that is unreachable or misbehaving.
    """

    def ping(self) -> bool:
        """Raise ConnectionError unconditionally.

        Raises:
            valkey.exceptions.ConnectionError: Always.
        """
        raise valkey.exceptions.ConnectionError("simulated failure")

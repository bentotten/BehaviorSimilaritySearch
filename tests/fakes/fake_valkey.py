"""Fake Valkey client for use in tests."""

import valkey as valkey


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


class FailingFakeValkey(FakeValkey):
    """FakeValkey variant that always raises ConnectionError on ping.

    Use this to simulate a Valkey instance that is unreachable.
    """

    def ping(self) -> bool:
        """Raise ConnectionError unconditionally.

        Raises:
            valkey.exceptions.ConnectionError: Always.
        """
        raise valkey.exceptions.ConnectionError("simulated failure")

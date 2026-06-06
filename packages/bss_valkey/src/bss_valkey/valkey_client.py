"""Valkey client utilities for BehaviorSimilaritySearch."""

from __future__ import annotations

import time
from typing import TypedDict

import valkey

#: Default maximum number of ping attempts before raising a connection error.
DEFAULT_MAX_PING_RETRIES: int = 5
#: Default seconds to wait between ping attempts.
DEFAULT_PING_RETRY_DELAY: int = 2

valkey_client: ValkeyClient | None = None


class ValkeyKwargs(TypedDict, total=False):
    """Optional keyword arguments for constructing a Valkey connection."""

    #: Valkey host/ip
    host: str
    #: Valkey port
    port: int


def get_client(host: str | None = None, port: int | None = None) -> ValkeyClient:
    """Return the singleton Valkey client, initialising it if necessary.

    Args:
        host: Optional hostname used when initializing the client.
        port: Optional port used when initializing the client.

    Returns:
        ValkeyClient: The singleton client instance.

    """
    global valkey_client

    if valkey_client is None:
        valkey_client = ValkeyClient(host=host, port=port)

    return valkey_client


class ValkeyClient:
    """Valkey client wrapper. Use get_client() to obtain the singleton instance."""

    #: Valkey client handle
    _client: valkey.Valkey

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        """Initialise the underlying Valkey connection.

        Falls back to the valkey library defaults if host or port are not provided.

        Args:
            host: Optional Valkey server hostname or IP address.
            port: Optional Valkey server port.
        """
        kwargs: ValkeyKwargs = {}
        if host is not None:
            kwargs["host"] = host
        if port is not None:
            kwargs["port"] = port

        self._client = valkey.Valkey(**kwargs)

    @property
    def client(self) -> valkey.Valkey:
        """Return the underlying Valkey client."""
        return self._client

    def ping(
        self,
        max_retries: int = DEFAULT_MAX_PING_RETRIES,
        retry_delay: int = DEFAULT_PING_RETRY_DELAY,
    ) -> None:
        """Ping the Valkey server, retrying on failure.

        Args:
            max_retries: Maximum number of attempts before raising.
            retry_delay: Seconds to wait between attempts.

        Raises:
            ConnectionError: If the server does not respond after all retries.
        """
        for attempt in range(1, max_retries + 1):
            try:
                if self._client.ping():
                    return
            except valkey.exceptions.ConnectionError:
                pass
            print(f"Attempt {attempt}/{max_retries} failed. Retrying in {retry_delay}s ...")
            time.sleep(retry_delay)
        raise ConnectionError(f"Could not connect to Valkey after {max_retries} attempts.")

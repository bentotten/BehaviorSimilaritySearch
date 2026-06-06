"""Configuration loading utilities for BehaviorSimilaritySearch."""

from pathlib import Path

from dotenv import dotenv_values


def load_config(config: Path) -> dict[str, str]:
    """Load configurations from file.

    Args:
        config: Path to the configuration file.

    Returns:
        dict[str, str]: Key/value pairs parsed from the config file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
    """
    if not config.exists():
        raise FileNotFoundError(f"Config file not found: {config}")

    match config.suffix.lower():
        case ".env":
            return {k: v for k, v in dotenv_values(config).items() if v}
        case _:
            raise ValueError(f"Unsupported config file extension '{config.suffix}'. Expected .env")

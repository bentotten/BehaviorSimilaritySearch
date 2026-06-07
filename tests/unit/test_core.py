"""Unit tests for bss_core."""

from pathlib import Path

import pytest

from bss_core import __version__
from bss_core.config import load_config

# ---------------------------------------------------------------------------
# Package smoke tests
# ---------------------------------------------------------------------------


def test_version_defined() -> None:
    """__version__ is a non-empty string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


def test_load_config_nonexistent_file_raises() -> None:
    """load_config raises error for a nonexistent file."""
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(Path("/tmp/does_not_exist.env"))


def test_load_config_unsupported_extension_raises(tmp_path: Path) -> None:
    """load_config raises error for unsupported file extensions."""
    bad_file = tmp_path / "config.xyz"
    bad_file.write_text("[section]\nfoo = bar\n")
    with pytest.raises(ValueError, match="Unsupported config file extension"):
        load_config(bad_file)


def test_load_config_reads_env_file_happy_path(tmp_path: Path) -> None:
    """load_config parses a .env file into a dict."""
    env_file = tmp_path / "test.env"
    env_file.write_text("FOO=bar\nBAZ=123\n")
    assert load_config(env_file) == {"FOO": "bar", "BAZ": "123"}


def test_load_config_ignores_blank_values(tmp_path: Path) -> None:
    """load_config excludes keys with no value."""
    env_file = tmp_path / "test.env"
    env_file.write_text("PRESENT=yes\nEMPTY=\n")
    result = load_config(env_file)
    assert "PRESENT" in result
    assert "EMPTY" not in result

"""Unit tests for behavior_core."""

import behavior_core
from behavior_core import __version__
from behavior_core.main import run


def test_package_importable() -> None:
    """Test that behavior_core is importable."""
    assert behavior_core is not None


def test_version_defined() -> None:
    """Test that __version__ is a non-empty string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_run_importable() -> None:
    """Test that run() is importable and callable."""
    assert callable(run)

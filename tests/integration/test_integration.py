"""Integration tests — cross-package interactions."""

from behavior_cli.cli import main
from behavior_core.main import run


def test_core_and_cli_importable() -> None:
    """Test that both packages can be imported together."""
    assert callable(run)
    assert callable(main)

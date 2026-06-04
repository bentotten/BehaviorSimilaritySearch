"""Entry point for behavior_core."""

from behavior_core import __version__


def run() -> None:
    """Run the application.

    Prints the current version of the package to stdout.
    """
    print(f"BehaviorSimilaritySearch v{__version__}")


if __name__ == "__main__":
    run()

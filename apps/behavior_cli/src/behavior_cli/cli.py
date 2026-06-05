"""Command-line interface for BehaviorSimilaritySearch."""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="behavior-similarity-search",
        description="BehaviorSimilaritySearch.",
    )
    return parser


def main() -> None:
    """Entry point for the command-line interface.

    Parses command-line arguments and dispatches to the appropriate handler.
    """
    _parser = build_parser()  # noqa: F841
    print("Hello World")


if __name__ == "__main__":
    main()

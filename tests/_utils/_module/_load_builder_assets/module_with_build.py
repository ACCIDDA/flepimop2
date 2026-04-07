"""A test module with an existing build function."""

from typing import Any


def build(config: dict[str, Any]) -> dict[str, Any]:
    """An existing build function.

    Args:
        config: Configuration dictionary.

    Returns:
        Configuration with additional metadata.
    """
    return {**config, "from": "original_build"}

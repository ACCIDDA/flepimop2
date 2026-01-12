"""Common CLI options and arguments for flepimop2 commands."""

__all__ = []

import pathlib
from collections.abc import Callable
from typing import Any, Final, TypeVar

import click

AnyCallable = Callable[..., Any]
FC = TypeVar("FC", bound="AnyCallable | click.Command")

# Dictionary of common Click options and arguments
# These can be requested by command classes to maintain consistency
COMMON_OPTIONS: Final = {
    "config": click.argument(
        "config",
        type=click.Path(
            exists=True, dir_okay=False, readable=True, path_type=pathlib.Path
        ),
    ),
    "dry_run": click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Should this command be run using dry run?",
    ),
    "out_config": click.option(
        "-o",
        "--out-config",
        type=click.Path(
            exists=False, dir_okay=False, writable=True, path_type=pathlib.Path
        ),
        default=None,
        help="Path to write the resolved configuration to.",
    ),
    "path": click.argument(
        "path",
        type=click.Path(
            exists=False, file_okay=False, writable=True, path_type=pathlib.Path
        ),
        default=None,
    ),
    "target": click.option(
        "-t",
        "--target",
        default=None,
        help="The target to use for this command.",
    ),
    "verbosity": click.option(
        "-v",
        "--verbosity",
        count=True,
        default=0,
        help="The verbosity level to use for this command.",
    ),
}


def get_option(name: str) -> Callable[[FC], FC]:
    """
    Get a common option or argument by name.

    Args:
        name: The name of the option/argument to retrieve.

    Returns:
        The Click option or argument decorator.

    Raises:
        KeyError: If the option name is not found.
    """
    if (opt := COMMON_OPTIONS.get(name)) is None:
        msg = (
            f"Unknown option '{name}'. "
            f"Available options: {', '.join(COMMON_OPTIONS.keys())}"
        )
        raise KeyError(msg)
    return opt

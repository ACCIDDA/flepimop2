# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Common CLI options and arguments for flepimop2 commands."""

__all__ = []

from collections.abc import Callable
from pathlib import Path
from typing import Any, Final, TypeVar, cast

import click

AnyCallable = Callable[..., Any]
FC = TypeVar("FC", bound="AnyCallable | click.Command")
CommonOptionDecorator = Callable[[AnyCallable], AnyCallable]
CommonOptionEntry = tuple[CommonOptionDecorator, str | None]
_DEFAULT_CONFIG_SEARCH_ORDER: Final[tuple[Path, ...]] = (
    Path("config.yaml"),
    Path("config.yml"),
    Path("configuration.yaml"),
    Path("configuration.yml"),
    Path("configs/config.yaml"),
    Path("configs/config.yml"),
    Path("configs/configuration.yaml"),
    Path("configs/configuration.yml"),
)


def _resolve_config_argument(
    value: Path | None,
    *,
    cwd: Path | None = None,
) -> Path:
    r"""
    Resolve a config argument, falling back to a default search order.

    If `value` is provided, it is returned unchanged. Otherwise, the current
    working directory is searched for the first matching default config file.

    Args:
        value: The explicit config path given on the command line, if any.
        cwd: The directory to search when `value` is `None`.

    Returns:
        The explicit config path, or the first matching default config path.

    Raises:
        FileNotFoundError: If `value` is `None` and no default config file exists.

    Examples:
        >>> from pathlib import Path
        >>> _resolve_config_argument(Path("example.yaml"))
        PosixPath('example.yaml')
        >>> _ = Path("configuration.yml").write_text("x: 1\\n")
        >>> _resolve_config_argument(None).name
        'configuration.yml'
        >>> _ = Path("configuration.yml").unlink()
    """
    if value is not None:
        return value
    search_root = Path.cwd() if cwd is None else cwd
    for relative_path in _DEFAULT_CONFIG_SEARCH_ORDER:
        candidate = search_root / relative_path
        if candidate.is_file():
            return candidate
    searched = ", ".join(
        str(search_root / path) for path in _DEFAULT_CONFIG_SEARCH_ORDER
    )
    msg = (
        "No configuration file was provided and none was found in the default "
        f"search locations: {searched}"
    )
    raise FileNotFoundError(msg)


def _config_argument_callback(
    ctx: click.Context,
    param: click.Parameter,
    value: Path | None,
) -> Path:
    """
    Resolve the shared config argument for Click commands.

    Args:
        ctx: The active Click context.
        param: The Click parameter being processed.
        value: The explicit config path, if provided.

    Returns:
        The resolved config path.

    Raises:
        click.BadParameter: If no explicit or default config path can be found.
    """
    del ctx
    try:
        return _resolve_config_argument(value)
    except FileNotFoundError as exc:
        raise click.BadParameter(str(exc), param=param) from exc


def _argument_help_records(
    params: list[click.Parameter],
) -> list[tuple[str, str]]:
    """
    Build shared help records for common positional arguments.

    Args:
        params: The Click parameters used by a command.

    Returns:
        Help records suitable for `click.HelpFormatter.write_dl`.
    """
    return [
        (param.human_readable_name, option_entry[1])
        for param in params
        if param.name is not None
        and (option_entry := COMMON_OPTIONS.get(param.name)) is not None
        and option_entry[1] is not None
    ]


# Dictionary of common Click options and arguments
# These can be requested by command classes to maintain consistency
COMMON_OPTIONS: Final[dict[str, CommonOptionEntry]] = {
    "config": (
        click.argument(
            "config",
            callback=_config_argument_callback,
            default=None,
            required=False,
            type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
        ),
        (
            "Configuration file. If omitted, flepimop2 searches, in order, for "
            "`config.yaml`, `config.yml`, `configuration.yaml`, "
            "`configuration.yml`, `configs/config.yaml`, "
            "`configs/config.yml`, `configs/configuration.yaml`, and "
            "`configs/configuration.yml`."
        ),
    ),
    "dry_run": (
        click.option(
            "--dry-run",
            is_flag=True,
            default=False,
            help="Should this command be run using dry run?",
        ),
        None,
    ),
    "path": (
        click.argument(
            "path",
            type=click.Path(
                exists=False,
                file_okay=False,
                writable=True,
                path_type=Path,
            ),
            default=None,
        ),
        "Filesystem path used by the command.",
    ),
    "target": (
        click.option(
            "-t",
            "--target",
            default=None,
            help="The target to use for this command.",
        ),
        None,
    ),
    "verbosity": (
        click.option(
            "-v",
            "--verbosity",
            count=True,
            default=0,
            help="The verbosity level to use for this command.",
        ),
        None,
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
    if (entry := COMMON_OPTIONS.get(name)) is None:
        msg = (
            f"Unknown option '{name}'. "
            f"Available options: {', '.join(COMMON_OPTIONS.keys())}"
        )
        raise KeyError(msg)
    return cast("Callable[[FC], FC]", entry[0])

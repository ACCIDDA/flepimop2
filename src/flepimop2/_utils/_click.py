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
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from click import Argument as ClickArgument
from click import BadOptionUsage, UsageError
from click import Option as ClickOption
from click import Parameter as ClickParameter

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")
U = TypeVar("U")


def _override_or_val(override: T | None, value: U) -> T | U:
    """
    Return the override value if it is not None, otherwise return the value.

    Args:
        override: Optional override value.
        value: The value to return if the override is None.

    Returns:
        The `override` value if it is not None, otherwise `value`.
    """
    return value if override is None else override


def _resolve_config_target(
    group: dict[str, T],
    name: str | None,
    group_name: str,
) -> tuple[str, T]:
    """
    Resolve a named target from a configuration group.

    Args:
        group: The module group to get the target from.
        name: The name of the module target. If `None`, defaults to the first item
          in group.
        group_name: The name of the group, for error messages.

    Returns:
        The resolved target name and target value.

    Raises:
        click.UsageError: If the group is empty.
        click.BadOptionUsage: If the specified name is not found in the group.
    """
    if not group:
        msg = f"No targets available in the group for '{group_name}'."
        raise UsageError(msg)
    if name is None:
        name = next(iter(group.keys()))
    res = group.get(name)
    if res is None:
        msg = f"Target '{name}' not available from {group.keys()} for '{group_name}'."
        raise BadOptionUsage(option_name="target", message=msg)
    return name, res


def _get_config_target(group: dict[str, T], name: str | None, group_name: str) -> T:
    """
    Get a `T` by name from a group.

    Args:
        group: The module group to get the target from.
        name: The name of the module target. If `None`, defaults to the first item
          in group.
        group_name: The name of the group, for error messages.

    Returns:
        The `T` with the specified name.
    """
    _, res = _resolve_config_target(group, name, group_name)
    return res


def _click_param_for_option(
    decorator: "Callable[..., object]",
) -> ClickParameter | None:
    """Extract the Click parameter object produced by a `COMMON_OPTIONS` decorator.

    Applies the decorator to a dummy function and returns the last parameter
    it attached.  This is the mechanism `to_argv` uses to inspect whether a
    COMMON_OPTIONS entry is an argument, a flag, a count option, etc.

    Args:
        decorator: A Click decorator (e.g. `click.option(...)` or
            `click.argument(...)`).

    Returns:
        The `ClickParameter` instance attached by the decorator, or `None`
        if the decorator produced none.

    Examples:
        >>> import click
        >>> from flepimop2._utils._click import _click_param_for_option
        >>> opt_decorator = click.option("--dry-run", is_flag=True, default=False)
        >>> param = _click_param_for_option(opt_decorator)
        >>> isinstance(param, click.Option)
        True
        >>> param.name
        'dry_run'
        >>> _click_param_for_option(lambda f: f) is None
        True
    """
    dummy: object = lambda: None  # noqa: E731
    decorated = decorator(dummy)
    params: list[ClickParameter] = getattr(decorated, "__click_params__", [])
    return params[-1] if params else None


def _str_value(value: object) -> str:
    """Render a single option value as a string, resolving `Path` objects.

    `Path` values are resolved to their absolute form so that the resulting
    token replays correctly when the argv is re-executed on a remote with a
    shared filesystem.

    Args:
        value: Any bound option value.

    Returns:
        The string representation of the value, with `Path` objects rendered
        as their absolute path.

    Examples:
        >>> from pathlib import Path
        >>> from flepimop2._utils._click import _str_value
        >>> _str_value("hello")
        'hello'
        >>> _str_value(42)
        '42'
        >>> _str_value(Path("/abs/path"))
        '/abs/path'
        >>> result = _str_value(Path("relative"))
        >>> result == str(Path("relative").absolute())
        True
    """
    if isinstance(value, Path):
        return str(value.absolute())
    return str(value)


def _render_param(param: ClickParameter, value: object) -> list[str]:
    """Render a single Click parameter and its bound value into argv tokens.

    Converts a `(ClickParameter, value)` pair to the list of string tokens
    that represent it on the command line:

    - `click.Argument`: bare positional string, or `[]` if `value` is
      `None`.
    - `click.Option(is_flag=True)`: the first option string when truthy,
      `[]` when falsy.
    - `click.Option(count=True)`: repeated short flag, e.g. `["-vvv"]` for
      `value=3`, `[]` for `value=0`.
    - `click.Option` (regular): `["--name", str(value)]`, or `[]` if
      `value` is `None`.

    Args:
        param: The Click parameter descriptor.
        value: The bound value for that parameter.

    Returns:
        A (possibly empty) list of string tokens.

    Examples:
        >>> import click
        >>> from flepimop2._utils._click import _render_param
        >>> arg = click.Argument(["config"])
        >>> _render_param(arg, "config.yaml")
        ['config.yaml']
        >>> _render_param(arg, None)
        []
        >>> flag = click.Option(["--dry-run"], is_flag=True, default=False)
        >>> _render_param(flag, True)
        ['--dry-run']
        >>> _render_param(flag, False)
        []
        >>> verbosity = click.Option(["-v", "--verbosity"], count=True, default=0)
        >>> _render_param(verbosity, 3)
        ['-vvv']
        >>> _render_param(verbosity, 0)
        []
        >>> target = click.Option(["-t", "--target"], default=None)
        >>> _render_param(target, "sim1")
        ['--target', 'sim1']
        >>> _render_param(target, None)
        []
    """
    if isinstance(param, ClickArgument):
        return [_str_value(value)] if value is not None else []
    if not isinstance(param, ClickOption):
        return []
    if getattr(param, "is_flag", False):
        return [param.opts[0]] if value else []
    if getattr(param, "count", False):
        count = int(value) if isinstance(value, (int, str)) and value else 0
        short = next(
            (o for o in param.opts if o.startswith("-") and not o.startswith("--")),
            param.opts[0],
        )
        return ["-" + short.lstrip("-") * count] if count else []
    long_opt = next(
        (o for o in param.opts if o.startswith("--")),
        param.opts[0],
    )
    return [long_opt, _str_value(value)] if value is not None else []

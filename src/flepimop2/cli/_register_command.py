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
from collections.abc import Callable, Sequence
from typing import Any

import click
from click import Group

from flepimop2.cli._cli_command import CliCommand
from flepimop2.cli._options import _argument_help_records, get_option


class _ArgumentHelpCommand(click.Command):
    """Click command that renders shared positional argument help."""

    def format_options(
        self,
        ctx: click.Context,
        formatter: click.HelpFormatter,
    ) -> None:
        """Write shared argument help before the normal options section."""
        argument_help = _argument_help_records(self.get_params(ctx))
        if argument_help:
            with formatter.section("Arguments"):
                formatter.write_dl(argument_help)
        super().format_options(ctx, formatter)


def register_command(
    command_cls: type[CliCommand],
    group: Group,
    *,
    extra_options: Sequence[str] = (),
    on_invoke: Callable[[CliCommand, dict[str, Any]], None] | None = None,
) -> None:
    """
    Register a `CliCommand` subclass as a Click command.

    This function creates a Click command from a CliCommand subclass and
    registers it with the CLI group. It automatically applies any common
    CLI options/arguments requested by the command and extracts help text
    from the command's docstring.

    Args:
        command_cls: A `CliCommand` subclass to register.
        group: The click `Group` to register the command with.
        extra_options: Additional option names (from `COMMON_OPTIONS`) to
            prepend before the command's own options. These are extracted from
            `kwargs` before the command instance is constructed and passed to
            `on_invoke` as a separate dict.
        on_invoke: Optional callback invoked instead of `command_instance()`.
            Receives the constructed command instance and a dict of the extra
            kwargs extracted from `extra_options`.
    """

    def command_wrapper(**kwargs: Any) -> None:
        extra_kwargs = {k: kwargs.pop(k) for k in extra_options if k in kwargs}
        command_instance = command_cls(**kwargs)
        if on_invoke is not None:
            on_invoke(command_instance, extra_kwargs)
        else:
            command_instance()

    command_name = command_cls.command_name()
    command_wrapper.__name__ = command_name
    command_wrapper.__doc__ = command_cls.help_text()

    all_options = [*extra_options, *command_cls.options()]
    for option_name in reversed(all_options):
        option_decorator = get_option(option_name)
        command_wrapper = option_decorator(command_wrapper)

    group.command(name=command_name, cls=_ArgumentHelpCommand)(command_wrapper)

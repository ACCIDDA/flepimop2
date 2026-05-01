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
from typing import Any

import click
from click import Group

from flepimop2._cli._cli_command import CliCommand
from flepimop2._cli._options import _argument_help_records, get_option


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


def register_command(command_cls: type[CliCommand], group: Group) -> None:
    """
    Register a `CliCommand` subclass as a Click command.

    This function creates a Click command from a CliCommand subclass and
    registers it with the CLI group. It automatically applies any common
    CLI options/arguments requested by the command and extracts help text
    from the command's docstring.

    Args:
        command_cls: A `CliCommand` subclass to register.
        group: The click `Group` to register the command with.
    """

    # Create a wrapper function that instantiates and runs the command
    def command_wrapper(**kwargs: Any) -> None:
        command_instance = command_cls()
        command_instance(**kwargs)

    # Set the function name and docstring for Click
    command_name = command_cls.command_name()
    command_wrapper.__name__ = command_name
    command_wrapper.__doc__ = command_cls.help_text()

    # Apply the options/arguments in reverse order
    # (Click decorators are applied bottom-up)
    for option_name in reversed(command_cls.options()):
        option_decorator = get_option(option_name)
        command_wrapper = option_decorator(command_wrapper)

    # Register the command with the CLI group
    group.command(name=command_name, cls=_ArgumentHelpCommand)(command_wrapper)

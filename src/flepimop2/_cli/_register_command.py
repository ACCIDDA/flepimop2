from typing import Any

from click import Group

from flepimop2._cli._cli_command import CliCommand
from flepimop2._cli._options import get_option


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
    for option_name in reversed(command_cls.options):  # type: ignore[call-overload]
        option_decorator = get_option(option_name)
        command_wrapper = option_decorator(command_wrapper)

    # Register the command with the CLI group
    group.command(name=command_name)(command_wrapper)

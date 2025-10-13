"""Abstract base class for CLI commands."""

__all__ = []
import re
from abc import ABC, abstractmethod
from typing import Any

_COMMAND_NAME_REGEX = re.compile(r"(?<!^)(?=[A-Z])")


class CliCommand(ABC):
    """
    Abstract base class for CLI commands.

    All CLI commands should inherit from this class and implement the `run`
    method. This design allows for easy composition of commands, particularly
    for batch operations.
    """

    @staticmethod
    @abstractmethod
    def run(**kwargs: Any) -> None:
        """
        Execute the command.

        Args:
            **kwargs: Command-specific arguments passed from Click options/arguments.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def options(self) -> tuple[str, ...]:
        """
        Get the list of common CLI options/arguments this command uses.

        Commands should override this method to specify which common options
        they want to use from `cli_options.COMMON_OPTIONS`.

        The options will be applied in the order specified, with arguments
        typically appearing before options in the list for proper Click behavior.

        Returns:
            List of option names to request from `COMMON_OPTIONS`.
        """
        raise NotImplementedError

    @classmethod
    def command_name(cls) -> str:
        """
        Get the command name for CLI registration.

        By default, converts the class name from CamelCase to kebab-case.
        For example, SimulateCommand -> simulate. Commands can override this
        method to provide a custom command name.

        Returns:
            The command name to use in the CLI.
        """
        return _COMMAND_NAME_REGEX.sub(
            "-", cls.__name__.removesuffix("Command")
        ).lower()

    @classmethod
    def help_text(cls) -> str:
        """
        Get the help text for this command.

        By default, extracts the help text from the class docstring.
        The first line becomes the short help (shown in command list),
        and the full docstring becomes the long help (shown in command --help).

        Commands can override this method to provide custom help text.

        Returns:
            The help text for the command.
        """
        if cls.__doc__:
            return cls.__doc__.strip()
        return "No description available."

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
"""Abstract base class for CLI commands."""

__all__ = []

import inspect
import logging
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from flepimop2._utils._click import _click_param_for_option, _render_param
from flepimop2.cli._logging import get_script_logger
from flepimop2.cli._options import COMMON_OPTIONS
from flepimop2.typing import ExitCode

_COMMAND_NAME_REGEX = re.compile(r"(?<!^)(?=[A-Z])")


class CliCommand(ABC):
    """
    Abstract base class for CLI commands.

    All CLI commands should inherit from this class and implement the `run`
    method. This design allows for easy composition of commands, particularly
    for batch operations.
    """

    auto_append_verbosity: bool = True
    logger: logging.Logger | None = None
    bound_kwargs: dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """
        Bind CLI kwargs to this command instance.

        Args:
            **kwargs: Keyword arguments corresponding to the options declared
                by this command's `options()` classmethod.
        """
        self.bound_kwargs = dict(kwargs)

    def __call__(self) -> None:
        """
        Execute this command using the kwargs bound at construction time.

        Consumes 'verbosity' for logger setup. If 'verbosity' was
        auto-appended (not in `_literal_options`), it is removed from the
        kwargs passed to `run()`. The return value from `run()` is forwarded
        to `sys.exit()`.
        """
        kwargs = dict(self.bound_kwargs)
        verbosity = kwargs.pop("verbosity", 0)
        self.logger = get_script_logger(__name__, verbosity)
        longest_key = max((len(str(k)) for k in kwargs), default=0)
        self.debug("Given %u options/arguments:", len(kwargs))
        for key, value in kwargs.items():
            self.debug("%s = %s", key.ljust(longest_key, " "), self.format(value))
        if "verbosity" in self._literal_options():
            kwargs |= {"verbosity": verbosity}
        sys.exit(self.run(**kwargs))

    @abstractmethod
    def run(self, **kwargs: Any) -> ExitCode:
        """
        Execute the command.

        Args:
            **kwargs: Command-specific arguments passed from Click options/arguments.
        """
        raise NotImplementedError

    @classmethod
    def _literal_options(cls) -> list[str]:
        """
        Get the literal options from the run method signature.

        This method introspects the keyword-only parameters of the `run` method
        and returns their names exactly as they appear in the signature, without
        any automatic additions like verbosity.

        Returns:
            List of option names from the run method signature.
        """
        return [
            param_name
            for param_name, param in inspect.signature(cls.run).parameters.items()
            if param.kind == inspect.Parameter.KEYWORD_ONLY
        ]

    @classmethod
    def options(cls) -> list[str]:
        """
        Get the list of common CLI options/arguments this command uses.

        By default, this method uses _literal_options() to get the keyword-only
        parameters from the `run` method. If 'verbosity' is not present and
        `auto_append_verbosity` is True, it will be automatically appended.

        Commands can override this method to specify custom options that differ
        from the `run` method's parameters, or when more complex logic is needed.

        The options will be applied in the order specified, with arguments
        typically appearing before options in the list for proper Click behavior.

        Returns:
            List of option names to request from `COMMON_OPTIONS`.

        Examples:
            >>> from flepimop2.typing import ExitCode
            >>> class MyCommand(CliCommand):
            ...     def run(self, *, config: Path, dry_run: bool) -> ExitCode:
            ...         return ExitCode.OKAY
            >>> MyCommand.options()
            ['config', 'dry_run', 'verbosity']

            >>> class MyCommandWithVerbosity(CliCommand):
            ...     def run(
            ...         self, *, config: Path, verbosity: int, dry_run: bool
            ...     ) -> ExitCode:
            ...         return ExitCode.OKAY
            >>> MyCommandWithVerbosity.options()
            ['config', 'verbosity', 'dry_run']
        """
        options = cls._literal_options()
        if cls.auto_append_verbosity and "verbosity" not in options:
            options.append("verbosity")
        return options

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

    def __str__(self) -> str:
        """Render this command as a CLI invocation string.

        Returns:
            The command rendered as a CLI invocation.
        """
        return " ".join(("flepimop2", self.command_name(), *self.to_argv()))

    def to_argv(self) -> list[str]:
        """Render this instance's bound kwargs back into argv tokens.

        Walks `cls.options()` in declaration order and converts each bound
        value to its CLI representation:

        - `click.Argument`: bare positional string (skipped if `None`).
        - `click.Option` with `is_flag=True`: long flag name when truthy, omitted when
            falsy.
        - `click.Option` with `count=True`: repeated short flag
            (e.g. `-vvv` for `verbosity=3`).
        - `click.Option` otherwise: `--name value` pair.

        `Path` values are rendered as their absolute string form so the
        resulting argv replays correctly on a remote with a shared filesystem.

        Returns:
            A list of string tokens suitable for passing to `subprocess`.
        """
        tokens: list[str] = []
        for name in type(self).options():
            entry = COMMON_OPTIONS.get(name)
            if entry is None:
                continue
            param = _click_param_for_option(entry[0])
            if param is None:
                continue
            tokens.extend(_render_param(param, self.bound_kwargs.get(name)))
        return tokens

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
        return inspect.cleandoc(cls.__doc__ or "No description available.")

    def log(self, level: int, *args: Any, **kwargs: Any) -> None:
        """Log a message at the specified level."""
        if self.logger is None:
            return
        self.logger.log(level, *args, **kwargs)

    def debug(self, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        if self.logger is None:
            return
        self.logger.debug(*args, **kwargs)

    def info(self, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        if self.logger is None:
            return
        self.logger.info(*args, **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        if self.logger is None:
            return
        self.logger.warning(*args, **kwargs)

    def error(self, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        if self.logger is None:
            return
        self.logger.error(*args, **kwargs)

    def critical(self, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        if self.logger is None:
            return
        self.logger.critical(*args, **kwargs)

    @staticmethod
    def format(value: object) -> str:
        """
        Format a value for logging output.

        Args:
            value: The value to format.

        Returns:
            A string representation of the value.

        Examples:
            >>> from pathlib import Path
            >>> from flepimop2.cli import CliCommand
            >>> CliCommand.format("abc")
            'abc'
            >>> CliCommand.format(Path("/some/path"))
            '/some/path'
            >>> CliCommand.format(Path("relative/path"))
            '/.../relative/path'
            >>> CliCommand.format(1000000)
            '1,000,000'
            >>> CliCommand.format(1234.5678)
            '1,234.5678'
        """
        if isinstance(value, Path):
            return str(value.absolute())
        if isinstance(value, int | float):
            return f"{value:,}"
        return str(value)

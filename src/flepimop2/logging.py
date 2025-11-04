"""
Logging utilities for consistent script output.

This module provides functionality for creating consistent outputs from CLI tools
provided by this package.
"""

__all__ = ["DEFAULT_LOG_FORMAT", "ClickHandler", "LoggingLevel", "get_script_logger"]


import logging
import sys
from enum import IntEnum
from pathlib import Path
from typing import IO, Any, Final

import click

_PUNCTUATION: Final = (".", ",", "?", "!", ":")
_VERBOSITY_TO_LOGGING_LEVEL: Final = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
}
DEFAULT_LOG_FORMAT: Final = "%(asctime)s:%(levelname)s> %(message)s"


class ClickHandler(logging.Handler):
    """Custom logging handler specifically for click based CLI tools."""

    def __init__(  # noqa: PLR0913
        self,
        level: int | str = 0,
        file: IO[Any] | None = None,
        *,
        nl: bool = True,
        err: bool = False,
        color: bool | None = None,
        punctuate: bool = True,
    ) -> None:
        """
        Initialize an instance of the click handler.

        Args:
            level: The logging level to use for this handler.
            file: The file to write to. Defaults to stdout.
            nl: Print a newline after the message. Enabled by default.
            err: Write to stderr instead of stdout.
            color: Force showing or hiding colors and other styles. By default click
                will remove color if the output does not look like an interactive
                terminal.
            punctuate: A boolean indicating if punctuation should be added to the end
                of a log message provided if missing.

        Notes:
            For more details on the `file`, `nl`, `err`, and `color` args please refer
            to [`click.echo`](https://click.palletsprojects.com/en/8.1.x/api/#click.echo).
        """
        super().__init__(level)
        self._file = file
        self._nl = nl
        self._err = err
        self._color = color
        self._punctuate = punctuate

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a given log record via `click.echo`.

        Args:
            record: The log record to output.

        See Also:
            [`logging.Handler.emit`](https://docs.python.org/3/library/logging.html#logging.Handler.emit).
        """
        msg = self.format(record)
        msg = f"{msg}." if self._punctuate and not msg.endswith(_PUNCTUATION) else msg
        click.echo(
            message=msg, file=self._file, nl=self._nl, err=self._err, color=self._color
        )


def get_script_logger(
    name: str,
    verbosity: int,
    handler: logging.Handler | None = None,
    log_format: str = DEFAULT_LOG_FORMAT,
) -> logging.Logger:
    """
    Create a logger for use in scripts/CLI tools.

    Args:
        name: The name to display in the log message, useful for locating the source
            of logging messages. Almost always `__name__`.
        verbosity: A non-negative integer for the verbosity level.
        handler: An optional logging handler to use in creating the logger returned, or
            `None` to just use the `ClickHandler`.
        log_format: The format to use for logged messages. Passed directly to the `fmt`
            argument of [logging.Formatter](https://docs.python.org/3/library/logging.html#logging.Formatter).

    Returns:
        An instance of `logging.Logger` that has the appropriate level set based on
        `verbosity` and a custom handler for outputting for CLI tools.

    Examples:
        >>> from flepimop2.logging import get_script_logger
        >>> logger = get_script_logger(__name__, 3)
        >>> logger.info("This is a log info message")  # doctest: +SKIP
        2024-10-29 16:07:20,272:INFO> This is a log info message.
    """
    logger = logging.getLogger(name)
    logger.setLevel(LoggingLevel.from_verbosity(verbosity))
    handler = ClickHandler() if handler is None else handler
    log_formatter = logging.Formatter(log_format)
    for old_handler in logger.handlers:
        logger.removeHandler(old_handler)
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)
    # pytest-dev/pytest#3697
    logger.propagate = Path(sys.argv[0]).name == "pytest" if sys.argv else False
    return logger


class LoggingLevel(IntEnum):
    """
    An enumeration of the logging levels used in this package.

    Attributes:
        DEBUG: Detailed information, typically of interest only when diagnosing
            problems.
        INFO: Confirmation that things are working as expected.
        WARNING: An indication that something unexpected happened, or indicative of some
            problem in the near future (e.g., 'ode unstable'). The software is still
            working as expected.
        ERROR: Due to a more serious problem, the software has not been able to perform
            some function.
        CRITICAL: A serious error, indicating that the program itself may be unable to
            continue running.

    Examples:
        >>> from flepimop2.logging import LoggingLevel
        >>> LoggingLevel.DEBUG
        <LoggingLevel.DEBUG: 10>
        >>> LoggingLevel.from_verbosity(2)
        <LoggingLevel.INFO: 20>
        >>> LoggingLevel.from_verbosity(LoggingLevel.ERROR)
        <LoggingLevel.ERROR: 40>
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def from_verbosity(cls, verbosity: "int | LoggingLevel") -> "LoggingLevel":
        """
        Convert a verbosity level to a `LoggingLevel`.

        Args:
            verbosity: The verbosity level to convert.

        Returns:
            The corresponding `LoggingLevel`.

        Raises:
            ValueError: If `verbosity` is negative.
        """
        if isinstance(verbosity, cls):
            return verbosity
        if verbosity < 0:
            msg = f"`verbosity` must be non-negative, was given '{verbosity}'."
            raise ValueError(msg)
        if verbosity in set(cls):
            return cls(verbosity)
        return cls(_VERBOSITY_TO_LOGGING_LEVEL.get(verbosity, logging.DEBUG))

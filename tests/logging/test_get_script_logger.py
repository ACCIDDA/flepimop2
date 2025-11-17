"""Unit tests for the `get_script_logger` function in `flepimop2.flepilog` module."""

import logging
import random
import string

import pytest

from flepimop2.flepilog import DEFAULT_LOG_FORMAT, LoggingLevel, get_script_logger


@pytest.mark.parametrize("name", ["foobar", "fizzbuzz"])
@pytest.mark.parametrize(
    "verbosity",
    [
        0,
        1,
        2,
        3,
        4,
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
    ],
)
@pytest.mark.parametrize("handler", [None, logging.StreamHandler()])
@pytest.mark.parametrize("log_format", [None, "%(message)s"])
def test_correct_logging_output(
    caplog: pytest.LogCaptureFixture,
    name: str,
    verbosity: int,
    handler: logging.Handler | None,
    log_format: str | None,
) -> None:
    """Test the number of logs emitted by a logger from `get_script_logger`."""
    caplog.set_level(logging.DEBUG, logger=name)
    logger = get_script_logger(
        name,
        verbosity,
        handler=handler,
        log_format=log_format or DEFAULT_LOG_FORMAT,
    )
    assert isinstance(logger, logging.Logger)
    assert logger.name == name
    assert logger.level == LoggingLevel.from_verbosity(verbosity)
    if handler is not None:
        assert len(logger.handlers) == 1
        assert logger.handlers[0] == handler
    if logger.handlers[0].formatter:
        assert logger.handlers[0].formatter._fmt == (log_format or DEFAULT_LOG_FORMAT)
    i = 0
    for val, lvl in [
        (10, "debug"),
        (20, "info"),
        (30, "warning"),
        (40, "error"),
        (50, "critical"),
    ]:
        msg = "".join(random.choice(string.ascii_letters) for _ in range(20))  # noqa: S311
        getattr(logger, lvl)(msg)
        if val < LoggingLevel.from_verbosity(verbosity):
            assert len(caplog.records) == i
            continue
        assert caplog.records[i].levelno == val
        assert caplog.records[i].message == msg
        i += 1

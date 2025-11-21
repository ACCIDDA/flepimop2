"""Unit tests for the `LoggingLevel` class in `flepimop2._cli._logging` module."""

import logging

import pytest

from flepimop2._cli._logging import LoggingLevel


@pytest.mark.parametrize("verbosity", [-1, -100])
def test_from_verbosity_negative_verbosity_raises_value_error(verbosity: int) -> None:
    """Test `from_verbosity` raises `ValueError` for negative verbosity values."""
    with pytest.raises(
        ValueError, match=f"`verbosity` must be non-negative, was given '{verbosity}'."
    ):
        LoggingLevel.from_verbosity(verbosity)


@pytest.mark.parametrize(
    ("verbosity", "expected_level"),
    [
        (logging.ERROR, logging.ERROR),
        (logging.WARNING, logging.WARNING),
        (logging.INFO, logging.INFO),
        (logging.DEBUG, logging.DEBUG),
        (0, logging.ERROR),
        (1, logging.WARNING),
        (2, logging.INFO),
        (3, logging.DEBUG),
        (4, logging.DEBUG),
        (5, logging.DEBUG),
    ],
)
def test_from_verbosity_output_validation(verbosity: int, expected_level: int) -> None:
    """Test `from_verbosity` returns expected logging level for given verbosity."""
    assert LoggingLevel.from_verbosity(verbosity) == expected_level

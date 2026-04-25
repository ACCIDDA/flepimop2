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

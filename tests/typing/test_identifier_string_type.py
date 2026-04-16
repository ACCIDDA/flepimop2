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
"""Unit tests for the `IdentifierString` type."""

import pytest
from pydantic import BaseModel, ValidationError

from flepimop2.typing import IdentifierString


class Example(BaseModel):
    """Example model using IdentifierString."""

    name: IdentifierString


@pytest.mark.parametrize(
    "name",
    [
        "gamma",
        "valid_name",
        "valid_name_123",
        "r0",
    ],
)
def test_valid_identifier_strings(name: str) -> None:
    """Test that valid identifier strings are accepted."""
    example = Example(name=name)
    assert example.name == name


@pytest.mark.parametrize(
    "name",
    [
        "1invalidStart",
        "invalid char!",
        "-invalidStartHyphen",
        "invalidEnd-",
        "",
        "invalid@char",
        "A",
        "name-with-hyphens",
        "validName",
        "class",
        "def",
    ],
)
def test_invalid_identifier_strings(name: str) -> None:
    """Test that invalid identifier strings raise ValidationError."""
    with pytest.raises(ValidationError):
        Example(name=name)

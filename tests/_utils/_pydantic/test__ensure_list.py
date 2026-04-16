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
"""Test the `_ensure_list` function."""

from typing import TypeVar

import pytest

from flepimop2._utils._pydantic import _ensure_list

T = TypeVar("T")


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        (None, None),
        (5, [5]),
        ([1, 2, 3], [1, 2, 3]),
        ((4, 5), [4, 5]),
    ],
)
def test_ensure_list(
    input_value: T | list[T] | tuple[T] | None, expected_output: list[T] | None
) -> None:
    """Test that various inputs are correctly converted to lists."""
    assert _ensure_list(input_value) == expected_output

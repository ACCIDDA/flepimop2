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
"""
Tests for the `_override_or_val` function.

Helper for click options with defaults computed at runtime.
"""

from typing import TypeVar

import pytest

from flepimop2._utils._click import _override_or_val

T = TypeVar("T")
U = TypeVar("U")


@pytest.mark.parametrize(
    ("override", "value", "expected"),
    [(None, 1, 1), (None, "abc", "abc"), (1, "abc", 1), ("", "foo", "")],
)
def test_exact_results_for_select_values(
    override: T | None, value: U, expected: T | U
) -> None:
    """`_override_or_val` returns the default or override as appropriate."""
    assert _override_or_val(override, value) == expected

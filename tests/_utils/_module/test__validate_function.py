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
"""Unit tests for `_validate_function` function."""

from unittest.mock import MagicMock

import pytest

from flepimop2._utils._module import _validate_function


@pytest.mark.parametrize(
    ("func_name", "expected"),
    [
        ("callable_function", True),
        ("non_callable_attr", False),
        ("missing_attr", False),
    ],
)
def test_validate_function(func_name: str, expected: bool) -> None:  # noqa: FBT001
    """Test `_validate_function` with various module configurations."""
    # Create a mock module with specific attributes
    mock_module = MagicMock(spec=[])
    mock_module.callable_function = lambda: None
    mock_module.non_callable_attr = "not a function"

    # Run the validation
    assert _validate_function(mock_module, func_name) == expected

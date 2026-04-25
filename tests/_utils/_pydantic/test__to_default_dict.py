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
"""Test the `_to_default_dict` function."""

from typing import Any

import pytest

from flepimop2._utils._pydantic import _to_default_dict


@pytest.mark.parametrize(
    "input_obj",
    [
        [{"a": 1, "b": 2}],
    ],
)
def test_list_of_dict_input(input_obj: list[dict[str, Any]]) -> None:
    """Test that a list is converted to a dict with a default key."""
    output_dict = _to_default_dict(input_obj)
    assert output_dict == {"default": input_obj[0]}


@pytest.mark.parametrize(
    "input_obj",
    [
        {"a": 1, "b": 2},
    ],
)
def test_dict_input(input_obj: dict[str, Any]) -> None:
    """Test that a dict input is returned unchanged."""
    output_dict = _to_default_dict(input_obj)
    assert output_dict == input_obj

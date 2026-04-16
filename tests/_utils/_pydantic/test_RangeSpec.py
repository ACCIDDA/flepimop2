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
"""Test for the `_to_np_array` function."""

import numpy as np
import pytest
from numpy.testing import assert_array_equal
from pydantic import TypeAdapter, ValidationError

from flepimop2._utils._pydantic import RangeSpec, _to_np_array

ta: TypeAdapter[RangeSpec] = TypeAdapter(RangeSpec)


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        ("1:2:3", np.array([1.0, 3.0], dtype=np.float64)),
        ("0:0.5:2", np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float64)),
        ("5:10", np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0], dtype=np.float64)),
        ([1, 2, 3], np.array([1.0, 2.0, 3.0], dtype=np.float64)),
    ],
)
def test_to_np_array(
    input_value: str | list[float] | float, expected_output: np.ndarray
) -> None:
    """Test `RangeSpec` with various inputs."""
    result = _to_np_array(ta.validate_python(input_value))
    assert_array_equal(result, expected_output)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "1:2:3:4",  # Too many parts
        "a:b:c",  # Non-numeric values
        "1::3",  # Missing step
        1,  # Single float not in list
    ],
)
def test_to_np_array_invalid_input(invalid_input: str) -> None:
    """Test `RangeSpec` with invalid inputs."""
    with pytest.raises(ValidationError):
        ta.validate_python(invalid_input)

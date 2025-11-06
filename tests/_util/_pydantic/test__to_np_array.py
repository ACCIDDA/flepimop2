"""Test for the `_to_np_array` function."""

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from flepimop2._utils._pydantic import _to_np_array


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        ("1:2:3", np.array([1.0, 3.0], dtype=np.float64)),
        ("0:0.5:2", np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float64)),
        ("5:10", np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0], dtype=np.float64)),
        (["1", "2", "3"], np.array([1.0, 2.0, 3.0], dtype=np.float64)),
        ("1", np.array([1.0], dtype=np.float64)),
    ],
)
def test_to_np_array(input_value: str | list[str], expected_output: np.ndarray) -> None:
    """Test `_to_np_array` with various inputs."""
    result = _to_np_array(input_value)
    assert_array_equal(result, expected_output)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "1:2:3:4",  # Too many parts
        "a:b:c",  # Non-numeric values
        "1::3",  # Missing step
    ],
)
def test_to_np_array_invalid_input(invalid_input: str) -> None:
    """Test `_to_np_array` with invalid inputs."""
    with pytest.raises(ValueError, match=f"{invalid_input}"):
        _to_np_array(invalid_input)

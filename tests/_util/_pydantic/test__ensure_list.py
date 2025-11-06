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

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

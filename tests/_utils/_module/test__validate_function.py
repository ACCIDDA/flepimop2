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

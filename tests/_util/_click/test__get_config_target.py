"""
Tests for the `_get_config_target` function.

Helper for the 'target' click option and handling bad values only knowable at runtime.
"""

import pytest
from click import BadOptionUsage

from flepimop2._utils._click import _get_config_target


@pytest.fixture
def sample_group() -> dict[str, int]:
    """
    Provide a sample group dictionary for testing.

    Returns:
        A dictionary mapping string keys to integer values.
    """
    return {"first": 1, "second": 2, "third": 3}


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (None, 1),  # Default to first item
        ("first", 1),
        ("second", 2),
        ("third", 3),
    ],
)
def test_get_config_target_valid(
    sample_group: dict[str, int], name: str | None, expected: int
) -> None:
    """Test `_get_config_target` with valid names."""
    result = _get_config_target(sample_group, name)
    assert result == expected


def test_get_config_target_invalid(sample_group: dict[str, int]) -> None:
    """Test `_get_config_target` with an invalid name."""
    invalid_name = "fourth"
    with pytest.raises(BadOptionUsage) as exc_info:
        _get_config_target(sample_group, invalid_name)
    assert f"'{invalid_name}'" in str(exc_info.value)
    for key in sample_group:
        assert f"{key}" in str(exc_info.value)

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
Tests for the `_get_config_target` function.

Helper for the 'target' click option and handling bad values only knowable at runtime.
"""

import pytest
from click import BadOptionUsage, UsageError

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
    result = _get_config_target(sample_group, name, "test")
    assert result == expected


def test_get_config_target_invalid(sample_group: dict[str, int]) -> None:
    """Test `_get_config_target` with an invalid name."""
    invalid_name = "fourth"
    with pytest.raises(BadOptionUsage) as exc_info:
        _get_config_target(sample_group, invalid_name, "test")
    assert f"'{invalid_name}'" in str(exc_info.value)
    for key in sample_group:
        assert f"{key}" in str(exc_info.value)


def test__get_config_target_empty_group() -> None:
    """Test `_get_config_target` with an empty group."""
    empty_group: dict[str, int] = {}
    with pytest.raises(UsageError):
        _get_config_target(empty_group, None, "test")

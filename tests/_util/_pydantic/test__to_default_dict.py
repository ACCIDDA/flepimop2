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

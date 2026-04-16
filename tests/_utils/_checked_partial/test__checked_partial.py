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
Tests for the `_checked_partial` function.

Helper for functools.partial with validation of offered parameters against a
function signature.
"""

from collections.abc import Callable
from typing import Any

import pytest

from flepimop2._utils._checked_partial import _checked_partial


def dummy_func(a: int, b: int, c: int) -> int:
    """A dummy function for testing _checked_partial.

    Args:
        a: An integer parameter.
        b: An integer parameter.
        c: An integer parameter.

    Returns:
        The product of a, b, and c.
    """
    return a * b * c


def dumb_func(a, b: Any, c):  # type: ignore[no-untyped-def] # noqa: ANN001, ANN201, ANN401
    """A function for testing _checked_partial. Deliberately missing annotations.

    Args:
        a: An unannotated-but-should-be-integer parameter.
        b: An unannotated-but-should-be-integer parameter.
        c: An unannotated-but-should-be-integer parameter.

    Returns:
        The product of a, b, and c.
    """
    return a * b * c


pars = pytest.mark.parametrize("func", [dummy_func])
badfun = pytest.mark.parametrize("func", [dumb_func])


@pars
def test_set_valid_static_parameters(func: Callable[..., int]) -> None:
    """Confirm no errors when setting all valid parameters."""
    newfun = _checked_partial(func, {"a": 5})
    assert newfun(b=10, c=2) == 100
    assert newfun(a=2, c=2, b=10) == 40
    newfun = _checked_partial(func, {"a": 10})
    assert newfun(b=10, c=2) == 200
    newfun = _checked_partial(func)
    assert newfun(a=1, b=10, c=2) == 20


@pars
@pytest.mark.xfail(
    reason="Currently allows using the function with static parameters, "
    "but should raise error.",
    strict=True,
)
def test_static_parameters_fixed(func: Callable[..., int]) -> None:
    """Confirm errors when calling with a static parameter set."""
    newfun = _checked_partial(func, {"a": 5})
    with pytest.raises(TypeError):
        newfun(a=5, b=10, c=2)


@pars
def test_set_static_parameter_throws_error_on_invalid_params(
    func: Callable[..., int],
) -> None:
    """Confirm errors raised for various invalid scenarios."""
    with pytest.raises(TypeError):
        _checked_partial(func, {"nonexistent_param": 5.0})
    with pytest.raises(TypeError):
        _checked_partial(func, {"c": "invalid_string"})


@badfun
def test_unannotated_function_raises(func: Callable[..., int]) -> None:
    """Confirm that a function without annotations does not raise an error."""
    _checked_partial(func, {"a": "a string"})
    _checked_partial(func, {"b": "57.5"})

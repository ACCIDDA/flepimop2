"""
Tests for the `_checked_partial` function.

Helper for functools.partial with validation of offered parameters against a
function signature.
"""

from collections.abc import Callable

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


testpars = pytest.mark.parametrize("func", [dummy_func])


@testpars
def test_set_valid_static_parameters(func: Callable[..., int]) -> None:
    """Confirm no errors when setting all valid parameters."""
    newfun = _checked_partial(func, forbidden={"b"}, a=5)
    assert newfun(b=10, c=2) == 100
    assert newfun(a=2, c=2, b=10) == 40
    newfun = _checked_partial(func, forbidden={"b"}, params={"a": 10})
    assert newfun(b=10, c=2) == 200
    newfun = _checked_partial(func)
    assert newfun(a=1, b=10, c=2) == 20


@testpars
@pytest.mark.xfail(
    reason="Currently allows using the function with static parameters, "
    "but should raise error.",
    strict=True,
)
def test_static_parameters_fixed(func: Callable[..., int]) -> None:
    """Confirm errors when calling with a static parameter set."""
    newfun = _checked_partial(func, forbidden={"b"}, a=5)
    with pytest.raises(TypeError):
        newfun(a=5, b=10, c=2)


@testpars
def test_set_static_parameter_throws_error_on_fixed_time(
    func: Callable[..., int],
) -> None:
    """Confirm errors raised for various invalid scenarios."""
    with pytest.raises(TypeError):
        _checked_partial(func, forbidden={"b"}, b=100)
    with pytest.raises(TypeError):
        _checked_partial(func, nonexistent_param=5.0)
    with pytest.raises(TypeError):
        _checked_partial(func, c="invalid_string")

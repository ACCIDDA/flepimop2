
from typing import TypeVar, overload

T = TypeVar("T")
U = TypeVar("U")

@overload
def _override_or_val(override: T, value: U) -> T: ...


@overload
def _override_or_val(override: None, value: U) -> U: ...


def _override_or_val(override: T | None, value: U) -> T | U:
    """
    Return the override value if it is not None, otherwise return the value.

    Args:
        override: Optional override value.
        value: The value to return if the override is None.

    Returns:
        The `override` value if it is not None, otherwise `value`.
    """
    return value if override is None else override

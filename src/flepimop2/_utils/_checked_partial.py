import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from flepimop2.configuration._types import IdentifierString

T = TypeVar("T")


def _checked_partial(
    func: Callable[..., T],
    forbidden: set[IdentifierString] | None = None,
    params: dict[IdentifierString, Any] | None = None,
    **kwargs: Any,
) -> Callable[..., T]:
    """
    Bind static parameters to a callable, checking their validity.

    Args:
        func: The callable to bind parameters to.
        forbidden: A set of parameter names that are not allowed to be bound.
        params: A dictionary of parameters to statically define for the System.
        **kwargs: Additional parameters to statically define for the System.

    Returns:
        A partial function with static parameters bound.

    Raises:
        TypeError: If offered forbidden keys, keys not in `func` signature, or
            keys with values of incompatible types with `func` signature.

    Examples:
        >>> def example_func(a: float, b: list[float], c: float) -> float:
        ...     return sum([a, c, *b])
        >>> new_func = _checked_partial(example_func, forbidden={"b"}, c=5.0)
        >>> new_func(a=1.0, b=[1.0, 2.0, 3.0])
        12.0
    """
    # Combine params and kwargs, with kwargs taking precedence
    combined_params = {**(params or {}), **kwargs}

    offered_keys = set(combined_params.keys())
    if not offered_keys:
        return func

    validation_errors = []

    forbidden = forbidden or set()

    # Validate that forbidden keys are not offered
    if forbidden.intersection(offered_keys):
        msg = f"Cannot bind forbidden keys: {forbidden}; offered keys: {offered_keys}."
        validation_errors.append(msg)

    # Validate that offered keys are in the func signature
    signature = inspect.signature(func)
    signature_keys = set(signature.parameters.keys())
    if invalid_keys := offered_keys - signature_keys:
        msg = (
            "Offered keys are not in func signature: "
            f"{invalid_keys}. Eligible system parameters are: "
            f"{signature_keys - forbidden}."
        )
        validation_errors.append(msg)

    # Validate parameter value types against signature annotations
    for key, value in signature.parameters.items():
        if key in offered_keys:
            expected_type = value.annotation
            if (
                expected_type is not inspect.Parameter.empty
                and expected_type is not Any
            ):
                if isinstance(expected_type, type) and isinstance(
                    combined_params[key], expected_type
                ):
                    continue
                try:
                    casted_value = expected_type(combined_params[key])
                    combined_params[key] = casted_value
                except (ValueError, TypeError) as e:
                    offered_type = type(combined_params[key])
                    msg = (
                        f"Parameter '{key}' (type {offered_type.__name__}) "
                        f"could not be cast to {expected_type.__name__}. Error: {e!s}"
                    )
                    validation_errors.append(msg)

    if validation_errors:
        validation_errors = [
            "Setting System static parameters failed.",
            *validation_errors,
        ]
        raise TypeError("\n".join(validation_errors))

    return functools.partial(func, **combined_params)

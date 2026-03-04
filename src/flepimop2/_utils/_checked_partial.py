import functools
import inspect
from typing import Any, Protocol

from flepimop2.configuration._types import IdentifierString
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue


def _checked_partial(
    func: Protocol,
    forbidden: set[IdentifierString] | None = None,
    params: dict[IdentifierString, Any] | None = None,
    **kwargs: Any,
) -> Protocol:
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
        Flepimop2ValidationError: If forbidden keys are offered
            or if value types are incompatible with func signature.

    """
    # Combine params and kwargs, with kwargs taking precedence
    combined_params = {**(params or {}), **kwargs}

    offered_keys = set(combined_params.keys())
    if not offered_keys:
        return func

    validation_errors = []

    if forbidden is None:
        forbidden = set()

    # Validate that forbidden keys are not offered
    if forbidden.intersection(offered_keys):
        msg = f"Cannot bind forbidden keys: {forbidden}; offered keys: {offered_keys}."
        validation_errors.append(ValidationIssue(msg, "binding_values"))

    # Validate that offered keys are in the func signature
    signature = inspect.signature(func)
    signature_keys = set(signature.parameters.keys())
    if invalid_keys := offered_keys - signature_keys:
        msg = (
            "Offered keys are not in func signature: "
            f"{invalid_keys}. Eligible system parameters are: "
            f"{signature_keys - forbidden}."
        )
        validation_errors.append(ValidationIssue(msg, "binding_values"))

    # Validate parameter value types against signature annotations
    for key, value in signature.parameters.items():
        if key in offered_keys:
            expected_type = value.annotation
            try:
                casted_value = expected_type(combined_params[key])
                combined_params[key] = casted_value
            except (ValueError, TypeError) as e:
                msg = (
                    f"Parameter '{key}' (type {type(combined_params[key]).__name__}) "
                    f"could not be cast to {expected_type.__name__}. Error: {e!s}"
                )
                validation_errors.append(ValidationIssue(msg, "binding_values"))

    if validation_errors:
        raise Flepimop2ValidationError(validation_errors)

    return functools.partial(func, **combined_params)

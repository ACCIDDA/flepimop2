"""Abstract class for Dynamic Systems."""

__all__ = ["SystemABC", "SystemProtocol", "build"]

import functools
import inspect
from typing import Any, Protocol, runtime_checkable

import numpy as np

from flepimop2.exceptions import ValidationIssue, Flepimop2ValidationError
from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray, StateChangeEnum


@runtime_checkable
class SystemProtocol(Protocol):
    """Type-definition (Protocol) for system stepper functions."""

    def __call__(
        self, time: np.float64, state: Float64NDArray, **kwargs: Any
    ) -> Float64NDArray:
        """Protocol for system stepper functions."""
        ...


def _no_step_function(
    time: np.float64,
    state: Float64NDArray,
    **kwargs: Any,
) -> Float64NDArray:
    msg = "SystemABC::stepper must be provided by a concrete implementation."
    raise NotImplementedError(msg)


class SystemABC(ModuleABC):
    """
    Abstract class for Dynamic Systems.

    Attributes:
        module: The module name for the system.
        state_change: The type of state change.
        options: Optional dictionary of additional options the system exposes for
            `flepimop2` to take advantage of.

    """

    state_change: StateChangeEnum

    _stepper: SystemProtocol

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Ensure concrete subclasses define a valid state change type.

        Args:
            **kwargs: Additional keyword arguments passed to parent classes.

        Raises:
            TypeError: If a concrete subclass does not define `state_change`.

        """
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return
        annotations = inspect.get_annotations(cls)
        has_state_change = (
            "state_change" in cls.__dict__ or "state_change" in annotations
        )
        if not has_state_change:
            msg = (
                f"Concrete class '{cls.__name__}' must define 'state_change' as "
                "a class attribute or type annotation."
            )
            raise TypeError(msg)

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Initialize the SystemABC.

        The default initialization sets the stepper to a no-op function. Concrete
        implementations should override this with a valid stepper function.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        self._stepper = _no_step_function

    def bind(self, params: dict[str, Any] | None = None, **kwargs: dict[str, Any]) -> SystemProtocol:
        """
        Bind static parameters to the system's stepper function.

        Args:
            params: A dictionary of parameters to statically define for the System.
            **kwargs: Additional parameters to statically define for the System.

        Returns:
            A stepper from this System with static parameters defined.

        Raises:
            ValueError: If params contains "time" or "state" keys or if value types
                are incompatible with stepper signature.

        """
        if params is None:
            params = {}
        # Combine params and kwargs, with kwargs taking precedence
        combined_params = {**params, **kwargs}

        forbidden_keys = {"time", "state"}
        offered_keys = set(combined_params.keys())
        validation_errors = []

        # Validate that forbidden keys are not offered
        if forbidden_keys.intersection(offered_keys):
            msg = f"Cannot bind 'time' or 'state' keys; offered keys: {offered_keys}."
            validation_errors.append(ValidationIssue(msg, "binding_values"))
        
        # Validate that offered keys are in the stepper signature
        signature_keys = set(inspect.signature(self._stepper).parameters.keys())
        if invalid_keys := offered_keys - signature_keys:
            msg = f"Offered keys are not in stepper signature: {invalid_keys}. Eligible system parameters are: {signature_keys - forbidden_keys}."
            validation_errors.append(ValidationIssue(msg, "binding_values"))

        # Validate parameter value types against signature annotations
        annotations = inspect.get_annotations(self._stepper)
        for key, value in combined_params.items():
            if key in annotations:
                expected_type = annotations[key]
                try:
                    casted_value = expected_type(value)
                    combined_params[key] = casted_value
                except (ValueError, TypeError) as e:
                    msg = (
                        f"Parameter '{key}' (type {type(value).__name__}) could not be "
                        f"cast to {expected_type.__name__}. Error: {str(e)}"
                    )
                    validation_errors.append(ValidationIssue(msg, "binding_values"))

        if validation_errors:
            raise Flepimop2ValidationError(validation_errors)

        return functools.partial(self._stepper, **combined_params)

    def step(
        self, time: np.float64, state: Float64NDArray, **params: Any
    ) -> Float64NDArray:
        """
        Perform a single step of the system's dynamics.

        Args:
            time: The current time.
            state: The current state array.
            **params: Additional parameters for the stepper.

        Returns:
            The next state array after one step.
        """
        return self._stepper(time, state, **params)


def build(config: dict[str, Any] | ModuleModel) -> SystemABC:
    """
    Build a `SystemABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance.

    Returns:
        The constructed system instance.

    """
    return _build(
        config,
        "system",
        "flepimop2.system.wrapper",
        SystemABC,
    )

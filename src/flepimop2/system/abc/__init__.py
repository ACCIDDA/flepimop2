"""Abstract class for Dynamic Systems."""

__all__ = [
    "Flepimop2ValidationError",
    "SystemABC",
    "SystemProtocol",
    "ValidationIssue",
    "build",
]

import inspect
from typing import Any, Protocol, runtime_checkable

import numpy as np

from flepimop2._utils._checked_partial import _checked_partial
from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.configuration._types import IdentifierString
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
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

    def bind(
        self,
        params: dict[IdentifierString, Any] | None = None,
        **kwargs: Any,
    ) -> SystemProtocol:
        """
        Bind static parameters to the system's stepper function.

        Args:
            params: A dictionary of parameters to statically define for the System.
            **kwargs: Additional parameters to statically define for the System.

        Returns:
            A SystemProtocol for this System with static parameters defined.

        Raises: # noqa: DOC502
            Flepimop2ValidationError: If params contains "time" or "state" keys,
                or parameters not in the System definition,
                or if the parameter values are incompatible with System definition.

        """
        return _checked_partial(
            func=self._stepper,
            forbidden={"time", "state"},
            params=params,
            **kwargs,
        )

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

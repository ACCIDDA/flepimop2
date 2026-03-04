"""Abstract class for Dynamic Systems."""

__all__ = ["SystemABC", "SystemProtocol", "build"]

import inspect
from typing import Any, Protocol, Self, runtime_checkable

import numpy as np

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

    def build_stepper(self) -> SystemProtocol:  # noqa: PLR6301
        """
        Build the stepper function for this system.

        Concrete implementations can override this hook to dynamically construct
        stepper functions from instance state.

        Returns:
            The stepper function for this system.
        """
        return _no_step_function

    def build(self) -> Self:
        """
        Build the system internals required for stepping.

        This method is idempotent and supports three strategies, in order:

        1. Keep an existing instance-level stepper if already set.
        2. Reuse a class-level `_stepper` callable if provided.
        3. Fallback to `build_stepper()` for dynamic construction.

        Returns:
            The built system instance.

        """
        current_stepper = getattr(self, "_stepper", _no_step_function)
        if current_stepper is not _no_step_function:
            return self

        class_stepper = type(self).__dict__.get("_stepper")
        if isinstance(class_stepper, staticmethod):
            class_stepper = class_stepper.__func__
        if callable(class_stepper) and class_stepper is not _no_step_function:
            self._stepper = class_stepper
            return self

        self._stepper = self.build_stepper()
        return self

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
        self.build()
        return self._stepper(time, state, **params)


def build(config: dict[str, Any] | ModuleModel) -> SystemABC:
    """
    Build a `SystemABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance.

    Returns:
        The constructed system instance.

    """
    return _build(config, "system", "flepimop2.system.wrapper", SystemABC)

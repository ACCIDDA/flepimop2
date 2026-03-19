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
from flepimop2.axis import AxisCollection
from flepimop2.configuration import ModuleModel
from flepimop2.configuration._types import IdentifierString
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.module import ModuleABC
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterRequest,
    ParameterValue,
)
from flepimop2.typing import Float64NDArray, StateChangeEnum


@runtime_checkable
class SystemProtocol(Protocol):
    """Type-definition (Protocol) for system stepper functions."""

    def __call__(
        self, time: np.float64, state: Float64NDArray, **kwargs: ParameterValue
    ) -> Float64NDArray:
        """Protocol for system stepper functions."""
        ...


def _no_step_function(
    time: np.float64,
    state: Float64NDArray,
    **kwargs: ParameterValue,
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
            params: A dictionary of parameters to statically define for the system.
            **kwargs: Additional parameters to statically define for the system.

        Returns:
            A stepper function for this system with static parameters defined.

        Notes:
            The `time` and `state` arguments to the underlying stepper function cannot
            be statically defined via params or kwargs. Doing so will result in a
            `TypeError`.

            Additionally, any parameters not defined in the system's stepper function
            signature, or any parameter values that are incompatible with the system
            definition, will also result in a `TypeError`.

        """
        return _checked_partial(
            func=self._stepper,
            forbidden={"time", "state"},
            params=params,
            **kwargs,
        )

    def step(
        self, time: np.float64, state: Float64NDArray, **params: ParameterValue
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

    def requested_parameters(
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> dict[IdentifierString, ParameterRequest]:
        """
        Infer parameter requests from the stepper signature by default.

        Args:
            axes: Resolved runtime axes for the active simulation.

        Returns:
            A mapping of parameter names to runtime parameter requests.

        Notes:
            Parameters with default values are treated as optional scalar inputs.
            Subclasses are encouraged to override this method when they need
            broadcasting behavior or named-axis shapes that cannot be recovered
            from plain Python annotations.
        """
        requests: dict[IdentifierString, ParameterRequest] = {}
        signature = inspect.signature(self._stepper)
        for name, parameter in signature.parameters.items():
            if name in {"time", "state"}:
                continue
            if parameter.kind in {
                inspect.Parameter.VAR_KEYWORD,
                inspect.Parameter.VAR_POSITIONAL,
            }:
                continue
            requests[name] = ParameterRequest(
                name=name,
                optional=parameter.default is not inspect.Parameter.empty,
            )
        return requests

    def model_state(  # noqa: PLR6301
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> ModelStateSpecification | None:
        """
        Return metadata describing how parameters assemble the model state.

        Args:
            axes: Resolved runtime axes for the active simulation.

        Returns:
            The runtime model-state specification, if defined.

        Notes:
            Override this in systems whose evolving state is assembled from configured
            parameter entries. For an age-by-region SEIR system, this could return
            `parameter_names=("S0", "E0", "I0", "R0")` with
            `axes=("region", "age")`, allowing an engine to stack those entries into
            an array shaped `(4, n_region, n_age)` or to keep them in dictionary form
            if that is more natural for the engine.
        """
        return None


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

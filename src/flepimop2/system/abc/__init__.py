"""Abstract class for Dynamic Systems."""

__all__ = [
    "Flepimop2ValidationError",
    "SystemABC",
    "SystemProtocol",
    "ValidationIssue",
    "build",
]

import inspect
import sys
from abc import abstractmethod
from collections.abc import Callable
from typing import Any, Literal

import numpy as np

from flepimop2._utils._checked_partial import _checked_partial, _consolidate_args
from flepimop2._utils._module import _build
from flepimop2.axis import AxisCollection
from flepimop2.configuration import ModuleModel
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.module import ModuleABC
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterRequest,
    ParameterValue,
)
from flepimop2.typing import (
    Float64NDArray,
    IdentifierString,
    StateChangeEnum,
    SystemProtocol,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


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

    def bind(
        self,
        params: dict[IdentifierString, Any] | None = None,
        **kwargs: Any,
    ) -> SystemProtocol:
        """
        Create a particular SystemProtocol.

        `bind()` translates a generic model specification into a particular
        realization. This can include statically defining parameters, but can
        also be called with no arguments to simply get the most flexible
        SystemProtocol available.

        Args:
            params: A dictionary of parameters to statically define for the system.
            **kwargs: Additional parameters to statically define for the system.

        Returns:
            A stepper function for this system with static parameters defined.

        Raises:
            TypeError: If params contains "time" or "state" keys,
                or parameters not in the System definition,
                or if the parameter values are incompatible with System definition.
        """  # noqa: DOC502
        checked_pars = _consolidate_args(
            forbidden={"time", "state"}, params=params, **kwargs
        )
        return self._bind_impl(params=checked_pars)

    @abstractmethod
    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None
    ) -> SystemProtocol:
        """
        Abstract method to create a particular SystemProtocol.

        Concrete implementations of SystemABC must implement this method to
        define how to create a SystemProtocol with static parameters.

        Args:
            params: A dictionary of parameters to statically define for the System.

        Returns:
            A SystemProtocol for this System with static parameters defined.

        Raises:
            TypeError: If params contains "time" or "state" keys,
                or parameters not in the System definition,
                or if the parameter values are incompatible with System definition.
        """
        msg = "Concrete implementations must implement _bind_impl."
        raise NotImplementedError(msg)

    def step(
        self, time: np.float64, state: Float64NDArray, **params: ParameterValue
    ) -> Float64NDArray:
        """
        Perform a single step of the system's dynamics.

        Details:
            This method is only intended to be used for troubleshooting. Calling
            this method simply routes to `bind()` and then invokes the resulting
            SystemProtocol with the provided arguments.

        Args:
            time: The current time.
            state: The current state array.
            **params: Additional parameters for the stepper.

        Returns:
            The next state array after one step.
        """
        return self.bind()(time, state, **params)

    def requested_parameters(
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> dict[IdentifierString, ParameterRequest]:
        """
        Infer parameter requests from the unbound stepper signature by default.

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
        signature = inspect.signature(self.bind())
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


class _AdapterSystem(SystemABC):
    """A `SystemABC` which wraps a user-defined function."""

    module: Literal["flepimop2.system.wrapper"] = "flepimop2.system.wrapper"
    state_change: StateChangeEnum
    stepper: SystemProtocol
    options: dict[IdentifierString, Any]
    _requested_parameters_func: (
        Callable[[AxisCollection], dict[IdentifierString, ParameterRequest]] | None
    )
    _model_state_func: Callable[[AxisCollection], ModelStateSpecification | None] | None

    def __init__(
        self,
        state_change: StateChangeEnum,
        stepper: SystemProtocol,
        options: dict[IdentifierString, Any] | None = None,
        requested_parameters: (
            Callable[[AxisCollection], dict[IdentifierString, ParameterRequest]] | None
        ) = None,
        model_state: (
            Callable[[AxisCollection], ModelStateSpecification | None] | None
        ) = None,
    ) -> None:
        """
        Initialize the AdapterSystem with a state change and a stepper.

        Args:
            state_change: The type of state change for the system.
            stepper: A user-defined function that implements the system's dynamics.
            options: Optional dictionary of additional information about the system.
            requested_parameters: Optional callback declaring runtime parameter
                requests for the system.
            model_state: Optional callback declaring how parameters assemble the
                evolving model state.

        """
        self.state_change = state_change
        self.stepper = stepper
        self.options = options or {}
        self._requested_parameters_func = requested_parameters
        self._model_state_func = model_state

    @override
    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None
    ) -> SystemProtocol:
        return _checked_partial(
            func=self.stepper,
            params=params,
        )

    @override
    def requested_parameters(
        self,
        axes: AxisCollection,
    ) -> dict[IdentifierString, ParameterRequest]:
        """Return adapter parameter requests from an explicit callback when provided."""
        if self._requested_parameters_func is not None:
            return self._requested_parameters_func(axes)
        return super().requested_parameters(axes)

    @override
    def model_state(self, axes: AxisCollection) -> ModelStateSpecification | None:
        """Return adapter model-state metadata from an explicit callback."""
        if self._model_state_func is not None:
            return self._model_state_func(axes)
        return super().model_state(axes)


def build(config: dict[IdentifierString, Any] | ModuleModel) -> SystemABC:
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


def wrap(
    stepper: SystemProtocol,
    state_change: StateChangeEnum,
    options: dict[IdentifierString, Any] | None = None,
    *,
    requested_parameters: (
        Callable[[AxisCollection], dict[IdentifierString, ParameterRequest]] | None
    ) = None,
    model_state: (
        Callable[[AxisCollection], ModelStateSpecification | None] | None
    ) = None,
) -> SystemABC:
    """
    Adapt a user-defined function into a `SystemABC`.

    Args:
        stepper: A user-defined function that implements the system's dynamics.
        state_change: The type of state change for the system.
        options: Optional dictionary of additional information about the system.
        requested_parameters: Optional callback declaring runtime parameter requests
            for the system.
        model_state: Optional callback declaring how parameters assemble the evolving
            model state.

    Returns:
        A `SystemABC` instance that wraps the provided stepper function.

    Raises:
        TypeError: If the provided stepper function does not conform to the expected
            signature or if offered an erroneous state_change.
    """
    if not isinstance(state_change, StateChangeEnum):
        msg = (
            "state_change must be an instance of StateChangeEnum; "
            f"got {type(state_change)}."
        )
        raise TypeError(msg)
    if state_change == StateChangeEnum.ERROR:
        msg = "state_change cannot be StateChangeEnum.ERROR for a valid system."
        raise TypeError(msg)

    return _AdapterSystem(
        state_change=state_change,
        stepper=stepper,
        options=options,
        requested_parameters=requested_parameters,
        model_state=model_state,
    )

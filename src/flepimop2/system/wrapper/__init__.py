"""A `SystemABC` which wraps a user-defined script file."""

__all__ = ["WrapperSystem"]

from collections.abc import Callable
from pathlib import Path
from typing import Literal, Self

from pydantic import model_validator

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.axis import AxisCollection
from flepimop2.configuration import ModuleModel
from flepimop2.parameter.abc import ModelStateSpecification, ParameterRequest
from flepimop2.system.abc import SystemABC
from flepimop2.typing import StateChangeEnum


class WrapperSystem(ModuleModel, SystemABC):
    """A `SystemABC` which wraps a user-defined script file."""

    module: Literal["flepimop2.system.wrapper"] = "flepimop2.system.wrapper"
    state_change: StateChangeEnum
    script: Path
    _requested_parameters_func: (
        Callable[[AxisCollection], dict[str, ParameterRequest]] | None
    ) = None
    _model_state_func: (
        Callable[[AxisCollection], ModelStateSpecification | None] | None
    ) = None

    @model_validator(mode="after")
    def _validate_stepper(self) -> Self:
        """
        Validator to load and validate the stepper function from the script file.

        Returns:
            The validated `WrapperSystem` instance.

        Raises:
            AttributeError: If the module does not have a valid 'stepper' function.
        """
        mod = _load_module(self.script, "flepimop2.system.wrapped")
        if not _validate_function(mod, "stepper"):
            msg = f"Module at {self.script} does not have a valid 'stepper' function."
            raise AttributeError(msg)
        self._stepper = mod.stepper
        if _validate_function(mod, "requested_parameters"):
            self._requested_parameters_func = mod.requested_parameters
        if _validate_function(mod, "model_state"):
            self._model_state_func = mod.model_state
        return self

    def requested_parameters(
        self,
        axes: AxisCollection,
    ) -> dict[str, ParameterRequest]:
        """Return wrapper-system parameter requests from the script when provided."""
        if self._requested_parameters_func is not None:
            return self._requested_parameters_func(axes)
        return super().requested_parameters(axes)

    def model_state(self, axes: AxisCollection) -> ModelStateSpecification | None:
        """Return wrapper-system state metadata from the script when provided."""
        if self._model_state_func is not None:
            return self._model_state_func(axes)
        return super().model_state(axes)

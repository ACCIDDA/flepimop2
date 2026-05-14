# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""A `SystemABC` which wraps a user-defined script file."""

import functools
import inspect
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)

from flepimop2._utils._checked_partial import _checked_partial
from flepimop2._utils._inspect import _is_ndarray_annotation, _unwrap_annotation
from flepimop2._utils._module import _as_dict as _as_dict
from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.axis import AxisCollection
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterRequest,
    ParameterValue,
)
from flepimop2.system.abc import SystemABC
from flepimop2.typing import (
    Float64NDArray,
    IdentifierString,
    StateChangeEnum,
    SystemProtocol,
    as_system_protocol,
)


class _ParameterRequestConfiguration(BaseModel):
    """
    Declarative wrapper-system parameter request configuration.

    Attributes:
        axes: Ordered axis names the parameter should align with.
        broadcast: Whether scalar parameter values may broadcast to `axes`.
        optional: Whether the system may omit this parameter and rely on a
            stepper default.
    """

    axes: tuple[IdentifierString, ...] = ()
    broadcast: bool = False
    optional: bool = False


class _ModelStateConfiguration(BaseModel):
    """
    Declarative wrapper-system model-state configuration.

    Attributes:
        parameter_names: Ordered parameter names used to assemble model state.
        axes: Ordered axis names shared by each state entry.
        broadcast: Whether scalar state entries may broadcast to `axes`.
        labels: Optional human-readable labels for state entries.
    """

    parameter_names: tuple[IdentifierString, ...]
    axes: tuple[IdentifierString, ...] = ()
    broadcast: bool = False
    labels: tuple[str, ...] | None = None


class WrapperSystem(SystemABC, module="wrapper"):
    """
    A `SystemABC` that wraps a user-defined Python script file.

    The script must define a `stepper` function compatible with
    `SystemProtocol`.

    Attributes:
        script: Path to the Python script containing the `stepper` function.
        state_change: State-change convention declared by the wrapped system.
        options: Opaque extra options exposed through `ModuleBase.option`.
        requested_parameters: Optional declarative runtime parameter metadata.
        model_state: Optional declarative model-state metadata.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    script: Path
    state_change: StateChangeEnum
    parameter_requests: (
        dict[IdentifierString, _ParameterRequestConfiguration] | None
    ) = Field(default=None, alias="requested_parameters")
    model_state_config: _ModelStateConfiguration | None = Field(
        default=None, alias="model_state"
    )

    _stepper: Any = PrivateAttr(default=None)
    _requested_parameters_func: Any = PrivateAttr(default=None)
    _model_state_func: Any = PrivateAttr(default=None)

    @field_validator("parameter_requests", mode="before")
    @classmethod
    def _normalize_requested_parameters(
        cls,
        value: object,
    ) -> object:
        """
        Normalize shorthand parameter-request entries to empty dictionaries.

        This allows YAML values such as `beta:`, `beta: ~`, or `beta: null` to
        resolve to the default `ParameterRequest` configuration.

        Returns:
            The original value when no normalization is needed, or a copy of the
            parameter mapping with `None` entries replaced by empty dictionaries.

        Examples:
            >>> from flepimop2.system.wrapper import WrapperSystem
            >>> WrapperSystem._normalize_requested_parameters(None) is None
            True
            >>> WrapperSystem._normalize_requested_parameters({"beta": None})
            {'beta': {}}
            >>> WrapperSystem._normalize_requested_parameters({
            ...     "beta": None,
            ...     "gamma": {"axes": ["age"], "broadcast": True},
            ... })
            {'beta': {}, 'gamma': {'axes': ['age'], 'broadcast': True}}
        """
        if value is None:
            return value
        if not isinstance(value, dict):
            return value
        return {name: {} if spec is None else spec for name, spec in value.items()}

    @model_validator(mode="after")
    def _load_and_adapt_stepper(self) -> Self:
        """
        Load the script, validate the stepper, and build runtime callbacks.

        Returns:
            This instance, after wiring up the stepper and callbacks.

        Raises:
            AttributeError: If the script does not define a valid `stepper` function.
        """
        mod = _load_module(self.script, "flepimop2.system.wrapped")
        if not _validate_function(mod, "stepper"):
            msg = f"Module at {self.script} does not have a valid 'stepper' function."
            raise AttributeError(msg)
        adapted = as_system_protocol(_adapt_wrapper_stepper(mod.stepper))
        self._stepper = adapted
        self._requested_parameters_func = self._build_requested_parameters_func()
        self._model_state_func = self._build_model_state_func()
        return self

    def _build_requested_parameters_func(
        self,
    ) -> Callable[[AxisCollection], dict[IdentifierString, ParameterRequest]] | None:
        """
        Build a runtime parameter-request callback from config.

        Returns:
            A callable that returns the parameter requests, or `None` if no
            `requested_parameters` configuration was provided.
        """
        if self.parameter_requests is None:
            return None
        requests = {
            name: ParameterRequest(
                name=name,
                axes=spec.axes,
                broadcast=spec.broadcast,
                optional=spec.optional,
            )
            for name, spec in self.parameter_requests.items()
        }

        def _fn(_axes: AxisCollection) -> dict[IdentifierString, ParameterRequest]:
            return requests.copy()

        return _fn

    def _build_model_state_func(
        self,
    ) -> Callable[[AxisCollection], ModelStateSpecification] | None:
        """
        Build a runtime model-state callback from config.

        Returns:
            A callable that returns the model-state specification, or `None` if no
            `model_state` configuration was provided.
        """
        if self.model_state_config is None:
            return None
        specification = ModelStateSpecification(
            parameter_names=self.model_state_config.parameter_names,
            axes=self.model_state_config.axes,
            broadcast=self.model_state_config.broadcast,
            labels=self.model_state_config.labels,
        )

        def _fn(_axes: AxisCollection) -> ModelStateSpecification:
            return specification

        return _fn

    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None
    ) -> SystemProtocol:
        return _checked_partial(func=self._stepper, params=params)

    def requested_parameters(
        self,
        axes: AxisCollection,
    ) -> dict[IdentifierString, ParameterRequest]:
        """Return wrapper parameter requests from an explicit callback when provided."""
        if self._requested_parameters_func is not None:
            return self._requested_parameters_func(axes)  # type: ignore[no-any-return]
        return super().requested_parameters(axes)

    def model_state(self, axes: AxisCollection) -> ModelStateSpecification | None:
        """Return wrapper model-state metadata from an explicit callback."""
        if self._model_state_func is not None:
            return self._model_state_func(axes)  # type: ignore[no-any-return]
        return super().model_state(axes)


def _binding_annotation(annotation: object) -> object:
    """Return a bind-time validator compatible with `_checked_partial`."""
    annotation = _unwrap_annotation(annotation)
    if annotation in {inspect.Parameter.empty, Any}:
        return Any
    if annotation is ParameterValue:
        return ParameterValue
    if annotation in {float, int}:

        def _validate_scalar(value: object) -> object:
            if isinstance(value, ParameterValue):
                value.item()
                return value
            annotation(value)
            return value

        _validate_scalar.__name__ = f"coercible_{annotation.__name__}"
        return _validate_scalar
    if _is_ndarray_annotation(annotation):

        def _validate_array(value: object) -> object:
            if isinstance(value, ParameterValue):
                return value
            return np.asarray(value, dtype=np.float64)

        _validate_array.__name__ = "coercible_ndarray"
        return _validate_array
    return Any


def _coerce_parameter_value(
    name: str,
    annotation: object,
    value: object,
) -> object:
    """
    Coerce `ParameterValue` objects to the wrapped stepper's expected payload.

    Returns:
        The original value for pass-through annotations, or an unwrapped scalar/array
        payload when the wrapped stepper expects one.

    Raises:
        TypeError: If a scalar annotation receives a non-scalar `ParameterValue`.
    """
    if not isinstance(value, ParameterValue):
        return value
    annotation = _unwrap_annotation(annotation)
    if annotation in {float, int}:
        try:
            scalar = value.item()
        except ValueError as exc:
            msg = (
                f"Parameter '{name}' expects a scalar {annotation.__name__}, "
                f"but received shape {value.shape.sizes}."
            )
            raise TypeError(msg) from exc
        if annotation is int and not math.isclose(scalar, round(scalar)):
            msg = (
                f"Parameter '{name}' is annotated as int "
                f"but received non-integer value {scalar}."
            )
            raise TypeError(msg)
        return annotation(scalar)
    if _is_ndarray_annotation(annotation):
        return value.value
    return value


def _adapt_wrapper_stepper(stepper: Callable[..., Any]) -> Callable[..., Any]:
    """
    Adapt a wrapped stepper to coerce `ParameterValue` inputs by annotation.

    Returns:
        A callable with the wrapped stepper's signature that unwraps
        `ParameterValue` arguments into scalars or arrays as requested by the
        wrapped stepper's annotations.
    """
    raw_signature = inspect.signature(stepper)
    adapted_parameters = []
    for name, parameter in raw_signature.parameters.items():
        if name in {"time", "state"} or parameter.kind in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }:
            adapted_parameters.append(parameter)
            continue
        adapted_parameters.append(
            parameter.replace(annotation=_binding_annotation(parameter.annotation))
        )
    adapted_signature = raw_signature.replace(parameters=adapted_parameters)

    @functools.wraps(stepper)
    def _adapted_stepper(*args: Any, **kwargs: Any) -> Float64NDArray:
        bound = raw_signature.bind_partial(*args, **kwargs)
        for name, parameter in raw_signature.parameters.items():
            if name in {"time", "state"} or name not in bound.arguments:
                continue
            bound.arguments[name] = _coerce_parameter_value(
                name,
                parameter.annotation,
                bound.arguments[name],
            )
        return stepper(*bound.args, **bound.kwargs)  # type: ignore[no-any-return]

    _adapted_stepper.__signature__ = adapted_signature  # type: ignore[attr-defined]
    return _adapted_stepper

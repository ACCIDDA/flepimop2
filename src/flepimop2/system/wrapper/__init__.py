"""A `SystemABC` which wraps a user-defined script file."""

import functools
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, Literal, cast, get_args, get_origin

import numpy as np
from pydantic import BaseModel, Field, field_validator

from flepimop2._utils._module import _as_dict, _load_module, _validate_function
from flepimop2.axis import AxisCollection
from flepimop2.configuration import ModuleModel
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterRequest,
    ParameterValue,
)
from flepimop2.system.abc import SystemABC
from flepimop2.system.abc import wrap as system_wrap
from flepimop2.typing import (
    Float64NDArray,
    IdentifierString,
    StateChangeEnum,
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


class _WrapperSystemConfig(ModuleModel):
    """
    Validated configuration for `flepimop2.system.wrapper`.

    Attributes:
        module: Wrapper-system module identifier.
        script: Path to the wrapped Python script containing `stepper`.
        state_change: State-change convention declared by the wrapped system.
        options: Opaque wrapper-system options exposed through `ModuleABC.option`.
        requested_parameters: Optional declarative runtime parameter metadata.
        model_state: Optional declarative model-state metadata.
    """

    module: Literal["flepimop2.system.wrapper", "wrapper"] = "flepimop2.system.wrapper"
    script: Path
    state_change: StateChangeEnum
    options: dict[IdentifierString, Any] = Field(default_factory=dict)
    requested_parameters: (
        dict[IdentifierString, _ParameterRequestConfiguration] | None
    ) = None
    model_state: _ModelStateConfiguration | None = None

    @field_validator("requested_parameters", mode="before")
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
            >>> config = _WrapperSystemConfig.model_validate({
            ...     "module": "wrapper",
            ...     "script": "system.py",
            ...     "state_change": "flow",
            ... })
            >>> config.requested_parameters is None
            True
            >>> config = _WrapperSystemConfig.model_validate({
            ...     "module": "wrapper",
            ...     "script": "system.py",
            ...     "state_change": "flow",
            ...     "requested_parameters": {"beta": None},
            ... })
            >>> config.requested_parameters["beta"]
            _ParameterRequestConfiguration(axes=(), broadcast=False, optional=False)
            >>> config = _WrapperSystemConfig.model_validate({
            ...     "module": "wrapper",
            ...     "script": "system.py",
            ...     "state_change": "flow",
            ...     "requested_parameters": {
            ...         "beta": None,
            ...         "gamma": {"axes": ["age"], "broadcast": True},
            ...     },
            ... })
            >>> config.requested_parameters["beta"]
            _ParameterRequestConfiguration(axes=(), broadcast=False, optional=False)
            >>> config.requested_parameters["gamma"]
            _ParameterRequestConfiguration(axes=('age',), broadcast=True, optional=False)
        """  # noqa: E501
        if value is None:
            return value
        if not isinstance(value, dict):
            return value
        return {name: {} if spec is None else spec for name, spec in value.items()}

    def requested_parameters_function(
        self,
    ) -> Callable[[AxisCollection], dict[IdentifierString, ParameterRequest]] | None:
        """
        Build a runtime parameter-request callback from config.

        Returns:
            A callback returning configured parameter requests, or `None` when the
            wrapper configuration omits `requested_parameters`.
        """
        if self.requested_parameters is None:
            return None
        requests = {
            name: ParameterRequest(
                name=name,
                axes=spec.axes,
                broadcast=spec.broadcast,
                optional=spec.optional,
            )
            for name, spec in self.requested_parameters.items()
        }

        def _requested_parameters(
            _axes: AxisCollection,
        ) -> dict[IdentifierString, ParameterRequest]:
            return requests.copy()

        return _requested_parameters

    def model_state_function(
        self,
    ) -> Callable[[AxisCollection], ModelStateSpecification] | None:
        """
        Build a runtime model-state callback from config.

        Returns:
            A callback returning configured model-state metadata, or `None` when the
            wrapper configuration omits `model_state`.
        """
        if self.model_state is None:
            return None
        specification = ModelStateSpecification(
            parameter_names=self.model_state.parameter_names,
            axes=self.model_state.axes,
            broadcast=self.model_state.broadcast,
            labels=self.model_state.labels,
        )

        def _model_state(_axes: AxisCollection) -> ModelStateSpecification:
            return specification

        return _model_state


def _unwrap_annotation(annotation: object) -> object:
    """
    Strip simple wrappers like `Annotated[...]` from runtime annotations.

    Returns:
        The innermost annotation after peeling supported typing wrappers.
    """
    while get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]
    return annotation


def _is_ndarray_annotation(annotation: object) -> bool:
    """Return whether an annotation refers to a NumPy ndarray payload."""
    annotation = _unwrap_annotation(annotation)
    return annotation is np.ndarray or get_origin(annotation) is np.ndarray


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
        return cast("Float64NDArray", stepper(*bound.args, **bound.kwargs))

    _adapted_stepper.__signature__ = adapted_signature  # type: ignore[attr-defined]
    return _adapted_stepper


def build(config: dict[IdentifierString, Any] | ModuleModel) -> SystemABC:
    """
    Build a `SystemABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance.

    Returns:
        The constructed system instance.

    Raises:
        AttributeError: If the loaded module does not have a valid 'stepper' function.
    """
    wrapper_config = _WrapperSystemConfig.model_validate(_as_dict(config))
    mod = _load_module(wrapper_config.script, "flepimop2.system.wrapped")
    if not _validate_function(mod, "stepper"):
        msg = (
            f"Module at {wrapper_config.script} does not have a valid "
            "'stepper' function."
        )
        raise AttributeError(msg)
    stepper = as_system_protocol(_adapt_wrapper_stepper(mod.stepper))
    options = wrapper_config.options.copy()
    options["script"] = wrapper_config.script
    return system_wrap(
        stepper,
        wrapper_config.state_change,
        options,
        requested_parameters=wrapper_config.requested_parameters_function(),
        model_state=wrapper_config.model_state_function(),
    )

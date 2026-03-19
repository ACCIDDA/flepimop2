"""Stepper function for SIR model integration tests."""

import functools
import sys
from typing import Any

import numpy as np

from flepimop2.axis import AxisCollection
from flepimop2.configuration import ModuleModel
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
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


def stepper(
    time: np.float64,  # noqa: ARG001
    state: Float64NDArray,
    *,
    beta: ParameterValue,
    gamma: ParameterValue | None = None,
    **kwargs: Any,  # noqa: ARG001
) -> Float64NDArray:
    """
    ODE for an age-stratified SIR model with isolated age groups.

    Args:
        time: Current time (not used in this model).
        state: Current state array shaped `(3, n_age)`.
        beta: Age-specific transmission rates from the external provider.
        gamma: The recovery-rate parameter.
        **kwargs: Additional parameters.

    Returns:
        Next state array after one step with shape `(3, n_age)`.
    """
    y_s, y_i, y_r = np.asarray(state, dtype=float)
    gamma_value = gamma.item() if gamma is not None else 0.1
    totals = y_s + y_i + y_r
    infection = beta.value * y_s * y_i / totals
    recovery = gamma_value * y_i
    return np.vstack((-infection, infection - recovery, recovery)).astype(np.float64)


class SirSystem(SystemABC):
    """The SIR model system."""

    module = "flepimop2.system.sir"
    state_change = StateChangeEnum.FLOW

    @override
    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None
    ) -> SystemProtocol:
        return functools.partial(stepper, **(params or {}))

    def requested_parameters(
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> dict[str, ParameterRequest]:
        """
        Declare the non-state parameters consumed by the SIR stepper.

        Returns:
            Runtime parameter requests for the SIR stepper.
        """
        return {
            "beta": ParameterRequest(name="beta", axes=("age",)),
            "gamma": ParameterRequest(name="gamma", optional=True),
        }

    def model_state(
        self,
        axes: AxisCollection,  # noqa: ARG002
    ) -> ModelStateSpecification:
        """
        Declare how parameter entries assemble the SIR state vector.

        Returns:
            The model-state specification for the SIR system.
        """
        return ModelStateSpecification(
            parameter_names=("s0", "i0", "r0"),
            axes=("age",),
            labels=("S", "I", "R"),
        )


def build(config: dict[str, Any] | ModuleModel) -> SirSystem:  # noqa: ARG001
    """
    Build an SIR system.

    Returns:
        An instance of the SIR system.
    """
    return SirSystem()

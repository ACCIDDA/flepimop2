"""A wrapper-system asset with explicit runtime parameter contracts."""

from flepimop2.axis import AxisCollection
from flepimop2.parameter.abc import (
    ModelStateSpecification,
    ParameterRequest,
    ParameterValue,
)
from flepimop2.typing import Float64NDArray


def stepper(
    time: float,  # noqa: ARG001
    state: Float64NDArray,
    beta: ParameterValue,
    gamma: ParameterValue,
) -> Float64NDArray:
    """
    A dummy stepper using both scalar and age-indexed parameters.

    Returns:
        The updated state.
    """
    return state + beta.item() + gamma.value


def requested_parameters(
    axes: AxisCollection,  # noqa: ARG001
) -> dict[str, ParameterRequest]:
    """
    Declare one scalar and one age-indexed parameter.

    Returns:
        Runtime parameter requests for the dummy system.
    """
    return {
        "beta": ParameterRequest(name="beta"),
        "gamma": ParameterRequest(
            name="gamma",
            axes=("age",),
            broadcast=True,
        ),
    }


def model_state(axes: AxisCollection) -> ModelStateSpecification:  # noqa: ARG001
    """
    Assemble the model state from parameter entries under `parameters`.

    Returns:
        The model-state specification for the dummy system.
    """
    return ModelStateSpecification(
        parameter_names=("s0", "i0", "r0"),
        axes=("age",),
        broadcast=True,
        labels=("S", "I", "R"),
    )

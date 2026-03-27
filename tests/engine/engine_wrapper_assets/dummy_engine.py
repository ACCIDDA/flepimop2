"""A dummy stepper function for testing `WrapperEngine`."""

from collections.abc import Mapping

import numpy as np

from flepimop2.configuration import IdentifierString
from flepimop2.parameter.abc import ModelStateSpecification, ParameterValue
from flepimop2.system.abc import SystemProtocol
from flepimop2.typing import Float64NDArray


def runner(  # noqa: PLR0913
    f: SystemProtocol,
    times: Float64NDArray,
    initial_state: dict[IdentifierString, ParameterValue],
    params: Mapping[IdentifierString, ParameterValue],
    *,
    model_state: ModelStateSpecification | None = None,
    accumulate: bool = False,
) -> Float64NDArray:
    """
    A dummy runner function for testing purposes: only evaluates stepper at times.

    Args:
        f: The stepper function.
        times: Array of time points.
        initial_state: Structured initial-state entries.
        params: Additional parameters for the stepper.
        model_state: Specification describing how to order the initial-state
            entries into a numeric state array.
        accumulate: Whether to accumulate results over time.

    Returns:
        The state array evaluated at each time point.

    Raises:
        ValueError: If `model_state` is not provided.
    """
    if model_state is None:
        msg = "model_state must be provided to assemble the initial state."
        raise ValueError(msg)
    state = np.stack([
        initial_state[name].value for name in model_state.parameter_names
    ]).astype(np.float64)
    flat_state = state.reshape(-1)
    res = np.zeros((len(times), flat_state.size + 1), dtype=np.float64)
    res[:, 0] = times
    res[0, 1:] = flat_state
    current_state = state
    for i, t in enumerate(times[1:], start=1):
        next_state = f(t, current_state, **params)
        current_state = current_state + next_state if accumulate else next_state
        res[i, 1:] = current_state.reshape(-1)
    return res

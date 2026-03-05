"""A dummy stepper function for testing `WrapperEngine`."""

from typing import Any

import numpy as np

from flepimop2.configuration import IdentifierString
from flepimop2.system.abc import SystemProtocol
from flepimop2.typing import Float64NDArray


def runner(
    f: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    *,
    accumulate: bool,
) -> Float64NDArray:
    """
    A dummy runner function for testing purposes: only evaluates stepper at times.

    Args:
        f: The stepper function.
        times: Array of time points.
        state: The current state array.
        params: Additional parameters for the stepper.
        accumulate: Whether to accumulate results over time.

    Returns:
        The state array evaluated at each time point.
    """
    # numpy array to hold results - first column time, rest state
    res = np.zeros((len(times), len(state) + 1), dtype=np.float64)
    res[:, 0] = times
    res[0, 1:] = state
    for i, t in enumerate(times[1:]):
        if accumulate:
            res[i + 1, 1:] = res[i, 1:]
        res[i + 1, 1:] += f(t, res[i, 1:], **params)
    return res

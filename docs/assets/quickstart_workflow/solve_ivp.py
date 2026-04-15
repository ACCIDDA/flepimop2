"""ODE solver plugin that wraps `scipy.integrate.solve_ivp` for flepimop2 demo."""

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from flepimop2.system.abc import SystemProtocol
from flepimop2.typing import Float64NDArray


def runner(
    fun: SystemProtocol,
    times: Float64NDArray,
    y0: Float64NDArray,
    params: dict[str, Any] | None = None,
    **solver_options: Any,
) -> Float64NDArray:
    """Solve an initial value problem using scipy.solve_ivp.

    Args:
        fun (SystemProtocol): A function that computes derivatives.
        times (Float64NDArray): sequence of time points where we evaluate the
          solution. Must have length >= 1.
        y0 (Float64NDArray): Initial condition.
        params: Optional dict of keyword parameters forwarded to fun.
        **solver_options: Additional keyword options forwarded to
          scipy.integrate.solve_ivp.

    Returns:
        FloatArray: Array with time and state values evaluated at `times`.
        Each row is [t, y...].

    Raises:
        ValueError: If `times` is not a 1D sequence of time points with length >= 1, or
            if the first time point is negative.

    """
    if not (times.ndim == 1 and times.size >= 1):
        msg = "times must be a 1D sequence of time points"
        raise ValueError(msg)

    times.sort()

    t0, tf = 0.0, times[-1]
    if times[0] < t0:
        msg = f"times[0] must be >= 0; got times[0]={times[0]}"
        raise ValueError(msg)

    args = tuple(val for val in params.values()) if params is not None else None
    result = solve_ivp(
        fun,
        (t0, tf),
        y0,
        t_eval=times,
        args=args,  # type: ignore[arg-type]
        **solver_options,
    )
    return np.transpose(np.vstack((result.t, result.y)))

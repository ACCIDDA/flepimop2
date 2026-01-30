"""ODE solver plugin that wraps `scipy.integrate.solve_ivp` for flepimop2 demo."""

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from flepimop2.system.abc import SystemProtocol


def runner(
    fun: SystemProtocol,
    times: NDArray[np.float64],
    y0: NDArray[np.float64],
    params: dict[str, Any] | None = None,
    **solver_options: Any,
) -> NDArray[np.float64]:
    """Solve an initial value problem using scipy.solve_ivp.

    Args:
        fun (SystemProtocol): A function that computes derivatives.
        times (NDArray[np.float64]): sequence of time points where we evaluate the
          solution. Must have length >= 1.
        y0 (NDArray[np.float64]): Initial condition.
        params: Optional dict of keyword parameters forwarded to fun.
        **solver_options: Additional keyword options forwarded to
          scipy.integrate.solve_ivp.

    Returns:
        FloatArray: Array with time and state values evaluated at `times`.
        Each row is [t, y...].

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
    result = solve_ivp(fun, (t0, tf), y0, t_eval=times, args=args, **solver_options)
    return np.transpose(np.vstack((result.t, result.y)))

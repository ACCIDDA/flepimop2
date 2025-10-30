"""Abstract class for Engines to evolve Dynamic Systems."""

from abc import ABC
from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2._utils import _load_builder
from flepimop2.engine.protocol import EngineProtocol
from flepimop2.system import SystemABC, SystemProtocol


def _no_run_func(
    stepper: SystemProtocol,
    times: NDArray[np.float64],
    state: NDArray[np.float64],
    params: dict[str, Any],
    **kwargs: Any,
) -> NDArray[np.float64]:
    msg = "EngineABC::_runner must be provided by a concrete implementation."
    raise NotImplementedError(msg)


class EngineABC(ABC):
    """Abstract class for Engines to evolve Dynamic Systems."""

    def __init__(self, runner: EngineProtocol = _no_run_func) -> None:
        """
        Initialize an `EngineABC` from a runner function.

        Args:
            runner: The runner function for the engine. Defaults to a function that
                raises `NotImplementedError`.
        """
        self._runner = runner

    _runner: EngineProtocol

    def run(
        self,
        system: SystemABC,
        eval_times: NDArray[np.float64],
        initial_state: NDArray[np.float64],
        params: dict[str, Any],
        **kwargs: Any,
    ) -> NDArray[np.float64]:
        """
        Run the engine with the provided system and parameters.

        Args:
            system: The dynamic system to be evolved.
            eval_times: Array of time points for evaluation.
            initial_state: The initial state array.
            params: Additional parameters for the stepper.
            **kwargs: Additional keyword arguments for the engine.

        Returns:
            The evolved time x state array.
        """
        return self._runner(
            system.stepper,
            eval_times,
            initial_state,
            params,
            **kwargs,
        )


def build(config: dict[str, Any] | EngineProtocol) -> EngineABC:
    """Build a `EngineABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a EngineProtocol. In dict mode, it contains
            a 'module' key, it will be used to lookup the Engine module path. The module
            will have "flepimop2.engine." prepended.

    Returns:
        The constructed engine instance.

    Raises:
        TypeError: If the built engine is not an instance of EngineABC.
    """
    if isinstance(config, EngineProtocol):
        return EngineABC(config)
    builder = _load_builder(f"flepimop2.engine.{config.pop('module', 'wrapper')}")
    engine = builder.build(**config)
    if not isinstance(engine, EngineABC):
        msg = "The built engine is not an instance of EngineABC."
        raise TypeError(msg)
    return engine

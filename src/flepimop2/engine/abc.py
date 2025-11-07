"""Abstract class for Engines to evolve Dynamic Systems."""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2._utils import _load_builder
from flepimop2.configuration import ModuleModel
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


class EngineABC:
    """Abstract class for Engines to evolve Dynamic Systems."""

    _runner: EngineProtocol

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Initialize the EngineABC.

        The default initialization sets the runner to a no-op function. Concrete
        implementations should override this with a valid runner function.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        self._runner = _no_run_func

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
            system._stepper,  # noqa: SLF001
            eval_times,
            initial_state,
            params,
            **kwargs,
        )


def build(config: dict[str, Any] | ModuleModel) -> EngineABC:
    """Build a `EngineABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            engine from.

    Returns:
        The constructed engine instance.

    Raises:
        TypeError: If the built engine is not an instance of EngineABC.
    """
    config = {"module": "wrapper"} | (
        config.model_dump() if isinstance(config, ModuleModel) else config
    )
    builder = _load_builder(f"flepimop2.engine.{config['module']}")
    engine = builder.build(config)
    if not isinstance(engine, EngineABC):
        msg = "The built engine is not an instance of EngineABC."
        raise TypeError(msg)
    return engine

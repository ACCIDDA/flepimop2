"""Abstract class for Engines to evolve Dynamic Systems."""

from typing import Any, Protocol, runtime_checkable

from flepimop2._utils._module import _build
from flepimop2.configuration import IdentifierString, ModuleModel
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import Float64NDArray


def _no_run_func(
    stepper: SystemProtocol,
    times: Float64NDArray,
    state: Float64NDArray,
    params: dict[IdentifierString, Any],
    **kwargs: Any,
) -> Float64NDArray:
    msg = "EngineABC::_runner must be provided by a concrete implementation."
    raise NotImplementedError(msg)


@runtime_checkable
class EngineProtocol(Protocol):
    """Type-definition (Protocol) for engine runner functions."""

    def __call__(
        self,
        stepper: SystemProtocol,
        times: Float64NDArray,
        state: Float64NDArray,
        params: dict[IdentifierString, Any],
        **kwargs: Any,
    ) -> Float64NDArray:
        """Protocol for engine runner functions."""
        ...


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
        eval_times: Float64NDArray,
        initial_state: Float64NDArray,
        params: dict[IdentifierString, Any],
        **kwargs: Any,
    ) -> Float64NDArray:
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

    """
    return _build(config, "engine", "flepimop2.engine.wrapper", EngineABC)

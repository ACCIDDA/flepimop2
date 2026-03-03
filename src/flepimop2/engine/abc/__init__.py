"""Abstract class for Engines to evolve Dynamic Systems."""

__all__ = ["EngineABC", "EngineProtocol", "build"]

from typing import Any, Protocol, Self, runtime_checkable

from flepimop2._utils._module import _build
from flepimop2.configuration import IdentifierString, ModuleModel
from flepimop2.exceptions import ValidationIssue
from flepimop2.module import ModuleABC
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


class EngineABC(ModuleABC):
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

    def build_runner(self) -> EngineProtocol:  # noqa: PLR6301
        """
        Build the runner function for this engine.

        Concrete implementations can override this hook to dynamically construct
        runner functions from instance state.

        Returns:
            The runner function for this engine.
        """
        return _no_run_func

    def build(self) -> Self:
        """
        Build the engine internals required for running systems.

        This method is idempotent and supports three strategies, in order:

        1. Keep an existing instance-level runner if already set.
        2. Reuse a class-level `_runner` callable if provided.
        3. Fallback to `build_runner()` for dynamic construction.

        Returns:
            The built engine instance.

        Raises:
            TypeError: If `build_runner()` returns a non-callable object.
        """
        current_runner = getattr(self, "_runner", _no_run_func)
        if current_runner is not _no_run_func:
            return self

        class_runner = type(self).__dict__.get("_runner")
        if isinstance(class_runner, staticmethod):
            class_runner = class_runner.__func__
        if callable(class_runner) and class_runner is not _no_run_func:
            self._runner = class_runner
            return self

        self._runner = self.build_runner()
        if not callable(self._runner):
            msg = "EngineABC::build_runner must return a callable runner function."
            raise TypeError(msg)
        return self

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
        self.build()
        system.build()
        return self._runner(
            system._stepper,  # noqa: SLF001
            eval_times,
            initial_state,
            params,
            **kwargs,
        )

    def validate_system(  # noqa: PLR6301
        self,
        system: SystemABC,  # noqa: ARG002
    ) -> list[ValidationIssue] | None:
        """
        Validation hook for system properties.

        Args:
            system: The system to validate.

        Returns:
            A list of validation issues, or `None` if not implemented.
        """
        return None


def build(config: dict[str, Any] | ModuleModel) -> EngineABC:
    """Build a `EngineABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            engine from.

    Returns:
        The constructed engine instance.

    """
    return _build(config, "engine", "flepimop2.engine.wrapper", EngineABC)

"""Abstract class for Optimization Targets."""

__all__ = ["TargetABC", "TargetProtocol", "build"]

import inspect
from typing import Any, Protocol, runtime_checkable

import numpy as np

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray


@runtime_checkable
class TargetProtocol(Protocol):
    """Type-definition (Protocol) for target functions."""

    def __call__(
        self, simulated: Float64NDArray, **kwargs: Any
    ) -> Float64NDArray:
        """Protocol for target functions."""
        ...


def _no_target_function(
    simulated: Float64NDArray,
    **kwargs: Any,
) -> Float64NDArray:
    msg = "TargetABC::target must be provided by a concrete implementation."
    raise NotImplementedError(msg)


class TargetABC(ModuleABC):
    """
    Abstract class for Optimization Targets.

    Attributes:
        module: The module name for the target.
        options: Optional dictionary of additional options the target exposes for
            `flepimop2` to take advantage of.
    """

    _evaluator: TargetProtocol

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Initialize the TargetABC.

        The default initialization sets the evaluator to a no-op function.
        Concrete implementations should override this with a valid evaluator
        function.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.
        """
        self._evaluator = _no_target_function

    def evaluate(
        self, simulated: Float64NDArray, **kwargs: Any
    ) -> Float64NDArray:
        """
        Evaluate the target function.

        Args:
            simulated: The simulated observations.
            standard: The standard comparison.
            **kwargs: Additional keyword arguments for the evaluator.

        Returns:
            The next state array after one step.
        """
        return self._evaluator(simulated, **kwargs)


def build(config: dict[str, Any] | ModuleModel) -> TargetABC:
    """
    Build a `TargetABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance.

    Returns:
        The constructed target instance.

    """
    return _build(
        config,
        "target",
        "flepimop2.target.wrapper",
        TargetABC,
    )

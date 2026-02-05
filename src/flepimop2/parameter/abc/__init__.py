"""Abstract base class for parameters."""

__all__ = ["ParameterABC", "build"]

from abc import abstractmethod
from typing import Any

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel
from flepimop2.module import ModuleABC
from flepimop2.typing import Float64NDArray


class ParameterABC(ModuleABC):
    """Abstract base class for parameters."""

    @abstractmethod
    def sample(self) -> Float64NDArray:
        """Sample a value from the parameter.

        Returns:
            A sampled value from the parameter.
        """
        raise NotImplementedError


def build(config: dict[str, Any] | ModuleModel) -> ParameterABC:
    """Build a `ParameterABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            parameter from.

    Returns:
        The constructed parameter instance.

    """
    return _build(config, "parameter", "flepimop2.parameter.wrapper", ParameterABC)  # type: ignore[type-abstract]

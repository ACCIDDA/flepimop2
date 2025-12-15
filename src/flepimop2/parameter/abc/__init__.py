"""Abstract base class for parameters."""

__all__ = ["ParameterABC", "build"]

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from numpy.typing import NDArray

from flepimop2._utils._module import _build
from flepimop2.configuration import ModuleModel


class ParameterABC(ABC):
    """Abstract base class for parameters."""

    @abstractmethod
    def sample(self) -> NDArray[np.float64]:
        """Sample a value from the parameter.

        Returns:
            A sampled value from the parameter.
        """
        raise NotImplementedError


def build(config: dict[str, Any] | ModuleModel) -> ParameterABC:
    """Build a `ParameterABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary or a `ModuleModel` instance to construct the
            engine from.

    Returns:
        The constructed engine instance.

    """
    return _build(config, "parameter", "flepimop2.parameter.wrapper", ParameterABC)  # type: ignore[type-abstract]

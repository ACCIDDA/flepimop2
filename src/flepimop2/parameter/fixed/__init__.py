"""Fixed parameter implementation."""

__all__ = ["FixedParameter"]

from typing import Literal

import numpy as np

from flepimop2.configuration import ModuleModel
from flepimop2.parameter.abc import ParameterABC
from flepimop2.typing import Float64NDArray


class FixedParameter(ModuleModel, ParameterABC):
    """
    Parameter with a fixed value.

    Examples:
        >>> from flepimop2.parameter.fixed import FixedParameter
        >>> param = FixedParameter(value=42.0)
        >>> param.sample()
        array([42.])

    """

    module: Literal["flepimop2.parameter.fixed"] = "flepimop2.parameter.fixed"
    value: float

    def sample(self) -> Float64NDArray:
        """
        Return the fixed value of the parameter.

        Returns:
            The fixed numeric value of the parameter.
        """
        return np.array([self.value], dtype=np.float64)
